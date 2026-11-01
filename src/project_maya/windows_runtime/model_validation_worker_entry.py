"""Fixed M03a worker with bounded failure-only startup diagnostics on stderr."""
import sys


class StartupDiagnostic:
    stages = frozenset(('bootstrap_preflight', 'bootstrap_imports', 'bootstrap_paths', 'worker_import',
        'worker_preflight', 'worker_root', 'dependency_readback', 'canonical_preflight', 'config_read',
        'policy_read', 'literals_read', 'audit_open', 'service_config', 'request_build', 'request_open',
        'request_write', 'request_flush', 'request_sync', 'request_close', 'request_write_checked',
        'service_import', 'service_construct', 'ready_send', 'ready_sent'))
    errors = frozenset(('ProtocolError', 'HostFileError', 'ValueError', 'OSError', 'PermissionError',
        'FileNotFoundError', 'ModuleNotFoundError', 'ImportError', 'TypeError', 'AttributeError',
        'RuntimeError', 'KeyError', 'UnicodeError', 'UnicodeDecodeError', 'UnicodeEncodeError'))

    def __init__(self):
        self.stage = 'bootstrap_preflight'
        self.sent = self.ready = False

    def mark(self, stage):
        self.stage = stage if stage in self.stages else 'bootstrap_preflight'
        if stage == 'ready_sent':
            self.ready = True

    def fail(self, error=None):
        if self.sent or self.ready:
            return
        self.sent = True
        code = 'PreflightRejected' if error is None else type(error).__name__
        if code not in self.errors and code != 'PreflightRejected':
            code = 'OtherError'
        # Never include exception messages, tracebacks, paths or request data.
        try:
            sys.stderr.write('MAYA_WORKER_STARTUP_V1|' + self.stage + '|' + code + '\n')
            sys.stderr.flush()
        except Exception:
            pass


def launch(*, wrong_route=False, wrong_attempt=False, wrong_body=False, expire_grant=False, revoke_grant=False, replay_grant=False, same_client_budget=False, recreated_client_budget=False):
    diagnostic = StartupDiagnostic()
    if (sys.platform != 'win32' or sys.version_info[:3] != (3, 13, 14) or not all(
            (sys.flags.isolated, sys.flags.no_site, sys.flags.dont_write_bytecode))):
        diagnostic.fail()
        return 2
    try:
        diagnostic.mark('bootstrap_imports')
        import os
        from pathlib import Path
        diagnostic.mark('bootstrap_paths')
        runtime = Path(__file__).resolve().parent
        if Path.cwd().resolve() != runtime.parent/'host' or os.environ.get('HERMES_DISABLE_LAZY_INSTALLS') != '1':
            diagnostic.fail()
            return 2
        sys.path[:0] = [str(runtime), str(runtime/'dependencies')]
        diagnostic.mark('worker_import')
        from project_maya.bridge.model_worker import main
        if any(type(mode) is not bool for mode in (wrong_route, wrong_attempt, wrong_body, expire_grant, revoke_grant, replay_grant, same_client_budget, recreated_client_budget)) or sum((wrong_route, wrong_attempt, wrong_body, expire_grant, revoke_grant, replay_grant, same_client_budget, recreated_client_budget)) > 1:
            raise ValueError()
        return main(wrong_model=not (wrong_route or wrong_attempt or wrong_body or expire_grant or revoke_grant or replay_grant or same_client_budget or recreated_client_budget), wrong_route=wrong_route,
            wrong_attempt=wrong_attempt, wrong_body=wrong_body, expire_grant=expire_grant, revoke_grant=revoke_grant, replay_grant=replay_grant, same_client_budget=same_client_budget, recreated_client_budget=recreated_client_budget, startup=diagnostic)
    except Exception as error:
        diagnostic.fail(error)
        return 1


if __name__ == "__main__":
    raise SystemExit(launch())

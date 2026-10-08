"""Frozen combined failure bodies; explicit fresh-host publisher verification."""
from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import io
import json
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publisher_combined_parent', ROOT / 'tests/hermes_g2_reset_combined_faults_native.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
reset_host = base.reset_host
for name in vars(base):
    if name.startswith('test_'):
        globals()[name] = getattr(base, name)
spec = importlib.util.spec_from_file_location('publisher_combined_verification', ROOT / 'tests/hermes_g2_publisher_reset_native.py')
verification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verification)
verified_source = verification.verified_source
base.__file__ = __file__


def restart_probe(stage, directory):
    verification.verify_source(worker=True)
    from hermes_cli import middleware
    from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
    resume = base.fixtures.module('publisher_combined_restart', 'hermes_g2_restart_loop_native.py')
    patcher = pytest.MonkeyPatch()
    original, _, _ = resume.resume_host(directory, patcher)
    store, db, binding, _ = original
    binding.gateway = PolicyAuthorizationGateway((PolicyRule('session.read', operation='route_state', actor_id='alice'),))
    before = base.fixtures.persisted(directory)
    try:
        with pytest.raises(middleware.MandatoryMiddlewareError):
            store.read_owned_session_candidate(binding.owner)
        with pytest.raises(middleware.MandatoryMiddlewareError):
            with store.authenticated_owned_session_candidate(binding.owner):
                pytest.fail('restart adopted uncertain route')
        assert base.fixtures.persisted(directory) == before
        return {'status': 'blocked', 'unchanged': True}
    finally:
        middleware._mandatory_enabled = False
        db.close()
        patcher.undo()


if __name__ == '__main__':
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = restart_probe(Path(sys.argv[1]), Path(sys.argv[2]))
    except BaseException:
        print(json.dumps({'status': 'failed', 'reason_code': 'g2.publisher_restart_failed'}))
        raise SystemExit(1) from None
    print(json.dumps(result, sort_keys=True))

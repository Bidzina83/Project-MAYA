"""Separate final-profile evidence; frozen parent tests/verifiers stay unchanged."""
import importlib.util
import os
import json
import sqlite3
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

import hermes_state
import pytest
from hermes_cli import middleware

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"tests/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


create = load("hermes_g2_create_native")
caller = load("hermes_g2_caller_native")
qualified = load("hermes_g2_caller_qualification_native")
loss = load("hermes_g2_create_authority_loss_native")
failures = load("hermes_g2_create_failures_native")
reader_cases = load("hermes_g2_reader_native")
crashes = load("hermes_g2_create_crash_native")
host = create.host
caller_host = caller.caller_host


def verify_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from verify_governance_g2_final_create import verify_stage
        source = Path(hermes_state.__file__).resolve().parent
        native, maya = verify_stage(source.parent)
        assert source == native.resolve()
        import project_maya.hermes_plugins.session_creation as module
        assert Path(module.__file__).resolve().is_relative_to(maya.resolve())
    finally:
        sys.path.pop(0)


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    verify_source()


# Import only unchanged case functions, not parent autouse verification fixtures.
# The independent full-tree verifier above authorizes this final-profile replay.
for suite in (create, caller, qualified, loss, failures):
    for name in dir(suite):
        if name.startswith("test_") and name not in {
            "test_allowed_native_create_commits_and_publishes_without_dispatch_or_cache",
            "test_caller_failure_after_receipt_does_not_dispatch_or_compensate",
            "test_native_receipt_update_failure_quarantines_without_replay",
            "test_real_process_exit_before_ack_stays_pending_on_fresh_host",
        }:
            globals()[name] = getattr(suite, name)


@pytest.fixture
def reader_host(caller_host):
    native_host, _, reader = caller_host
    store, _, binding, _ = native_host
    with store.prepare_owned_session_candidate(binding.owner) as receipt:
        pass
    from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
    binding.gateway = PolicyAuthorizationGateway(tuple(
        PolicyRule(capability, operation=operation, actor_id="alice")
        for capability, operation in (("session.read", "route_state"), ("session.read", "history"),
                                     ("session.write", "append"))))
    middleware._mandatory_callbacks["session_write"].__self__.gateway = binding.gateway
    return native_host, reader, receipt


for name in dir(reader_cases):
    if name.startswith("test_"):
        globals()[name] = getattr(reader_cases, name)


@pytest.mark.parametrize("state", ["projection_verified", "published_pending_caller"])
def test_final_receipt_update_failure(host, state):
    store, db, binding, coordinator = host
    db._conn.execute("CREATE TRIGGER fixture_receipt_failure BEFORE UPDATE ON maya_session_transitions_v1 "
        f"WHEN NEW.state='{state}' BEGIN SELECT RAISE(ABORT,'synthetic-private-value'); END")
    db._conn.commit()
    with pytest.raises(middleware.MandatoryMiddlewareError) as error:
        create.create(host)
    assert "synthetic-private-value" not in str(error.value)
    assert caller.state(host) == ("committed_pending_projection" if state == "projection_verified" else "projection_verified")
    assert json.loads(coordinator.index.read_bytes())["generation"] == 1
    before = create.snapshot(host)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        create.create(host)
    assert create.snapshot(host) == before and not store._entries and not db._conn.in_transaction
    with coordinator._exclusive():
        pass


def worker(directory, boundary):
    verify_source()
    directory = Path(directory).resolve()
    if boundary == "restart":
        crashes.restart_worker(directory)
        return
    if boundary in {"race", "locked", "selected"}:
        concurrency_worker(directory, boundary)
        return
    assert directory.is_dir() and not any(directory.iterdir())
    if boundary != "caller":
        crashes.crash_worker(directory, boundary)
        return
    patcher = pytest.MonkeyPatch()
    fixture = create.host.__wrapped__(directory, patcher)
    native_host = next(fixture)
    native_host, _, _ = caller.caller_host.__wrapped__(native_host)
    with native_host[0].prepare_owned_session_candidate(native_host[2].owner):
        os._exit(77)


def reopen_host(directory):
    from gateway.config import GatewayConfig
    from gateway.session import SessionStore
    from project_maya.audit import LocalJsonlAuditSink
    from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
    from project_maya.hermes_plugins.governance import MayaGovernancePlugin, RequestIdentity
    from project_maya.hermes_plugins.session_transitions import CandidateCreateSessionBinding
    from project_maya.hermes_plugins.session_creation import CandidateNativeSessionCreate
    from project_maya.hermes_plugins.session_readers import CandidatePublishedSessionReader
    from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT
    from hermes_cli import plugins
    db = hermes_state.SessionDB(directory / "native.db")
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(hermes_state, "SessionDB", lambda: db)
        store = SessionStore(directory / "sessions", GatewayConfig())
    gateway = PolicyAuthorizationGateway(tuple(
        PolicyRule(capability, operation=operation, actor_id="alice")
        for capability, operation in (("session.read", "route_state"), ("session.read", "history"),
                                     ("session.transition", "create"), ("session.write", "create"))))
    audit = LocalJsonlAuditSink(directory / f"concurrent-audit-{os.getpid()}.jsonl")
    owner = RequestIdentity("alice", "confidential")
    binding = CandidateCreateSessionBinding(owner=owner, instance_id="g2-test", database=db.db_path,
        route_slot="telegram:fixture", binding_version=1, gateway=gateway,
        audit_sink=audit, acknowledgement=ACKNOWLEDGEMENT)
    # This fixture needs only the local governance fields; reuse the immutable
    # configuration factory rather than production credentials or startup.
    from project_maya.config import config_from_mapping
    config = config_from_mapping({"schema_version": 2,
        "product": {"edition": "enterprise", "instance_id": "g2-test"},
        "deployment": {"class": "desktop", "network_policy": "standard", "data_dir": str(directory)},
        "runtime": {"hermes_compatibility": ">=0.1", "enabled_profiles": ["maya-core"]},
        "broker": {"mode": "disabled"},
        "llm": {"mode": "customer_owned", "provider": "openai", "model": "synthetic-model",
                "credential_ref": "secret://llm/test", "endpoint": "https://api.openai.com/v1"},
        "memory": {"hermes_provider": "local", "retriever": "local_vector", "registry": "sqlite", "governance_enabled": True},
        "governance": {"policy_file": str(directory / "policy.json"), "default_action": "deny", "minimum_memory_trust": 0.7},
        "metabase": {"enabled": False, "deployment": "managed_local"}})
    plugin = MayaGovernancePlugin(config, gateway, audit)
    context = plugins.PluginContext(plugins.PluginManifest(name="maya-final-create-fixture"), plugins.get_plugin_manager())
    for kind, callback in (("llm_execution", plugin.model_execution), ("tool_execution", plugin.tool_execution),
                           ("tool_result", plugin.tool_result), ("model_output", plugin.model_output),
                           ("session_write", plugin.session_write)):
        context.register_middleware(kind, callback)
        middleware.require_middleware(kind, callback)
    coordinator = CandidateNativeSessionCreate(store, binding, acknowledgement=ACKNOWLEDGEMENT)
    reader = CandidatePublishedSessionReader(coordinator, acknowledgement=ACKNOWLEDGEMENT)
    return (store, db, binding, coordinator), reader


def concurrency_worker(directory, boundary):
    native_host, reader = reopen_host(directory)
    store, db, binding, _ = native_host
    before = create.snapshot(native_host)
    try:
        if boundary == "race":
            with binding.authenticated_create(binding.owner) as authority:
                print("ready", flush=True)
                assert sys.stdin.readline().strip() == "go"
                try:
                    receipt = store.create_owned_session_candidate(authority)
                except middleware.MandatoryMiddlewareError:
                    report = {"status": "denied"}
                else:
                    assert receipt["state"] == "published_pending_caller"
                    assert not receipt["dispatch_allowed"]
                    report = {"status": "pending", "session_id": receipt["session_id"]}
        elif boundary == "locked":
            with pytest.raises(middleware.MandatoryMiddlewareError):
                store.read_owned_session_candidate(binding.owner)
            assert create.snapshot(native_host) == before
            report = {"status": "blocked"}
        else:
            entry = store.read_owned_session_candidate(binding.owner)
            assert entry.session_key == binding.route_slot
            with store.authenticated_owned_session_candidate(binding.owner):
                assert reader._active is not None
            assert create.snapshot(native_host) == before
            report = {"status": "selected"}
        assert reader._active is None and not store._entries
        print(json.dumps(report), flush=True)
    finally:
        middleware._mandatory_enabled = False
        db.close()


def process_environment(directory):
    source = Path(hermes_state.__file__).resolve().parent
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((str(source.parent / "host/src"), str(source)))
    environment["HERMES_HOME"] = str(directory / "fixture-home")
    return source, environment


def run_worker(directory, boundary):
    source, environment = process_environment(directory)
    return subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()),
        "--worker", str(directory), boundary], cwd=source, env=environment,
        capture_output=True, timeout=120)


@pytest.mark.parametrize("boundary", ["before_commit", "after_commit", "before_replace", "after_replace", "caller"])
def test_final_process_crash_and_restart(tmp_path, boundary):
    result = run_worker(tmp_path, boundary)
    assert result.returncode == (77 if boundary == "caller" else 73), "selected process boundary was not reached"
    with sqlite3.connect(tmp_path / "native.db") as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchone() is None
        count = int(boundary != "before_commit")
        for table in ("sessions", "maya_session_owners_v1", "maya_session_routes_v1"):
            assert conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == count
        states = conn.execute("SELECT state FROM maya_session_transitions_v1").fetchall()
        expected = "published_pending_caller" if boundary == "caller" else "committed_pending_projection"
        assert states == ([(expected,)] if count else [])
    projection = json.loads((tmp_path / "sessions/sessions.json").read_bytes())
    assert projection["generation"] == int(boundary in {"after_replace", "caller"})
    import portalocker
    with portalocker.Lock(tmp_path / "sessions/maya-session-projection.lock", mode="r+b",
                          timeout=0, fail_when_locked=True):
        pass
    if count:
        restarted = run_worker(tmp_path, "restart")
        assert restarted.returncode == 0, "fresh host failed pending-route denial"
        assert json.loads(restarted.stdout)["caller_body_entries"] == 0


def test_final_cross_process_lock_and_reader(caller_host):
    native_host, _, _ = caller_host
    store, _, binding, coordinator = native_host
    with store.prepare_owned_session_candidate(binding.owner):
        pass
    before = create.snapshot(native_host)
    directory = store.sessions_dir.parent
    with coordinator._exclusive():
        denied = run_worker(directory, "locked")
    assert denied.returncode == 0 and json.loads(denied.stdout) == {"status": "blocked"}
    allowed = run_worker(directory, "selected")
    assert allowed.returncode == 0 and json.loads(allowed.stdout) == {"status": "selected"}
    assert create.snapshot(native_host) == before


def test_final_competing_allocation_processes(host):
    store, db, _, coordinator = host
    directory = store.sessions_dir.parent
    source, environment = process_environment(directory)
    workers = []
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            for _ in range(2):
                workers.append(subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()),
                    "--worker", str(directory), "race"], cwd=source, env=environment,
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
            ready = [executor.submit(process.stdout.readline) for process in workers]
            assert all(future.result(timeout=120).strip() == "ready" for future in ready)
            for process in workers:
                process.stdin.write("go\n")
                process.stdin.flush()
            reports = []
            for process in workers:
                output, _ = process.communicate(timeout=120)
                assert process.returncode == 0, "allocation worker failed"
                reports.append(json.loads(output))
        assert sorted(report["status"] for report in reports) == ["denied", "pending"]
        winner = next(report["session_id"] for report in reports if report["status"] == "pending")
        assert caller.state(host) == "published_pending_caller"
        for table in ("sessions", "maya_session_owners_v1", "maya_session_routes_v1", "maya_session_transitions_v1"):
            assert db._conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 1
        assert db._conn.execute("SELECT target_session FROM maya_session_transitions_v1").fetchone()[0] == winner
        assert json.loads(coordinator.index.read_bytes())["generation"] == 1
        assert not store._entries and not db._conn.in_transaction
        assert db._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert db._conn.execute("PRAGMA foreign_key_check").fetchone() is None
    finally:
        for process in workers:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)


def test_final_direct_create_is_pending_not_dispatch_authority(host):
    receipt = create.create(host)
    assert receipt["state"] == "published_pending_caller"
    assert receipt["dispatch_allowed"] is False
    assert caller.state(host) == "published_pending_caller"
    assert not host[0]._entries and not host[1]._conn.in_transaction


@pytest.mark.parametrize("boundary", ["write", "fsync"])
def test_projection_io_failure_retains_blocked_commit(host, monkeypatch, boundary):
    import project_maya.hermes_plugins.session_creation as module
    store, db, binding, coordinator = host
    old = create.snapshot(host)[1]
    calls = []
    original_publish = coordinator._publish

    def publish(raw):
        # Restrict injection to the actual projection sink, not audit I/O.
        with pytest.MonkeyPatch.context() as patcher:
            if boundary == "fsync":
                def deny_fsync(fd):
                    calls.append("fsync")
                    raise OSError("synthetic-private-value")
                patcher.setattr(module.os, "fsync", deny_fsync)
            else:
                original_fdopen = module.os.fdopen

                class FailingWriter:
                    def __init__(self, stream):
                        self.stream = stream

                    def __enter__(self):
                        self.stream.__enter__()
                        return self

                    def __exit__(self, *args):
                        return self.stream.__exit__(*args)

                    def write(self, raw):
                        self.stream.write(raw[:7])
                        calls.append("write")
                        raise OSError("synthetic-private-value")

                patcher.setattr(module.os, "fdopen", lambda *args, **kwargs:
                    FailingWriter(original_fdopen(*args, **kwargs)))
            return original_publish(raw)

    monkeypatch.setattr(coordinator, "_publish", publish)
    with pytest.raises(middleware.MandatoryMiddlewareError) as error:
        create.create(host)
    assert calls == [boundary]
    assert "synthetic-private-value" not in str(error.value)
    assert create.snapshot(host)[1] == old
    assert caller.state(host) == "committed_pending_projection"
    for table in ("sessions", "maya_session_owners_v1", "maya_session_routes_v1"):
        assert db._conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 1
    assert not db._conn.in_transaction and not store._entries
    assert db._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert db._conn.execute("PRAGMA foreign_key_check").fetchone() is None
    assert not list(store.sessions_dir.glob(".maya-projection-*"))
    before = create.snapshot(host)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        create.create(host)
    assert create.snapshot(host) == before
    with coordinator._exclusive():
        pass
    assert "synthetic-private-value" not in binding.audit.path.read_text()


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        worker(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit("explicit isolated worker invocation required")

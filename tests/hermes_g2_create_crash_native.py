"""Real-process crash diagnostics; no recovery or production activation."""
import importlib.util
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import portalocker
import pytest
import hermes_state

ROOT = Path(__file__).resolve().parents[1]


def fixture_module():
    spec = importlib.util.spec_from_file_location("create_fixture", ROOT / "tests/hermes_g2_create_native.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def crash_worker(directory, boundary):
    module = fixture_module()
    monkeypatch = pytest.MonkeyPatch()
    fixture = module.host.__wrapped__(Path(directory), monkeypatch)
    host = next(fixture)
    coordinator = host[3]
    if boundary in {"before_commit", "after_commit"}:
        original = coordinator._commit
        def crash(conn):
            if boundary == "after_commit":
                original(conn)
            os._exit(73)
        coordinator._commit = crash
    else:
        original = coordinator._publish
        def crash(raw):
            if boundary == "after_replace":
                original(raw)
            os._exit(73)
        coordinator._publish = crash
    module.create(host)
    raise RuntimeError("crash boundary not reached")


def restart_worker(directory, *, published=False, contended=False, race=False):
    from gateway.config import GatewayConfig
    from gateway.session import SessionStore
    from hermes_cli import middleware, plugins
    from project_maya.audit import LocalJsonlAuditSink
    from project_maya.config import config_from_mapping
    from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
    from project_maya.hermes_plugins.governance import GovernanceBoundaryError, MayaGovernancePlugin, RequestIdentity
    from project_maya.hermes_plugins.session_creation import CandidateNativeSessionCreate
    from project_maya.hermes_plugins.session_readers import CandidatePublishedSessionReader
    from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT
    from project_maya.hermes_plugins.session_transitions import CandidateCreateSessionBinding

    directory = Path(directory)
    assert (directory / "native.db").is_file()
    db = hermes_state.SessionDB(directory / "native.db")
    before = list(db._conn.iterdump())
    projection = (directory / "sessions/sessions.json").read_bytes()
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(hermes_state, "SessionDB", lambda: db)
        store = SessionStore(directory / "sessions", GatewayConfig())
    audit = LocalJsonlAuditSink(directory / (f"race-audit-{os.getpid()}.jsonl" if race else "restart-audit.jsonl"))
    gateway = PolicyAuthorizationGateway(tuple(
        PolicyRule(capability, operation=operation, actor_id="alice")
        for capability, operation in (("session.read", "route_state"), ("session.read", "history"),
                                     ("session.transition", "create"), ("session.write", "create"))))
    owner = RequestIdentity("alice", "confidential")
    binding = CandidateCreateSessionBinding(owner=owner, instance_id="g2-test", database=db.db_path,
        route_slot="telegram:fixture", binding_version=1, gateway=gateway,
        audit_sink=audit, acknowledgement=ACKNOWLEDGEMENT)
    config = config_from_mapping({
        "schema_version": 2, "product": {"edition": "enterprise", "instance_id": "g2-test"},
        "deployment": {"class": "desktop", "network_policy": "standard", "data_dir": str(directory)},
        "runtime": {"hermes_compatibility": ">=0.1", "enabled_profiles": ["maya-core"]},
        "broker": {"mode": "disabled"},
        "llm": {"mode": "customer_owned", "provider": "openai", "model": "synthetic-model",
                "credential_ref": "secret://llm/test", "endpoint": "https://api.openai.com/v1"},
        "memory": {"hermes_provider": "local", "retriever": "local_vector", "registry": "sqlite", "governance_enabled": True},
        "governance": {"policy_file": str(directory / "policy.json"), "default_action": "deny", "minimum_memory_trust": 0.7},
        "metabase": {"enabled": False, "deployment": "managed_local"},
    })
    plugin = MayaGovernancePlugin(config, gateway, audit)
    context = plugins.PluginContext(plugins.PluginManifest(name="maya-restart-test"), plugins.get_plugin_manager())
    for kind, callback in (("llm_execution", plugin.model_execution), ("tool_execution", plugin.tool_execution),
                           ("tool_result", plugin.tool_result), ("model_output", plugin.model_output),
                           ("session_write", plugin.session_write)):
        context.register_middleware(kind, callback)
        middleware.require_middleware(kind, callback)
    coordinator = CandidateNativeSessionCreate(store, binding, acknowledgement=ACKNOWLEDGEMENT)
    reader = CandidatePublishedSessionReader(coordinator, acknowledgement=ACKNOWLEDGEMENT)
    if race:
        with binding.authenticated_create(owner) as authority:
            print("ready", flush=True)
            assert sys.stdin.readline().strip() == "go"
            try:
                receipt = store.create_owned_session_candidate(authority)
            except middleware.MandatoryMiddlewareError:
                report = {"status": "denied"}
            else:
                assert receipt["state"] == "published" and not receipt["dispatch_allowed"]
                report = {"status": "published", "session_id": receipt["session_id"]}
        assert reader._active is None and not store._entries
        middleware._mandatory_enabled = False
        db.close()
        print(json.dumps(report), flush=True)
        return
    dispatches = 0
    if published:
        entry = store.read_owned_session_candidate(owner)
        with store.authenticated_owned_session_candidate(owner):
            dispatches += 1
        assert entry.session_key == binding.route_slot
    else:
        with pytest.raises(middleware.MandatoryMiddlewareError):
            store.read_owned_session_candidate(owner)
        with pytest.raises(middleware.MandatoryMiddlewareError):
            with store.authenticated_owned_session_candidate(owner):
                dispatches += 1
    with binding.authenticated_create(owner) as authority:
        with pytest.raises(middleware.MandatoryMiddlewareError):
            store.create_owned_session_candidate(authority)
    if contended:
        with binding.authenticated_create(owner) as authority:
            with pytest.raises(GovernanceBoundaryError, match="governance.transition_busy"):
                coordinator.create(store, authority)
    assert dispatches == int(published) and reader._active is None and not store._entries
    assert list(db._conn.iterdump()) == before
    assert (directory / "sessions/sessions.json").read_bytes() == projection
    middleware._mandatory_enabled = False
    db.close()
    print(json.dumps({"status": "selected_as_expected" if published else "blocked_as_expected", "caller_body_entries": dispatches,
                      "database_unchanged": True, "projection_unchanged": True}))


@pytest.mark.parametrize("boundary", ["before_commit", "after_commit", "before_replace", "after_replace"])
def test_process_crash_preserves_transaction_and_quarantines_publication(tmp_path, boundary):
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_reader import verify_reader_stage
        source = Path(hermes_state.__file__).resolve().parent
        verified, _ = verify_reader_stage(source.parent)
        assert source == verified.resolve()
    finally:
        sys.path.pop(0)
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((str(source), str(ROOT / "src")))
    result = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()),
                             "--crash-worker", str(tmp_path), boundary],
                            cwd=source, env=environment, capture_output=True, timeout=60)
    assert result.returncode == 73, "worker did not reach selected crash boundary"
    # New connections after actual process exit observe SQLite recovery, not
    # an in-process rollback or a replacement persistence implementation.
    with sqlite3.connect(tmp_path / "native.db") as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchone() is None
        count = conn.execute("SELECT count(*) FROM sessions").fetchone()[0]
        receipts = conn.execute("SELECT state FROM maya_session_transitions_v1").fetchall()
        generation = conn.execute("SELECT generation FROM maya_session_projection_v1").fetchone()[0]
        assert count == generation == (0 if boundary == "before_commit" else 1)
        assert receipts == ([] if boundary == "before_commit" else [("committed_pending_projection",)])
        assert conn.execute("SELECT count(*) FROM maya_session_owners_v1").fetchone()[0] == count
        assert conn.execute("SELECT count(*) FROM maya_session_routes_v1").fetchone()[0] == count
    projection = json.loads((tmp_path / "sessions/sessions.json").read_bytes())
    assert projection["generation"] == (1 if boundary == "after_replace" else 0)
    assert len(projection["routes"]) == projection["generation"]
    # Kernel exclusion must be released by process termination, without repair.
    with portalocker.Lock(tmp_path / "sessions/maya-session-projection.lock", mode="r+b",
                          timeout=0, fail_when_locked=True):
        pass
    audit = [json.loads(line) for line in (tmp_path / "audit.jsonl").read_text().splitlines()]
    assert not any(row.get("event_type") == "outcome.session_transition" for row in audit)


@pytest.mark.parametrize("boundary", ["after_commit", "before_replace", "after_replace"])
def test_fresh_host_denies_pending_route_without_repair_or_dispatch(tmp_path, boundary):
    source = Path(hermes_state.__file__).resolve().parent
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_reader import verify_reader_stage
        verified, _ = verify_reader_stage(source.parent)
        assert source == verified.resolve()
    finally:
        sys.path.pop(0)
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((str(source), str(ROOT / "src")))
    crashed = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()),
                              "--crash-worker", str(tmp_path), boundary],
                             cwd=source, env=environment, capture_output=True, timeout=60)
    assert crashed.returncode == 73
    restarted = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()),
                                "--restart-worker", str(tmp_path)],
                               cwd=source, env=environment, capture_output=True, timeout=60)
    assert restarted.returncode == 0, "restart denial qualification failed"
    report = json.loads(restarted.stdout)
    assert report == {"status": "blocked_as_expected", "caller_body_entries": 0,
                      "database_unchanged": True, "projection_unchanged": True}


def test_second_native_process_is_denied_during_projection_lock_then_can_select(tmp_path):
    source = Path(hermes_state.__file__).resolve().parent
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_reader import verify_reader_stage
        verified, _ = verify_reader_stage(source.parent)
        assert source == verified.resolve()
    finally:
        sys.path.pop(0)
    module = fixture_module()
    monkeypatch = pytest.MonkeyPatch()
    fixture = module.host.__wrapped__(tmp_path, monkeypatch)
    host = next(fixture)
    try:
        module.create(host)
        before = module.snapshot(host)
        environment = os.environ.copy()
        environment["PYTHONPATH"] = os.pathsep.join((str(source), str(ROOT / "src")))
        with host[3]._exclusive():
            denied = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()),
                                     "--contended-worker", str(tmp_path)],
                                    cwd=source, env=environment, capture_output=True, timeout=60)
        assert denied.returncode == 0, "contending native host did not fail closed"
        assert json.loads(denied.stdout)["caller_body_entries"] == 0
        assert module.snapshot(host) == before
        allowed = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()),
                                  "--published-worker", str(tmp_path)],
                                 cwd=source, env=environment, capture_output=True, timeout=60)
        assert allowed.returncode == 0, "published route was not selectable after lock release"
        assert json.loads(allowed.stdout)["caller_body_entries"] == 1
        assert module.snapshot(host) == before
        assert host[1]._conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 1
        assert not host[0]._entries
    finally:
        fixture.close()
        monkeypatch.undo()


def test_two_prepared_native_hosts_allocate_one_route_once(tmp_path):
    source = Path(hermes_state.__file__).resolve().parent
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_reader import verify_reader_stage
        verified, _ = verify_reader_stage(source.parent)
        assert source == verified.resolve()
    finally:
        sys.path.pop(0)
    module = fixture_module()
    monkeypatch = pytest.MonkeyPatch()
    fixture = module.host.__wrapped__(tmp_path, monkeypatch)
    host = next(fixture)
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((str(source), str(ROOT / "src")))
    workers = []
    try:
        with ThreadPoolExecutor(max_workers=2) as readers:
            try:
                for _ in range(2):
                    workers.append(subprocess.Popen(
                        [sys.executable, "-B", str(Path(__file__).resolve()), "--race-worker", str(tmp_path)],
                        cwd=source, env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, text=True))
                ready = [readers.submit(worker.stdout.readline) for worker in workers]
                assert all(future.result(timeout=60).strip() == "ready" for future in ready)
                for worker in workers:
                    worker.stdin.write("go\n")
                    worker.stdin.flush()
                reports = []
                for worker in workers:
                    stdout, _ = worker.communicate(timeout=60)
                    assert worker.returncode == 0, "native allocation worker failed"
                    reports.append(json.loads(stdout))
            finally:
                for worker in workers:
                    if worker.poll() is None:
                        worker.kill()
                    worker.wait(timeout=10)
        assert sorted(report["status"] for report in reports) == ["denied", "published"]
        winner = next(report["session_id"] for report in reports if report["status"] == "published")
        conn = host[1]._conn
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchone() is None
        for table in ("sessions", "maya_session_owners_v1", "maya_session_routes_v1", "maya_session_transitions_v1"):
            assert conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 1
        assert tuple(conn.execute("SELECT target_session,state,result_route_version FROM maya_session_transitions_v1").fetchone()) == (winner, "published", 1)
        projection = json.loads((tmp_path / "sessions/sessions.json").read_bytes())
        assert projection["generation"] == 1
        assert projection["routes"] == {"telegram:fixture": {"session_id": winner, "version": 1}}
        assert not host[0]._entries
        outcomes = [json.loads(line) for path in tmp_path.glob("race-audit-*.jsonl")
                    for line in path.read_text().splitlines()]
        assert sum(row.get("event_type") == "outcome.session_transition" for row in outcomes) == 1
    finally:
        fixture.close()
        monkeypatch.undo()


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--crash-worker":
        crash_worker(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 3 and sys.argv[1] == "--restart-worker":
        restart_worker(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == "--published-worker":
        restart_worker(sys.argv[2], published=True)
    elif len(sys.argv) == 3 and sys.argv[1] == "--contended-worker":
        restart_worker(sys.argv[2], contended=True)
    elif len(sys.argv) == 3 and sys.argv[1] == "--race-worker":
        restart_worker(sys.argv[2], race=True)
    else:
        raise SystemExit("explicit crash-worker invocation required")

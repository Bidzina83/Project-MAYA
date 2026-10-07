"""Real reset worker termination and fresh authenticated restart; no recovery."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
BOUNDARIES = ("before_native_commit", "after_native_commit", "before_replace", "after_replace",
              "caller_pending", "before_ack_commit", "after_ack_commit", "after_confirmation")


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tests" / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def stage_verifier():
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_governance_g2_reset_crash import verify_worker_stage
    return verify_worker_stage


def crash_worker(stage, directory, boundary):
    assert boundary in BOUNDARIES and directory.is_dir() and not any(directory.iterdir())
    source, host_source = stage_verifier()(stage)
    import hermes_state
    from project_maya.hermes_plugins import reset_publication
    assert Path(hermes_state.__file__).resolve().is_relative_to(source)
    assert Path(reset_publication.__file__).resolve().is_relative_to(host_source)
    base = module("crash_gate_fixture", "hermes_g2_reset_gate_native.py")
    patcher = pytest.MonkeyPatch()
    patcher.setenv("HERMES_HOME", str(directory / "home"))
    def forbidden(*args, **kwargs):
        raise AssertionError("g2.reset_crash_unexpected_transport")
    patcher.setattr(socket, "create_connection", forbidden)
    patcher.setattr(socket.socket, "connect", forbidden)
    root = base.host.__wrapped__(directory, patcher)
    original = next(root)
    caller = base.caller_host.__wrapped__(original)
    loop = base.loop_host.__wrapped__(caller, patcher, directory)
    host = base.reset_host.__wrapped__(base.cache_host.__wrapped__(
        base.recognition_host.__wrapped__(next(loop)), patcher))
    conn = host.db._conn
    cursor = conn.execute("SELECT * FROM sessions WHERE id=?", (host.source,))
    source_row = dict(zip((column[0] for column in cursor.description), cursor.fetchone()))
    snapshot = {"source": host.source, "database": list(conn.iterdump()),
                "messages": [list(row) for row in conn.execute("SELECT * FROM messages ORDER BY id")],
                "source_row": source_row, "projection": host.reset.coordinator.index.read_text()}
    (directory / "before-reset.json").write_text(json.dumps(snapshot, sort_keys=True), encoding="utf-8")
    def terminate():
        assert not host.requests and not host.agents
        os._exit(73)
    if boundary in {"before_native_commit", "after_native_commit"}:
        commit = host.reset._commit
        def stop(conn):
            if boundary == "after_native_commit":
                commit(conn)
            terminate()
        host.reset._commit = stop
    elif boundary in {"before_replace", "after_replace"}:
        publish = host.reset.coordinator._publish
        def stop(raw):
            if boundary == "after_replace":
                publish(raw)
            terminate()
        host.reset.coordinator._publish = stop
    elif boundary in {"before_ack_commit", "after_ack_commit"}:
        commit = host.preparation._commit
        def stop(conn):
            if base.base.state(host) == "caller_acknowledged":
                if boundary == "after_ack_commit":
                    commit(conn)
                terminate()
            commit(conn)
        host.preparation._commit = stop
    with host.store.prepare_owned_reset_candidate(host.binding.owner):
        if boundary == "caller_pending":
            terminate()
    if boundary == "after_confirmation":
        assert host.preparation._confirmed is not None
        assert not host.requests and not host.agents
        terminate()
    raise AssertionError("g2.reset_crash_boundary_not_reached")


def restart_worker(stage, directory, allow_source):
    stage_verifier()(stage)
    from hermes_cli import middleware
    from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
    base = module("reset_restart_fixture", "hermes_g2_restart_loop_native.py")
    patcher = pytest.MonkeyPatch()
    original, _, reader = base.resume_host(directory, patcher)
    store, db, binding, coordinator = original
    binding.gateway = PolicyAuthorizationGateway(tuple(PolicyRule("session.read", operation=operation, actor_id="alice")
        for operation in ("route_state", "history")))
    before = list(db._conn.iterdump())
    projection = coordinator.index.read_bytes()
    body_entries = 0
    if allow_source:
        store.read_owned_session_candidate(binding.owner)
        with store.authenticated_owned_session_candidate(binding.owner):
            body_entries += 1
    else:
        with pytest.raises(middleware.MandatoryMiddlewareError):
            store.read_owned_session_candidate(binding.owner)
        with pytest.raises(middleware.MandatoryMiddlewareError):
            with store.authenticated_owned_session_candidate(binding.owner):
                body_entries += 1
    assert body_entries == int(allow_source) and reader._active is None and not store._entries
    assert list(db._conn.iterdump()) == before and coordinator.index.read_bytes() == projection
    middleware._mandatory_enabled = False
    db.close()
    return {"status": "source_selected" if allow_source else "reset_blocked",
            "caller_body_entries": body_entries, "database_unchanged": True, "projection_unchanged": True}


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    import hermes_state
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_governance_g2_reset_crash import verify_stage
    verify_stage(Path(hermes_state.__file__).resolve().parent.parent)


@pytest.mark.parametrize("boundary", BOUNDARIES)
def test_crash_boundary_and_fresh_host_routing(tmp_path, boundary):
    import hermes_state
    import portalocker
    stage = Path(hermes_state.__file__).resolve().parent.parent
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    command = [sys.executable, "-B", str(Path(__file__).resolve())]
    crashed = subprocess.run([*command, "crash", str(stage), str(tmp_path), boundary],
                             cwd=stage / "source", env=env, capture_output=True, timeout=120)
    assert crashed.returncode == 73, "native reset worker did not reach crash boundary"
    snapshot = json.loads((tmp_path / "before-reset.json").read_text())
    precommit = boundary == "before_native_commit"
    expected_receipt = (None if precommit else "published_pending_caller"
        if boundary in {"caller_pending", "before_ack_commit"} else "caller_acknowledged"
        if boundary in {"after_ack_commit", "after_confirmation"} else "committed_pending_projection")
    with sqlite3.connect(tmp_path / "native.db") as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchone() is None
        if precommit:
            assert list(conn.iterdump()) == snapshot["database"]
        assert [list(row) for row in conn.execute("SELECT * FROM messages ORDER BY id")] == snapshot["messages"]
        cursor = conn.execute("SELECT * FROM sessions WHERE id=?", (snapshot["source"],))
        old = dict(zip((column[0] for column in cursor.description), cursor.fetchone()))
        assert {key: value for key, value in old.items() if key not in {"ended_at", "end_reason"}} == {
            key: value for key, value in snapshot["source_row"].items() if key not in {"ended_at", "end_reason"}}
        assert (old["ended_at"] is None) == precommit
        assert old["end_reason"] == (None if precommit else "session_reset")
        reset = conn.execute("SELECT state,target_session FROM maya_session_transitions_v1 WHERE operation='reset'").fetchone()
        assert (reset[0] if reset else None) == expected_receipt
        assert conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == (1 if precommit else 2)
        assert conn.execute("SELECT generation FROM maya_session_projection_v1").fetchone()[0] == (1 if precommit else 2)
        if reset:
            assert tuple(conn.execute("SELECT parent_session_id,user_id FROM sessions WHERE id=?", (reset[1],)).fetchone()) == (snapshot["source"], "alice")
            assert tuple(conn.execute("SELECT lifecycle_status,parent_session_id FROM maya_session_owners_v1 WHERE session_id=?", (reset[1],)).fetchone()) == ("active", snapshot["source"])
            assert tuple(conn.execute("SELECT session_id,route_version FROM maya_session_routes_v1").fetchone()) == (reset[1], 2)
    raw = (tmp_path / "sessions/sessions.json").read_text()
    if boundary in {"before_native_commit", "after_native_commit", "before_replace"}:
        assert raw == snapshot["projection"]
    else:
        assert json.loads(raw)["generation"] == 2
    with portalocker.Lock(tmp_path / "sessions/maya-session-projection.lock", mode="r+b", timeout=0, fail_when_locked=True):
        pass
    restarted = subprocess.run([*command, "restart", str(stage), str(tmp_path), "source" if precommit else "reset"],
                               cwd=stage / "source", env=env, capture_output=True, timeout=120, text=True)
    assert restarted.returncode == 0, "fresh-host reset routing qualification failed"
    report = json.loads(restarted.stdout)
    assert report == {"status": "source_selected" if precommit else "reset_blocked",
                      "caller_body_entries": int(precommit), "database_unchanged": True, "projection_unchanged": True}


if __name__ == "__main__":
    try:
        operation, stage, directory, scenario = sys.argv[1:]
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            if operation == "crash":
                crash_worker(Path(stage), Path(directory), scenario)
            elif operation == "restart" and scenario in {"source", "reset"}:
                report = restart_worker(Path(stage), Path(directory), scenario == "source")
            else:
                raise ValueError("invalid scenario")
    except Exception:
        print(json.dumps({"status": "blocked", "reason_code": "g2.reset_crash_worker_failed"}))
        raise SystemExit(1)
    print(json.dumps(report, sort_keys=True))

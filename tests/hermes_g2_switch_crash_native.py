"""Real switch worker termination and independent restart; never repair/adopt."""
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
BOUNDARIES = ("before_native_commit", "after_native_commit", "before_publish", "after_publish",
              "caller_pending", "before_cleanup", "after_cleanup", "before_ack_commit",
              "after_ack_commit", "after_confirmation")


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tests" / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def verify_worker(stage):
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_governance_g2_switch_crash import verify_worker_stage
    return verify_worker_stage(stage)


def no_transport(patcher):
    def forbidden(*args, **kwargs):
        raise AssertionError("g2.switch_crash_unexpected_transport")
    patcher.setattr(socket, "create_connection", forbidden)
    patcher.setattr(socket.socket, "connect", forbidden)
    patcher.setattr(socket.socket, "connect_ex", forbidden)
    patcher.setattr(socket.socket, "sendto", forbidden)


def crash_worker(stage, directory, boundary):
    assert boundary in BOUNDARIES and directory.is_dir() and not any(directory.iterdir())
    source, host_source = verify_worker(stage)
    import hermes_state
    from project_maya.hermes_plugins import switch_publication
    assert Path(hermes_state.__file__).resolve().is_relative_to(source)
    assert Path(switch_publication.__file__).resolve().is_relative_to(host_source)
    fixtures = module("switch_crash_fixture", "hermes_g2_switch_composition_native.py")
    patcher = pytest.MonkeyPatch()
    patcher.setenv("HERMES_HOME", str(directory / "home"))
    no_transport(patcher)
    root = fixtures.host.__wrapped__(directory, patcher)
    original = next(root)
    caller = fixtures.caller_host.__wrapped__(original)
    loop = fixtures.loop_host.__wrapped__(caller, patcher, directory)
    host = fixtures.composed_host.__wrapped__(fixtures.switch_host.__wrapped__(
        fixtures.reset_host.__wrapped__(fixtures.cache_host.__wrapped__(
            fixtures.recognition_host.__wrapped__(next(loop)), patcher))), patcher)
    conn = host.db._conn
    cursor = conn.execute("SELECT * FROM sessions ORDER BY id")
    columns = [column[0] for column in cursor.description]
    snapshot = {"parent": host.source, "child": host.child, "route_slot": host.binding.route_slot,
        "database": list(conn.iterdump()),
        "messages": [list(row) for row in conn.execute("SELECT * FROM messages ORDER BY id")],
        "sessions": [dict(zip(columns, row)) for row in cursor.fetchall()],
        "receipts": [list(row) for row in conn.execute("SELECT * FROM maya_session_transitions_v1 ORDER BY correlation_id")],
        "projection": host.original[3].index.read_text()}
    (directory / "before-switch.json").write_text(json.dumps(snapshot, sort_keys=True), encoding="utf-8")

    def terminate():
        assert not host.requests and not host.agents and not host.wire
        os._exit(73)

    if boundary in {"before_native_commit", "after_native_commit"}:
        commit = host.switch._commit
        def stop(conn):
            if boundary == "after_native_commit":
                commit(conn)
            terminate()
        host.switch._commit = stop
    elif boundary in {"before_publish", "after_publish"}:
        publish = host.original[3]._publish
        def stop(raw):
            if boundary == "after_publish":
                publish(raw)
            terminate()
        host.original[3]._publish = stop
    elif boundary in {"before_cleanup", "after_cleanup"}:
        cleanup = host.runner._clear_owned_switch_security_candidate
        def stop(preparation):
            if boundary == "after_cleanup":
                cleanup(preparation)
                assert preparation._cleanup_authority is preparation._current
            terminate()
        host.runner._clear_owned_switch_security_candidate = stop
    elif boundary in {"before_ack_commit", "after_ack_commit"}:
        commit = host.switch_preparation._commit
        def stop(conn):
            if fixtures.state(host) == "caller_acknowledged":
                if boundary == "after_ack_commit":
                    commit(conn)
                terminate()
            commit(conn)
        host.switch_preparation._commit = stop
    with host.store.prepare_owned_switch_candidate(host.binding.owner, host.source):
        if boundary == "caller_pending":
            terminate()
    if boundary == "after_confirmation":
        assert host.switch_preparation._confirmed is not None
        assert host.store.read_owned_session_candidate(host.binding.owner).session_id == host.source
        terminate()
    raise AssertionError("g2.switch_crash_boundary_not_reached")


def restart_worker(stage, directory):
    verify_worker(stage)
    from hermes_cli import middleware
    from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
    base = module("switch_restart_fixture", "hermes_g2_restart_loop_native.py")
    patcher = pytest.MonkeyPatch()
    no_transport(patcher)
    original, _, reader = base.resume_host(directory, patcher)
    store, db, binding, coordinator = original
    binding.gateway = PolicyAuthorizationGateway(tuple(PolicyRule("session.read", operation=op, actor_id="alice")
        for op in ("route_state", "history")))
    before = list(db._conn.iterdump())
    projection = coordinator.index.read_bytes()
    body_entries = 0
    with pytest.raises(middleware.MandatoryMiddlewareError):
        store.read_owned_session_candidate(binding.owner)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        with store.authenticated_owned_session_candidate(binding.owner):
            body_entries += 1
    assert body_entries == 0 and reader._active is None and not store._entries
    assert list(db._conn.iterdump()) == before and coordinator.index.read_bytes() == projection
    # Isolated fixture disposal is not product shutdown/reconciliation authority.
    middleware._mandatory_enabled = False
    db.close()
    return {"status": "routing_blocked", "caller_body_entries": 0,
            "database_unchanged": True, "projection_unchanged": True}


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    import hermes_state
    verify_worker(Path(hermes_state.__file__).resolve().parent.parent)


@pytest.mark.parametrize("boundary", BOUNDARIES)
def test_real_crash_and_fresh_host_cannot_adopt_confirmation(tmp_path, boundary):
    import hermes_state
    import portalocker
    stage = Path(hermes_state.__file__).resolve().parent.parent
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    command = [sys.executable, "-B", str(Path(__file__).resolve())]
    crashed = subprocess.run([*command, "crash", str(stage), str(tmp_path), boundary],
                             cwd=tmp_path, env=env, capture_output=True, timeout=150)
    assert crashed.returncode == 73, "native switch worker did not reach crash boundary"
    snapshot = json.loads((tmp_path / "before-switch.json").read_text())
    precommit = boundary == "before_native_commit"
    pending_caller = {"caller_pending", "before_cleanup", "after_cleanup", "before_ack_commit"}
    acknowledged = {"after_ack_commit", "after_confirmation"}
    expected_state = (None if precommit else "published_pending_caller" if boundary in pending_caller
                      else "caller_acknowledged" if boundary in acknowledged else "committed_pending_projection")
    with sqlite3.connect((tmp_path / "native.db").resolve().as_uri() + "?mode=ro", uri=True) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchone() is None
        if precommit:
            assert list(conn.iterdump()) == snapshot["database"]
        assert [list(row) for row in conn.execute("SELECT * FROM messages ORDER BY id")] == snapshot["messages"]
        cursor = conn.execute("SELECT * FROM sessions ORDER BY id")
        columns = [column[0] for column in cursor.description]
        sessions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        assert len(sessions) == 2
        retained = lambda row: {k: v for k, v in row.items() if k not in {"ended_at", "end_reason"}}
        assert [retained(row) for row in sessions] == [retained(row) for row in snapshot["sessions"]]
        rows = {row["id"]: row for row in sessions}
        parent, child = rows[snapshot["parent"]], rows[snapshot["child"]]
        assert (parent["ended_at"] is None) == (not precommit)
        assert parent["end_reason"] == ("session_reset" if precommit else None)
        assert (child["ended_at"] is None) == precommit
        assert child["end_reason"] == (None if precommit else "session_switch")
        assert [list(row) for row in conn.execute("SELECT * FROM maya_session_transitions_v1 WHERE operation<>'switch' ORDER BY correlation_id")] == snapshot["receipts"]
        receipt = conn.execute("SELECT state,target_session,generation FROM maya_session_transitions_v1 WHERE operation='switch'").fetchone()
        assert (receipt[0] if receipt else None) == expected_state
        if receipt:
            assert tuple(receipt[1:]) == (snapshot["parent"], 3)
        target = snapshot["child"] if precommit else snapshot["parent"]
        version = 2 if precommit else 3
        assert tuple(conn.execute("SELECT session_id,route_version FROM maya_session_routes_v1").fetchone()) == (target, version)
        assert conn.execute("SELECT generation FROM maya_session_projection_v1").fetchone()[0] == version
        assert tuple(conn.execute("SELECT lifecycle_status,parent_session_id FROM maya_session_owners_v1 WHERE session_id=?", (snapshot["parent"],)).fetchone()) == ("ended" if precommit else "active", None)
        assert tuple(conn.execute("SELECT lifecycle_status,parent_session_id FROM maya_session_owners_v1 WHERE session_id=?", (snapshot["child"],)).fetchone()) == ("active" if precommit else "ended", snapshot["parent"])
        after_database = list(conn.iterdump())
    index = tmp_path / "sessions/sessions.json"
    raw = index.read_text()
    if boundary in {"before_native_commit", "after_native_commit", "before_publish"}:
        assert raw == snapshot["projection"]
    else:
        assert json.loads(raw)["generation"] == 3
        assert json.loads(raw)["routes"][snapshot["route_slot"]] == {"session_id": snapshot["parent"], "version": 3}
    with portalocker.Lock(tmp_path / "sessions/maya-session-projection.lock", mode="r+b", timeout=0, fail_when_locked=True):
        pass
    restarted = subprocess.run([*command, "restart", str(stage), str(tmp_path), "blocked"],
                               cwd=tmp_path, env=env, capture_output=True, timeout=150, text=True)
    assert restarted.returncode == 0, "fresh-host switch routing qualification failed"
    assert json.loads(restarted.stdout) == {"status": "routing_blocked", "caller_body_entries": 0,
                                           "database_unchanged": True, "projection_unchanged": True}
    assert index.read_text() == raw
    with sqlite3.connect((tmp_path / "native.db").resolve().as_uri() + "?mode=ro", uri=True) as conn:
        assert list(conn.iterdump()) == after_database


if __name__ == "__main__":
    try:
        operation, stage, directory, scenario = sys.argv[1:]
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            if operation == "crash":
                crash_worker(Path(stage), Path(directory), scenario)
            elif operation == "restart" and scenario == "blocked":
                report = restart_worker(Path(stage), Path(directory))
            else:
                raise ValueError("invalid scenario")
    except Exception:
        print(json.dumps({"status": "blocked", "reason_code": "g2.switch_crash_worker_failed"}))
        raise SystemExit(1)
    print(json.dumps(report, sort_keys=True))

"""Real competing reset processes over native SQLite; no agents or transports."""
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
from time import monotonic, sleep

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tests" / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def wait_file(path, process=None):
    deadline = monotonic() + 90
    while not path.is_file():
        if (process is not None and process.poll() is not None) or monotonic() >= deadline:
            raise AssertionError("g2.reset_contention_barrier_failed")
        sleep(0.02)


def persisted(directory):
    with sqlite3.connect((directory / "native.db").resolve().as_uri() + "?mode=ro", uri=True) as conn:
        return list(conn.iterdump()), (directory / "sessions/sessions.json").read_bytes()


def worker(stage, directory, name, operation):
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_governance_g2_reset_contention import verify_worker_stage
    source, host_source = verify_worker_stage(stage)
    import hermes_state
    from hermes_cli import middleware
    from project_maya.audit import LocalJsonlAuditSink
    from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
    from project_maya.hermes_plugins import session_reset
    from project_maya.hermes_plugins.reset_publication import CandidateResetPreparation
    from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT
    assert Path(hermes_state.__file__).resolve().is_relative_to(source)
    assert Path(session_reset.__file__).resolve().is_relative_to(host_source)
    gate = module("contention_gate_worker", "hermes_g2_reset_gate_native.py")
    restart = module("contention_restart_worker", "hermes_g2_restart_loop_native.py")
    patcher = pytest.MonkeyPatch()
    original, caller, reader = restart.resume_host(directory, patcher)
    loop = gate.loop_host.__wrapped__((original, caller, reader), patcher, directory)
    h = next(loop)
    h.binding.audit = LocalJsonlAuditSink(directory / (name + "-audit.jsonl"))
    rules = [("session.read", "route_state"), ("session.transition", "reset"),
             ("session.transition", "acknowledge_reset"), ("session.write", "end"), ("session.write", "create")]
    h.binding.gateway = PolicyAuthorizationGateway(tuple(PolicyRule(cap, operation=op, actor_id="alice") for cap, op in rules))
    h.reset = session_reset.CandidateNativeSessionReset(original[3], acknowledgement=ACKNOWLEDGEMENT)
    h.preparation = CandidateResetPreparation(h.reset, acknowledgement=ACKNOWLEDGEMENT, gateway_runner=h.runner)
    def forbidden(*args, **kwargs):
        raise AssertionError("g2.reset_contention_unexpected_transport")
    patcher.setattr(socket, "create_connection", forbidden)
    patcher.setattr(socket.socket, "connect", forbidden)
    ready, go = directory / (name + ".ready"), directory / (name + ".go")
    try:
        if operation == "atomic":
            with h.reset.authenticated_reset(h.binding.owner) as authority:
                ready.touch()
                wait_file(go)
                try:
                    receipt = h.store.reset_owned_session_candidate(authority)
                    assert receipt["state"] == "committed_pending_projection" and not receipt["dispatch_allowed"]
                    status = "committed"
                except middleware.MandatoryMiddlewareError:
                    status = "blocked"
            assert not authority.active and h.reset._active is None
        elif operation == "prepare":
            ready.touch()
            wait_file(go)
            try:
                with h.store.prepare_owned_reset_candidate(h.binding.owner):
                    pass
                status = "acknowledged"
            except middleware.MandatoryMiddlewareError:
                status = "blocked"
            assert h.preparation._current is None and h.reset._active is None
        else:
            raise ValueError("invalid operation")
        assert not h.agents and not h.requests and not h.db._conn.in_transaction
        return {"status": status, "pid": os.getpid(), "agents": 0, "requests": 0}
    finally:
        next(loop, None)
        middleware._mandatory_enabled = False
        h.db.close()
        patcher.undo()


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    import hermes_state
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_governance_g2_reset_contention import verify_stage
    verify_stage(Path(hermes_state.__file__).resolve().parent.parent)


@pytest.fixture
def reset_host(tmp_path, monkeypatch):
    gate = module("contention_gate_fixture", "hermes_g2_reset_gate_native.py")
    root = gate.host.__wrapped__(tmp_path, monkeypatch)
    original = next(root)
    loop = gate.loop_host.__wrapped__(gate.caller_host.__wrapped__(original), monkeypatch, tmp_path)
    try:
        h = gate.reset_host.__wrapped__(gate.cache_host.__wrapped__(gate.recognition_host.__wrapped__(next(loop)), monkeypatch))
        cursor = h.db._conn.execute("SELECT * FROM sessions WHERE id=?", (h.source,))
        h.original_source = dict(zip((column[0] for column in cursor.description), cursor.fetchone()))
        h.original_messages = list(h.db._conn.execute("SELECT * FROM messages ORDER BY id"))
        yield h
    finally:
        try:
            next(loop, None)
        finally:
            next(root, None)


@contextmanager
def child(directory, name, operation="prepare"):
    import hermes_state
    stage = Path(hermes_state.__file__).resolve().parent.parent
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", HERMES_HOME=str(directory / (name + "-home")))
    process = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), str(stage),
                                str(directory), name, operation], cwd=stage / "source", env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        wait_file(directory / (name + ".ready"), process)
        yield process
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=30)


def release(directory, name):
    (directory / (name + ".go")).touch()


def report(process):
    out, err = process.communicate(timeout=90)
    assert process.returncode == 0, "g2.reset_contention_worker_failed"
    assert "SYNTHETIC_OLD_HISTORY" not in out + err
    data = json.loads(out)
    assert data["agents"] == data["requests"] == 0 and data["pid"] != os.getpid()
    return data


def committed_once(h, state):
    conn = h.db._conn
    assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert conn.execute("PRAGMA foreign_key_check").fetchone() is None
    assert conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 2
    assert conn.execute("SELECT count(*) FROM maya_session_transitions_v1 WHERE operation='reset'").fetchone()[0] == 1
    target, version = conn.execute("SELECT session_id,route_version FROM maya_session_routes_v1").fetchone()
    assert target != h.source and version == 2
    assert conn.execute("SELECT generation FROM maya_session_projection_v1").fetchone()[0] == 2
    assert conn.execute("SELECT state FROM maya_session_transitions_v1 WHERE operation='reset'").fetchone()[0] == state
    assert conn.execute("SELECT ended_at,end_reason FROM sessions WHERE id=?", (h.source,)).fetchone()[0] is not None
    assert conn.execute("SELECT end_reason FROM sessions WHERE id=?", (h.source,)).fetchone()[0] == "session_reset"
    assert tuple(conn.execute("SELECT parent_session_id,user_id FROM sessions WHERE id=?", (target,)).fetchone()) == (h.source, "alice")
    assert tuple(conn.execute("SELECT lifecycle_status,parent_session_id FROM maya_session_owners_v1 WHERE session_id=?", (target,)).fetchone()) == ("active", h.source)
    cursor = conn.execute("SELECT * FROM sessions WHERE id=?", (h.source,))
    retained = dict(zip((column[0] for column in cursor.description), cursor.fetchone()))
    assert {key: value for key, value in retained.items() if key not in {"ended_at", "end_reason"}} == {
        key: value for key, value in h.original_source.items() if key not in {"ended_at", "end_reason"}}
    assert list(conn.execute("SELECT * FROM messages ORDER BY id")) == h.original_messages
    assert not h.agents and not h.requests and h.db.get_messages(target) == []
    if state == "caller_acknowledged":
        assert h.store.read_owned_session_candidate(h.binding.owner).session_id == target
    return target


def test_busy_old_authenticated_request_blocks_other_process(reset_host, tmp_path):
    h = reset_host
    before = persisted(tmp_path)
    with child(tmp_path, "busy") as process:
        with h.store.authenticated_owned_session_candidate(h.binding.owner) as entry:
            root = h.reader._active
            assert entry.session_id == h.source and root.lease.is_active
            cache = dict(h.store._entries)
            release(tmp_path, "busy")
            assert report(process)["status"] == "blocked"
            assert persisted(tmp_path) == before and h.store._entries == cache and root.lease.is_active
    assert not root.lease.is_active and h.reader._active is None and not h.store._entries
    with h.store.prepare_owned_reset_candidate(h.binding.owner):
        pass
    committed_once(h, "caller_acknowledged")


def test_native_commit_exclusion_blocks_competing_preparation(reset_host, tmp_path, monkeypatch):
    h = reset_host
    before = persisted(tmp_path)
    old = h.db.get_messages(h.source)
    with child(tmp_path, "commit") as process:
        commit = h.reset._commit
        def held(conn):
            assert conn.in_transaction
            release(tmp_path, "commit")
            assert report(process)["status"] == "blocked"
            assert persisted(tmp_path) == before
            commit(conn)
        monkeypatch.setattr(h.reset, "_commit", held)
        with h.store.prepare_owned_reset_candidate(h.binding.owner):
            pass
    committed_once(h, "caller_acknowledged")
    assert h.db.get_messages(h.source) == old


def test_competing_prepared_descriptors_allocate_only_once(reset_host, tmp_path):
    from hermes_cli import middleware
    h = reset_host
    old = h.db.get_messages(h.source)
    old_projection = h.reset.coordinator.index.read_bytes()
    with child(tmp_path, "first", "atomic") as first, child(tmp_path, "second", "atomic") as second:
        release(tmp_path, "first")
        release(tmp_path, "second")
        outcomes = [report(first), report(second)]
    assert outcomes[0]["pid"] != outcomes[1]["pid"]
    assert sorted(item["status"] for item in outcomes) == ["blocked", "committed"]
    committed_once(h, "committed_pending_projection")
    assert h.db.get_messages(h.source) == old and h.reset.coordinator.index.read_bytes() == old_projection
    before = persisted(tmp_path)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.read_owned_session_candidate(h.binding.owner)
    assert persisted(tmp_path) == before


def test_pending_caller_receipt_blocks_competing_reset(reset_host, tmp_path):
    h = reset_host
    old = h.db.get_messages(h.source)
    with child(tmp_path, "pending") as process:
        with h.store.prepare_owned_reset_candidate(h.binding.owner):
            before = persisted(tmp_path)
            assert not h.db._conn.in_transaction
            release(tmp_path, "pending")
            assert report(process)["status"] == "blocked"
            assert persisted(tmp_path) == before and h.preparation._confirmed is None
    committed_once(h, "caller_acknowledged")
    assert h.db.get_messages(h.source) == old


if __name__ == "__main__":
    try:
        stage, directory, name, operation = sys.argv[1:]
        assert name in {"busy", "commit", "first", "second", "pending"}
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = worker(Path(stage), Path(directory), name, operation)
    except BaseException:
        print(json.dumps({"status": "failed", "reason_code": "g2.reset_contention_worker_failed"}))
        raise SystemExit(1) from None
    print(json.dumps(result, sort_keys=True))

"""Real process locks/denied competing hosts; never transfer live confirmation."""
from contextlib import closing, contextmanager, redirect_stderr, redirect_stdout
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
DENIALS = frozenset({"governance.transition_busy", "governance.transition_recovery_required",
                    "governance.switch_source_invalid", "governance.reset_confirmation_required"})
SENTINELS = ("SYNTHETIC_OLD_HISTORY", "SYNTHETIC_CHILD_HISTORY", "synthetic-fixture-not-a-secret", "sk-proj-")


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tests" / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def wait_file(path, process=None):
    deadline = monotonic() + 90
    while not path.is_file():
        if (process is not None and process.poll() is not None) or monotonic() >= deadline:
            raise AssertionError("g2.switch_contention_barrier_failed")
        sleep(0.02)


def persisted(directory):
    with sqlite3.connect((directory / "native.db").resolve().as_uri() + "?mode=ro", uri=True) as conn:
        return list(conn.iterdump()), (directory / "sessions/sessions.json").read_bytes()


def no_transport(patcher):
    def forbidden(*args, **kwargs):
        raise AssertionError("g2.switch_contention_unexpected_transport")
    patcher.setattr(socket, "create_connection", forbidden)
    patcher.setattr(socket.socket, "connect", forbidden)
    patcher.setattr(socket.socket, "connect_ex", forbidden)
    patcher.setattr(socket.socket, "sendto", forbidden)


def verify_worker(stage):
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_governance_g2_switch_contention import verify_worker_stage
    return verify_worker_stage(stage)


def worker(stage, directory, name, operation):
    source, host_source = verify_worker(stage)
    import hermes_state
    from hermes_cli import middleware
    from project_maya.hermes_plugins import session_switch
    assert Path(hermes_state.__file__).resolve().is_relative_to(source)
    assert Path(session_switch.__file__).resolve().is_relative_to(host_source)
    patcher = pytest.MonkeyPatch()
    no_transport(patcher)
    ready = directory / (name + ".ready")
    result = {"pid": os.getpid(), "agents": 0, "requests": 0}
    if operation in {"projection", "sqlite"}:
        ready.touch()
        wait_file(directory / (name + ".go1"))
        if operation == "projection":
            import portalocker
            assert portalocker.__version__ == "3.2.0"
            lock = portalocker.Lock(directory / "sessions/maya-session-projection.lock",
                                   mode="r+b", timeout=0, fail_when_locked=True)
        else:
            # Real external SQLite write-lock holder; no DDL/DML or authority.
            @contextmanager
            def transaction():
                with closing(sqlite3.connect(directory / "native.db", isolation_level=None)) as conn:
                    conn.execute("BEGIN IMMEDIATE")
                    try:
                        yield
                    finally:
                        conn.rollback()
            lock = transaction()
        with lock:
            (directory / (name + ".held")).touch()
            wait_file(directory / (name + ".go2"))
        return dict(result, status="released")

    assert operation in {"prepare", "pending", "atomic"}
    from project_maya.audit import LocalJsonlAuditSink
    from project_maya.hermes_plugins.governance import GovernanceBoundaryError
    from project_maya.hermes_plugins.reset_publication import CandidateResetPreparation
    from project_maya.hermes_plugins.session_reset import CandidateNativeSessionReset
    from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT
    from project_maya.hermes_plugins.switch_publication import CandidateSwitchPreparation
    fixtures = module("switch_contention_fixture", "hermes_g2_switch_composition_native.py")
    restart = module("switch_contention_restart", "hermes_g2_restart_loop_native.py")
    original, caller, reader = restart.resume_host(directory, patcher)
    loop = fixtures.loop_host.__wrapped__((original, caller, reader), patcher, directory)
    h = next(loop)
    h.binding.audit = LocalJsonlAuditSink(directory / (name + "-audit.jsonl"))
    fixtures.policy(h)
    h.reset = CandidateNativeSessionReset(original[3], acknowledgement=ACKNOWLEDGEMENT)
    h.preparation = CandidateResetPreparation(h.reset, acknowledgement=ACKNOWLEDGEMENT, gateway_runner=h.runner)
    h.switch = session_switch.CandidateNativeSessionSwitch(h.preparation, acknowledgement=ACKNOWLEDGEMENT)
    h.switch_preparation = CandidateSwitchPreparation(h.switch, acknowledgement=ACKNOWLEDGEMENT, gateway_runner=h.runner)
    parent = h.db._conn.execute("SELECT session_id FROM maya_session_owners_v1 WHERE parent_session_id IS NULL").fetchone()[0]
    assert h.preparation._confirmed is h.switch_preparation._confirmed is None
    observed = []
    authority_entries = 0
    exclusive = original[3]._exclusive
    read_source = h.switch.source
    authenticate = h.switch.authenticated_switch

    def remember(error):
        code = str(error)
        assert code in DENIALS, "g2.switch_contention_unexpected_denial"
        observed.append(code)

    @contextmanager
    def observe_lock():
        try:
            with exclusive():
                yield
        except GovernanceBoundaryError as error:
            remember(error)
            raise

    def observe_source(*args, **kwargs):
        try:
            return read_source(*args, **kwargs)
        except GovernanceBoundaryError as error:
            remember(error)
            raise

    @contextmanager
    def observe_authority(*args):
        nonlocal authority_entries
        with authenticate(*args) as authority:
            authority_entries += 1
            yield authority

    patcher.setattr(original[3], "_exclusive", observe_lock)
    patcher.setattr(h.switch, "source", observe_source)
    patcher.setattr(h.switch, "authenticated_switch", observe_authority)
    codes = []
    try:
        ready.touch()
        for phase in range(1, 3 if operation == "pending" else 2):
            wait_file(directory / (name + ".go" + str(phase)))
            before = persisted(directory)
            observed.clear()
            with pytest.raises((GovernanceBoundaryError, middleware.MandatoryMiddlewareError)):
                if operation == "atomic":
                    with h.switch.authenticated_switch(h.binding.owner, parent) as authority:
                        h.store.switch_owned_session_candidate(authority)
                else:
                    with h.store.prepare_owned_switch_candidate(h.binding.owner, parent):
                        pytest.fail("unconfirmed competing host entered caller")
            assert observed and authority_entries == 0
            code = observed[0]
            codes.append(code)
            assert persisted(directory) == before
            assert h.preparation._confirmed is h.switch_preparation._confirmed is None
            assert h.switch._active is h.switch_preparation._current is reader._active is None
            assert not h.agents and not h.requests and not h.store._entries and not h.db._conn.in_transaction
            audit = h.binding.audit.path.read_text() if h.binding.audit.path.exists() else ""
            assert not any(marker in audit for marker in SENTINELS)
            result_path = directory / (name + ".result" + str(phase) + ".json")
            temporary = result_path.with_suffix(".tmp")
            temporary.write_text(json.dumps({"status": "blocked", "code": code}), encoding="utf-8")
            temporary.replace(result_path)
        return dict(result, status="blocked", codes=codes, authority_entries=authority_entries,
                    reset_confirmation=False, switch_confirmation=False)
    finally:
        next(loop, None)
        middleware._mandatory_enabled = False
        h.db.close()
        patcher.undo()


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    import hermes_state
    verify_worker(Path(hermes_state.__file__).resolve().parent.parent)


@pytest.fixture
def switch_host(tmp_path, monkeypatch):
    fixtures = module("switch_contention_parent", "hermes_g2_switch_composition_native.py")
    root = fixtures.host.__wrapped__(tmp_path, monkeypatch)
    original = next(root)
    no_transport(monkeypatch)
    loop = fixtures.loop_host.__wrapped__(fixtures.caller_host.__wrapped__(original), monkeypatch, tmp_path)
    try:
        h = fixtures.composed_host.__wrapped__(fixtures.switch_host.__wrapped__(
            fixtures.reset_host.__wrapped__(fixtures.cache_host.__wrapped__(
                fixtures.recognition_host.__wrapped__(next(loop)), monkeypatch))), monkeypatch)
        cursor = h.db._conn.execute("SELECT * FROM sessions ORDER BY id")
        columns = [c[0] for c in cursor.description]
        h.retained_sessions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        h.retained_messages = list(h.db._conn.execute("SELECT * FROM messages ORDER BY id"))
        h.retained_receipts = list(h.db._conn.execute("SELECT * FROM maya_session_transitions_v1 ORDER BY correlation_id"))
        yield h
    finally:
        try:
            next(loop, None)
        finally:
            next(root, None)


@contextmanager
def child(directory, name, operation):
    import hermes_state
    stage = Path(hermes_state.__file__).resolve().parent.parent
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", HERMES_HOME=str(directory / (name + "-home")))
    process = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), str(stage),
                                str(directory), name, operation], cwd=directory, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        wait_file(directory / (name + ".ready"), process)
        yield process
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=30)


def release(directory, name, phase=1):
    (directory / (name + ".go" + str(phase))).touch()


def report(process):
    out, err = process.communicate(timeout=90)
    assert process.returncode == 0, "g2.switch_contention_worker_failed"
    assert not any(marker in out + err for marker in SENTINELS)
    data = json.loads(out)
    assert data["agents"] == data["requests"] == 0 and data["pid"] != os.getpid()
    return data


def phase_report(directory, name, phase, process):
    path = directory / (name + ".result" + str(phase) + ".json")
    wait_file(path, process)
    data = json.loads(path.read_text())
    assert data["status"] == "blocked" and data["code"] in DENIALS
    return data["code"]


def complete(h):
    with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source) as receipt:
        assert receipt["state"] == "published_pending_caller" and not receipt["dispatch_allowed"]
    completed(h)


def completed(h):
    conn = h.db._conn
    assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert conn.execute("PRAGMA foreign_key_check").fetchone() is None
    assert conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 2
    assert tuple(conn.execute("SELECT session_id,route_version FROM maya_session_routes_v1").fetchone()) == (h.source, 3)
    assert conn.execute("SELECT generation FROM maya_session_projection_v1").fetchone()[0] == 3
    assert conn.execute("SELECT count(*) FROM maya_session_transitions_v1 WHERE operation='switch'").fetchone()[0] == 1
    assert conn.execute("SELECT state FROM maya_session_transitions_v1 WHERE operation='switch'").fetchone()[0] == "caller_acknowledged"
    assert list(conn.execute("SELECT * FROM maya_session_transitions_v1 WHERE operation<>'switch' ORDER BY correlation_id")) == h.retained_receipts
    assert list(conn.execute("SELECT * FROM messages ORDER BY id")) == h.retained_messages
    cursor = conn.execute("SELECT * FROM sessions ORDER BY id")
    columns = [c[0] for c in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    kept = lambda row: {k: v for k, v in row.items() if k not in {"ended_at", "end_reason"}}
    assert [kept(row) for row in rows] == [kept(row) for row in h.retained_sessions]
    assert tuple(conn.execute("SELECT ended_at,end_reason FROM sessions WHERE id=?", (h.source,)).fetchone()) == (None, None)
    assert conn.execute("SELECT end_reason FROM sessions WHERE id=? AND ended_at IS NOT NULL", (h.child,)).fetchone()[0] == "session_switch"
    assert conn.execute("SELECT lifecycle_status FROM maya_session_owners_v1 WHERE session_id=?", (h.source,)).fetchone()[0] == "active"
    assert conn.execute("SELECT lifecycle_status FROM maya_session_owners_v1 WHERE session_id=?", (h.child,)).fetchone()[0] == "ended"
    assert h.original[3].index.read_bytes() == h.original[3]._state(conn)[2]
    assert h.store.read_owned_session_candidate(h.binding.owner).session_id == h.source
    assert h.switch._active is h.switch_preparation._current is h.reader._active is None
    assert not h.agents and not h.requests and not h.wire and not conn.in_transaction
    audit = h.binding.audit.path.read_text()
    assert not any(marker in audit for marker in SENTINELS)
    outcomes = [json.loads(line)["operation"] for line in audit.splitlines()
                if json.loads(line)["event_type"] == "outcome.session_switch"]
    assert outcomes == ["switch_published", "acknowledge_switch"]


@pytest.mark.parametrize("prepared", [False, True], ids=["projection_lock", "prepared_sink_lock"])
def test_external_projection_lock_has_zero_effects(switch_host, tmp_path, prepared):
    from hermes_cli import middleware
    h = switch_host
    before = persisted(tmp_path)
    with child(tmp_path, "projection", "projection") as process:
        if prepared:
            with h.switch.authenticated_switch(h.binding.owner, h.source) as authority:
                release(tmp_path, "projection")
                wait_file(tmp_path / "projection.held", process)
                with pytest.raises(middleware.MandatoryMiddlewareError):
                    h.store.switch_owned_session_candidate(authority)
                assert not authority.attempted and persisted(tmp_path) == before
                release(tmp_path, "projection", 2)
                assert report(process)["status"] == "released"
            assert not authority.active
            with pytest.raises(middleware.MandatoryMiddlewareError):
                h.store.switch_owned_session_candidate(authority)
        else:
            release(tmp_path, "projection")
            wait_file(tmp_path / "projection.held", process)
            with pytest.raises(middleware.MandatoryMiddlewareError):
                with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source):
                    pytest.fail("busy projection accepted")
            assert persisted(tmp_path) == before and h.switch._active is None
            release(tmp_path, "projection", 2)
            assert report(process)["status"] == "released"
    complete(h)


def test_external_sqlite_writer_blocks_prepared_sink(switch_host, tmp_path):
    from hermes_cli import middleware
    h = switch_host
    before = persisted(tmp_path)
    busy_timeout = h.db._conn.execute("PRAGMA busy_timeout").fetchone()[0]
    with child(tmp_path, "sqlite", "sqlite") as process:
        with h.switch.authenticated_switch(h.binding.owner, h.source) as authority:
            release(tmp_path, "sqlite")
            wait_file(tmp_path / "sqlite.held", process)
            with pytest.raises(middleware.MandatoryMiddlewareError):
                h.store.switch_owned_session_candidate(authority)
            assert authority.attempted and not h.db._conn.in_transaction and persisted(tmp_path) == before
            assert h.db._conn.execute("PRAGMA busy_timeout").fetchone()[0] == busy_timeout
            release(tmp_path, "sqlite", 2)
            assert report(process)["status"] == "released"
        assert not authority.active
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.store.switch_owned_session_candidate(authority)
    complete(h)


def test_active_source_conversation_blocks_competing_host(switch_host, tmp_path):
    h = switch_host
    before = persisted(tmp_path)
    with child(tmp_path, "busy", "prepare") as process:
        with h.store.authenticated_owned_session_candidate(h.binding.owner) as entry:
            root = h.reader._active
            cache = dict(h.store._entries)
            assert entry.session_id == h.child and root.lease.is_active
            release(tmp_path, "busy")
            assert report(process)["codes"] == ["governance.transition_busy"]
            assert persisted(tmp_path) == before and h.store._entries == cache and root.lease.is_active
    assert not root.lease.is_active and h.reader._active is None and not h.store._entries
    complete(h)


@pytest.mark.parametrize("boundary", ["native_commit", "publication"])
def test_owner_exclusion_blocks_competing_host(switch_host, tmp_path, monkeypatch, boundary):
    h = switch_host
    with child(tmp_path, "excluded", "prepare") as process:
        target, name = (h.switch, "_commit") if boundary == "native_commit" else (h.original[3], "_publish")
        original = getattr(target, name)
        def held(value):
            if boundary == "native_commit":
                assert h.db._conn.in_transaction
            before = persisted(tmp_path)
            release(tmp_path, "excluded")
            assert report(process)["codes"] == ["governance.transition_busy"]
            assert persisted(tmp_path) == before
            return original(value)
        monkeypatch.setattr(target, name, held)
        complete(h)


def test_pending_and_acknowledged_owner_cannot_be_overwritten(switch_host, tmp_path):
    h = switch_host
    with child(tmp_path, "pending", "pending") as process:
        with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source):
            before = persisted(tmp_path)
            assert not h.db._conn.in_transaction and h.switch_preparation._confirmed is None
            release(tmp_path, "pending")
            assert phase_report(tmp_path, "pending", 1, process) == "governance.transition_recovery_required"
            assert persisted(tmp_path) == before
        completed(h)
        before = persisted(tmp_path)
        release(tmp_path, "pending", 2)
        data = report(process)
        assert data["codes"] == ["governance.transition_recovery_required", "governance.switch_source_invalid"]
        assert persisted(tmp_path) == before
    completed(h)


def test_independent_hosts_cannot_mint_switch_descriptors(switch_host, tmp_path):
    h = switch_host
    before = persisted(tmp_path)
    with child(tmp_path, "first", "atomic") as first, child(tmp_path, "second", "atomic") as second:
        release(tmp_path, "first")
        one = report(first)
        release(tmp_path, "second")
        two = report(second)
    assert one["pid"] != two["pid"]
    assert one["codes"] == two["codes"] == ["governance.reset_confirmation_required"]
    assert one["authority_entries"] == two["authority_entries"] == 0
    assert not one["reset_confirmation"] and not two["reset_confirmation"]
    assert persisted(tmp_path) == before
    complete(h)


if __name__ == "__main__":
    try:
        stage, directory, name, operation = sys.argv[1:]
        assert name in {"projection", "sqlite", "busy", "excluded", "pending", "first", "second"}
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = worker(Path(stage), Path(directory), name, operation)
    except BaseException:
        print(json.dumps({"status": "failed", "reason_code": "g2.switch_contention_worker_failed"}))
        raise SystemExit(1) from None
    print(json.dumps(result, sort_keys=True))

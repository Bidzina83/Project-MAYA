"""Native switch outcome uncertainty plus failed quarantine; no runtime patch."""
import asyncio
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
SENTINELS = ("SYNTHETIC_PRIVATE_FAILURE", "SYNTHETIC_OLD_HISTORY", "SYNTHETIC_CHILD_HISTORY",
             "synthetic-fixture-not-a-secret")


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tests" / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def verify_worker(stage):
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_governance_g2_switch_uncertainty import verify_worker_stage
    return verify_worker_stage(stage)


def persisted(directory):
    with sqlite3.connect((directory / "native.db").resolve().as_uri() + "?mode=ro", uri=True) as conn:
        return list(conn.iterdump()), (directory / "sessions/sessions.json").read_bytes()


def failure(*args, **kwargs):
    raise OSError("SYNTHETIC_PRIVATE_FAILURE")


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    import hermes_state
    verify_worker(Path(hermes_state.__file__).resolve().parent.parent)


@pytest.fixture
def switch_host(tmp_path, monkeypatch):
    fixtures = module("switch_uncertainty_fixture", "hermes_g2_switch_composition_native.py")
    root = fixtures.host.__wrapped__(tmp_path, monkeypatch)
    original = next(root)
    loop = fixtures.loop_host.__wrapped__(fixtures.caller_host.__wrapped__(original), monkeypatch, tmp_path)
    try:
        h = fixtures.composed_host.__wrapped__(fixtures.switch_host.__wrapped__(
            fixtures.reset_host.__wrapped__(fixtures.cache_host.__wrapped__(
                fixtures.recognition_host.__wrapped__(next(loop)), monkeypatch))), monkeypatch)
        no_transport(monkeypatch)
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


def no_transport(patcher):
    import socket
    def forbidden(*args, **kwargs):
        raise AssertionError("g2.switch_uncertainty_unexpected_socket")
    patcher.setattr(socket, "create_connection", forbidden)
    patcher.setattr(socket.socket, "connect", forbidden)
    patcher.setattr(socket.socket, "connect_ex", forbidden)
    patcher.setattr(socket.socket, "sendto", forbidden)


def state(h):
    return h.db._conn.execute("SELECT state FROM maya_session_transitions_v1 WHERE operation='switch'").fetchone()[0]


def run_failed(h):
    from hermes_cli import middleware
    with pytest.raises(middleware.MandatoryMiddlewareError) as error:
        with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source):
            pass
    assert not any(marker in str(error.value) for marker in SENTINELS)


def blocked(h, directory, expected, *, old_projection=False):
    from hermes_cli import middleware
    conn = h.db._conn
    assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert conn.execute("PRAGMA foreign_key_check").fetchone() is None
    assert conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 2
    assert conn.execute("SELECT count(*) FROM maya_session_transitions_v1 WHERE operation='switch'").fetchone()[0] == 1
    assert state(h) == expected
    assert tuple(conn.execute("SELECT session_id,route_version FROM maya_session_routes_v1").fetchone()) == (h.source, 3)
    assert conn.execute("SELECT generation FROM maya_session_projection_v1").fetchone()[0] == 3
    assert list(conn.execute("SELECT * FROM messages ORDER BY id")) == h.retained_messages
    assert list(conn.execute("SELECT * FROM maya_session_transitions_v1 WHERE operation<>'switch' ORDER BY correlation_id")) == h.retained_receipts
    cursor = conn.execute("SELECT * FROM sessions ORDER BY id")
    columns = [c[0] for c in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    keep = lambda row: {k: v for k, v in row.items() if k not in {"ended_at", "end_reason"}}
    assert [keep(row) for row in rows] == [keep(row) for row in h.retained_sessions]
    assert tuple(conn.execute("SELECT ended_at,end_reason FROM sessions WHERE id=?", (h.source,)).fetchone()) == (None, None)
    assert conn.execute("SELECT end_reason FROM sessions WHERE id=? AND ended_at IS NOT NULL", (h.child,)).fetchone()[0] == "session_switch"
    assert conn.execute("SELECT lifecycle_status FROM maya_session_owners_v1 WHERE session_id=?", (h.source,)).fetchone()[0] == "active"
    assert conn.execute("SELECT lifecycle_status FROM maya_session_owners_v1 WHERE session_id=?", (h.child,)).fetchone()[0] == "ended"
    if not old_projection:
        assert h.original[3].index.read_bytes() == h.original[3]._state(conn)[2]
    assert h.switch_preparation._confirmed is h.switch_preparation._current is h.switch._active is None
    assert h.switch_preparation._phase == "idle" and not conn.in_transaction
    assert not h.agents and not h.requests and not h.wire
    before = persisted(directory)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.read_owned_session_candidate(h.binding.owner)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        with h.store.authenticated_owned_session_candidate(h.binding.owner):
            pytest.fail("uncertain switch entered caller")
    with pytest.raises(middleware.MandatoryMiddlewareError):
        with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source):
            pytest.fail("uncertain switch replayed")
    assert persisted(directory) == before and not h.store._entries and h.reader._active is None
    audit = h.binding.audit.path.read_text()
    assert not any(marker in audit for marker in SENTINELS)


def restart(directory):
    import hermes_state
    stage = Path(hermes_state.__file__).resolve().parent.parent
    before = persisted(directory)
    result = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), str(stage), str(directory)],
        cwd=directory, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", HERMES_HOME=str(directory / "restart-home")),
        capture_output=True, text=True, timeout=150)
    assert result.returncode == 0, "g2.switch_uncertainty_restart_failed"
    assert not any(marker in result.stdout + result.stderr for marker in SENTINELS)
    assert json.loads(result.stdout) == {"status": "blocked", "unchanged": True, "confirmations": False}
    assert persisted(directory) == before


@pytest.fixture(autouse=True)
def secret_safe_output(capsys, caplog):
    yield
    output = capsys.readouterr()
    assert not any(marker in output.out + output.err + caplog.text for marker in SENTINELS)


def test_unknown_atomic_commit_blocks_publication_and_retry(switch_host, tmp_path, monkeypatch):
    h = switch_host
    old = persisted(tmp_path)[1]
    commit = h.switch._commit
    def uncertain(conn):
        commit(conn)
        failure()
    monkeypatch.setattr(h.switch, "_commit", uncertain)
    publish = Mock(side_effect=AssertionError("unknown commit must not publish"))
    monkeypatch.setattr(h.switch_preparation, "_publish", publish)
    run_failed(h)
    publish.assert_not_called()
    assert persisted(tmp_path)[1] == old
    blocked(h, tmp_path, "committed_pending_projection", old_projection=True)
    restart(tmp_path)


def test_completed_publication_reports_failure(switch_host, tmp_path, monkeypatch):
    h = switch_host
    old = persisted(tmp_path)[1]
    publish = h.original[3]._publish
    def uncertain(raw):
        publish(raw)
        failure()
    monkeypatch.setattr(h.original[3], "_publish", uncertain)
    run_failed(h)
    assert persisted(tmp_path)[1] != old
    blocked(h, tmp_path, "committed_pending_projection")
    restart(tmp_path)


@pytest.mark.parametrize("expected", ["projection_verified", "published_pending_caller"])
def test_publication_receipt_commit_reports_uncertainty(switch_host, tmp_path, monkeypatch, expected):
    h = switch_host
    commit = h.switch_preparation._commit
    def uncertain(conn):
        commit(conn)
        if state(h) == expected:
            failure()
    monkeypatch.setattr(h.switch_preparation, "_commit", uncertain)
    run_failed(h)
    blocked(h, tmp_path, expected)


@pytest.mark.parametrize("timing", ["before", "after"])
@pytest.mark.parametrize("cleanup", ["normal", "unavailable", "audit_unavailable"])
def test_ack_commit_failure_with_quarantine_faults(switch_host, tmp_path, monkeypatch, timing, cleanup):
    h = switch_host
    p = h.switch_preparation
    commit = p._commit
    def uncertain(conn):
        if state(h) == "caller_acknowledged":
            if timing == "after":
                commit(conn)
            failure()
        commit(conn)
    monkeypatch.setattr(p, "_commit", uncertain)
    if cleanup == "unavailable":
        monkeypatch.setattr(p, "_quarantine", failure)
    elif cleanup == "audit_unavailable":
        audit = h.binding.audit.write
        def unavailable(record):
            if record.event_type == "outcome.session_switch" and record.operation == "quarantine_switch":
                failure()
            return audit(record)
        monkeypatch.setattr(h.binding.audit, "write", unavailable)
    run_failed(h)
    expected = ("caller_acknowledged" if timing == "after" else "published_pending_caller") if cleanup == "unavailable" else "caller_quarantined"
    blocked(h, tmp_path, expected)
    if cleanup == "unavailable":
        restart(tmp_path)


@pytest.mark.parametrize("operation", ["switch_published", "acknowledge_switch"])
def test_required_outcome_and_quarantine_audit_fail(switch_host, tmp_path, monkeypatch, operation):
    h = switch_host
    audit = h.binding.audit.write
    def unavailable(record):
        if record.event_type == "outcome.session_switch" and record.operation in {operation, "quarantine_switch"}:
            failure()
        return audit(record)
    monkeypatch.setattr(h.binding.audit, "write", unavailable)
    run_failed(h)
    blocked(h, tmp_path, "projection_verified" if operation == "switch_published" else "caller_quarantined")


@pytest.mark.parametrize("kind", ["exception", "cancel"])
def test_original_caller_failure_survives_failed_quarantine(switch_host, tmp_path, monkeypatch, kind):
    h = switch_host
    monkeypatch.setattr(h.switch_preparation, "_quarantine", failure)
    expected = ValueError if kind == "exception" else asyncio.CancelledError
    with pytest.raises(expected) as error:
        with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source):
            if kind == "exception":
                raise ValueError("caller_failed_fixture")
            raise asyncio.CancelledError()
    assert not any(marker in str(error.value) for marker in SENTINELS)
    blocked(h, tmp_path, "published_pending_caller")


@pytest.mark.parametrize("timing", ["before", "after"])
def test_quarantine_commit_failure_preserves_original_ack_failure(switch_host, tmp_path, monkeypatch, timing):
    h = switch_host
    p = h.switch_preparation
    connection = h.db._conn
    commit = p._commit
    def ack_failure(conn):
        if state(h) == "caller_acknowledged":
            failure()
        commit(conn)
    class ConnectionFault:
        def __getattr__(self, name):
            return getattr(connection, name)
        def commit(self):
            if p._phase == "failed" and state(h) == "caller_quarantined":
                if timing == "after":
                    connection.commit()
                failure()
            connection.commit()
    monkeypatch.setattr(h.db, "_conn", ConnectionFault())
    monkeypatch.setattr(p, "_commit", ack_failure)
    run_failed(h)
    blocked(h, tmp_path, "published_pending_caller" if timing == "before" else "caller_quarantined")
    if timing == "after":
        restart(tmp_path)


def test_final_lock_failure_and_audit_outage_do_not_adopt_ack(switch_host, tmp_path, monkeypatch):
    from hermes_cli import middleware
    h = switch_host
    p = h.switch_preparation
    lock, audit = p._lock, h.binding.audit.write
    calls = []
    def unavailable(record):
        calls.append(record.operation)
        failure()
    class FailedRelease:
        def acquire(self, **kwargs):
            return lock.acquire(**kwargs)
        def release(self):
            lock.release()
            h.binding.audit.write = unavailable
            failure()
    monkeypatch.setattr(p, "_lock", FailedRelease())
    run_failed(h)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.read_owned_session_candidate(h.binding.owner)
    assert calls
    # Restoring the audit sink cannot manufacture the missing live confirmation.
    monkeypatch.setattr(h.binding.audit, "write", audit)
    blocked(h, tmp_path, "caller_acknowledged")
    restart(tmp_path)


def test_native_cleanup_then_error_with_unavailable_quarantine(switch_host, tmp_path, monkeypatch):
    h = switch_host
    cleanup = h.runner._clear_owned_switch_security_candidate
    called = []
    def partial(preparation):
        cleanup(preparation)
        assert preparation._cleanup_authority is preparation._current
        called.append(True)
        failure()
    monkeypatch.setattr(h.runner, "_clear_owned_switch_security_candidate", partial)
    monkeypatch.setattr(h.switch_preparation, "_quarantine", failure)
    run_failed(h)
    assert called == [True]
    blocked(h, tmp_path, "published_pending_caller")


def restart_probe(stage, directory):
    source, host_source = verify_worker(stage)
    import hermes_state
    from hermes_cli import middleware
    from project_maya.hermes_plugins import switch_publication
    from project_maya.hermes_plugins.reset_publication import CandidateResetPreparation
    from project_maya.hermes_plugins.session_reset import CandidateNativeSessionReset
    from project_maya.hermes_plugins.session_switch import CandidateNativeSessionSwitch
    from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT
    assert Path(hermes_state.__file__).resolve().is_relative_to(source)
    assert Path(switch_publication.__file__).resolve().is_relative_to(host_source)
    before = persisted(directory)
    fixtures = module("switch_uncertainty_restart_fixture", "hermes_g2_switch_composition_native.py")
    resume = module("switch_uncertainty_reopen", "hermes_g2_restart_loop_native.py")
    patcher = pytest.MonkeyPatch()
    no_transport(patcher)
    original, caller, reader = resume.resume_host(directory, patcher)
    loop = fixtures.loop_host.__wrapped__((original, caller, reader), patcher, directory)
    h = next(loop)
    fixtures.policy(h)
    h.reset = CandidateNativeSessionReset(original[3], acknowledgement=ACKNOWLEDGEMENT)
    h.preparation = CandidateResetPreparation(h.reset, acknowledgement=ACKNOWLEDGEMENT, gateway_runner=h.runner)
    h.switch = CandidateNativeSessionSwitch(h.preparation, acknowledgement=ACKNOWLEDGEMENT)
    h.switch_preparation = switch_publication.CandidateSwitchPreparation(h.switch,
        acknowledgement=ACKNOWLEDGEMENT, gateway_runner=h.runner)
    target = h.db._conn.execute("SELECT session_id FROM maya_session_routes_v1").fetchone()[0]
    try:
        assert h.preparation._confirmed is h.switch_preparation._confirmed is None
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.store.read_owned_session_candidate(h.binding.owner)
        with pytest.raises(middleware.MandatoryMiddlewareError):
            with h.store.authenticated_owned_session_candidate(h.binding.owner):
                pytest.fail("restart entered uncertain caller")
        with pytest.raises(middleware.MandatoryMiddlewareError):
            with h.store.prepare_owned_switch_candidate(h.binding.owner, target):
                pytest.fail("restart replayed uncertain switch")
        assert not h.agents and not h.requests and not h.store._entries and reader._active is None
        assert persisted(directory) == before
        return {"status": "blocked", "unchanged": True, "confirmations": False}
    finally:
        next(loop, None)
        middleware._mandatory_enabled = False
        h.db.close()
        patcher.undo()


if __name__ == "__main__":
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = restart_probe(Path(sys.argv[1]), Path(sys.argv[2]))
    except BaseException:
        print(json.dumps({"status": "failed", "reason_code": "g2.switch_uncertainty_restart_failed"}))
        raise SystemExit(1) from None
    print(json.dumps(result, sort_keys=True))

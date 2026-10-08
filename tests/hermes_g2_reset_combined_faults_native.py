"""Combined reset failures on real native stores; unchanged Patch 34."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("combined_contention", ROOT / "tests/hermes_g2_reset_contention_native.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
reset_host = fixtures.reset_host


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    import hermes_state
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_governance_g2_reset_combined_faults import verify_stage
    verify_stage(Path(hermes_state.__file__).resolve().parent.parent)


def failure(*args, **kwargs):
    raise OSError("SYNTHETIC_PRIVATE_FAILURE")


def blocked(h, directory, expected):
    from hermes_cli import middleware
    target = fixtures.committed_once(h, expected) if expected != "caller_acknowledged" else None
    if target is None:
        # Durable acknowledgement is deliberately not host confirmation.
        conn = h.db._conn
        assert conn.execute("SELECT state FROM maya_session_transitions_v1 WHERE operation='reset'").fetchone()[0] == expected
        assert conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 2
        target = conn.execute("SELECT session_id FROM maya_session_routes_v1").fetchone()[0]
        assert h.db.get_messages(target) == []
        assert list(conn.execute("SELECT * FROM messages ORDER BY id")) == h.original_messages
        cursor = conn.execute("SELECT * FROM sessions WHERE id=?", (h.source,))
        old = dict(zip((column[0] for column in cursor.description), cursor.fetchone()))
        assert old["end_reason"] == "session_reset" and old["ended_at"] is not None
        assert {k: v for k, v in old.items() if k not in {"ended_at", "end_reason"}} == {
            k: v for k, v in h.original_source.items() if k not in {"ended_at", "end_reason"}}
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchone() is None
        assert conn.execute("SELECT route_version FROM maya_session_routes_v1").fetchone()[0] == 2
        assert conn.execute("SELECT generation FROM maya_session_projection_v1").fetchone()[0] == 2
        assert conn.execute("SELECT count(*) FROM maya_session_transitions_v1 WHERE operation='reset'").fetchone()[0] == 1
        assert tuple(conn.execute("SELECT parent_session_id,user_id FROM sessions WHERE id=?", (target,)).fetchone()) == (h.source, "alice")
    assert h.preparation._confirmed is None and h.preparation._current is None
    assert h.reset._active is None and h.preparation._phase == "idle"
    assert not h.db._conn.in_transaction and not h.agents and not h.requests
    before = fixtures.persisted(directory)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.read_owned_session_candidate(h.binding.owner)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        with h.store.authenticated_owned_session_candidate(h.binding.owner):
            pytest.fail("uncertain reset dispatched")
    with pytest.raises(middleware.MandatoryMiddlewareError):
        with h.store.prepare_owned_reset_candidate(h.binding.owner):
            pytest.fail("uncertain reset retried")
    assert fixtures.persisted(directory) == before
    assert not h.store._entries and not h.agents and not h.requests


def run_failed(h):
    from hermes_cli import middleware
    with pytest.raises(middleware.MandatoryMiddlewareError) as error:
        with h.store.prepare_owned_reset_candidate(h.binding.owner):
            pass
    assert "SYNTHETIC_PRIVATE_FAILURE" not in str(error.value)


def restart(directory):
    import hermes_state
    stage = Path(hermes_state.__file__).resolve().parent.parent
    result = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), str(stage), str(directory)],
        cwd=stage / "source", env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", HERMES_HOME=str(directory / "restart-home")),
        capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, "g2.reset_combined_restart_failed"
    assert "SYNTHETIC" not in result.stdout + result.stderr
    assert json.loads(result.stdout) == {"status": "blocked", "unchanged": True}


def test_unknown_atomic_commit_prevents_publication_and_retry(reset_host, tmp_path, monkeypatch):
    h = reset_host
    before = fixtures.persisted(tmp_path)
    commit = h.reset._commit
    def uncertain(conn):
        commit(conn)
        failure()
    monkeypatch.setattr(h.reset, "_commit", uncertain)
    monkeypatch.setattr(h.preparation, "_publish", lambda authority: pytest.fail("unknown commit published"))
    run_failed(h)
    assert fixtures.persisted(tmp_path)[1] == before[1]
    blocked(h, tmp_path, "committed_pending_projection")
    restart(tmp_path)


def test_publication_succeeds_but_reports_failure(reset_host, tmp_path, monkeypatch):
    h = reset_host
    before = fixtures.persisted(tmp_path)[1]
    publish = h.reset.coordinator._publish
    def uncertain(raw):
        publish(raw)
        failure()
    monkeypatch.setattr(h.reset.coordinator, "_publish", uncertain)
    run_failed(h)
    assert fixtures.persisted(tmp_path)[1] != before
    blocked(h, tmp_path, "committed_pending_projection")
    restart(tmp_path)


@pytest.mark.parametrize("state", ["projection_verified", "published_pending_caller"])
def test_publication_state_commit_reports_uncertainty(reset_host, tmp_path, monkeypatch, state):
    h = reset_host
    commit = h.preparation._commit
    def uncertain(conn):
        commit(conn)
        if conn.execute("SELECT state FROM maya_session_transitions_v1 WHERE operation='reset'").fetchone()[0] == state:
            failure()
    monkeypatch.setattr(h.preparation, "_commit", uncertain)
    run_failed(h)
    blocked(h, tmp_path, state)


@pytest.mark.parametrize("timing", ["before", "after"])
@pytest.mark.parametrize("cleanup", ["normal", "unavailable", "audit_unavailable"])
def test_ack_commit_failure_combined_with_cleanup(reset_host, tmp_path, monkeypatch, timing, cleanup):
    h = reset_host
    commit = h.preparation._commit
    def uncertain(conn):
        state = conn.execute("SELECT state FROM maya_session_transitions_v1 WHERE operation='reset'").fetchone()[0]
        if state == "caller_acknowledged":
            if timing == "after":
                commit(conn)
            failure()
        commit(conn)
    monkeypatch.setattr(h.preparation, "_commit", uncertain)
    if cleanup == "unavailable":
        monkeypatch.setattr(h.preparation, "_quarantine", failure)
    elif cleanup == "audit_unavailable":
        audit = h.binding.audit.write
        def audit_failure(record):
            if record.event_type == "outcome.session_reset" and record.operation == "quarantine_reset":
                failure()
            return audit(record)
        monkeypatch.setattr(h.binding.audit, "write", audit_failure)
    run_failed(h)
    expected = ("caller_acknowledged" if timing == "after" else "published_pending_caller") if cleanup == "unavailable" else "caller_quarantined"
    blocked(h, tmp_path, expected)
    if cleanup == "unavailable":
        restart(tmp_path)


@pytest.mark.parametrize("operation", ["reset_published", "acknowledge_reset"])
def test_required_outcome_audit_and_cleanup_audit_fail(reset_host, tmp_path, monkeypatch, operation):
    h = reset_host
    audit = h.binding.audit.write
    def unavailable(record):
        if record.event_type == "outcome.session_reset" and record.operation in {operation, "quarantine_reset"}:
            failure()
        return audit(record)
    monkeypatch.setattr(h.binding.audit, "write", unavailable)
    run_failed(h)
    blocked(h, tmp_path, "projection_verified" if operation == "reset_published" else "caller_quarantined")


def test_caller_exception_with_failed_quarantine_preserves_original_failure(reset_host, tmp_path, monkeypatch):
    h = reset_host
    monkeypatch.setattr(h.preparation, "_quarantine", failure)
    with pytest.raises(ValueError, match="caller_cancelled_fixture"):
        with h.store.prepare_owned_reset_candidate(h.binding.owner):
            raise ValueError("caller_cancelled_fixture")
    blocked(h, tmp_path, "published_pending_caller")


def restart_probe(stage, directory):
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_governance_g2_reset_combined_faults import contract, inventory_digest
    data = contract()
    assert inventory_digest(stage / "source") == data["native_inventory_sha256"]
    assert inventory_digest(stage / "host") == data["host_inventory_sha256"]
    from hermes_cli import middleware
    from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
    resume = fixtures.module("combined_restart", "hermes_g2_restart_loop_native.py")
    patcher = pytest.MonkeyPatch()
    original, _, _ = resume.resume_host(directory, patcher)
    store, db, binding, _ = original
    binding.gateway = PolicyAuthorizationGateway((PolicyRule("session.read", operation="route_state", actor_id="alice"),))
    before = fixtures.persisted(directory)
    try:
        with pytest.raises(middleware.MandatoryMiddlewareError):
            store.read_owned_session_candidate(binding.owner)
        with pytest.raises(middleware.MandatoryMiddlewareError):
            with store.authenticated_owned_session_candidate(binding.owner):
                pytest.fail("restart adopted uncertain route")
        assert fixtures.persisted(directory) == before
        return {"status": "blocked", "unchanged": True}
    finally:
        middleware._mandatory_enabled = False
        db.close()
        patcher.undo()


if __name__ == "__main__":
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = restart_probe(Path(sys.argv[1]), Path(sys.argv[2]))
    except BaseException:
        print(json.dumps({"status": "failed", "reason_code": "g2.reset_combined_restart_failed"}))
        raise SystemExit(1) from None
    print(json.dumps(result, sort_keys=True))

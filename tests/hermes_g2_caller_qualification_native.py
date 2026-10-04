"""Native caller failure matrix; not full agent-loop or product qualification."""
import asyncio
from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest
import hermes_state
from hermes_cli import middleware
from project_maya.hermes_plugins import session_transitions
from project_maya.hermes_plugins.governance import GovernanceBoundaryError
from project_maya.hermes_plugins.session_creation import projection_bytes, _digest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("qualified_caller_fixture", ROOT / "tests/hermes_g2_caller_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
host = base.host
caller_host = base.caller_host


def verify_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_caller_qualification import verify_stage
        source = Path(hermes_state.__file__).resolve().parent
        native, maya = verify_stage(source.parent)
        assert source == native.resolve()
        assert Path(session_transitions.__file__).resolve().is_relative_to(maya.resolve())
    finally:
        sys.path.pop(0)


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    verify_source()


def blocked(caller_host, expected):
    host, caller, reader = caller_host
    store, db, binding, coordinator = host
    assert base.state(host) == expected
    assert not db._conn.in_transaction and not store._entries
    assert caller._current is None and caller._phase == "idle" and reader._active is None
    assert db._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert db._conn.execute("PRAGMA foreign_key_check").fetchone() is None
    before = base.parent.snapshot(host)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        store.read_owned_session_candidate(binding.owner)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        base.parent.create(host)
    assert base.parent.snapshot(host) == before
    assert "synthetic-private-value" not in (store.sessions_dir.parent / "audit.jsonl").read_text()
    with coordinator._exclusive():
        pass


@pytest.mark.parametrize("loss", ["expiry", "revocation", "task_cancellation"])
def test_normal_exit_authority_loss_prevents_acknowledgement(caller_host, monkeypatch, loss):
    host, caller, _ = caller_host
    store, _, binding, _ = host
    completions = []
    async def exercise():
        with pytest.raises(middleware.MandatoryMiddlewareError):
            with store.prepare_owned_session_candidate(binding.owner):
                authority = caller._current[0]
                if loss == "expiry":
                    monkeypatch.setattr(session_transitions, "monotonic", lambda: authority._deadline)
                elif loss == "revocation":
                    authority.revoke()
                else:
                    asyncio.current_task().cancel()
            completions.append("unreachable")
        await asyncio.sleep(0)
    if loss == "task_cancellation":
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(exercise())
    else:
        asyncio.run(exercise())
    assert not completions
    blocked(caller_host, "caller_quarantined")


def test_ack_audit_failure_cannot_grant_authority(caller_host, monkeypatch):
    host, _, _ = caller_host
    store, _, binding, _ = host
    original = binding.audit.write
    def audit(record):
        if record.operation == "acknowledge_create":
            raise OSError("synthetic-private-value")
        original(record)
    monkeypatch.setattr(binding.audit, "write", audit)
    with pytest.raises(middleware.MandatoryMiddlewareError) as caught:
        with store.prepare_owned_session_candidate(binding.owner):
            pass
    assert "synthetic-private-value" not in str(caught.value)
    blocked(caller_host, "caller_quarantined")


def test_native_ack_sql_failure_rolls_back_and_quarantines(caller_host):
    host, _, _ = caller_host
    store, db, binding, _ = host
    db._conn.execute("CREATE TRIGGER fixture_ack_failure BEFORE UPDATE ON maya_session_transitions_v1 "
                     "WHEN NEW.state='caller_acknowledged' BEGIN SELECT RAISE(ABORT,'synthetic-private-value'); END")
    db._conn.commit()
    with pytest.raises(middleware.MandatoryMiddlewareError) as caught:
        with store.prepare_owned_session_candidate(binding.owner):
            pass
    assert "synthetic-private-value" not in str(caught.value)
    blocked(caller_host, "caller_quarantined")


@pytest.mark.parametrize("committed", [False, True])
def test_unknown_ack_commit_reports_no_scope_success_and_does_not_replay(caller_host, monkeypatch, committed):
    host, caller, _ = caller_host
    store, _, binding, _ = host
    completed = []
    def ambiguous(conn):
        if committed:
            conn.commit()
        raise OSError("synthetic-private-value")
    monkeypatch.setattr(caller, "_commit", ambiguous)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        with store.prepare_owned_session_candidate(binding.owner):
            pass
        completed.append("unreachable")
    assert not completed
    if not committed:
        blocked(caller_host, "caller_quarantined")
    else:
        # A lost acknowledgement is not proof of rollback. The fresh authorized
        # reader can confirm the durable acknowledged state, without replay.
        assert base.state(host) == "caller_acknowledged"
        before = base.parent.snapshot(host)
        entry = store.read_owned_session_candidate(binding.owner)
        assert entry.session_id
        with pytest.raises(middleware.MandatoryMiddlewareError):
            base.parent.create(host)
        assert base.parent.snapshot(host) == before


def test_duplicate_ack_after_scope_exit_is_not_another_grant(caller_host):
    host, caller, _ = caller_host
    with host[0].prepare_owned_session_candidate(host[2].owner):
        old_authority = caller._current[0]
    before = base.parent.snapshot(host)
    with pytest.raises(GovernanceBoundaryError):
        caller._acknowledge(old_authority)
    assert base.parent.snapshot(host) == before


@pytest.mark.parametrize("field,value", [("correlation_id", "foreign-correlation"), ("principal", "bob")])
def test_foreign_descriptor_cannot_acknowledge_an_owned_receipt(caller_host, monkeypatch, field, value):
    host, caller, _ = caller_host
    with pytest.raises(middleware.MandatoryMiddlewareError):
        with host[0].prepare_owned_session_candidate(host[2].owner):
            authority = caller._current[0]
            monkeypatch.setattr(authority, "_descriptor", replace(authority.descriptor, **{field: value}))
    # Only the original host-created cleanup descriptor can reduce this receipt.
    blocked(caller_host, "caller_quarantined")


def test_stale_route_cannot_acknowledge_or_quarantine_newer_state(caller_host):
    host, _, _ = caller_host
    store, db, binding, coordinator = host
    newer = None
    with pytest.raises(middleware.MandatoryMiddlewareError):
        with store.prepare_owned_session_candidate(binding.owner) as receipt:
            # Fixture-only newer-state injection; no reset/switch is enabled.
            db._conn.execute("UPDATE maya_session_routes_v1 SET route_version=2")
            raw = projection_bytes(binding.instance_id, str(binding.database), 2,
                {binding.route_slot: {"session_id": receipt["session_id"], "version": 2}})
            db._conn.execute("UPDATE maya_session_projection_v1 SET generation=2,projection_hash=?", (_digest(raw),))
            db._conn.commit()
            coordinator.index.write_bytes(raw)
            newer = base.parent.snapshot(host)
    assert base.parent.snapshot(host) == newer
    blocked(caller_host, "published_pending_caller")


def crash_before_ack(directory):
    verify_source()
    monkeypatch = pytest.MonkeyPatch()
    fixture = base.host.__wrapped__(Path(directory), monkeypatch)
    native_host = next(fixture)
    host, _, _ = base.caller_host.__wrapped__(native_host)
    with host[0].prepare_owned_session_candidate(host[2].owner):
        os._exit(77)


def test_real_process_exit_before_ack_stays_pending_on_fresh_host(tmp_path):
    source = Path(hermes_state.__file__).resolve().parent
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((str(source), str(source.parent / "host/src")))
    crashed = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--crash-before-ack", str(tmp_path)],
        cwd=source, env=environment, capture_output=True, timeout=90)
    assert crashed.returncode == 77, "worker did not reach pending caller boundary"
    with sqlite3.connect(tmp_path / "native.db") as conn:
        assert conn.execute("SELECT state FROM maya_session_transitions_v1").fetchone()[0] == "published_pending_caller"
    restarted = subprocess.run([sys.executable, "-B", str(ROOT / "tests/hermes_g2_create_crash_native.py"),
        "--restart-worker", str(tmp_path)], cwd=source, env=environment, capture_output=True, timeout=60)
    assert restarted.returncode == 0, "fresh native host did not deny the pending caller route"
    assert json.loads(restarted.stdout)["caller_body_entries"] == 0


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--crash-before-ack":
        crash_before_ack(sys.argv[2])
    else:
        raise SystemExit("explicit crash-before-ack invocation required")

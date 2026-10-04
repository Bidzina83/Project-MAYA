"""Native commit/publication authority-loss diagnostics, not activation."""
import asyncio
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import sys

import pytest
import hermes_state
from hermes_cli import middleware
from project_maya.hermes_plugins import session_transitions

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("authority_loss_fixture", ROOT / "tests/hermes_g2_create_native.py")
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
host = parent.host


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_reader import verify_reader_stage
        source = Path(hermes_state.__file__).resolve().parent
        verified, _ = verify_reader_stage(source.parent)
        assert source == verified.resolve()
    finally:
        sys.path.pop(0)


@pytest.mark.parametrize("loss", ["expiry", "cancellation", "revocation"])
@pytest.mark.parametrize("boundary", ["before_commit", "after_commit", "after_replace"])
def test_authority_loss_rolls_back_or_retains_undispatched_receipt(host, monkeypatch, loss, boundary):
    store, db, binding, coordinator = host
    before = parent.snapshot(host)
    triggered = []

    async def exercise():
        with binding.authenticated_create(binding.owner) as authority:
            def lose():
                assert not triggered
                triggered.append(boundary)
                if loss == "expiry":
                    monkeypatch.setattr(session_transitions, "monotonic", lambda: authority._deadline)
                elif loss == "cancellation":
                    asyncio.current_task().cancel()
                else:
                    authority.revoke()

            if boundary == "before_commit":
                def trace(statement):
                    if statement.startswith("UPDATE maya_session_projection_v1 SET generation="):
                        lose()
                db._conn.set_trace_callback(trace)
            elif boundary == "after_commit":
                original = authority.publication_guard
                @contextmanager
                def publish_guard(identity, descriptor):
                    lose()
                    with original(identity, descriptor):
                        yield
                monkeypatch.setattr(authority, "publication_guard", publish_guard)
            else:
                begins = []
                def trace_acknowledgement(statement):
                    if statement == "BEGIN IMMEDIATE":
                        begins.append(statement)
                        if len(begins) == 2:
                            lose()
                # The second transaction begins after strict replacement and
                # publication-guard exit, before receipt acknowledgement.
                db._conn.set_trace_callback(trace_acknowledgement)

            try:
                with pytest.raises(middleware.MandatoryMiddlewareError):
                    store.create_owned_session_candidate(authority)
                assert triggered == [boundary]
                after = parent.snapshot(host)
                with pytest.raises(middleware.MandatoryMiddlewareError):
                    store.create_owned_session_candidate(authority)
                assert parent.snapshot(host) == after
            finally:
                db._conn.set_trace_callback(None)
        # Deliver an actual queued cancellation after synchronous native denial.
        # No await is introduced inside the native commit guard.
        await asyncio.sleep(0)

    if loss == "cancellation":
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(exercise())
    else:
        asyncio.run(exercise())
    assert not db._conn.in_transaction and not store._entries
    assert db._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert db._conn.execute("PRAGMA foreign_key_check").fetchone() is None
    if boundary == "before_commit":
        assert parent.snapshot(host) == before
    else:
        assert db._conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 1
        assert db._conn.execute("SELECT state FROM maya_session_transitions_v1").fetchone()[0] == "committed_pending_projection"
        projection = json.loads((store.sessions_dir / "sessions.json").read_bytes())
        assert projection["generation"] == int(boundary == "after_replace")
        for table in ("maya_session_owners_v1", "maya_session_routes_v1"):
            assert db._conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 1
    audit = [json.loads(line) for line in (store.sessions_dir.parent / "audit.jsonl").read_text().splitlines()]
    assert not any(row.get("event_type") == "outcome.session_transition" for row in audit)
    # All exclusion is released despite denial; this does not repair any receipt.
    with coordinator._exclusive():
        pass

"""Reset publication/acknowledgement and real conversation; synthetic transport only."""
import asyncio
import importlib.util
import json
from pathlib import Path
import sys

import hermes_state
import pytest
from hermes_cli import middleware
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.reset_publication import CandidateResetPreparation
from project_maya.hermes_plugins.session_reset import CandidateNativeSessionReset
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reset_cache_fixture", ROOT / "tests/hermes_g2_prompt_cache_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
host = base.host
caller_host = base.caller_host
loop_host = base.loop_host
recognition_host = base.recognition_host
cache_host = base.cache_host


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_reset_composition import verify_stage
        stage = Path(hermes_state.__file__).resolve().parent.parent
        verify_stage(stage, ROOT / ".codex-build/governance-g2-reset-20261006-final-b",
                     ROOT / ".codex-build/governance-g2-prompt-cache-20261005-final-c")
    finally:
        sys.path.pop(0)


@pytest.fixture
def reset_host(cache_host):
    h = cache_host
    with h.store.prepare_owned_session_candidate(h.binding.owner) as receipt:
        pass
    h.source = receipt["session_id"]
    h.db._conn.execute("INSERT INTO messages(session_id,role,content,timestamp) VALUES (?,'user','SYNTHETIC_OLD_HISTORY',1)", (h.source,))
    h.db._conn.commit()
    rules = [("session.read", op) for op in ("route_state", "history", "existing_session", "prompt_cache_rebuild_without_snapshot")]
    rules += [("session.transition", op) for op in ("reset", "acknowledge_reset")]
    rules += [("session.write", op) for op in ("end", "create")]
    h.binding.gateway = PolicyAuthorizationGateway(tuple(PolicyRule(cap, operation=op, actor_id="alice") for cap, op in rules))
    h.reset = CandidateNativeSessionReset(h.original[3], acknowledgement=ACKNOWLEDGEMENT)
    h.preparation = CandidateResetPreparation(h.reset, acknowledgement=ACKNOWLEDGEMENT)
    return h


def state(h):
    return h.db._conn.execute("SELECT state FROM maya_session_transitions_v1 WHERE operation='reset'").fetchone()[0]


def prepare(h):
    with h.store.prepare_owned_reset_candidate(h.binding.owner) as receipt:
        assert state(h) == "published_pending_caller"
        assert not h.db._conn.in_transaction
        # Storage locks must not cross the bounded caller body.
        assert h.store._lock.acquire(blocking=False)
        h.store._lock.release()
        assert not receipt["dispatch_allowed"]
        with pytest.raises(TypeError):
            receipt["state"] = "caller_acknowledged"
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.store.read_owned_session_candidate(h.binding.owner)
    return receipt


def test_normal_exit_acknowledges_and_preserves_source(reset_host):
    h = reset_host
    old = h.db.get_messages(h.source)
    receipt = prepare(h)
    assert state(h) == "caller_acknowledged"
    assert h.store.read_owned_session_candidate(h.binding.owner).session_id == receipt["session_id"]
    assert h.db.get_messages(h.source) == old
    assert h.db.get_messages(receipt["session_id"]) == []
    assert not h.agents and not h.requests


@pytest.mark.parametrize("failure", ["exception", "cancel", "ack_policy", "revocation", "expiry", "publication", "audit"])
def test_failed_preparation_never_dispatches(reset_host, monkeypatch, failure):
    h = reset_host
    before = h.db.get_messages(h.source)
    if failure == "publication":
        monkeypatch.setattr(h.original[3], "_publish", lambda raw: (_ for _ in ()).throw(OSError("private-fixture")))
    if failure == "audit":
        original = h.binding.audit.write
        def audit(record):
            if record.operation == "reset_published":
                raise OSError("private-fixture")
            return original(record)
        monkeypatch.setattr(h.binding.audit, "write", audit)
    expected = RuntimeError if failure == "exception" else asyncio.CancelledError if failure == "cancel" else middleware.MandatoryMiddlewareError
    with pytest.raises(expected):
        with h.store.prepare_owned_reset_candidate(h.binding.owner):
            if failure == "exception":
                raise RuntimeError("synthetic caller failure")
            if failure == "cancel":
                raise asyncio.CancelledError()
            if failure == "ack_policy":
                h.binding.gateway = PolicyAuthorizationGateway(())
            if failure == "revocation":
                h.reset._active.revoke()
            if failure == "expiry":
                h.reset._active.deadline = 0
    assert state(h) != "caller_acknowledged"
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.read_owned_session_candidate(h.binding.owner)
    assert h.db.get_messages(h.source) == before
    assert not h.requests and not h.agents and not h.db._conn.in_transaction


@pytest.mark.parametrize("damage", ["parent", "source_end", "receipt", "version"])
def test_lineage_damage_is_not_adopted(reset_host, damage):
    h = reset_host
    receipt = prepare(h)
    statements = {
        "parent": "UPDATE maya_session_owners_v1 SET parent_session_id=NULL WHERE parent_session_id IS NOT NULL",
        "source_end": "UPDATE sessions SET end_reason='other' WHERE ended_at IS NOT NULL",
        "receipt": "UPDATE maya_session_transitions_v1 SET operation='create' WHERE operation='reset'",
        "version": "UPDATE maya_session_transitions_v1 SET expected_route_version=0 WHERE operation='reset'",
    }
    h.db._conn.execute(statements[damage])
    h.db._conn.commit()
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.read_owned_session_candidate(h.binding.owner)
    assert not h.agents and not h.requests


@pytest.mark.asyncio
@pytest.mark.parametrize("model_denied", [False, True])
async def test_reset_to_real_fresh_conversation(reset_host, model_denied):
    h = reset_host
    old = h.db.get_messages(h.source)
    receipt = prepare(h)
    if model_denied:
        h.plugin.gateway = PolicyAuthorizationGateway((PolicyRule("session.write", actor_id="alice"),))
        with pytest.raises(middleware.MandatoryMiddlewareError):
            await base.execute(h)
        assert not h.requests
    else:
        result = await base.execute(h)
        assert result["final_response"] == "Synthetic approved response"
        assert len(h.agents) == 1 and len(h.requests) == 1
        assert "SYNTHETIC_OLD_HISTORY" not in json.dumps(h.wire)
        assert h.db.get_messages(receipt["session_id"])
        assert all(sdk.max_retries == 0 for sdk in h.clients)
    assert h.db.get_messages(h.source) == old
    assert h.reader._active is None and not h.store._entries


@pytest.mark.asyncio
async def test_existing_agent_and_snapshot_are_not_reused(reset_host):
    h = reset_host
    first = await base.execute(h)
    assert first["final_response"] == "Synthetic approved response"
    old_agent = h.agents[0]
    old_agent._cached_system_prompt = "SYNTHETIC_OLD_AGENT_CACHE"
    h.db._conn.execute("UPDATE sessions SET system_prompt='SYNTHETIC_OLD_SNAPSHOT' WHERE id=?", (h.source,))
    h.db._conn.commit()
    old = h.db.get_messages(h.source)
    prepare(h)
    second = await base.execute(h)
    assert second["final_response"] == "Synthetic approved response"
    assert len(h.agents) == 2 and h.agents[1] is not old_agent
    assert len(h.wire) == 2 and "SYNTHETIC_OLD_HISTORY" not in json.dumps(h.wire[1])
    assert "SYNTHETIC_OLD_AGENT_CACHE" not in json.dumps(h.wire[1])
    assert "SYNTHETIC_OLD_SNAPSHOT" not in json.dumps(h.wire[1])
    assert h.db.get_messages(h.source) == old
    assert h.reader._active is None and not h.store._entries

"""Initial A-to-B-to-A composition; native loop/SQLite, synthetic SDK transport."""
import asyncio
from collections import OrderedDict
import importlib.util
import json
from pathlib import Path
import sys
from threading import Lock

import hermes_state
import httpx
import pytest
from gateway.config import Platform
from gateway.session import SessionSource
from hermes_cli import middleware
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.switch_publication import CandidateSwitchPreparation
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("switch_composition_parent", ROOT / "tests/hermes_g2_switch_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
for name in ("host", "caller_host", "loop_host", "recognition_host", "cache_host", "reset_host", "switch_host"):
    globals()[name] = getattr(base, name)


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_switch_composition import verify_worker_stage
        verify_worker_stage(Path(hermes_state.__file__).resolve().parent.parent)
    finally:
        sys.path.pop(0)


PERMISSIONS = base.PERMISSIONS + (("session.transition", "acknowledge_switch"),) + tuple(
    ("session.read", op) for op in ("history", "existing_session", "prompt_cache_rebuild_without_snapshot"))


def policy(h, missing=None):
    h.binding.gateway = PolicyAuthorizationGateway(tuple(
        PolicyRule(cap, operation=op, actor_id="alice") for cap, op in PERMISSIONS if (cap, op) != missing))


@pytest.fixture
def composed_host(switch_host, monkeypatch):
    import gateway.run as native
    import run_agent
    h = switch_host
    policy(h)
    h.switch_preparation = CandidateSwitchPreparation(h.switch,
        acknowledgement=ACKNOWLEDGEMENT, gateway_runner=h.runner)
    # Select an isolated synthetic provider independently of the old per-route override.
    monkeypatch.setattr(native, "_resolve_runtime_agent_kwargs", lambda: {
        "model": "synthetic-model", "provider": "openai", "api_key": "synthetic-fixture-not-a-secret",
        "base_url": "https://api.openai.com/v1", "api_mode": "chat_completions"})
    h.wire = []
    original_client = run_agent.OpenAI

    def client(**kwargs):
        sdk = original_client(**kwargs)
        transport = sdk._client._transport
        def capture(request):
            h.wire.append(json.loads(request.content))
            return transport.handle_request(request)
        sdk._client._transport = httpx.MockTransport(capture)
        return sdk

    monkeypatch.setattr(run_agent, "OpenAI", client)
    return h


def state(h):
    row = h.db._conn.execute("SELECT state FROM maya_session_transitions_v1 WHERE operation='switch'").fetchone()
    return row[0] if row else None


def blocked(h):
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.read_owned_session_candidate(h.binding.owner)
    assert h.switch_preparation._confirmed is None
    assert not h.requests and not h.agents and not h.db._conn.in_transaction
    assert h.reader._active is None and h.switch._active is None


def prepare(h):
    with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source) as receipt:
        assert receipt["session_id"] == h.source and receipt["source_session"] == h.child
        assert receipt["state"] == "published_pending_caller" and not receipt["dispatch_allowed"]
        assert not h.db._conn.in_transaction and h.switch_preparation._confirmed is None
        with pytest.raises(TypeError):
            receipt["dispatch_allowed"] = True
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.store.read_owned_session_candidate(h.binding.owner)
    return receipt


async def execute(h):
    with h.store.authenticated_owned_session_candidate(h.binding.owner) as entry:
        h.session_id = entry.session_id
        history = h.store.load_transcript(entry.session_id)
        return await h.runner._run_agent("Synthetic current question", "", history,
            SessionSource(platform=Platform.LOCAL, chat_id="fixture", user_id="alice"),
            entry.session_id, session_key=h.binding.route_slot)


def test_exact_receipt_and_both_histories_survive(composed_host):
    h = composed_host
    old = h.db._conn.execute("SELECT * FROM maya_session_transitions_v1 ORDER BY correlation_id").fetchall()
    messages = h.db._conn.execute("SELECT * FROM messages").fetchall()
    prepare(h)
    assert state(h) == "caller_acknowledged"
    assert h.store.read_owned_session_candidate(h.binding.owner).session_id == h.source
    assert h.db._conn.execute("SELECT * FROM messages").fetchall() == messages
    assert h.db._conn.execute("SELECT * FROM maya_session_transitions_v1 WHERE operation<>'switch' ORDER BY correlation_id").fetchall() == old
    assert h.original[3].index.read_bytes() == h.original[3]._state(h.db._conn)[2]
    assert not h.requests and not h.agents
    assert h.db._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


@pytest.mark.asyncio
@pytest.mark.parametrize("denied", [False, True])
async def test_fresh_native_agent_restores_only_parent_and_gates_model(composed_host, denied):
    h = composed_host
    # Existing snapshots are retained as native records but never used for this profile.
    h.db._conn.execute("UPDATE sessions SET system_prompt='SYNTHETIC_PARENT_SNAPSHOT' WHERE id=?", (h.source,))
    h.db._conn.execute("UPDATE sessions SET system_prompt='SYNTHETIC_CHILD_SNAPSHOT' WHERE id=?", (h.child,))
    h.db._conn.commit()
    child = h.db.get_messages(h.child)
    prepare(h)
    if denied:
        h.plugin.gateway = PolicyAuthorizationGateway((PolicyRule("session.write", actor_id="alice"),))
        with pytest.raises(middleware.MandatoryMiddlewareError):
            await execute(h)
        assert not h.requests and not h.wire
    else:
        result = await execute(h)
        assert result["final_response"] == "Synthetic approved response"
        assert h.requests == ["/v1/chat/completions"]
        wire = json.dumps(h.wire)
        assert "SYNTHETIC_OLD_HISTORY" in wire and "SYNTHETIC_CHILD_HISTORY" not in wire
        assert "SYNTHETIC_PARENT_SNAPSHOT" not in wire and "SYNTHETIC_CHILD_SNAPSHOT" not in wire
    assert len(h.agents) == 1 and h.agents[0].session_id == h.source
    assert h.db.get_messages(h.child) == child
    assert h.db._conn.execute("SELECT system_prompt FROM sessions WHERE id=?", (h.source,)).fetchone()[0] == "SYNTHETIC_PARENT_SNAPSHOT"
    assert h.db._conn.execute("SELECT system_prompt FROM sessions WHERE id=?", (h.child,)).fetchone()[0] == "SYNTHETIC_CHILD_SNAPSHOT"
    assert all(sdk.max_retries == 0 for sdk in h.clients)
    # The native gateway calls this inert fixture after success. No title worker is qualified.
    assert h.title_calls.call_count == (0 if denied else 1)
    assert h.reader._active is None and not h.store._entries
    audit = h.binding.audit.path.read_text()
    assert "SYNTHETIC_OLD_HISTORY" not in audit and "SYNTHETIC_CHILD_HISTORY" not in audit
    assert "synthetic-fixture-not-a-secret" not in audit


def test_native_approval_and_route_cache_cleanup(composed_host, monkeypatch):
    from tools import approval, slash_confirm
    h = composed_host
    waiter = base.base.seed_approvals(h, monkeypatch)
    key = h.binding.route_slot
    cache_marker = object()
    h.runner._agent_cache = OrderedDict(((key, (cache_marker, "old", 1)), ("other-route", (object(), "kept", 1))))
    h.runner._agent_cache_lock = Lock()
    for name in ("_session_model_overrides", "_session_reasoning_overrides", "_voice_mode", "_pending_messages", "_last_resolved_model"):
        setattr(h.runner, name, {key: "OLD_SOURCE_STATE", "other-route": "preserved"})
    h.runner._last_resolved_model["*"] = "OLD_SOURCE_STATE"
    try:
        prepare(h)
        assert waiter.event.is_set() and waiter.result == "deny"
        assert not approval.is_approved(key, "synthetic-old-pattern") and not approval.is_session_yolo_enabled(key)
        assert key not in approval._pending and key not in approval._gateway_notify_cbs
        assert slash_confirm.get_pending(key) is None
        assert list(h.runner._agent_cache) == ["other-route"]
        for name in ("_pending_approvals", "_update_prompt_pending", "_pending_skills_reload_notes"):
            assert getattr(h.runner, name) == {"other-route": {"preserved": True}}
        for name in ("_session_model_overrides", "_session_reasoning_overrides", "_voice_mode", "_pending_messages", "_last_resolved_model"):
            assert getattr(h.runner, name) == {"other-route": "preserved"}
    finally:
        approval.clear_session(key)
        approval.unregister_gateway_notify(key)
        slash_confirm.clear(key)


@pytest.mark.asyncio
async def test_real_child_agent_is_not_reused_for_parent(composed_host):
    h = composed_host
    await execute(h)
    assert h.agents[0].session_id == h.child
    child_agent = h.agents[0]
    child_messages = h.db.get_messages(h.child)
    h.runner._agent_cache = OrderedDict(((h.binding.route_slot, (child_agent, "old-signature", 1)),))
    h.runner._agent_cache_lock = Lock()
    h.requests.clear()
    h.wire.clear()
    # Preparation must not create/dispatch an agent; the earlier agent is an actual native control.
    with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source):
        pass
    assert h.binding.route_slot not in h.runner._agent_cache
    result = await execute(h)
    assert result["final_response"] == "Synthetic approved response"
    assert len(h.agents) == 2 and h.agents[1] is not child_agent and h.agents[1].session_id == h.source
    assert h.db.get_messages(h.child) == child_messages
    assert "SYNTHETIC_CHILD_HISTORY" not in json.dumps(h.wire)


@pytest.mark.parametrize("failure", ["body", "cancel", "close", "ack_denied", "revoked", "expired"])
def test_caller_failure_cannot_acknowledge(composed_host, failure):
    h = composed_host
    error = asyncio.CancelledError if failure == "cancel" else GeneratorExit if failure == "close" else RuntimeError if failure == "body" else middleware.MandatoryMiddlewareError
    with pytest.raises(error):
        with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source):
            if failure == "body":
                raise RuntimeError("synthetic caller error")
            if failure == "cancel":
                raise asyncio.CancelledError()
            if failure == "close":
                raise GeneratorExit()
            if failure == "ack_denied":
                policy(h, ("session.transition", "acknowledge_switch"))
            if failure == "revoked":
                h.switch_preparation._current.revoke()
            if failure == "expired":
                h.switch_preparation._current.deadline = 0
    assert state(h) == "caller_quarantined"
    blocked(h)


@pytest.mark.parametrize("failure", ["raise", "noop", "invalid_dict", "invalid_cache", "missing_lock", "running", "whole_noop"])
def test_cleanup_failure_blocks_confirmation(composed_host, monkeypatch, failure):
    from tools import approval, slash_confirm
    h = composed_host
    base.base.seed_approvals(h, monkeypatch)
    key = h.binding.route_slot
    if failure == "raise":
        monkeypatch.setattr(slash_confirm, "clear", lambda key: (_ for _ in ()).throw(OSError("synthetic private error")))
    elif failure == "noop":
        monkeypatch.setattr(approval, "clear_session", lambda key: None)
    elif failure == "invalid_dict":
        h.runner._session_model_overrides = []
    elif failure in {"invalid_cache", "missing_lock"}:
        h.runner._agent_cache = [] if failure == "invalid_cache" else {key: object()}
        h.runner._agent_cache_lock = Lock() if failure == "invalid_cache" else None
    elif failure == "running":
        h.runner._running_agents[key] = object()
    else:
        monkeypatch.setattr(h.runner, "_clear_owned_switch_security_candidate", lambda preparation: None)
    try:
        with pytest.raises(middleware.MandatoryMiddlewareError) as caught:
            prepare(h)
        assert "synthetic private error" not in str(caught.value)
        blocked(h)
    finally:
        monkeypatch.undo()
        approval.clear_session(key)
        approval.unregister_gateway_notify(key)
        slash_confirm.clear(key)


@pytest.mark.parametrize("failure", ["publication", "audit", "ack_commit", "ack_uncertain", "final_cleanup"])
def test_publication_and_ack_uncertainty_remain_blocked(composed_host, monkeypatch, failure):
    h = composed_host
    p = h.switch_preparation
    def fail(*args):
        raise OSError("PRIVATE_SYNTHETIC_FAILURE")
    if failure == "publication":
        monkeypatch.setattr(h.original[3], "_publish", fail)
    elif failure == "audit":
        monkeypatch.setattr(p, "_audit", fail)
    elif failure in {"ack_commit", "ack_uncertain"}:
        original = p._commit
        def commit(conn):
            if state(h) == "caller_acknowledged":
                if failure == "ack_uncertain":
                    original(conn)
                fail()
            original(conn)
        monkeypatch.setattr(p, "_commit", commit)
        if failure == "ack_uncertain":
            monkeypatch.setattr(p, "_quarantine", fail)
    else:
        original = p._lock
        class FailedRelease:
            def acquire(self, **kwargs):
                return original.acquire(**kwargs)
            def release(self):
                original.release()
                fail()
        p._lock = FailedRelease()
    with pytest.raises(middleware.MandatoryMiddlewareError) as caught:
        prepare(h)
    assert "PRIVATE_SYNTHETIC_FAILURE" not in str(caught.value)
    if failure in {"ack_uncertain", "final_cleanup"}:
        assert state(h) == "caller_acknowledged"
    blocked(h)


@pytest.mark.parametrize("failure", ["none", "forged", "pid", "runner", "registration", "phase", "reset_only", "new_host"])
def test_durable_receipt_or_reset_confirmation_is_not_switch_authority(composed_host, failure):
    h = composed_host
    prepare(h)
    p = h.switch_preparation
    if failure in {"none", "reset_only"}:
        p._confirmed = None
    elif failure == "forged":
        p._confirmed = ("forged",)
    elif failure == "pid":
        p._pid = -1
    elif failure == "runner":
        p._runner._session_db = None
    elif failure == "registration":
        h.store._maya_switch_preparation = None
    elif failure == "new_host":
        h.store._maya_switch_preparation = None
        h.runner._maya_switch_preparation = None
        replacement = CandidateSwitchPreparation(h.switch, acknowledgement=ACKNOWLEDGEMENT, gateway_runner=h.runner)
        assert replacement._confirmed is None
    else:
        p._phase = "preparing"
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.read_owned_session_candidate(h.binding.owner)
    assert not h.agents and not h.requests


@pytest.mark.parametrize("damage", ["create_receipt", "reset_receipt", "correlation", "parent", "child", "owner", "projection", "pending", "extra_child"])
def test_current_and_historical_receipts_are_checked_separately(composed_host, damage):
    h = composed_host
    prepare(h)
    conn = h.db._conn
    if damage in {"create_receipt", "reset_receipt"}:
        op = "create" if damage == "create_receipt" else "reset"
        conn.execute("UPDATE maya_session_transitions_v1 SET descriptor_digest='forged' WHERE operation=?", (op,))
    elif damage == "correlation":
        corr = conn.execute("SELECT correlation_id FROM maya_session_transitions_v1 WHERE operation='create'").fetchone()[0]
        conn.execute("UPDATE maya_session_routes_v1 SET correlation_id=?", (corr,))
    elif damage == "parent":
        conn.execute("UPDATE sessions SET ended_at=5 WHERE id=?", (h.source,))
    elif damage == "child":
        conn.execute("UPDATE sessions SET end_reason='session_reset' WHERE id=?", (h.child,))
    elif damage == "owner":
        conn.execute("UPDATE maya_session_owners_v1 SET classification='public' WHERE session_id=?", (h.source,))
    elif damage == "projection":
        h.original[3].index.write_bytes(b"{}")
    elif damage == "pending":
        conn.execute("UPDATE maya_session_transitions_v1 SET state='published_pending_caller' WHERE operation='switch'")
    else:
        # Damage the declared lineage without fabricating a native production schema.
        conn.execute("UPDATE sessions SET parent_session_id=? WHERE id=?", (h.source, h.source))
        conn.execute("UPDATE maya_session_owners_v1 SET parent_session_id=? WHERE session_id=?", (h.source, h.source))
    conn.commit()
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.read_owned_session_candidate(h.binding.owner)
    assert not h.agents and not h.requests and not h.store._entries


def test_history_permission_is_not_granted_by_switch(composed_host):
    h = composed_host
    prepare(h)
    policy(h, ("session.read", "history"))
    with pytest.raises(middleware.MandatoryMiddlewareError):
        with h.store.authenticated_owned_session_candidate(h.binding.owner):
            pytest.fail("history authority missing")
    assert not h.agents and not h.requests


def test_cleanup_cannot_be_called_outside_exact_acknowledgement(composed_host):
    h = composed_host
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.runner._clear_owned_switch_security_candidate(h.switch_preparation)
    with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source):
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.runner._clear_owned_switch_security_candidate(h.switch_preparation)
    assert state(h) == "caller_acknowledged"

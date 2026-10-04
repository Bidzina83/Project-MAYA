"""Actual native published-reader/cache/G1 scope diagnostics, source-only."""
import asyncio
from contextvars import copy_context
import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

import hermes_state
from hermes_cli import middleware
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.governance import RequestIdentity, _session_write
from project_maya.hermes_plugins.session_readers import CandidatePublishedSessionReader
from project_maya.hermes_plugins.session_handoff import CandidateSessionExecutorHandoff
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT

ROOT = Path(__file__).resolve().parents[1]
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    from prepare_governance_g2_reader import verify_reader_stage

# Reuse immutable fixture provisioning, not an alternate native runtime/store.
spec = importlib.util.spec_from_file_location("maya_g2_create_fixture", ROOT / "tests/hermes_g2_create_native.py")
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
host = parent.host


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    source = Path(hermes_state.__file__).resolve().parent
    verified, _ = verify_reader_stage(source.parent)
    assert source == verified.resolve()


@pytest.fixture
def reader_host(host):
    store, db, binding, coordinator = host
    receipt = parent.create(host)
    binding.gateway = PolicyAuthorizationGateway((
        PolicyRule("session.read", operation="route_state", actor_id="alice"),
        PolicyRule("session.read", operation="history", actor_id="alice"),
        PolicyRule("session.write", operation="append", actor_id="alice"),
    ))
    middleware._mandatory_callbacks["session_write"].__self__.gateway = binding.gateway
    reader = CandidatePublishedSessionReader(coordinator, acknowledgement=ACKNOWLEDGEMENT)
    return host, reader, receipt


def test_native_reader_refreshes_detached_cache_from_published_authority(reader_host):
    host, _, receipt = reader_host
    store, _, binding, _ = host
    store._entries = {"forged-route": object()}
    store._loaded = True
    entry = store.read_owned_session_candidate(binding.owner)
    assert entry.session_id == receipt["session_id"]
    assert list(store._entries) == [binding.route_slot] and not store._loaded
    entry.session_id = "forged-by-caller"
    assert store._entries[binding.route_slot].session_id == receipt["session_id"]
    assert _session_write.get() is None


def test_published_scope_uses_actual_g1_append_and_bounded_executor_read(reader_host):
    host, reader, receipt = reader_host
    store, db, binding, _ = host
    async def exercise():
        with store.authenticated_owned_session_candidate(binding.owner) as entry:
            scope = _session_write.get()
            assert scope.session_id == receipt["session_id"] and scope.operations == frozenset({"append"})
            assert not db._conn.in_transaction
            db.append_message(entry.session_id, "user", "synthetic authorized history")
            def native_read():
                return store.load_transcript(entry.session_id)
            handoff = CandidateSessionExecutorHandoff(native_read, audit_sink=binding.audit, acknowledgement=ACKNOWLEDGEMENT)
            result = await handoff.execute(native_read)
            assert result[0]["content"] == "synthetic authorized history"
            with pytest.raises(middleware.MandatoryMiddlewareError):
                store.load_transcript("foreign-session")
            with pytest.raises(middleware.MandatoryMiddlewareError):
                db.create_session("unapproved-child", source="forged")
            return scope
    scope = asyncio.run(exercise())
    assert not scope.lease.is_active
    assert reader._active is None and _session_write.get() is None
    assert store._entries == {} and not store._loaded
    assert len(db.get_messages(receipt["session_id"])) == 1


@pytest.mark.parametrize("identity", [RequestIdentity("mallory", "confidential"), RequestIdentity("alice", "public")])
def test_wrong_owner_or_classification_never_yields_fixed_scope(reader_host, identity):
    host, reader, _ = reader_host
    store, _, _, _ = host
    before = parent.snapshot(host)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        with store.authenticated_owned_session_candidate(identity):
            pytest.fail("foreign identity yielded scope")
    assert _session_write.get() is None and reader._active is None
    assert parent.snapshot(host) == before


@pytest.mark.parametrize("damage", ["projection", "pending", "owner", "version", "ended", "receipt", "instance", "gate"])
def test_published_reader_rejects_corrupt_or_unfinished_authority(reader_host, damage):
    host, _, receipt = reader_host
    store, db, binding, _ = host
    if damage == "projection":
        (store.sessions_dir / "sessions.json").write_bytes(b'{"forged":true}')
    elif damage == "pending":
        db._conn.execute("UPDATE maya_session_transitions_v1 SET state='projection_verified'")
    elif damage == "owner":
        db._conn.execute("UPDATE maya_session_owners_v1 SET classification='restricted'")
    elif damage == "version":
        db._conn.execute("UPDATE maya_session_owners_v1 SET binding_version=2")
    elif damage == "ended":
        db._conn.execute("UPDATE sessions SET ended_at=1 WHERE id=?", (receipt["session_id"],))
    elif damage == "receipt":
        db._conn.execute("UPDATE maya_session_routes_v1 SET correlation_id='unmatched'")
    elif damage == "instance":
        db._conn.execute("UPDATE maya_session_projection_v1 SET instance_id='foreign-instance'")
    else:
        middleware._mandatory_callbacks.pop("session_write")
    db._conn.commit()
    before = parent.snapshot(host)
    store._entries = {"poisoned-cache": object()}
    with pytest.raises(middleware.MandatoryMiddlewareError):
        store.read_owned_session_candidate(binding.owner)
    assert parent.snapshot(host) == before
    # Missing native middleware is rejected at entry, before the reader runs.
    if damage != "gate":
        assert store._entries == {} and not store._loaded
    with pytest.raises(middleware.MandatoryMiddlewareError):
        with store.authenticated_owned_session_candidate(binding.owner):
            pytest.fail("invalid authority yielded scope")
    assert _session_write.get() is None


@pytest.mark.parametrize("method", ["_ensure_loaded", "_ensure_loaded_locked", "_save", "list_sessions", "lookup_by_session_id", "has_any_sessions"])
def test_legacy_index_roots_deny_even_with_loaded_cache(reader_host, method):
    host, _, receipt = reader_host
    store, _, _, _ = host
    store._loaded = True
    before = parent.snapshot(host)
    args = (receipt["session_id"],) if method == "lookup_by_session_id" else ()
    with pytest.raises(middleware.MandatoryMiddlewareError):
        getattr(store, method)(*args)
    assert parent.snapshot(host) == before


def test_captured_scope_cannot_read_or_write_after_request_exit(reader_host):
    host, _, receipt = reader_host
    store, db, binding, _ = host
    with store.authenticated_owned_session_candidate(binding.owner):
        captured = copy_context()
    before = parent.snapshot(host)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        captured.run(store.load_transcript, receipt["session_id"])
    with pytest.raises(middleware.MandatoryMiddlewareError):
        captured.run(db.append_message, receipt["session_id"], "user", "late denied content")
    assert parent.snapshot(host) == before


def test_native_scope_preserves_typed_body_failure_and_revokes_root(reader_host):
    host, reader, _ = reader_host
    store, _, binding, _ = host
    failure = middleware.MandatoryMiddlewareError("fixture_denial")
    with pytest.raises(middleware.MandatoryMiddlewareError) as raised:
        with store.authenticated_owned_session_candidate(binding.owner):
            scope = _session_write.get()
            raise failure
    assert raised.value is failure
    assert not scope.lease.is_active and scope.lease.termination == "failed"
    assert reader._active is None and store._entries == {}


@pytest.mark.parametrize("failure", ["policy", "audit"])
def test_scope_permission_and_audit_failures_never_bind_conversation(reader_host, failure, monkeypatch):
    host, _, _ = reader_host
    store, _, binding, _ = host
    if failure == "policy":
        binding.gateway = PolicyAuthorizationGateway((PolicyRule("session.read", operation="route_state", actor_id="alice"),))
    else:
        def broken(record):
            raise RuntimeError("synthetic-private-audit-value")
        monkeypatch.setattr(binding.audit, "write", broken)
    before = parent.snapshot(host)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        with store.authenticated_owned_session_candidate(binding.owner):
            pytest.fail("failed policy/audit yielded scope")
    assert parent.snapshot(host) == before
    assert _session_write.get() is None

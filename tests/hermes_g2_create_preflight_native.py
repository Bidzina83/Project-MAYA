"""Actual SessionStore deny controls; create persistence remains unimplemented."""
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

from gateway.config import GatewayConfig
from gateway.session import SessionStore
from hermes_cli import middleware
import hermes_state
from project_maya.audit import LocalJsonlAuditSink
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.governance import RequestIdentity
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT
from project_maya.hermes_plugins.session_transitions import CandidateCreateSessionBinding


ROOT = Path(__file__).resolve().parents[1]
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    from prepare_governance_g1_caller_lifecycle import verify_lifecycle_stage


@pytest.fixture
def native(tmp_path, monkeypatch):
    # Reject a mismatched native export rather than silently testing another wheel.
    source = Path(hermes_state.__file__).resolve().parent
    verified, _ = verify_lifecycle_stage(source.parent)
    assert verified.resolve() == source
    monkeypatch.setattr(middleware, "_mandatory_enabled", False)
    db = hermes_state.SessionDB(tmp_path / "native.db")
    # Only default path selection is fixture-controlled; real SessionStore and
    # SessionDB construction/behavior are used, not mock dictionaries/backends.
    monkeypatch.setattr(hermes_state, "SessionDB", lambda: db)
    store = SessionStore(tmp_path / "sessions", GatewayConfig())
    assert store._db is db
    audit = LocalJsonlAuditSink(tmp_path / "audit.jsonl")
    owner = RequestIdentity("alice", "confidential")
    binding = CandidateCreateSessionBinding(
        owner=owner, instance_id="native-preflight", database=db.db_path,
        route_slot="telegram:private-fixture", binding_version=1,
        gateway=PolicyAuthorizationGateway((
            PolicyRule("session.read", operation="route_state", actor_id="alice"),
            PolicyRule("session.transition", operation="create", actor_id="alice"),
            PolicyRule("session.write", operation="create", actor_id="alice"),
        )), audit_sink=audit, acknowledgement=ACKNOWLEDGEMENT,
    )
    monkeypatch.setattr(middleware, "_mandatory_enabled", True)
    yield store, db, binding, owner
    monkeypatch.setattr(middleware, "_mandatory_enabled", False)
    db.close()


@pytest.mark.parametrize("operation", ["create", "reset", "switch"])
def test_preflight_cannot_enable_unqualified_native_transition(native, operation):
    store, db, binding, owner = native
    before = list(db._conn.iterdump())
    with binding.authenticated_create(owner) as authority:
        with authority.commit_guard(owner, authority.descriptor):
            with pytest.raises(middleware.MandatoryMiddlewareError, match="session_write_unqualified"):
                if operation == "create":
                    store.get_or_create_session(None)
                elif operation == "reset":
                    store.reset_session(None)
                else:
                    store.switch_session(None, "foreign-session")
    assert list(db._conn.iterdump()) == before
    assert store._entries == {} and store._loaded is False
    assert not store.sessions_dir.exists()


def test_unbound_native_create_denies_before_source_or_storage_access(native):
    store, db, _, _ = native
    before = list(db._conn.iterdump())
    with pytest.raises(middleware.MandatoryMiddlewareError, match="session_write_unqualified"):
        store.get_or_create_session(None)
    assert list(db._conn.iterdump()) == before
    assert store._entries == {} and store._loaded is False
    assert not store.sessions_dir.exists()

"""Actual native caller-overlay probes, not full caller/product qualification."""
import asyncio
import importlib.util
from pathlib import Path
import sys

import pytest
import hermes_state
from hermes_cli import middleware
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.caller_preparation import CandidateCallerPreparation
from project_maya.hermes_plugins.governance import GovernanceBoundaryError
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT
from project_maya.hermes_plugins.session_readers import CandidatePublishedSessionReader

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("caller_fixture", ROOT / "tests/hermes_g2_create_native.py")
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
host = parent.host


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_caller import verify_caller_stage
        source = Path(hermes_state.__file__).resolve().parent
        native, maya = verify_caller_stage(source.parent)
        assert source == native.resolve()
        import project_maya.hermes_plugins.session_creation as module
        assert Path(module.__file__).resolve().is_relative_to(maya.resolve())
    finally:
        sys.path.pop(0)


@pytest.fixture
def caller_host(host):
    store, _, binding, coordinator = host
    binding.gateway = PolicyAuthorizationGateway(tuple(
        PolicyRule(capability, operation=operation, actor_id="alice")
        for capability, operation in (("session.read", "route_state"), ("session.read", "history"),
            ("session.transition", "create"), ("session.transition", "acknowledge_create"),
            ("session.write", "create"))))
    caller = CandidateCallerPreparation(coordinator, acknowledgement=ACKNOWLEDGEMENT)
    reader = CandidatePublishedSessionReader(coordinator, acknowledgement=ACKNOWLEDGEMENT)
    return host, caller, reader


def state(host):
    return host[1]._conn.execute("SELECT state FROM maya_session_transitions_v1").fetchone()[0]


def test_normal_exit_acknowledges_only_after_pending_reader_denial(caller_host):
    host, _, reader = caller_host
    store, db, binding, _ = host
    with store.prepare_owned_session_candidate(binding.owner) as receipt:
        assert state(host) == "published_pending_caller" and receipt["dispatch_allowed"] is False
        assert not db._conn.in_transaction
        with pytest.raises(TypeError):
            receipt["state"] = "caller_acknowledged"
        with pytest.raises(middleware.MandatoryMiddlewareError):
            store.read_owned_session_candidate(binding.owner)
    assert state(host) == "caller_acknowledged"
    assert store.read_owned_session_candidate(binding.owner).session_id == receipt["session_id"]
    with store.authenticated_owned_session_candidate(binding.owner):
        pass
    assert not store._entries and reader._active is None


@pytest.mark.parametrize("failure", ["exception", "cancellation"])
def test_failed_caller_quarantines_and_preserves_original(caller_host, failure):
    host, _, _ = caller_host
    store, _, binding, _ = host
    error = RuntimeError("synthetic-private-caller-value") if failure == "exception" else asyncio.CancelledError()
    with pytest.raises(type(error)) as caught:
        with store.prepare_owned_session_candidate(binding.owner):
            raise error
    assert caught.value is error and state(host) == "caller_quarantined"
    with pytest.raises(middleware.MandatoryMiddlewareError):
        store.read_owned_session_candidate(binding.owner)


def test_quarantine_sql_failure_leaves_pending_and_preserves_exception(caller_host):
    host, _, _ = caller_host
    store, db, binding, _ = host
    db._conn.execute("CREATE TRIGGER fixture_quarantine_failure BEFORE UPDATE ON maya_session_transitions_v1 "
                     "WHEN NEW.state='caller_quarantined' BEGIN SELECT RAISE(ABORT,'fixture'); END")
    db._conn.commit()
    error = RuntimeError("synthetic caller failure")
    with pytest.raises(RuntimeError) as caught:
        with store.prepare_owned_session_candidate(binding.owner):
            raise error
    assert caught.value is error and state(host) == "published_pending_caller"
    assert not db._conn.in_transaction
    with pytest.raises(middleware.MandatoryMiddlewareError):
        store.read_owned_session_candidate(binding.owner)


def test_ack_policy_denial_never_implicitly_reuses_create_permission(caller_host):
    host, _, _ = caller_host
    store, _, binding, _ = host
    with pytest.raises(middleware.MandatoryMiddlewareError):
        with store.prepare_owned_session_candidate(binding.owner):
            binding.gateway = PolicyAuthorizationGateway(())
    assert state(host) == "caller_quarantined"


def test_direct_native_create_stays_pending_without_scope_ack(caller_host):
    host, _, _ = caller_host
    receipt = parent.create(host)
    assert receipt["state"] == "published_pending_caller" and not receipt["dispatch_allowed"]
    with pytest.raises(middleware.MandatoryMiddlewareError):
        host[0].read_owned_session_candidate(host[2].owner)


def test_legacy_published_receipt_is_not_adopted(caller_host):
    host, _, _ = caller_host
    parent.create(host)
    host[1]._conn.execute("UPDATE maya_session_transitions_v1 SET state='published'")
    host[1]._conn.commit()
    before = parent.snapshot(host)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        host[0].read_owned_session_candidate(host[2].owner)
    assert parent.snapshot(host) == before


def test_acknowledgement_helper_cannot_run_inside_preparation_body(caller_host):
    host, caller, _ = caller_host
    with host[0].prepare_owned_session_candidate(host[2].owner):
        with pytest.raises(GovernanceBoundaryError):
            caller._acknowledge(caller._current[0])
        assert state(host) == "published_pending_caller"
    assert state(host) == "caller_acknowledged"
    assert caller._current is None and caller._phase == "idle"

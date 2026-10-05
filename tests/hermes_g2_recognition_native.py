"""Real native recognition and new-session loop; source-only qualification."""
import importlib.util
from dataclasses import replace
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import hermes_state
import run_agent
from hermes_cli import middleware
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins import governance
from project_maya.hermes_plugins.session_handoff import CandidateSessionExecutorHandoff
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("recognition_loop_fixture", ROOT / "tests/hermes_g2_create_loop_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
host = base.host
caller_host = base.caller_host
loop_host = base.loop_host


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_recognition import verify_stage
        source, staged = verify_stage(Path(hermes_state.__file__).resolve().parent.parent)
        assert Path(run_agent.__file__).resolve().is_relative_to(source)
        assert Path(governance.__file__).resolve().is_relative_to(staged)
    finally:
        sys.path.pop(0)


@pytest.fixture
def recognition_host(loop_host):
    host = loop_host
    host.binding.gateway = PolicyAuthorizationGateway(tuple(
        PolicyRule(capability, operation=operation, actor_id="alice")
        for capability, operation in (("session.read", "route_state"), ("session.read", "history"),
            ("session.read", "existing_session"), ("session.transition", "create"),
            ("session.transition", "acknowledge_create"), ("session.write", "create"))))
    return host


def prepare(host):
    with host.store.prepare_owned_session_candidate(host.binding.owner) as receipt:
        assert not receipt["dispatch_allowed"] and not host.agents and not host.requests
    return receipt


@pytest.mark.asyncio
async def test_new_session_actual_loop_allows_without_recreation(recognition_host, monkeypatch):
    host = recognition_host
    receipt = prepare(host)
    create = Mock(side_effect=AssertionError("lazy create is forbidden"))
    monkeypatch.setattr(host.db, "create_session", create)
    response = await base.execute(host)
    assert response["final_response"] == "Synthetic approved response"
    assert len(host.agents) == 1 and host.requests == ["/v1/chat/completions"]
    assert all(sdk.max_retries == 0 for sdk in host.clients)
    create.assert_not_called()
    rows = host.db.get_messages(receipt["session_id"])
    assert any(row["content"] == "Synthetic current question" for row in rows)
    assert any(row["content"] == "Synthetic approved response" for row in rows)
    records = [json.loads(line) for line in host.binding.audit.path.read_text().splitlines()]
    recognition = next(i for i, row in enumerate(records) if row.get("operation") == "existing_session")
    egress = next(i for i, row in enumerate(records) if row.get("capability") == "model.egress")
    assert recognition < egress
    assert host.reader._active is None and not host.store._entries
    assert host.db._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


@pytest.mark.asyncio
async def test_model_denial_after_successful_recognition(recognition_host):
    host = recognition_host
    prepare(host)
    host.plugin.gateway = PolicyAuthorizationGateway(tuple(
        PolicyRule(capability, actor_id="alice") for capability in ("session.write", "model.output")))
    with pytest.raises(middleware.MandatoryMiddlewareError):
        await base.execute(host)
    assert not host.requests
    records = [json.loads(line) for line in host.binding.audit.path.read_text().splitlines()]
    assert any(row.get("operation") == "existing_session" and row.get("decision") == "allow" for row in records)
    assert any(row.get("capability") == "model.egress" and row.get("decision") == "deny" for row in records)


@pytest.mark.asyncio
@pytest.mark.parametrize("damage", ["missing", "replaced", "session", "identity", "revoked", "expired",
    "pending", "legacy", "route", "projection", "policy", "audit", "gate", "database",
    "request", "classification", "operations", "thread", "task", "foreign_root", "audit_revocation"])
async def test_native_initializer_rejects_invalid_recognition(recognition_host, monkeypatch, damage):
    host = recognition_host
    receipt = prepare(host)
    with host.store.authenticated_owned_session_candidate(host.binding.owner):
        agent = object.__new__(run_agent.AIAgent)
        agent._session_db = host.db
        agent.session_id = receipt["session_id"]
        agent._session_db_created = True  # A cached flag is never authorization.
        before = list(host.db._conn.iterdump())

        def attempt():
            scope = governance._session_write.get()
            if damage == "missing":
                del host.db._maya_existing_session_reader
            elif damage == "replaced":
                host.db._maya_existing_session_reader = SimpleNamespace(
                    existing_session_contract=host.reader.existing_session_contract,
                    recognize_existing=lambda *args: True)
            elif damage == "session":
                agent.session_id = "foreign-session"
            elif damage == "identity":
                governance._identity.set(governance.RequestIdentity("foreign", "restricted"))
            elif damage in {"request", "classification", "operations", "thread", "task", "foreign_root"}:
                changes = {
                    "request": {"request_id": "foreign-request"},
                    "classification": {"identity": governance.RequestIdentity("alice", "public")},
                    "operations": {"operations": frozenset({"append", "create"})},
                    "thread": {"thread_id": -1},
                    "task": {"task": object()},
                    "foreign_root": {"lease": governance._SessionWriteLease()},
                }
                governance._session_write.set(replace(scope, **changes[damage]))
            elif damage == "revoked":
                scope.lease.revoke_request("cancelled")
            elif damage == "expired":
                scope.lease.deadline = 0
            elif damage in {"pending", "legacy"}:
                value = "published_pending_caller" if damage == "pending" else "published"
                host.db._conn.execute("UPDATE maya_session_transitions_v1 SET state=?", (value,))
                host.db._conn.commit()
            elif damage == "route":
                host.db._conn.execute("UPDATE maya_session_routes_v1 SET route_version=route_version+1")
                host.db._conn.commit()
            elif damage == "projection":
                host.reader.coordinator.index.write_bytes(b"{}")
            elif damage == "policy":
                host.binding.gateway = PolicyAuthorizationGateway(tuple(
                    PolicyRule("session.read", operation=operation, actor_id="alice")
                    for operation in ("route_state", "history")))
            elif damage == "audit":
                write = host.binding.audit.write
                def fail_recognition(record):
                    if record.operation == "existing_session":
                        raise OSError("synthetic-private-marker")
                    return write(record)
                monkeypatch.setattr(host.binding.audit, "write", fail_recognition)
            elif damage == "audit_revocation":
                write = host.binding.audit.write
                def revoke_recognition(record):
                    outcome = write(record)
                    if record.operation == "existing_session":
                        scope.lease.revoke_request("cancelled")
                    return outcome
                monkeypatch.setattr(host.binding.audit, "write", revoke_recognition)
            elif damage == "gate":
                middleware._mandatory_callbacks.pop("session_write")
            elif damage == "database":
                agent._session_db = SimpleNamespace(_maya_existing_session_reader=host.reader)
            damaged = list(host.db._conn.iterdump())
            with pytest.raises(middleware.MandatoryMiddlewareError) as caught:
                agent._ensure_db_session()
            assert "synthetic-private-marker" not in str(caught.value)
            assert list(host.db._conn.iterdump()) == damaged
            return True

        handoff = CandidateSessionExecutorHandoff(attempt, audit_sink=host.binding.audit,
            acknowledgement=ACKNOWLEDGEMENT)
        assert await handoff.execute(attempt) is True
        if damage not in {"pending", "legacy", "route"}:
            assert list(host.db._conn.iterdump()) == before
    assert not host.requests and not host.agents


@pytest.mark.asyncio
async def test_unbound_and_main_task_cannot_recognize(recognition_host):
    host = recognition_host
    receipt = prepare(host)
    agent = object.__new__(run_agent.AIAgent)
    agent._session_db = host.db
    agent.session_id = receipt["session_id"]
    agent._session_db_created = True
    with pytest.raises(middleware.MandatoryMiddlewareError):
        agent._ensure_db_session()
    with host.store.authenticated_owned_session_candidate(host.binding.owner):
        with pytest.raises(middleware.MandatoryMiddlewareError):
            agent._ensure_db_session()
    with pytest.raises(middleware.MandatoryMiddlewareError):
        agent._ensure_db_session()
    assert not host.requests and not host.agents

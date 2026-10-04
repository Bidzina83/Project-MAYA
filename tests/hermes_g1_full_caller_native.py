"""G1 complete-caller diagnostics; no production or provisioning qualification."""
import asyncio
import json
import sqlite3
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from openai import OpenAI

import gateway.run as native
from gateway.config import Platform
from gateway.session import SessionSource
from hermes_cli import middleware
from project_maya.governance import DenyByDefaultGateway, PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins import governance
from project_maya.hermes_plugins.session_handoff import CandidateSessionExecutorHandoff
from project_maya.hermes_plugins.candidate_transport import completion_response
from project_maya.hermes_plugins.session_requests import (
    ACKNOWLEDGEMENT, CandidateSessionRequestBinding,
)
from tests.hermes_g1_caller_entry_native import host


@pytest.fixture
def full_host(host, monkeypatch, tmp_path):
    import run_agent

    cfg = {
        "model": {"default": "synthetic-model"},
        "agent": {"max_turns": 2},
        "display": {"tool_progress": "off", "streaming": False,
                    "interim_assistant_messages": False, "thinking_progress": False},
    }
    host.cfg.side_effect = None
    host.cfg.return_value = cfg
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(native, "_hermes_home", tmp_path / "home")
    runner = host.runner
    runner.config = SimpleNamespace(multiplex_profiles=False, stt_enabled=False,
        thread_sessions_per_user=False, group_sessions_per_user=False)
    for name, value in {
        "adapters": {}, "_voice_mode": {}, "_prefill_messages": [],
        "_ephemeral_system_prompt": "", "_reasoning_config": None,
        "_provider_routing": {}, "_fallback_model": None,
        "_running_agents": {}, "_running_agents_ts": {},
        "_session_run_generation": {}, "_pending_messages": {},
        "_draining": False, "hooks": SimpleNamespace(loaded_hooks=False),
        "_session_reasoning_overrides": {},
        "_session_model_overrides": {"g1-fixed": {
            "model": "synthetic-model", "provider": "openai",
            "api_key": "synthetic-fixture-not-a-secret",
            "base_url": "https://api.openai.com/v1", "api_mode": "chat_completions",
        }},
    }.items():
        setattr(runner, name, value)
    plugin = middleware._mandatory_callbacks["llm_execution"].__self__
    plugin.gateway = PolicyAuthorizationGateway(tuple(
        PolicyRule(capability, actor_id="operator")
        for capability in ("model.egress", "model.output", "session.write")
    ))
    host.plugin = plugin
    host.binding = CandidateSessionRequestBinding(host.owner, "fixed-session", host.db.db_path,
        frozenset({"create", "append", "metadata"}), ACKNOWLEDGEMENT, audit_sink=host.audit)
    host.requests = []
    host.clients = []
    host.transport_entered = threading.Event()
    host.transport_release = threading.Event()
    host.worker_finished = threading.Event()
    host.block_transport = False
    host.native_agents = []
    host.executor_contexts = []
    host.probe_late_callbacks = False
    host.late_denials = []
    original_init = run_agent.AIAgent.__init__
    original_conversation = run_agent.AIAgent.run_conversation

    def construct(agent, *args, **kwargs):
        scope = governance._session_write.get()
        assert scope is not None and scope.identity == host.owner and scope.lease.is_active
        assert scope.session_id == "fixed-session" and scope.database == host.binding.database
        assert scope.thread_id == threading.get_ident() and scope.task is None
        host.executor_contexts.append(scope)
        original_init(agent, *args, **kwargs)
        host.native_agents.append(agent)

    def conversation(agent, *args, **kwargs):
        try:
            return original_conversation(agent, *args, **kwargs)
        finally:
            if host.probe_late_callbacks:
                probe_late_callbacks()
            host.worker_finished.set()

    def probe_late_callbacks():
        scope = governance._session_write.get()
        assert scope.thread_id == threading.get_ident() and scope.task is None
        assert scope.identity == host.owner and not scope.lease.is_active
        transport, handler = Mock(), Mock()
        for name, effect in (
            ("model", lambda: middleware.run_llm_execution_middleware(
                {"model": "synthetic-model", "messages": []}, transport,
                provider="openai", base_url="https://api.openai.com/v1")),
            ("tool", lambda: middleware.run_tool_execution_middleware(
                "read_file", {"path": "synthetic.txt"}, handler)),
            ("output", lambda: middleware.run_model_output_middleware("late synthetic response",
                provider="openai", model="synthetic-model", base_url="https://api.openai.com/v1")),
            ("write", lambda: host.db.append_message("fixed-session", "user", "late synthetic write")),
        ):
            with pytest.raises((governance.GovernanceBoundaryError, middleware.MandatoryMiddlewareError)):
                effect()
            host.late_denials.append(name)
        transport.assert_not_called()
        handler.assert_not_called()

    def respond(request):
        records = [json.loads(line) for line in host.audit.path.read_text().splitlines()]
        allowed = [r for r in records if r.get("capability") == "model.egress"
                   and r.get("decision") == "allow"]
        assert len(allowed) == len(host.requests) + 1
        host.requests.append(request.url.path)
        host.transport_entered.set()
        if host.block_transport:
            assert host.transport_release.wait(15), "synthetic transport was not released"
        return completion_response(request, tool=False)

    def client(**kwargs):
        assert middleware.validate_mandatory_middleware()
        kwargs["max_retries"] = 0
        kwargs["http_client"] = httpx.Client(transport=httpx.MockTransport(respond), trust_env=False)
        sdk = OpenAI(**kwargs)
        host.clients.append(sdk)
        return sdk

    monkeypatch.setattr(run_agent, "OpenAI", client)
    monkeypatch.setattr(run_agent.AIAgent, "__init__", construct)
    monkeypatch.setattr(run_agent.AIAgent, "run_conversation", conversation)
    monkeypatch.setattr(run_agent, "get_tool_definitions", lambda **kwargs: [])
    monkeypatch.setattr(run_agent, "check_toolset_requirements", lambda **kwargs: {})
    yield host
    host.transport_release.set()
    if host.transport_entered.is_set():
        assert host.worker_finished.wait(15), "native conversation thread did not finish"
    for sdk in host.clients:
        sdk.close()


async def full_call(host):
    # A resumed fixed session excludes auto-title's unqualified first-turn worker.
    history = [message for i in range(3) for message in (
        {"role": "user", "content": f"Synthetic prior question {i}"},
        {"role": "assistant", "content": f"Synthetic prior answer {i}"},
    )]
    return await host.runner._run_agent("Synthetic current question", "", history,
        SessionSource(platform=Platform.LOCAL, chat_id="g1-fixed", user_id="operator"),
        "fixed-session", session_key="g1-fixed")


@pytest.mark.asyncio
async def test_complete_native_caller_normal_return(full_host):
    with full_host.binding.authenticated_request(full_host.owner):
        root = governance._session_write.get()
        result = await full_call(full_host)
        assert not root.lease.is_active
        assert root.lease.termination == "completed"
    assert result["final_response"] == "Synthetic approved response"
    assert full_host.requests == ["/v1/chat/completions"]
    assert full_host.clients and all(sdk.max_retries == 0 for sdk in full_host.clients)
    assert len(full_host.native_agents) == 1 and full_host.worker_finished.is_set()
    assert len(full_host.executor_contexts) == 1
    lease = full_host.executor_contexts[0].lease
    while lease.parent is not None:
        lease = lease.parent
    assert lease is root.lease
    rows = full_host.db.get_messages("fixed-session")
    assert any(row["content"] == "Synthetic current question" for row in rows)
    assert any(row["content"] == "Synthetic approved response" for row in rows)
    records = [json.loads(line) for line in full_host.audit.path.read_text().splitlines()]
    assert any(row.get("event_type") == "authentication.native_caller" for row in records)
    assert any(row.get("capability") == "session.write" and row.get("decision") == "allow"
               for row in records)


@pytest.mark.asyncio
@pytest.mark.parametrize("damage", ["missing", "wrong-owner", "expired"])
async def test_complete_caller_denies_invalid_authority(full_host, damage):
    if damage == "missing":
        with pytest.raises(middleware.MandatoryMiddlewareError):
            await full_call(full_host)
    else:
        with full_host.binding.authenticated_request(full_host.owner):
            if damage == "expired":
                governance._session_write.get().lease.revoke("timeout")
                with pytest.raises(middleware.MandatoryMiddlewareError):
                    await full_call(full_host)
            else:
                with pytest.raises(middleware.MandatoryMiddlewareError):
                    await asyncio.create_task(full_call(full_host))
    assert not full_host.requests and not full_host.native_agents
    assert full_host.db.get_messages("fixed-session") == []


@pytest.mark.asyncio
async def test_complete_caller_policy_denial(full_host):
    full_host.plugin.gateway = DenyByDefaultGateway()
    with full_host.binding.authenticated_request(full_host.owner):
        root = governance._session_write.get()
        with pytest.raises(middleware.MandatoryMiddlewareError):
            await full_call(full_host)
        assert not root.lease.is_active and root.lease.termination == "failed"
    assert not full_host.requests
    assert full_host.db.get_messages("fixed-session") == []


@pytest.mark.asyncio
async def test_complete_caller_model_denial(full_host):
    full_host.plugin.gateway = PolicyAuthorizationGateway((
        PolicyRule("session.write", actor_id="operator"),
    ))
    with full_host.binding.authenticated_request(full_host.owner):
        root = governance._session_write.get()
        with pytest.raises(middleware.MandatoryMiddlewareError):
            await full_call(full_host)
        assert not root.lease.is_active and root.lease.termination == "failed"
    assert not full_host.requests


@pytest.mark.asyncio
async def test_complete_caller_model_audit_failure(full_host, monkeypatch):
    original_write = full_host.audit.write

    def write(record):
        if record.capability == "model.egress":
            raise OSError("synthetic-audit-storage-failure")
        return original_write(record)

    monkeypatch.setattr(full_host.audit, "write", write)
    with full_host.binding.authenticated_request(full_host.owner):
        root = governance._session_write.get()
        with pytest.raises(middleware.MandatoryMiddlewareError):
            await full_call(full_host)
        assert not root.lease.is_active and root.lease.termination == "failed"
    assert not full_host.requests


@pytest.mark.asyncio
async def test_complete_caller_real_sqlite_insert_failure(full_host):
    # Fault injection is in SQLite itself, not a replacement session store.
    with sqlite3.connect(full_host.db.db_path) as connection:
        connection.execute("CREATE TRIGGER g1_fail_insert BEFORE INSERT ON messages "
                           "BEGIN SELECT RAISE(ABORT, 'synthetic-storage-failure'); END")
    with full_host.binding.authenticated_request(full_host.owner):
        root = governance._session_write.get()
        with pytest.raises(middleware.MandatoryMiddlewareError, match="session_write_failed"):
            await full_call(full_host)
        assert not root.lease.is_active and root.lease.termination == "failed"
    assert full_host.db.get_messages("fixed-session") == []


@pytest.mark.asyncio
async def test_complete_caller_construction_failure(full_host, monkeypatch):
    import run_agent

    def fail(**kwargs):
        raise RuntimeError("synthetic-construction-failure")

    monkeypatch.setattr(run_agent, "OpenAI", fail)
    with full_host.binding.authenticated_request(full_host.owner):
        root = governance._session_write.get()
        with pytest.raises(middleware.MandatoryMiddlewareError, match="session_write_failed"):
            await full_call(full_host)
        assert not root.lease.is_active and root.lease.termination == "failed"
    assert not full_host.requests


@pytest.mark.asyncio
async def test_complete_caller_resource_cleanup_failure(full_host, monkeypatch):
    original_release = full_host.runner._release_running_agent_state

    def release(*args, **kwargs):
        original_release(*args, **kwargs)
        raise OSError("synthetic-resource-cleanup-failure")

    monkeypatch.setattr(full_host.runner, "_release_running_agent_state", release)
    with full_host.binding.authenticated_request(full_host.owner):
        root = governance._session_write.get()
        with pytest.raises(middleware.MandatoryMiddlewareError, match="caller_cleanup_failed"):
            await full_call(full_host)
        assert not root.lease.is_active
        with pytest.raises(governance.GovernanceBoundaryError):
            full_host.plugin._actor()
    assert len(full_host.requests) == 1
    assert full_host.runner._running_agents == {}
    # The authorized response was committed before cleanup failed, not rolled back.
    assert any(row["content"] == "Synthetic approved response"
               for row in full_host.db.get_messages("fixed-session"))


@pytest.mark.asyncio
@pytest.mark.parametrize("termination", ["cancelled", "timeout"])
async def test_complete_caller_cancellation_during_transport(full_host, termination):
    full_host.block_transport = True
    if termination == "timeout":
        full_host.binding = CandidateSessionRequestBinding(full_host.owner, "fixed-session",
            full_host.db.db_path, frozenset({"create", "append", "metadata"}), ACKNOWLEDGEMENT,
            audit_sink=full_host.audit, timeout_seconds=10)
    roots = []

    async def request():
        with full_host.binding.authenticated_request(full_host.owner):
            roots.append(governance._session_write.get())
            return await full_call(full_host)

    task = asyncio.create_task(request())
    try:
        for _ in range(1000):
            if full_host.transport_entered.is_set() or task.done():
                break
            await asyncio.sleep(.01)
        assert full_host.transport_entered.is_set()
        if termination == "cancelled":
            task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not roots[0].lease.is_active and roots[0].lease.termination == termination
        before = full_host.db.get_messages("fixed-session")
        full_host.transport_release.set()
        for _ in range(1000):
            if full_host.worker_finished.is_set():
                break
            await asyncio.sleep(.01)
        assert full_host.worker_finished.is_set()
        assert full_host.db.get_messages("fixed-session") == before
        assert len(full_host.requests) == 1  # Already authorized before cancellation.
    finally:
        full_host.transport_release.set()
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)


async def wait_signal(signal, task=None):
    for _ in range(1000):
        if signal.is_set():
            return
        if task is not None and task.done():
            await task
            raise AssertionError("native caller completed before the observed boundary")
        await asyncio.sleep(.01)
    raise AssertionError("native boundary was not reached")


@pytest.mark.asyncio
@pytest.mark.parametrize("race", ["repeated-cancellation", "swallowed-child"])
async def test_complete_caller_cancellation_races_and_late_callbacks(full_host, monkeypatch, race):
    full_host.block_transport = True
    full_host.probe_late_callbacks = True
    cleanup_entered, child_caught, child_release = asyncio.Event(), asyncio.Event(), asyncio.Event()
    roots, children = [], []
    original_schedule = full_host.factory.schedule

    def schedule(*args):
        task = original_schedule(*args)
        children.append(task)
        return task

    monkeypatch.setattr(full_host.factory, "schedule", schedule)
    if race == "repeated-cancellation":
        original_wait = asyncio.wait

        async def wait(*args, **kwargs):
            scope = governance._session_write.get()
            if scope is not None and scope.lease.parent is None and not scope.lease.is_active:
                # Suspend the cleanup await after actual native synchronous revocation.
                cleanup_entered.set()
                await asyncio.Event().wait()
            return await original_wait(*args, **kwargs)

        monkeypatch.setattr(asyncio, "wait", wait)
    else:
        original_execute = CandidateSessionExecutorHandoff.execute

        async def execute(handoff, *args):
            try:
                return await original_execute(handoff, *args)
            except asyncio.CancelledError:
                # Fault-inject a cancellation-swallowing await, not another agent/closure.
                child_caught.set()
                await child_release.wait()
                assert not governance._session_write.get().lease.is_active
                with pytest.raises(governance.GovernanceBoundaryError):
                    full_host.plugin._actor()
                return None

        monkeypatch.setattr(CandidateSessionExecutorHandoff, "execute", execute)

    async def request():
        with full_host.binding.authenticated_request(full_host.owner):
            roots.append(governance._session_write.get())
            return await full_call(full_host)

    task = asyncio.create_task(request())
    try:
        await wait_signal(full_host.transport_entered, task)
        task.cancel()
        if race == "repeated-cancellation":
            await wait_signal(cleanup_entered, task)
            assert not roots[0].lease.is_active
            task.cancel()
        else:
            await wait_signal(child_caught, task)
            assert not roots[0].lease.is_active
        with pytest.raises(asyncio.CancelledError):
            await task
        assert roots[0].lease.termination == "cancelled"
        before = full_host.db.get_messages("fixed-session")
        audit_before = [json.loads(line) for line in full_host.audit.path.read_text().splitlines()]
        full_host.transport_release.set()
        await wait_signal(full_host.worker_finished)
        assert full_host.late_denials == ["model", "tool", "output", "write"]
        assert full_host.db.get_messages("fixed-session") == before
        audit_after = [json.loads(line) for line in full_host.audit.path.read_text().splitlines()]
        assert audit_after[:len(audit_before)] == audit_before
        assert audit_after[len(audit_before):]
        assert all(record["decision"] == "deny" for record in audit_after[len(audit_before):])
        assert len(full_host.requests) == 1
        assert full_host.runner._running_agents == {}
        child_release.set()
        await asyncio.gather(*children, return_exceptions=True)
        assert all(child.done() for child in children)
    finally:
        full_host.transport_release.set()
        child_release.set()
        if not task.done():
            task.cancel()
        await asyncio.gather(task, *children, return_exceptions=True)

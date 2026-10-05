"""Create-to-agent composition; synthetic SDK transport, excluded title worker."""
import importlib.util
import json
from pathlib import Path
import sys
import threading
import traceback
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
from openai import OpenAI
import pytest
import gateway.run as native
from gateway.config import Platform
from gateway.session import SessionSource
from hermes_cli import middleware
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins import governance
from project_maya.hermes_plugins.session_handoff import CandidateConversationExecutorFactory
from project_maya.hermes_plugins.candidate_transport import completion_response
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("create_loop_fixture", ROOT / "tests/hermes_g2_caller_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
host = base.host
caller_host = base.caller_host


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    with_source = str(ROOT / "scripts")
    sys.path.insert(0, with_source)
    try:
        from prepare_governance_g2_caller_qualification import verify_stage
        import hermes_state
        source, staged = verify_stage(Path(hermes_state.__file__).resolve().parent.parent)
        assert Path(native.__file__).resolve().is_relative_to(source)
        assert Path(governance.__file__).resolve().is_relative_to(staged)
    finally:
        sys.path.remove(with_source)


@pytest.fixture
def loop_host(caller_host, monkeypatch, tmp_path):
    import run_agent
    import agent.title_generator as titles

    original, caller, reader = caller_host
    store, db, binding, coordinator = original
    runner = object.__new__(native.GatewayRunner)
    runner._session_db = db
    CandidateConversationExecutorFactory(runner, audit_sink=binding.audit, acknowledgement=ACKNOWLEDGEMENT)
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
        "_session_model_overrides": {binding.route_slot: {
            "model": "synthetic-model", "provider": "openai",
            "api_key": "synthetic-fixture-not-a-secret",
            "base_url": "https://api.openai.com/v1", "api_mode": "chat_completions"}},
    }.items():
        setattr(runner, name, value)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(native, "_hermes_home", tmp_path / "home")
    monkeypatch.setattr(runner, "_get_proxy_url", Mock(return_value=None))
    monkeypatch.setattr(runner, "_resolve_profile_home_for_source", Mock(side_effect=AssertionError("excluded profile")))
    monkeypatch.setattr(native, "_load_gateway_config", lambda: {
        "model": {"default": "synthetic-model"}, "agent": {"max_turns": 2},
        "display": {"tool_progress": "off", "streaming": False,
                    "interim_assistant_messages": False, "thinking_progress": False}})
    plugin = middleware._mandatory_callbacks["llm_execution"].__self__
    plugin.gateway = PolicyAuthorizationGateway(tuple(PolicyRule(capability, actor_id="alice")
        for capability in ("model.egress", "model.output", "session.write")))
    result = SimpleNamespace(original=original, store=store, db=db, binding=binding,
        reader=reader, caller=caller, runner=runner, plugin=plugin, agents=[], requests=[], clients=[])
    original_init = run_agent.AIAgent.__init__
    original_conversation = run_agent.AIAgent.run_conversation
    result.fixture_errors = []

    def construct(agent, *args, **kwargs):
        scope = governance._session_write.get()
        assert scope.identity == binding.owner and scope.lease.is_active
        assert scope.session_id == result.session_id and scope.database == binding.database
        assert scope.thread_id == threading.get_ident() and scope.task is None
        assert base.state(original) == "caller_acknowledged"
        try:
            original_init(agent, *args, **kwargs)
        except Exception as error:
            result.fixture_errors.append((type(error).__name__,
                [(frame.name, frame.lineno) for frame in traceback.extract_tb(error.__traceback__)]))
            raise
        result.agents.append(agent)

    def respond(request):
        records = [json.loads(line) for line in binding.audit.path.read_text().splitlines()]
        assert any(row.get("capability") == "model.egress" and row.get("decision") == "allow" for row in records)
        result.requests.append(request.url.path)
        return completion_response(request, tool=False)

    def conversation(agent, *args, **kwargs):
        try:
            return original_conversation(agent, *args, **kwargs)
        except Exception as error:
            result.fixture_errors.append((type(error).__name__,
                [(frame.name, frame.lineno) for frame in traceback.extract_tb(error.__traceback__)]))
            raise

    def client(**kwargs):
        kwargs["max_retries"] = 0
        kwargs["http_client"] = httpx.Client(transport=httpx.MockTransport(respond), trust_env=False)
        sdk = OpenAI(**kwargs)
        result.clients.append(sdk)
        return sdk

    # Title/background execution is explicitly excluded, not represented as qualified.
    result.title_calls = Mock(return_value=None)
    monkeypatch.setattr(titles, "maybe_auto_title", result.title_calls)
    monkeypatch.setattr(run_agent, "OpenAI", client)
    monkeypatch.setattr(run_agent.AIAgent, "__init__", construct)
    monkeypatch.setattr(run_agent.AIAgent, "run_conversation", conversation)
    monkeypatch.setattr(run_agent, "get_tool_definitions", lambda **kwargs: [])
    monkeypatch.setattr(run_agent, "check_toolset_requirements", lambda **kwargs: {})
    yield result
    for sdk in result.clients:
        sdk.close()


async def execute(host):
    with host.store.authenticated_owned_session_candidate(host.binding.owner) as entry:
        host.session_id = entry.session_id
        root = governance._session_write.get()
        history = host.store.load_transcript(entry.session_id)
        assert history == []
        result = await host.runner._run_agent("Synthetic current question", "", history,
            SessionSource(platform=Platform.LOCAL, chat_id="fixture", user_id="alice"),
            entry.session_id, session_key=host.binding.route_slot)
        assert not root.lease.is_active
        return result


@pytest.mark.asyncio
async def test_created_session_first_turn_blocks_lazy_recreation(loop_host):
    host = loop_host
    with host.store.prepare_owned_session_candidate(host.binding.owner) as receipt:
        assert not host.agents and not host.requests
    before = list(host.db._conn.iterdump())
    with pytest.raises(middleware.MandatoryMiddlewareError):
        await execute(host)
    assert not host.requests and len(host.agents) == 1
    assert all(sdk.max_retries == 0 for sdk in host.clients)
    assert host.db.get_messages(receipt["session_id"]) == []
    assert list(host.db._conn.iterdump()) == before
    assert base.state(host.original) == "caller_acknowledged"
    assert host.fixture_errors
    assert {"_ensure_db_session", "create_session"}.issubset(
        {name for name, _ in host.fixture_errors[0][1]})
    host.title_calls.assert_not_called()
    assert host.reader._active is None and not host.store._entries


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["preparation", "acknowledgement", "reader", "model"])
async def test_failed_handoff_cannot_reach_unauthorized_transport(loop_host, failure):
    host = loop_host
    expected = RuntimeError if failure == "preparation" else middleware.MandatoryMiddlewareError
    with pytest.raises(expected):
        with host.store.prepare_owned_session_candidate(host.binding.owner):
            if failure == "preparation":
                raise RuntimeError("synthetic preparation failure")
            if failure == "acknowledgement":
                host.binding.gateway = PolicyAuthorizationGateway(())
        if failure == "reader":
            host.binding.gateway = PolicyAuthorizationGateway(())
        if failure == "model":
            host.plugin.gateway = PolicyAuthorizationGateway((PolicyRule("session.write", actor_id="alice"),))
        await execute(host)
    assert not host.requests
    if failure != "model":
        assert not host.agents and not host.clients
    assert host.reader._active is None and not host.store._entries
    assert not host.db._conn.in_transaction

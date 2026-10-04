"""Complete native entry-method probes, not full conversation qualification."""
import asyncio
from contextvars import copy_context
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

import gateway.run as native
from hermes_cli import middleware, plugins
from hermes_state import SessionDB
from project_maya.audit import LocalJsonlAuditSink
from project_maya.config import config_from_mapping
from project_maya.governance import DenyByDefaultGateway
from project_maya.hermes_plugins import governance
from project_maya.hermes_plugins.session_handoff import CandidateConversationExecutorFactory, _caller_entry
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT, CandidateSessionRequestBinding


class ReachedConfiguration(RuntimeError):
    pass


@pytest.fixture
def host(tmp_path, monkeypatch):
    # Explicit fixture provisioning, not conversation-authorized schema creation.
    monkeypatch.setattr(middleware, "_mandatory_enabled", False)
    monkeypatch.setattr(middleware, "_mandatory_callbacks", {})
    db = SessionDB(tmp_path / "native.db")
    other = SessionDB(tmp_path / "other.db")
    db.create_session("fixed-session", source="g1-entry-test")
    audit = LocalJsonlAuditSink(tmp_path / "audit.jsonl")
    config = config_from_mapping({
        "schema_version": 2,
        "product": {"edition": "enterprise", "instance_id": "g1-test"},
        "deployment": {"class": "desktop", "network_policy": "standard", "data_dir": str(tmp_path)},
        "runtime": {"hermes_compatibility": ">=0.1", "enabled_profiles": ["maya-core"]},
        "broker": {"mode": "disabled"},
        "llm": {"mode": "customer_owned", "provider": "openai", "model": "synthetic-model",
                "credential_ref": "secret://llm/test", "endpoint": "https://api.openai.com/v1"},
        "memory": {"hermes_provider": "local", "retriever": "local_vector", "registry": "sqlite", "governance_enabled": True},
        "governance": {"policy_file": str(tmp_path / "policy.yaml"), "default_action": "deny", "minimum_memory_trust": 0.7},
        "metabase": {"enabled": False, "deployment": "managed_local"},
    })
    plugin = governance.MayaGovernancePlugin(config, DenyByDefaultGateway(), audit)
    manager = plugins.get_plugin_manager()
    monkeypatch.setattr(manager, "_middleware", {})
    context = plugins.PluginContext(plugins.PluginManifest(name="maya-g1-entry-test"), manager)
    # Direct candidate registration, not production discovery/contract activation.
    for kind, callback in (
        ("llm_execution", plugin.model_execution), ("tool_execution", plugin.tool_execution),
        ("tool_result", plugin.tool_result), ("model_output", plugin.model_output),
        ("session_write", plugin.session_write),
    ):
        context.register_middleware(kind, callback)
        middleware.require_middleware(kind, callback)
    owner = governance.RequestIdentity("operator", "restricted")
    binding = CandidateSessionRequestBinding(owner, "fixed-session", db.db_path,
        frozenset({"append"}), ACKNOWLEDGEMENT, audit_sink=audit)
    # Do not invoke native GatewayRunner construction/schema/service startup in G1.
    # The class and all invoked caller methods are the actual staged native code.
    runner = object.__new__(native.GatewayRunner)
    runner.config = SimpleNamespace(multiplex_profiles=False)
    runner._session_db = db
    factory = CandidateConversationExecutorFactory(runner, audit_sink=audit, acknowledgement=ACKNOWLEDGEMENT)
    proxy = Mock(return_value=None)
    monkeypatch.setattr(runner, "_get_proxy_url", proxy)
    cfg = Mock(side_effect=ReachedConfiguration("observed-before-provider-selection"))
    monkeypatch.setattr(native, "_load_gateway_config", cfg)
    profile = Mock(side_effect=AssertionError("excluded profile was accessed"))
    monkeypatch.setattr(runner, "_resolve_profile_home_for_source", profile)
    fixture = SimpleNamespace(runner=runner, factory=factory, binding=binding, owner=owner,
        db=db, other=other, audit=audit, proxy=proxy, cfg=cfg, profile=profile)
    yield fixture
    # Teardown is fixture-owned; candidate close/provisioning is G3 qualification.
    monkeypatch.setattr(middleware, "_mandatory_enabled", False)
    db.close()
    other.close()


async def call(host, method="_run_agent", **kwargs):
    return await getattr(host.runner, method)("synthetic question", "", [], None,
                                              kwargs.pop("session_id", "fixed-session"), **kwargs)


def no_early_effects(host):
    host.proxy.assert_not_called()
    host.cfg.assert_not_called()
    host.profile.assert_not_called()
    assert host.db.get_messages("fixed-session") == []
    assert _caller_entry.get() is None


@pytest.mark.asyncio
async def test_allowed_native_outer_and_inner_reach_configuration(host):
    with host.binding.authenticated_request(host.owner):
        with pytest.raises(ReachedConfiguration):
            await call(host)
        root = governance._session_write.get()
        assert root.identity == host.owner and root.session_id == "fixed-session"
    host.proxy.assert_called_once()
    host.cfg.assert_called_once()
    records = [json.loads(row) for row in host.audit.path.read_text().splitlines()]
    assert any(row["event_type"] == "authentication.native_caller" for row in records)


@pytest.mark.asyncio
async def test_unbound_denies_before_native_proxy_lookup(host):
    with pytest.raises(middleware.MandatoryMiddlewareError):
        await call(host)
    no_early_effects(host)


@pytest.mark.asyncio
@pytest.mark.parametrize("damage", ["missing", "replaced", "resolver", "method", "gate"])
async def test_missing_or_replaced_binding_denies_at_entry(host, damage):
    with host.binding.authenticated_request(host.owner):
        if damage == "missing":
            del host.runner._maya_conversation_executor_factory
        elif damage == "replaced":
            host.runner._maya_conversation_executor_factory = object()
        elif damage == "resolver":
            host.runner._maya_request_executor = object()
        elif damage == "method":
            host.runner._run_in_executor_with_context = Mock()
        else:
            middleware._mandatory_callbacks.pop("model_output")
        with pytest.raises(middleware.MandatoryMiddlewareError):
            await call(host)
    no_early_effects(host)


@pytest.mark.asyncio
@pytest.mark.parametrize("damage", ["identity", "session", "database", "expired", "unbounded"])
async def test_wrong_or_expired_authority_denies_before_lookup(host, damage):
    with host.binding.authenticated_request(host.owner):
        scope = governance._session_write.get()
        token = None
        if damage == "identity":
            token = governance._identity.set(governance.RequestIdentity("other", "restricted"))
        elif damage == "database":
            host.runner._session_db = host.other
        elif damage == "expired":
            scope.lease.revoke("timeout")
        elif damage == "unbounded":
            scope.lease.deadline = None
        try:
            with pytest.raises(middleware.MandatoryMiddlewareError):
                await call(host, session_id="other-session" if damage == "session" else "fixed-session")
        finally:
            if token is not None:
                governance._identity.reset(token)
    no_early_effects(host)


@pytest.mark.asyncio
async def test_unrelated_task_cannot_borrow_root_context(host):
    with host.binding.authenticated_request(host.owner):
        with pytest.raises(middleware.MandatoryMiddlewareError):
            await asyncio.create_task(call(host))
    no_early_effects(host)


@pytest.mark.asyncio
async def test_captured_context_cannot_reenter_after_root_exit(host):
    with host.binding.authenticated_request(host.owner):
        captured = copy_context()
    task = captured.run(asyncio.create_task, call(host))
    with pytest.raises(middleware.MandatoryMiddlewareError):
        await task
    no_early_effects(host)


@pytest.mark.asyncio
async def test_direct_inner_without_native_outer_scope_is_denied(host):
    with host.binding.authenticated_request(host.owner):
        with pytest.raises(middleware.MandatoryMiddlewareError):
            await call(host, "_run_agent_inner")
    no_early_effects(host)


@pytest.mark.asyncio
@pytest.mark.parametrize("root", ["proxy", "background", "background-command", "profiles", "continuation"])
async def test_excluded_roots_deny_before_support_work(host, root):
    with host.binding.authenticated_request(host.owner):
        with pytest.raises(middleware.MandatoryMiddlewareError):
            if root == "proxy":
                await call(host, "_run_agent_via_proxy")
            elif root == "background":
                await host.runner._run_background_task("synthetic", None, "job-1")
            elif root == "background-command":
                await host.runner._handle_background_command(None)
            elif root == "profiles":
                host.runner.config.multiplex_profiles = True
                await call(host)
            else:
                await call(host, _interrupt_depth=1)
    no_early_effects(host)


@pytest.mark.asyncio
async def test_configured_proxy_never_dispatches(host):
    host.proxy.return_value = "https://excluded.invalid"
    dispatch = Mock(side_effect=AssertionError("proxy dispatch reached"))
    with host.binding.authenticated_request(host.owner), patch.object(host.runner, "_run_agent_via_proxy", dispatch):
        with pytest.raises(middleware.MandatoryMiddlewareError, match="caller_entry_excluded"):
            await call(host)
    dispatch.assert_not_called()
    host.cfg.assert_not_called()


@pytest.mark.asyncio
async def test_entry_is_single_use_and_nested_caller_is_denied(host):
    with host.binding.authenticated_request(host.owner):
        with host.factory.caller_scope(host.runner, "fixed-session"):
            with pytest.raises(middleware.MandatoryMiddlewareError):
                await call(host)
        with pytest.raises(middleware.MandatoryMiddlewareError):
            await call(host)
    no_early_effects(host)


@pytest.mark.asyncio
async def test_audit_failure_is_fixed_and_precedes_native_lookup(host):
    with host.binding.authenticated_request(host.owner):
        with patch.object(host.audit, "write", side_effect=RuntimeError("private-marker-do-not-publish")):
            with pytest.raises(middleware.MandatoryMiddlewareError, match="caller_entry_failed") as failure:
                await call(host)
            assert "private-marker" not in str(failure.value)
    no_early_effects(host)


@pytest.mark.asyncio
async def test_ordinary_caller_still_reaches_same_native_configuration(host, monkeypatch):
    monkeypatch.setattr(middleware, "_mandatory_enabled", False)
    del host.runner._maya_conversation_executor_factory
    with pytest.raises(ReachedConfiguration):
        await call(host)
    host.proxy.assert_called_once()
    host.cfg.assert_called_once()

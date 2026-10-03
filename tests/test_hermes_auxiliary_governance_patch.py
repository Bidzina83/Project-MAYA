"""Exercise the actual pinned auxiliary router with the candidate patch series."""

import ast
import asyncio
import hashlib
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from urllib.parse import urlparse

from project_maya.config import config_from_mapping
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.governance import (
    GovernanceBoundaryError, MayaGovernancePlugin, bind_request_identity, require_runtime_contract,
)
from tests.test_phase0_contracts import valid_config_mapping


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "hermes_middleware"
PATCHES = ROOT / "patches" / "hermes"
HASHES = {
    "auxiliary_client.py": "317d71beee41a235171d25c441c46587d64246c1ca6efa9c9aee8c5c53475f3c",
    "plugin_llm.py": "4158b0ed2be2140eb99f09e1a488daed04da496052fe415cb84e412e4b71fb30",
}


class TestHermesAuxiliaryGovernancePatch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.target = Path(self.tmp.name)
        for relative, source in (("hermes_cli/middleware.py", "middleware.py"),
                                 ("agent/auxiliary_client.py", "auxiliary_client.py"),
                                 ("agent/plugin_llm.py", "plugin_llm.py")):
            destination = self.target / relative
            destination.parent.mkdir(exist_ok=True)
            shutil.copyfile(FIXTURE / source, destination)
        for filename in ("0001-opt-in-mandatory-middleware.patch", "0002-governed-auxiliary-inference.patch"):
            result = subprocess.run(["git", "apply", "--whitespace=error", str(PATCHES / filename)],
                                    cwd=self.tmp.name, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)

        self.manager = SimpleNamespace(_middleware={})
        self.config = {"plugins": {"entries": {"synthetic-plugin": {"llm": {
            "allow_provider_override": True, "allowed_providers": ["openai"],
            "allow_model_override": True, "allowed_models": ["synthetic-model"],
        }}}}}
        modules = {}
        for name in ("agent", "hermes_cli"):
            modules[name] = ModuleType(name)
            modules[name].__path__ = []
        modules["agent.credential_pool"] = SimpleNamespace(load_pool=Mock())
        modules["agent.portal_tags"] = SimpleNamespace(nous_portal_tags=lambda: [])
        modules["agent.anthropic_adapter"] = SimpleNamespace(_forbids_sampling_params=lambda model: False)
        modules["hermes_cli.config"] = SimpleNamespace(
            get_hermes_home=lambda: self.target, load_config=lambda: self.config,
        )
        modules["hermes_cli.plugins"] = SimpleNamespace(
            get_plugin_manager=lambda: self.manager, get_plugin_auxiliary_tasks=lambda: [],
        )
        modules["hermes_constants"] = SimpleNamespace(OPENROUTER_BASE_URL="https://openrouter.example/v1")
        modules["utils"] = SimpleNamespace(
            base_url_hostname=lambda url: urlparse(url).hostname or "",
            base_url_host_matches=lambda url, host: urlparse(url).hostname == host,
            env_float=lambda name, default, **kw: default,
            model_forces_max_completion_tokens=lambda model: False,
            normalize_proxy_env_vars=lambda: None,
        )
        self.start_patch(patch.dict(sys.modules, modules))
        # Resolution and transports are inert; socket use is a test failure.
        self.start_patch(patch("socket.create_connection", side_effect=AssertionError("network forbidden")))
        self.engine = self.load("hermes_cli.middleware", self.target / "hermes_cli/middleware.py")
        self.aux = self.load("agent.auxiliary_client", self.target / "agent/auxiliary_client.py")
        self.original = self.load("_original_auxiliary_client", FIXTURE / "auxiliary_client.py")
        self.plugin_llm = self.load("agent.plugin_llm", self.target / "agent/plugin_llm.py")
        self.response = SimpleNamespace(
            model="synthetic-model", choices=[SimpleNamespace(message=SimpleNamespace(content="synthetic result"))],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        )
        self.sync_transport = Mock(return_value=self.response)
        self.async_transport = AsyncMock(return_value=self.response)
        self.sync_client = self.client(self.sync_transport)
        self.async_client = self.client(self.async_transport)
        self.messages = [{"role": "user", "content": "Synthetic operational question"}]
        self.events = []
        self.caches = {}
        for module in (self.aux, self.original):
            cached = Mock(side_effect=lambda *args, **kw: (
                self.async_client if kw.get("async_mode") else self.sync_client, "synthetic-model",
            ))
            self.start_patch(patch.object(module, "_get_cached_client", cached))
            self.caches[module.__name__] = cached
            self.start_patch(patch.object(module, "_recoverable_pool_provider", return_value=None))
            self.start_patch(patch.object(module, "_refresh_provider_credentials", return_value=False))
            for name in ("_try_configured_fallback_chain", "_try_main_fallback_chain",
                         "_try_payment_fallback", "_try_main_agent_model_fallback"):
                self.start_patch(patch.object(module, name, return_value=(None, None, "")))

    def start_patch(self, patcher):
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def load(self, name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        self.start_patch(patch.dict(sys.modules, {name: module}))
        spec.loader.exec_module(module)
        return module

    def client(self, transport, endpoint="https://api.openai.com/v1"):
        return SimpleNamespace(base_url=endpoint, api_key="", chat=SimpleNamespace(completions=SimpleNamespace(create=transport)))

    def install_gates(self, gate=None):
        def allow(request, next_call, **context):
            self.events.append((dict(request), dict(context)))
            return next_call(request)
        model = gate or allow
        tool = lambda args, next_call, **kw: next_call(args)
        for kind, callback in (("llm_execution", model), ("tool_execution", tool)):
            self.manager._middleware[kind] = [callback]
            self.engine.require_middleware(kind, callback)

    def call(self, async_mode=False, module=None, **kwargs):
        module = module or self.aux
        args = dict(provider="openai", model="synthetic-model", messages=self.messages, task="compression")
        args.update(kwargs)
        if async_mode:
            return asyncio.run(module.async_call_llm(**args))
        return module.call_llm(**args)

    def test_pinned_sources_match_recorded_hashes(self):
        for filename, expected in HASHES.items():
            normalized = (FIXTURE / filename).read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(hashlib.sha256(normalized).hexdigest(), expected)

    def test_no_full_contract_marker_or_startup_unlock(self):
        with self.assertRaises(GovernanceBoundaryError):
            require_runtime_contract(self.engine)

    def test_default_sync_and_async_requests_match_unmodified_router(self):
        for async_mode in (False, True):
            with self.subTest(async_mode=async_mode):
                transport = self.async_transport if async_mode else self.sync_transport
                self.call(async_mode, self.original)
                original_request = transport.call_args.kwargs
                transport.reset_mock()
                self.assertIs(self.call(async_mode), self.response)
                self.assertEqual(transport.call_args.kwargs, original_request)
                transport.assert_called_once()

    def test_default_auxiliary_calls_do_not_gain_new_middleware_behavior(self):
        # Upstream auxiliary calls did not enter the conversation middleware.
        self.manager._middleware["llm_execution"] = [Mock(side_effect=RuntimeError("synthetic failure"))]
        self.assertIs(self.call(), self.response)
        self.assertIs(self.call(True), self.response)
        self.manager._middleware["llm_execution"][0].assert_not_called()

    def test_default_retry_requests_match_unmodified_router(self):
        for async_mode in (False, True):
            transport = self.async_transport if async_mode else self.sync_transport
            sequences = []
            for module in (self.original, self.aux):
                transport.reset_mock()
                transport.side_effect = [RuntimeError("incomplete chunked read"), self.response]
                self.assertIs(self.call(async_mode, module=module), self.response)
                sequences.append(transport.call_args_list)
            self.assertEqual(sequences[0], sequences[1])

    def test_default_parameter_retry_matches_unmodified_router(self):
        sequences = []
        for module in (self.original, self.aux):
            self.sync_transport.reset_mock()
            self.sync_transport.side_effect = [RuntimeError("unsupported parameter: temperature"), self.response]
            self.assertIs(self.call(module=module, temperature=0.3), self.response)
            sequences.append(self.sync_transport.call_args_list)
        self.assertEqual(sequences[0], sequences[1])

    def test_missing_gate_blocks_before_client_resolution(self):
        self.engine.enable_mandatory_middleware()
        for async_mode in (False, True):
            with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "gate_missing"):
                self.call(async_mode)
        self.caches[self.aux.__name__].assert_not_called()
        self.sync_transport.assert_not_called()
        self.async_transport.assert_not_called()

    def test_sync_and_async_preserve_declared_openai_alias_and_actual_route(self):
        self.install_gates()
        for async_mode in (False, True):
            self.assertIs(self.call(async_mode), self.response)
        for request, context in self.events:
            self.assertEqual(context["provider"], "openai")
            self.assertEqual(context["base_url"], "https://api.openai.com/v1")
            self.assertEqual(context["model"], request["model"])
            self.assertEqual(context["api_mode"], "chat_completions")
            self.assertEqual(context["auxiliary_task"], "compression")

    def test_config_declared_provider_is_preserved_without_explicit_argument(self):
        self.config["auxiliary"] = {"compression": {"provider": "openai", "model": "synthetic-model"}}
        self.install_gates()
        self.call(provider=None)
        self.assertEqual(self.events[0][1]["provider"], "openai")

    def test_required_gate_metadata_tracks_execution_middleware_model_changes(self):
        self.install_gates()
        for async_mode in (False, True):
            if async_mode:
                async def rewrite(request, next_call, **kw):
                    return await next_call({**request, "model": "changed-model"})
            else:
                def rewrite(request, next_call, **kw):
                    return next_call({**request, "model": "changed-model"})
            self.manager._middleware["llm_execution"] = [self.engine._mandatory_callbacks["llm_execution"], rewrite]
            self.assertIs(self.call(async_mode), self.response)
            request, context = self.events[-1]
            self.assertEqual(request["model"], "changed-model")
            self.assertEqual(context["model"], "changed-model")

    def test_ambiguous_auto_routes_are_blocked_in_both_modes(self):
        self.install_gates()
        for async_mode in (False, True):
            with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "route_ambiguous"):
                self.call(async_mode, provider="auto")
        self.sync_transport.assert_not_called()
        self.async_transport.assert_not_called()

    def test_policy_failure_does_not_trigger_retry_refresh_or_fallback(self):
        def deny(**kw):
            raise RuntimeError("payment required sensitive fixture error")
        self.install_gates(deny)
        for async_mode in (False, True):
            with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "callback_failed"):
                self.call(async_mode)
        self.sync_transport.assert_not_called()
        self.async_transport.assert_not_called()
        self.aux._refresh_provider_credentials.assert_not_called()
        self.aux._try_configured_fallback_chain.assert_not_called()

    def test_each_transient_retry_is_authorized_sync_and_async(self):
        self.install_gates()
        for async_mode, transport in ((False, self.sync_transport), (True, self.async_transport)):
            transport.side_effect = [RuntimeError("incomplete chunked read"), self.response]
            self.assertIs(self.call(async_mode), self.response)
            self.assertEqual(transport.call_count, 2)
        self.assertEqual(len(self.events), 4)

    def test_gate_removed_between_attempts_prevents_retry_and_fallback(self):
        self.install_gates()
        def transient(**kw):
            self.manager._middleware.clear()
            raise RuntimeError("incomplete chunked read")
        self.sync_transport.side_effect = transient
        with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "gate_missing"):
            self.call()
        self.sync_transport.assert_called_once()
        self.aux._try_configured_fallback_chain.assert_not_called()

    def test_temperature_retry_authorizes_modified_payload(self):
        self.install_gates()
        self.sync_transport.side_effect = [RuntimeError("unsupported parameter: temperature"), self.response]
        self.assertIs(self.call(temperature=0.3), self.response)
        self.assertIn("temperature", self.events[0][0])
        self.assertNotIn("temperature", self.events[1][0])
        self.assertEqual(self.sync_transport.call_count, 2)

    def test_credential_refresh_uses_new_client_route_and_keeps_provider_alias(self):
        self.install_gates()
        for async_mode, transport in ((False, self.sync_transport), (True, self.async_transport)):
            with self.subTest(async_mode=async_mode):
                error = RuntimeError("synthetic authentication failure")
                error.status_code = 401
                transport.side_effect = error
                refreshed_transport = AsyncMock(return_value=self.response) if async_mode else Mock(return_value=self.response)
                refreshed = self.client(refreshed_transport, "https://refreshed.example/v1")
                initial = self.async_client if async_mode else self.sync_client
                self.caches[self.aux.__name__].side_effect = [(initial, "synthetic-model"), (refreshed, "new-model")]
                self.aux._refresh_provider_credentials.return_value = True
                self.assertIs(self.call(async_mode), self.response)
                request, context = self.events[-1]
                self.assertEqual(context["provider"], "openai")
                self.assertEqual(context["base_url"], "https://refreshed.example/v1")
                self.assertEqual(request["model"], "new-model")
                refreshed_transport.assert_called_once()

    def test_nous_refresh_reauthorizes_new_model_and_endpoint_sync_and_async(self):
        self.install_gates()
        for async_mode, transport in ((False, self.sync_transport), (True, self.async_transport)):
            with self.subTest(async_mode=async_mode):
                error = RuntimeError("synthetic authentication failure")
                error.status_code = 401
                transport.side_effect = error
                refreshed_transport = AsyncMock(return_value=self.response) if async_mode else Mock(return_value=self.response)
                refreshed = self.client(refreshed_transport, "https://nous-refresh.example/v1")
                with patch.object(self.aux, "_refresh_nous_auxiliary_client", return_value=(refreshed, "new-model")):
                    self.assertIs(self.call(async_mode, provider="nous"), self.response)
                request, context = self.events[-1]
                self.assertEqual(context["provider"], "nous")
                self.assertEqual(context["base_url"], "https://nous-refresh.example/v1")
                self.assertEqual(request["model"], "new-model")

    def test_credential_pool_rotation_reauthorizes_rebuilt_request(self):
        self.install_gates()
        error = RuntimeError("payment required")
        self.sync_transport.side_effect = error
        refreshed_transport = Mock(return_value=self.response)
        refreshed = self.client(refreshed_transport, "https://pool-rebuilt.example/v1")
        self.caches[self.aux.__name__].side_effect = [(self.sync_client, "synthetic-model"), (refreshed, "new-model")]
        with patch.object(self.aux, "_recoverable_pool_provider", return_value="openai"), \
             patch.object(self.aux, "_recover_provider_pool", return_value=True):
            self.assertIs(self.call(), self.response)
        request, context = self.events[-1]
        self.assertEqual(context["base_url"], "https://pool-rebuilt.example/v1")
        self.assertEqual(context["provider"], "openai")
        self.assertEqual(request["model"], "new-model")
        self.aux._try_configured_fallback_chain.assert_not_called()

    def test_fallback_authorizes_actual_endpoint_provider_and_model(self):
        self.install_gates()
        self.sync_transport.side_effect = RuntimeError("payment required")
        fallback_transport = Mock(return_value=self.response)
        fallback_client = self.client(fallback_transport, "https://fallback.example/v1")
        self.aux._try_configured_fallback_chain.return_value = (fallback_client, "fallback-model", "other")
        self.assertIs(self.call(), self.response)
        request, context = self.events[-1]
        self.assertEqual(context["provider"], "other")
        self.assertEqual(context["base_url"], "https://fallback.example/v1")
        self.assertEqual(request["model"], "fallback-model")
        self.assertEqual(context["model"], "fallback-model")

    def test_async_fallback_authorizes_post_conversion_model_and_endpoint(self):
        self.install_gates()
        self.async_transport.side_effect = RuntimeError("payment required")
        fallback_transport = AsyncMock(return_value=self.response)
        async_client = self.client(fallback_transport, "https://async-fallback.example/v1")
        self.aux._try_configured_fallback_chain.return_value = (self.sync_client, "before-conversion", "other")
        with patch.object(self.aux, "_to_async_client", return_value=(async_client, "after-conversion")):
            self.assertIs(self.call(True), self.response)
        request, context = self.events[-1]
        self.assertEqual(request["model"], "after-conversion")
        self.assertEqual(context["base_url"], "https://async-fallback.example/v1")
        self.assertEqual(context["provider"], "other")

    def setup_maya(self):
        data = valid_config_mapping()
        data["deployment"]["data_dir"] = self.tmp.name
        data["llm"].update(mode="customer_owned", provider="openai", model="synthetic-model", endpoint="https://api.openai.com/v1")
        self.audit = Mock()
        gateway = PolicyAuthorizationGateway((
            PolicyRule("model.egress", target="model:openai", operation="infer", actor_id="alice"),
        ))
        plugin = MayaGovernancePlugin(config_from_mapping(data), gateway, self.audit)
        self.install_gates(plugin.model_execution)

    def test_real_maya_policy_allows_authenticated_sync_and_async_requests(self):
        self.setup_maya()
        with bind_request_identity("alice"):
            self.assertIs(self.call(), self.response)
            self.assertIs(self.call(True), self.response)
        self.assertEqual(self.audit.write.call_count, 2)

    def test_real_maya_policy_reauthorizes_transport_retries_in_both_modes(self):
        self.setup_maya()
        for async_mode, transport in ((False, self.sync_transport), (True, self.async_transport)):
            transport.side_effect = [RuntimeError("incomplete chunked read"), self.response]
            with bind_request_identity("alice"):
                self.assertIs(self.call(async_mode), self.response)
            self.assertEqual(transport.call_count, 2)
        self.assertEqual(self.audit.write.call_count, 4)

    def test_real_maya_denies_changed_fallback_before_transmission(self):
        self.setup_maya()
        self.sync_transport.side_effect = RuntimeError("payment required")
        fallback_transport = Mock(return_value=self.response)
        self.aux._try_configured_fallback_chain.return_value = (
            self.client(fallback_transport, "https://other.example/v1"), "synthetic-model", "openai",
        )
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.call()
        self.sync_transport.assert_called_once()
        fallback_transport.assert_not_called()
        self.aux._try_configured_fallback_chain.assert_called_once()

    def test_real_maya_missing_identity_denies_async_without_transmission(self):
        self.setup_maya()
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.call(True)
        self.async_transport.assert_not_called()

    def test_exhausted_error_and_logs_are_secret_safe_in_mandatory_mode(self):
        self.install_gates()
        self.sync_transport.side_effect = RuntimeError("payment required sensitive-fixture-error")
        with self.assertLogs(self.aux.logger, "INFO") as captured:
            with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "auxiliary_failed") as caught:
                self.call()
        self.assertNotIn("sensitive-fixture-error", " ".join(captured.output) + str(caught.exception))
        self.assertTrue(caught.exception.__suppress_context__)

    def test_mandatory_error_type_cannot_expose_arbitrary_exception_text(self):
        error = self.engine.MandatoryMiddlewareError("sensitive fixture error")
        self.assertEqual(str(error), "mandatory_middleware.callback_failed")

    def test_default_exhausted_error_preserves_original_exception(self):
        error = RuntimeError("synthetic validation failure")
        self.sync_transport.side_effect = error
        for module in (self.original, self.aux):
            with self.assertRaises(RuntimeError) as caught:
                self.call(module=module)
            self.assertIs(caught.exception, error)

    def test_plugin_sync_and_async_facades_use_governed_auxiliary_path(self):
        self.setup_maya()
        llm = self.plugin_llm.PluginLlm(plugin_id="synthetic-plugin")
        kwargs = dict(messages=self.messages, provider="openai", model="synthetic-model")
        with bind_request_identity("alice"):
            self.assertEqual(llm.complete(**kwargs).text, "synthetic result")
            self.assertEqual(asyncio.run(llm.acomplete(**kwargs)).text, "synthetic result")
        self.assertEqual(self.audit.write.call_count, 2)

    def test_injected_plugin_callers_are_blocked_only_in_mandatory_mode(self):
        sync_caller, async_caller = Mock(), AsyncMock()
        llm = self.plugin_llm.PluginLlm(plugin_id="synthetic-plugin", sync_caller=sync_caller, async_caller=async_caller)
        kwargs = dict(messages=self.messages, provider_override=None, model_override=None, profile_override=None,
                      temperature=None, max_tokens=None, timeout=None)
        llm._invoke_sync(**kwargs)
        asyncio.run(llm._invoke_async(**kwargs))
        sync_caller.reset_mock()
        async_caller.reset_mock()
        self.install_gates()
        with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "unsupported_plugin_caller"):
            llm._invoke_sync(**kwargs)
        with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "unsupported_plugin_caller"):
            asyncio.run(llm._invoke_async(**kwargs))
        sync_caller.assert_not_called()
        async_caller.assert_not_called()

    def test_all_central_attempts_use_dispatchers_and_catches_stop_mandatory_errors(self):
        tree = ast.parse((self.target / "agent/auxiliary_client.py").read_text(encoding="utf-8"))
        names = {"call_llm", "async_call_llm", "_retry_same_provider_sync", "_retry_same_provider_async"}
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                        self.assertNotEqual(child.func.attr, "create", node.name)
                    if isinstance(child, ast.ExceptHandler) and child.name:
                        first = child.body[0]
                        self.assertIsInstance(first, ast.Expr)
                        self.assertIsInstance(first.value, ast.Call)
                        self.assertEqual(first.value.func.id, "_raise_if_mandatory_failure")

    def test_async_gate_failure_cannot_be_swallowed_or_report_success(self):
        async def deny(**kw):
            raise RuntimeError("synthetic policy failure")
        self.install_gates(deny)
        async def swallow(request, next_call, **kw):
            try:
                return await next_call(request)
            except Exception:
                return self.response
        self.manager._middleware["llm_execution"].append(swallow)
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.call(True)
        self.async_transport.assert_not_called()

    def test_async_next_call_is_single_use(self):
        async def twice(request, next_call, **kw):
            result = await next_call(request)
            try:
                await next_call(request)
            except Exception:
                pass
            return result
        self.install_gates(twice)
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.call(True)
        self.async_transport.assert_awaited_once()

    def test_async_result_validation_failure_withholds_result(self):
        async def invalid(request, next_call, **kw):
            await next_call(request)
            raise RuntimeError("synthetic result validation failure")
        self.install_gates(invalid)
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.call(True)
        self.async_transport.assert_awaited_once()

    def test_downstream_mandatory_failure_cannot_be_swallowed_sync_or_async(self):
        self.install_gates()
        for async_mode, transport in ((False, self.sync_transport), (True, self.async_transport)):
            transport.side_effect = self.engine.MandatoryMiddlewareError("mandatory_middleware.synthetic_stop")
            if async_mode:
                async def swallow(request, next_call, **kw):
                    try:
                        return await next_call(request)
                    except Exception:
                        return self.response
            else:
                def swallow(request, next_call, **kw):
                    try:
                        return next_call(request)
                    except Exception:
                        return self.response
            self.manager._middleware["llm_execution"] = [swallow, self.engine._mandatory_callbacks["llm_execution"]]
            with self.assertRaises(self.engine.MandatoryMiddlewareError):
                self.call(async_mode)
            transport.assert_called_once()

    def test_async_cancellation_propagates_without_retry(self):
        self.install_gates()
        self.async_transport.side_effect = asyncio.CancelledError()
        with self.assertRaises(asyncio.CancelledError):
            self.call(True)
        self.async_transport.assert_awaited_once()
        self.aux._try_configured_fallback_chain.assert_not_called()


if __name__ == "__main__":
    unittest.main()

"""Pinned native summary/transport helpers with real gates and inert SDKs."""

import ast
import hashlib
import re
import shutil
import subprocess
import sys
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from project_maya.config import config_from_mapping
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.governance import MayaGovernancePlugin, bind_request_identity
from tests.test_phase0_contracts import valid_config_mapping
from tests import test_hermes_final_result_governance_patch as result_tests
from tests import test_hermes_conversation_governance_patch as loop_tests


class TestHermesSummaryAttemptsPatch(unittest.TestCase):
    def setUp(self):
        self.host = result_tests.TestHermesFinalResultGovernancePatch()
        self.addCleanup(self.host.doCleanups)
        self.host.setUp()
        self.base = self.host.base
        self.target = self.host.target
        for name in ("chat_completion_helpers.py", "codex_runtime.py", "anthropic_adapter.py"):
            shutil.copyfile(loop_tests.FIXTURE / name, self.target / "agent" / name)
        for name in ("0007-provider-diagnostic-boundaries.patch", "0008-summary-and-single-transport-attempts.patch"):
            result = subprocess.run(
                ["git", "apply", "--whitespace=error", str(loop_tests.ROOT / "patches/hermes" / name)],
                cwd=self.target, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        self.engine = self.host.load("_attempt_middleware", self.target / "hermes_cli/middleware.py")
        patcher = patch.dict(sys.modules, {
            "hermes_cli.middleware": self.engine,
            "agent.auxiliary_client": SimpleNamespace(_fixed_temperature_for_model=lambda *args: None,
                                                       OMIT_TEMPERATURE=object()),
            "httpx": SimpleNamespace(ReadTimeout=type("ReadTimeout", (Exception,), {}),
                                     ConnectTimeout=type("ConnectTimeout", (Exception,), {}),
                                     PoolTimeout=type("PoolTimeout", (Exception,), {}),
                                     ConnectError=type("ConnectError", (Exception,), {}),
                                     RemoteProtocolError=type("RemoteProtocolError", (Exception,), {}),
                                     Timeout=lambda **kw: kw),
        })
        patcher.start()
        self.addCleanup(patcher.stop)
        self.scope = {
            "MandatoryMiddlewareError": self.engine.MandatoryMiddlewareError,
            "mandatory_middleware_enabled": self.engine.mandatory_middleware_enabled,
            "require_single_attempt_client": self.engine.require_single_attempt_client,
            "run_llm_execution_middleware": self.engine.run_llm_execution_middleware,
            "logger": Mock(), "re": re, "time": time, "threading": threading,
            "SimpleNamespace": SimpleNamespace, "env_int": lambda name, default: default,
            "_env_float": lambda name, default: default,
            "_is_openai_codex_backend": lambda agent: False,
            "env_float": lambda name, default: default, "is_local_endpoint": lambda value: False,
            "get_provider_request_timeout": lambda *args: None,
            "get_provider_stale_timeout": lambda *args: None,
            "estimate_request_context_tokens": lambda payload: 10,
            "PARTIAL_STREAM_STUB_ID": "synthetic-partial", "FINISH_REASON_LENGTH": "length",
        }
        self.chat = self.compile("chat_completion_helpers.py", {
            "handle_max_iterations", "_summary_call", "_summary_chat_call",
            "interruptible_streaming_api_call", "interruptible_api_call",
        })
        self.codex = self.compile("codex_runtime.py", {"run_codex_stream"})
        self.anthropic = self.compile("anthropic_adapter.py", {"create_anthropic_message"},
            sanitize_anthropic_kwargs=Mock(), _is_stream_unavailable_error=lambda error: True)
        mapping = valid_config_mapping()
        mapping["deployment"]["data_dir"] = str(self.target / "data")
        mapping["llm"].update(mode="customer_owned", provider="openai", model="test-model",
                               endpoint="https://api.openai.com/v1")
        self.audit = Mock()
        self.plugin = MayaGovernancePlugin(config_from_mapping(mapping),
            PolicyAuthorizationGateway((PolicyRule("model.egress", target="model:openai",
                                                   operation="infer", actor_id="alice"),)), self.audit)
        self.client = SimpleNamespace(max_retries=0, chat=SimpleNamespace(completions=SimpleNamespace(create=Mock())))
        self.agent = Mock()
        for name, value in {
            "provider": "openai", "model": "test-model", "base_url": "https://api.openai.com/v1",
            "_base_url_lower": "https://api.openai.com/v1", "api_mode": "chat_completions",
            "session_id": "synthetic-session", "max_iterations": 2, "max_tokens": None,
            "reasoning_config": None, "_cached_system_prompt": "synthetic system",
            "ephemeral_system_prompt": "", "prefill_messages": [],
            "providers_allowed": [], "providers_ignored": [], "providers_order": [],
            "provider_sort": None, "_interrupt_requested": False, "_stream_callback": None,
            "stream_delta_callback": None, "reasoning_callback": None, "log_prefix": "",
        }.items():
            setattr(self.agent, name, value)
        self.agent._should_sanitize_tool_calls.return_value = False
        self.agent._sanitize_api_messages.side_effect = lambda messages: messages
        self.agent._drop_thinking_only_and_merge_users.side_effect = lambda messages: messages
        self.agent._supports_reasoning_extra_body.return_value = False
        self.agent._is_openrouter_url.return_value = False
        self.agent._ensure_primary_openai_client.return_value = self.client
        self.agent._create_request_openai_client.return_value = self.client
        self.agent._has_stream_consumers.return_value = False
        self.agent._is_provider_stream_parse_error.return_value = False
        self.agent._stream_diag_init.return_value = {}
        self.transport = Mock()
        self.transport.normalize_response.side_effect = lambda response, **kw: SimpleNamespace(content=response)
        self.transport.build_kwargs.side_effect = lambda **kw: {"model": kw["model"], "messages": kw["messages"]}
        self.agent._get_transport.return_value = self.transport
        self.agent._build_api_kwargs.side_effect = lambda messages: {"model": self.agent.model, "messages": messages}

    def compile(self, filename, names, **extra):
        tree = ast.parse((self.target / "agent" / filename).read_text(encoding="utf-8"))
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
        self.assertEqual(len(nodes), len(names))
        nodes.insert(0, ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0))
        scope = dict(self.scope, **extra)
        exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), filename, "exec"), scope)
        return scope

    def install(self, model=None):
        for kind, callback in (("llm_execution", model or self.plugin.model_execution),
                               ("tool_execution", self.plugin.tool_execution),
                               ("tool_result", self.plugin.tool_result)):
            self.base.manager._middleware[kind] = [callback]
            self.engine.require_middleware(kind, callback)

    def summary(self):
        with patch("builtins.print"):
            return self.chat["handle_max_iterations"](self.agent, [{"role": "user", "content": "synthetic question"}], 2)

    def stream(self):
        return self.chat["interruptible_streaming_api_call"](self.agent, {"model": "test-model", "messages": []})

    def test_pinned_fixture_hashes(self):
        for name, digest in {
            "chat_completion_helpers.py": "ff17762913d3e38aefa57fa22b56048f99d09fc18d189ab6441bf9c69433a76c",
            "codex_runtime.py": "3878e102cd53dd7e4dd5d767ca5b1e0f0f2778e16e521f4e37a11a1826c1d357",
            "anthropic_adapter.py": "c7541f69e5dd8515c6b8cf4afd93e38e66d25fbab86eef2a6b32a2249fb2b054",
        }.items():
            self.assertEqual(hashlib.sha256((loop_tests.FIXTURE / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest(), digest)

    def test_native_summary_allow_is_audited_and_dispatched_once(self):
        self.install()
        self.client.chat.completions.create.return_value = "safe summary"
        with bind_request_identity("alice"):
            self.assertEqual(self.summary(), "safe summary")
        self.client.chat.completions.create.assert_called_once()
        self.assertEqual(self.audit.write.call_count, 1)

    def test_summary_missing_identity_or_denied_actor_never_dispatches(self):
        self.install()
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.summary()
        with bind_request_identity("mallory"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.summary()
        self.client.chat.completions.create.assert_not_called()

    def test_summary_audit_crash_never_dispatches_or_logs_raw_error(self):
        self.install()
        self.audit.write.side_effect = RuntimeError("synthetic-private-error")
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError) as caught:
            self.summary()
        self.assertNotIn("synthetic-private", str(caught.exception))
        self.client.chat.completions.create.assert_not_called()
        self.chat["logger"].warning.assert_not_called()

    def test_summary_policy_crash_never_dispatches(self):
        self.install()
        self.plugin.gateway = Mock()
        self.plugin.gateway.authorize.side_effect = RuntimeError("synthetic-private-policy-error")
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.summary()
        self.client.chat.completions.create.assert_not_called()

    def test_all_summary_api_modes_reauthorize_empty_response_retry(self):
        self.install()
        for mode in ("chat_completions", "codex_responses", "anthropic_messages"):
            with self.subTest(mode=mode):
                self.agent.api_mode = mode
                callback = (self.client.chat.completions.create if mode == "chat_completions" else
                            self.agent._run_codex_stream if mode == "codex_responses" else self.agent._anthropic_messages_create)
                callback.reset_mock()
                callback.side_effect = ["", "safe retry summary"]
                self.audit.reset_mock()
                with bind_request_identity("alice"):
                    self.assertEqual(self.summary(), "safe retry summary")
                self.assertEqual(callback.call_count, 2)
                self.assertEqual(self.audit.write.call_count, 2)

    def test_gate_removal_between_summary_attempts_blocks_second_call(self):
        self.install()
        def first(**kwargs):
            self.base.manager._middleware["llm_execution"].clear()
            return ""
        self.client.chat.completions.create.side_effect = first
        with bind_request_identity("alice"), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "gate_missing"):
            self.summary()
        self.client.chat.completions.create.assert_called_once()

    def test_changed_route_between_summary_attempts_is_denied(self):
        self.install()
        def first(**kwargs):
            self.agent.base_url = "https://unapproved.example/v1"
            return ""
        self.client.chat.completions.create.side_effect = first
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.summary()
        self.client.chat.completions.create.assert_called_once()

    def test_sdk_retry_configuration_is_blocked_before_summary_transport(self):
        self.install()
        for retries in (2, None, True):
            with self.subTest(retries=retries):
                self.client.max_retries = retries
                with bind_request_identity("alice"), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "sdk_retries_enabled"):
                    self.summary()
        self.client.chat.completions.create.assert_not_called()

    def test_summary_normal_mode_preserves_direct_call_without_gate(self):
        self.client.max_retries = 2
        self.client.chat.completions.create.return_value = "legacy summary"
        self.chat["run_llm_execution_middleware"] = Mock(side_effect=AssertionError("legacy bypasses new gate"))
        self.assertEqual(self.summary(), "legacy summary")
        self.client.chat.completions.create.assert_called_once()

    def test_mandatory_stream_has_one_attempt_not_native_inner_retries(self):
        self.install()
        self.client.chat.completions.create.side_effect = ConnectionError("synthetic connection drop")
        with self.assertRaises(ConnectionError):
            self.stream()
        self.client.chat.completions.create.assert_called_once()
        self.agent._close_request_openai_client.assert_called_once()

    def test_normal_stream_preserves_three_attempts(self):
        self.client.chat.completions.create.side_effect = ConnectionError("synthetic connection drop")
        with self.assertRaises(ConnectionError):
            self.stream()
        self.assertEqual(self.client.chat.completions.create.call_count, 3)

    def test_stream_sdk_retries_denied_without_transport_or_partial_success(self):
        self.install()
        self.client.max_retries = 2
        with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "sdk_retries_enabled"):
            self.stream()
        self.client.chat.completions.create.assert_not_called()

    def test_next_outer_stream_attempt_must_pass_live_gate_again(self):
        self.install()
        def first(**kwargs):
            self.base.manager._middleware["llm_execution"].clear()
            raise ConnectionError("synthetic drop")
        self.client.chat.completions.create.side_effect = first
        payload = {"model": "test-model", "messages": []}
        def execute(request):
            return self.chat["interruptible_streaming_api_call"](self.agent, request)
        context = dict(provider="openai", base_url=self.agent.base_url)
        with bind_request_identity("alice"):
            with self.assertRaises(ConnectionError):
                self.engine.run_llm_execution_middleware(payload, execute, **context)
            with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "gate_missing"):
                self.engine.run_llm_execution_middleware(payload, execute, **context)
        self.client.chat.completions.create.assert_called_once()

    def test_nonstreaming_sdk_retry_guard_prevents_transport(self):
        self.install()
        self.client.max_retries = 2
        with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "sdk_retries_enabled"):
            self.chat["interruptible_api_call"](self.agent, {"model": "test-model"})
        self.client.chat.completions.create.assert_not_called()

    def test_cancelled_stream_never_dispatches(self):
        self.install()
        self.agent._interrupt_requested = True
        with self.assertRaises(InterruptedError):
            self.stream()
        self.client.chat.completions.create.assert_not_called()

    def test_codex_mandatory_retry_disabled_and_normal_retry_retained(self):
        client = SimpleNamespace(max_retries=0, responses=SimpleNamespace(create=Mock(side_effect=ConnectionError("synthetic drop"))))
        with self.assertRaises(ConnectionError):
            self.codex["run_codex_stream"](self.agent, {"model": "test-model"}, client=client)
        self.assertEqual(client.responses.create.call_count, 2)
        client.responses.create.reset_mock()
        self.install()
        with self.assertRaises(ConnectionError):
            self.codex["run_codex_stream"](self.agent, {"model": "test-model"}, client=client)
        client.responses.create.assert_called_once()

    def test_anthropic_mandatory_inline_fallback_disabled(self):
        self.install()
        client = SimpleNamespace(max_retries=0, messages=SimpleNamespace(stream=Mock(side_effect=RuntimeError("stream unavailable")), create=Mock()))
        with self.assertRaisesRegex(RuntimeError, "stream unavailable"):
            self.anthropic["create_anthropic_message"](client, {"model": "test-model"})
        client.messages.stream.assert_called_once()
        client.messages.create.assert_not_called()

    def test_anthropic_normal_inline_fallback_retained(self):
        client = SimpleNamespace(max_retries=2, messages=SimpleNamespace(stream=Mock(side_effect=RuntimeError("stream unavailable")), create=Mock(return_value="legacy result")))
        self.assertEqual(self.anthropic["create_anthropic_message"](client, {"model": "test-model"}), "legacy result")
        client.messages.create.assert_called_once()

    def test_bedrock_unqualified_retry_transport_is_blocked_before_worker(self):
        self.install()
        self.agent.api_mode = "bedrock_converse"
        for name in ("interruptible_api_call", "interruptible_streaming_api_call"):
            with self.subTest(name=name), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "unsupported_transport"):
                self.chat[name](self.agent, {"model": "test-model"})


if __name__ == "__main__":
    unittest.main()

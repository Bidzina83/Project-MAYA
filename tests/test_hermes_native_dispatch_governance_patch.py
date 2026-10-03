"""Pinned dispatcher -> real registry -> native middleware -> Maya gateway."""

import asyncio
import hashlib
import importlib.util
import shutil
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from project_maya.config import config_from_mapping
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.governance import MayaGovernancePlugin, bind_request_identity
from tests.test_phase0_contracts import valid_config_mapping
from tests import test_hermes_tool_preflight_governance_patch as preflight_tests


class TestHermesNativeDispatchGovernancePatch(unittest.TestCase):
    def setUp(self):
        harness = preflight_tests.TestHermesToolPreflightGovernancePatch()
        self.addCleanup(harness.doCleanups)
        harness.setUp()
        self.harness = harness
        self.engine = harness.engine
        self.target = harness.target
        (self.target / "tools").mkdir()
        shutil.copyfile(preflight_tests.FIXTURE / "model_tools.py", self.target / "model_tools.py")
        shutil.copyfile(preflight_tests.FIXTURE / "tool_registry.py", self.target / "tools/registry.py")
        result = subprocess.run(
            ["git", "apply", "--whitespace=error", str(preflight_tests.ROOT / "patches/hermes/0005-native-tool-dispatch-denial-propagation.patch")],
            cwd=self.target, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        spec = importlib.util.spec_from_file_location("_native_registry_test", self.target / "tools/registry.py")
        self.registry_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.registry_module)
        self.registry = self.registry_module.ToolRegistry()
        self.registry_module.logger = Mock()
        self.bridge = SimpleNamespace(is_bridge_tool=Mock(return_value=False))
        self.plugins = harness.modules["hermes_cli.plugins"]
        self.plugins.has_hook = Mock(return_value=False)
        self.reset = Mock()
        modules = {
            "tools": SimpleNamespace(tool_search=self.bridge),
            "tools.approval": SimpleNamespace(
                set_current_observability_context=Mock(return_value=object()),
                reset_current_observability_context=self.reset,
            ),
            "acp_adapter.edit_approval": SimpleNamespace(maybe_require_edit_approval=Mock(return_value=None)),
        }
        patcher = patch.dict(sys.modules, modules)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("socket.create_connection", side_effect=AssertionError("network forbidden"))
        patcher.start()
        self.addCleanup(patcher.stop)
        # Complete pinned function; only discovery/environment dependencies are inert.
        self.dispatch = harness.compile_functions(
            "../model_tools.py", {"handle_function_call"},
            registry=self.registry, coerce_tool_args=lambda name, args: args,
            validate_mandatory_middleware=self.engine.validate_mandatory_middleware,
            _AGENT_LOOP_TOOLS=set(), _READ_SEARCH_TOOLS={"read_file"},
            _emit_post_tool_call_hook=Mock(), _sanitize_tool_error=lambda value: value,
            _tool_result_observer_fields=lambda value: ("success", "", ""),
            get_tool_definitions=Mock(return_value=[]),
        )
        self.handler = Mock(return_value='{"result":"synthetic business record"}')
        self.registry.register("read_file", "test", {"name": "read_file"}, self.handler)
        mapping = valid_config_mapping()
        mapping["deployment"]["data_dir"] = str(self.target / "data")
        self.audit = Mock()
        self.plugin = MayaGovernancePlugin(
            config_from_mapping(mapping),
            PolicyAuthorizationGateway((PolicyRule("file.read", operation="read", actor_id="alice"),)),
            self.audit,
        )

    def install(self, callback=None):
        self.harness.install_gates(callback or self.plugin.tool_execution)

    def call(self, **kwargs):
        return self.dispatch["handle_function_call"]("read_file", {"path": "report.txt"}, **kwargs)

    def test_source_hashes(self):
        for name, digest in {
            "model_tools.py": "c0d96e11a5388dc66a4740859b1f9bc6efabe391c475de7a2a5fa957464faf52",
            "tool_registry.py": "1fff28948e5714763c26279f40a0188b657243942f8ad8e157a672c453515aef",
        }.items():
            self.assertEqual(hashlib.sha256((preflight_tests.FIXTURE / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest(), digest)

    def test_real_maya_denial_never_reaches_registered_handler(self):
        self.install()
        with bind_request_identity("mallory"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.call()
        self.handler.assert_not_called()
        self.dispatch["logger"].exception.assert_not_called()
        self.dispatch["_emit_post_tool_call_hook"].assert_not_called()
        self.reset.assert_called_once()

    def test_real_maya_allow_reaches_registry_once_with_canonical_path(self):
        self.install()
        with bind_request_identity("alice"):
            self.assertEqual(self.call(), self.handler.return_value)
        self.handler.assert_called_once()
        self.assertEqual(self.handler.call_args.args[0]["path"], (self.target / "data/documents/report.txt").resolve().as_posix())
        self.assertEqual(self.audit.write.call_count, 2)

    def test_missing_or_removed_gate_stops_before_argument_preparation(self):
        self.engine.enable_mandatory_middleware()
        prepare = Mock()
        self.dispatch["coerce_tool_args"] = prepare
        with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "gate_missing"):
            self.call()
        prepare.assert_not_called()
        self.handler.assert_not_called()

    def test_removed_gate_stops_before_registered_tool(self):
        self.install()
        self.harness.manager._middleware["tool_execution"].clear()
        with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "gate_missing"):
            self.call()
        self.handler.assert_not_called()

    def test_missing_trusted_identity_stops_real_dispatch(self):
        self.install()
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.call()
        self.handler.assert_not_called()

    def test_registry_preserves_typed_handler_failure_without_logging(self):
        self.install(lambda **kw: kw["next_call"](kw["args"]))
        error = self.engine.MandatoryMiddlewareError()
        error.args = ("synthetic-sensitive-error",)
        self.handler.side_effect = error
        with self.assertRaises(self.engine.MandatoryMiddlewareError) as caught:
            self.call()
        self.assertEqual(str(caught.exception), "mandatory_middleware.callback_failed")
        self.registry_module.logger.exception.assert_not_called()
        self.dispatch["logger"].exception.assert_not_called()

    def test_registry_async_typed_failure_propagates(self):
        self.install(lambda **kw: kw["next_call"](kw["args"]))
        async def handler(args, **kwargs):
            raise self.engine.MandatoryMiddlewareError("gate_missing")
        self.registry.register("async_test", "test", {}, handler, is_async=True)
        patcher = patch.dict(sys.modules, {"model_tools": SimpleNamespace(_run_async=asyncio.run)})
        with patcher, self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "gate_missing"):
            self.registry.dispatch("async_test", {})
        self.registry_module.logger.exception.assert_not_called()

    def test_policy_crash_is_fixed_and_stops_dispatch(self):
        self.install()
        self.plugin.gateway = Mock()
        self.plugin.gateway.authorize.side_effect = RuntimeError("synthetic sensitive policy text")
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.call()
        self.handler.assert_not_called()
        self.dispatch["logger"].exception.assert_not_called()

    def test_audit_crash_stops_before_side_effect(self):
        self.install()
        self.audit.write.side_effect = RuntimeError("synthetic sensitive audit text")
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.call()
        self.handler.assert_not_called()

    def test_postexecution_gate_failure_withholds_result_without_reexecution(self):
        def callback(**kw):
            kw["next_call"](kw["args"])
            raise RuntimeError("synthetic postprocessing failure")
        self.install(callback)
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.call()
        self.handler.assert_called_once()
        self.dispatch["_emit_post_tool_call_hook"].assert_not_called()

    def test_bridge_is_blocked_before_catalog_access_in_mandatory_mode(self):
        self.install()
        self.bridge.is_bridge_tool.return_value = True
        with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "gate_bypassed"):
            self.call()
        self.dispatch["get_tool_definitions"].assert_not_called()
        self.handler.assert_not_called()

    def test_request_middleware_typed_denial_is_not_suppressed(self):
        self.install()
        with patch.object(self.engine, "apply_tool_request_middleware", side_effect=self.engine.MandatoryMiddlewareError()):
            with self.assertRaises(self.engine.MandatoryMiddlewareError):
                self.call()
        self.handler.assert_not_called()

    def test_pre_tool_hook_typed_failure_stops_before_side_effect(self):
        self.install()
        self.plugins.get_pre_tool_call_block_message.side_effect = self.engine.MandatoryMiddlewareError()
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.call()
        self.handler.assert_not_called()

    def test_result_transform_typed_failure_is_fatal_not_a_result(self):
        self.install()
        self.plugins.has_hook.return_value = True
        self.plugins.invoke_hook.side_effect = self.engine.MandatoryMiddlewareError()
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.call()
        self.handler.assert_called_once()
        self.dispatch["logger"].exception.assert_not_called()

    def test_maya_withholds_secret_bearing_tool_result(self):
        self.install()
        self.handler.return_value = '{"api_key":"synthetic-not-a-real-key"}'
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.call()
        self.handler.assert_called_once()
        self.assertNotIn("synthetic-not-a-real-key", "".join(call.args[0].to_json() for call in self.audit.write.call_args_list))
        self.dispatch["_emit_post_tool_call_hook"].assert_not_called()

    def test_normal_mode_success_and_ordinary_error_still_use_registry(self):
        self.assertEqual(self.call(), self.handler.return_value)
        self.handler.side_effect = RuntimeError("synthetic ordinary failure")
        self.assertIn("synthetic ordinary failure", self.call())
        self.registry_module.logger.exception.assert_called_once()

    def test_serial_batch_uses_real_dispatcher_and_stops_after_denial(self):
        self.install()
        self.harness.tools["_ra"] = lambda: SimpleNamespace(handle_function_call=self.dispatch["handle_function_call"])
        agent = self.harness.agent()
        call = SimpleNamespace(id="call", function=SimpleNamespace(name="read_file", arguments='{"path":"report.txt"}'))
        messages = []
        with bind_request_identity("mallory"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.harness.tools["execute_tool_calls_sequential"](agent, SimpleNamespace(tool_calls=[call, call]), messages, "task")
        self.assertEqual(messages, [])
        self.handler.assert_not_called()


if __name__ == "__main__":
    unittest.main()

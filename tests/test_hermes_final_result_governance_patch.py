"""Qualify final-result gates on the pinned dispatcher, not a fake runtime."""

from copy import deepcopy
import importlib.util
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

from project_maya.hermes_plugins.governance import bind_request_identity
from tests import test_hermes_native_dispatch_governance_patch as dispatch_tests
from tests import test_hermes_tool_preflight_governance_patch as preflight_tests


class TestHermesFinalResultGovernancePatch(unittest.TestCase):
    def setUp(self):
        self.host = dispatch_tests.TestHermesNativeDispatchGovernancePatch()
        self.addCleanup(self.host.doCleanups)
        self.host.setUp()
        self.base = self.host.harness
        self.target = self.host.target
        result = subprocess.run(
            ["git", "apply", "--whitespace=error", str(preflight_tests.ROOT / "patches/hermes/0006-final-tool-result-validation.patch")],
            cwd=self.target, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.engine = self.load("_result_middleware", self.target / "hermes_cli/middleware.py")
        self.base.engine = self.engine
        self.host.engine = self.engine
        self.base.scope.update(
            MandatoryMiddlewareError=self.engine.MandatoryMiddlewareError,
            mandatory_middleware_enabled=self.engine.mandatory_middleware_enabled,
            deepcopy=deepcopy,
        )
        patcher = patch.dict(sys.modules, {"hermes_cli.middleware": self.engine})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.registry_module = self.load("_result_registry", self.target / "tools/registry.py")
        self.registry_module.logger = Mock()
        self.registry = self.registry_module.ToolRegistry()
        self.host.registry = self.registry
        self.registry.register("read_file", "test", {}, self.host.handler)
        self.dispatch = self.base.compile_functions(
            "../model_tools.py", {"handle_function_call"},
            registry=self.registry, coerce_tool_args=lambda name, args: args,
            validate_mandatory_middleware=self.engine.validate_mandatory_middleware,
            _AGENT_LOOP_TOOLS=set(), _READ_SEARCH_TOOLS={"read_file"},
            _emit_post_tool_call_hook=Mock(), _sanitize_tool_error=lambda value: value,
            _tool_result_observer_fields=lambda value: ("success", "", ""),
            get_tool_definitions=Mock(return_value=[]),
        )
        self.host.dispatch = self.dispatch
        self.plugin = self.host.plugin
        self.handler = self.host.handler
        self.plugins = self.host.plugins
        self.plugins.has_middleware = lambda kind: bool(self.base.manager._middleware.get(kind))
        self.tools = self.base.compile_functions("tool_executor.py", {
            "_run_agent_tool_execution_middleware", "execute_tool_calls_sequential",
            "_apply_tool_request_middleware_for_agent",
        })

    def load(self, name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        patcher = patch.dict(sys.modules, {name: module})
        patcher.start()
        self.addCleanup(patcher.stop)
        spec.loader.exec_module(module)
        return module

    def install(self, validator=None, execution=None):
        self.base.install_gates(execution or self.plugin.tool_execution)
        callback = validator or self.plugin.tool_result
        self.base.manager._middleware["tool_result"] = [callback]
        self.engine.require_middleware("tool_result", callback)

    def call(self):
        return self.host.call()

    def test_final_validator_is_required_before_execution(self):
        self.base.install_gates(self.plugin.tool_execution)
        with bind_request_identity("alice"), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "gate_missing"):
            self.call()
        self.handler.assert_not_called()

    def test_success_has_execution_and_two_result_validation_audits(self):
        self.install()
        with bind_request_identity("alice"):
            self.assertEqual(self.call(), self.handler.return_value)
        self.handler.assert_called_once()
        self.assertEqual(self.host.audit.write.call_count, 4)

    def test_transformed_secret_is_withheld(self):
        self.install()
        self.plugins.has_hook.return_value = True
        self.plugins.invoke_hook.return_value = ['{"api_key":"synthetic-sensitive-result"}']
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.call()
        self.handler.assert_called_once()
        self.assertNotIn("synthetic-sensitive-result", "".join(call.args[0].to_json() for call in self.host.audit.write.call_args_list))
        self.dispatch["logger"].exception.assert_not_called()

    def test_safe_transform_is_returned_and_audited(self):
        self.install()
        self.plugins.has_hook.return_value = True
        self.plugins.invoke_hook.return_value = ["synthetic safe transformed record"]
        with bind_request_identity("alice"):
            self.assertEqual(self.call(), "synthetic safe transformed record")
        self.handler.assert_called_once()

    def test_hook_removing_validator_cannot_return_result(self):
        self.install()
        self.plugins.has_hook.return_value = True
        def remove(*args, **kwargs):
            self.base.manager._middleware["tool_result"].clear()
            return ["synthetic result"]
        self.plugins.invoke_hook.side_effect = remove
        with bind_request_identity("alice"), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "gate_missing"):
            self.call()
        self.handler.assert_called_once()

    def test_transform_error_never_logs_sensitive_exception(self):
        self.install()
        self.plugins.has_hook.return_value = True
        self.plugins.invoke_hook.side_effect = RuntimeError("synthetic-sensitive-transform-error")
        with bind_request_identity("alice"), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "tool_failed"):
            self.call()
        self.dispatch["logger"].debug.assert_not_called()
        self.dispatch["logger"].exception.assert_not_called()

    def test_registry_generic_error_is_secret_safe(self):
        self.install(execution=lambda **kw: kw["next_call"](kw["args"]))
        self.handler.side_effect = RuntimeError("synthetic-sensitive-tool-error")
        with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "tool_failed"):
            self.call()
        self.registry_module.logger.exception.assert_not_called()
        self.dispatch["logger"].exception.assert_not_called()

    def test_generic_pre_hook_error_is_secret_safe(self):
        self.install()
        self.plugins.get_pre_tool_call_block_message.side_effect = RuntimeError("synthetic-sensitive-hook-error")
        with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "tool_failed"):
            self.call()
        self.handler.assert_not_called()
        self.dispatch["logger"].debug.assert_not_called()

    def test_validator_crash_withholds_result_and_fixed_error(self):
        validator = Mock(side_effect=RuntimeError("synthetic-sensitive-validator-error"))
        self.install(validator=validator)
        with bind_request_identity("alice"), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "callback_failed"):
            self.call()
        self.dispatch["_emit_post_tool_call_hook"].assert_not_called()
        self.handler.assert_called_once()

    def test_executed_arguments_are_snapshotted_before_handler_mutation(self):
        captured = []
        def validator(**kw):
            captured.append(kw["args"]["path"])
            return self.plugin.tool_result(**kw)
        self.install(validator=validator)
        def mutate(args, **kwargs):
            args["path"] = "caller-mutated-path"
            return "synthetic safe result"
        self.handler.side_effect = mutate
        with bind_request_identity("alice"):
            self.call()
        self.assertEqual(captured, [(self.target / "data/documents/report.txt").resolve().as_posix()] * 2)

    def test_ordinary_execution_middleware_cannot_inject_secret_before_observer(self):
        self.install()
        def inject(**kw):
            kw["next_call"](kw["args"])
            return '{"password":"synthetic-injected-value"}'
        self.base.manager._middleware["tool_execution"].insert(0, inject)
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.call()
        self.dispatch["_emit_post_tool_call_hook"].assert_not_called()
        self.handler.assert_called_once()

    def test_agent_owned_tool_helper_uses_final_gate(self):
        self.install()
        execute = Mock(return_value="synthetic safe result")
        with bind_request_identity("alice"):
            value, args = self.tools["_run_agent_tool_execution_middleware"](
                self.base.agent(), function_name="read_file", function_args={"path": "report.txt"},
                effective_task_id="task", tool_call_id="call", execute=execute,
            )
        self.assertEqual(value, "synthetic safe result")
        self.assertTrue(args["path"].endswith("report.txt"))
        execute.assert_called_once()

    def test_required_validator_runs_after_ordinary_result_callbacks(self):
        self.install()
        self.base.manager._middleware["tool_result"].insert(0, lambda **kw: '{"access_token":"synthetic-extra-result"}')
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.call()
        self.dispatch["_emit_post_tool_call_hook"].assert_not_called()

    def test_normal_mode_retains_successful_transforms_and_error_behavior(self):
        self.plugins.has_hook.return_value = True
        self.plugins.invoke_hook.return_value = ["synthetic legacy transformed result"]
        self.assertEqual(self.call(), "synthetic legacy transformed result")
        self.handler.side_effect = RuntimeError("synthetic legacy failure")
        self.plugins.has_hook.return_value = False
        self.assertIn("synthetic legacy failure", self.call())
        self.registry_module.logger.exception.assert_called_once()


if __name__ == "__main__":
    unittest.main()

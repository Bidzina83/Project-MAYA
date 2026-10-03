"""Exercise pinned diagnostic call sites; not full-loop qualification."""

import ast
import copy
import subprocess
import unittest
from unittest.mock import Mock

from tests import test_hermes_conversation_governance_patch as loop_tests
from tests import test_hermes_final_result_governance_patch as result_tests


class TestHermesProviderDiagnosticsPatch(unittest.TestCase):
    def setUp(self):
        self.host = loop_tests.TestHermesConversationGovernancePatch()
        self.addCleanup(self.host.doCleanups)
        self.host.setUp()
        result = subprocess.run(
            ["git", "apply", "--whitespace=error", str(loop_tests.ROOT / "patches/hermes/0007-provider-diagnostic-boundaries.patch")],
            cwd=self.host.target, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.tree = ast.parse((self.host.target / "agent/conversation_loop.py").read_text(encoding="utf-8"))
        self.enabled = False
        self.agent = Mock()
        self.scope = {
            "mandatory_middleware_enabled": lambda: self.enabled,
            "MandatoryMiddlewareError": self.host.middleware.MandatoryMiddlewareError,
            "agent": self.agent,
        }
        helpers = [node for node in self.tree.body if isinstance(node, ast.FunctionDef)
                   and node.name in {"_provider_error_summary", "_report_provider_error", "_dump_provider_error"}]
        self.assertEqual(len(helpers), 3)
        exec(compile(ast.Module(body=helpers, type_ignores=[]), "native-diagnostic-helpers", "exec"), self.scope)

    def statements(self, body, **values):
        self.scope.update(values)
        tree = ast.fix_missing_locations(ast.Module(body=copy.deepcopy(body), type_ignores=[]))
        exec(compile(tree, "native-diagnostic-call-sites", "exec"), self.scope)

    def test_summary_does_not_format_error_or_call_legacy_sanitizer(self):
        self.enabled = True
        error = Mock()
        error.__str__ = Mock(side_effect=AssertionError("must not format provider error"))
        self.assertEqual(self.scope["_provider_error_summary"](self.agent, error), "model.provider_error")
        error.__str__.assert_not_called()
        self.agent._summarize_api_error.assert_not_called()

    def test_actual_summary_assignments_use_fixed_diagnostics(self):
        self.enabled = True
        assignments = [node for node in ast.walk(self.tree) if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id in
                               {"_error_summary", "_nonretryable_summary", "_final_summary"}
                               for target in node.targets)]
        self.assertEqual(len(assignments), 3)
        self.statements(assignments, api_error=RuntimeError("synthetic-private-provider-body"))
        for name in ("_error_summary", "_nonretryable_summary", "_final_summary"):
            self.assertEqual(self.scope[name], "model.provider_error")
        self.agent._summarize_api_error.assert_not_called()

    def test_observer_receives_no_request_body_or_exception_text(self):
        self.enabled = True
        fields = dict(api_kwargs={"messages": ["synthetic-private-prompt"], "api_key": "synthetic-private-key"},
                      error_type="PrivateProviderClass", error_message="synthetic-private-provider-body",
                      status_code=401, retry_count=1, max_retries=3, retryable=False, reason="auth")
        self.scope["_report_provider_error"](self.agent, **fields)
        delivered = self.agent._invoke_api_request_error_hook.call_args.kwargs
        self.assertEqual(delivered["api_kwargs"], {})
        self.assertEqual(delivered["error_message"], "model.provider_error")
        self.assertEqual(delivered["error_type"], "ProviderError")
        self.assertEqual(delivered["status_code"], 401)
        self.assertNotIn("synthetic-private", repr(delivered))
        self.assertEqual(fields["api_kwargs"]["messages"], ["synthetic-private-prompt"])

    def test_observer_status_is_bounded(self):
        self.enabled = True
        for status in (True, 999, "synthetic-private-status", None):
            self.scope["_report_provider_error"](self.agent, status_code=status)
            self.assertIsNone(self.agent._invoke_api_request_error_hook.call_args.kwargs["status_code"])

    def test_actual_retry_diagnostic_block_does_not_publish_route_or_body(self):
        self.enabled = True
        handler = next(node for node in ast.walk(self.tree)
                       if isinstance(node, ast.ExceptHandler) and node.name == "api_error")
        start = next(index for index, node in enumerate(handler.body)
                     if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name)
                         and target.id == "error_type" for target in node.targets))
        end = next(index for index in range(start, len(handler.body))
                   if isinstance(handler.body[index], ast.Expr)
                   and "Elapsed:" in ast.unparse(handler.body[index]))
        self.agent.provider = self.agent.model = self.agent.base_url = "synthetic-private-route"
        self.agent._client_log_context.side_effect = AssertionError("unsafe diagnostic context")
        error = RuntimeError("synthetic-private-error")
        error.body = {"api_key": "synthetic-private-body"}
        logger = Mock()
        self.statements(handler.body[start:end + 1], api_error=error, logger=logger,
                        retry_count=1, max_retries=3, status_code=401,
                        elapsed_time=0.1, api_messages=[], approx_tokens=10)
        delivered = repr(logger.mock_calls) + repr(self.agent._buffer_vprint.mock_calls)
        self.assertNotIn("synthetic-private", delivered)
        self.assertIn("model.provider_error", delivered)
        self.agent._client_log_context.assert_not_called()

    def test_both_native_debug_dump_sites_are_suppressed(self):
        self.enabled = True
        sites = [node for node in ast.walk(self.tree) if isinstance(node, ast.Expr)
                 and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
                 and node.value.func.id == "_dump_provider_error"]
        self.assertEqual(len(sites), 2)
        self.statements(sites, api_kwargs={"messages": ["synthetic-private-prompt"]},
                        api_error=RuntimeError("synthetic-private-provider-body"))
        self.agent._dump_api_request_debug.assert_not_called()

    def test_normal_mode_keeps_legacy_diagnostic_arguments(self):
        error = RuntimeError("synthetic-private-provider-body")
        self.agent._summarize_api_error.return_value = "legacy summary"
        self.assertEqual(self.scope["_provider_error_summary"](self.agent, error), "legacy summary")
        self.agent._summarize_api_error.assert_called_once_with(error)
        fields = dict(api_kwargs={"messages": ["synthetic-private-prompt"]}, error_message=str(error))
        self.scope["_report_provider_error"](self.agent, **fields)
        self.agent._invoke_api_request_error_hook.assert_called_once_with(**fields)
        self.scope["_dump_provider_error"](self.agent, fields["api_kwargs"], reason="test", error=error)
        self.agent._dump_api_request_debug.assert_called_once_with(fields["api_kwargs"], reason="test", error=error)

    def test_unexpected_outer_failure_stops_before_logs_or_history(self):
        self.enabled = True
        handlers = [node for node in ast.walk(self.tree) if isinstance(node, ast.ExceptHandler)
                    and node.name == "e" and isinstance(node.type, ast.Name) and node.type.id == "Exception"
                    and node.body and isinstance(node.body[0], ast.If)
                    and ast.unparse(node.body[0].test) == "mandatory_middleware_enabled()"]
        self.assertEqual(len(handlers), 1)
        with self.assertRaisesRegex(self.host.middleware.MandatoryMiddlewareError, "callback_failed") as caught:
            self.statements([handlers[0].body[0]], e=RuntimeError("synthetic-private-error"))
        self.assertTrue(caught.exception.__suppress_context__)
        self.assertNotIn("synthetic-private", str(caught.exception))

    def test_classifier_and_retry_activation_calls_are_unchanged(self):
        original = ast.parse((loop_tests.FIXTURE / "conversation_loop.py").read_text(encoding="utf-8"))
        names = {"classify_api_error", "_recover_with_credential_pool", "_try_activate_fallback"}
        def calls(tree):
            return [ast.dump(node) for node in ast.walk(tree) if isinstance(node, ast.Call)
                    and ((isinstance(node.func, ast.Name) and node.func.id in names)
                         or (isinstance(node.func, ast.Attribute) and node.func.attr in names))]
        self.assertEqual(calls(self.tree), calls(original))

    def test_patch_applies_after_complete_six_patch_series(self):
        host = result_tests.TestHermesFinalResultGovernancePatch()
        self.addCleanup(host.doCleanups)
        host.setUp()
        result = subprocess.run(
            ["git", "apply", "--whitespace=error", str(loop_tests.ROOT / "patches/hermes/0007-provider-diagnostic-boundaries.patch")],
            cwd=host.target, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        compile((host.target / "agent/conversation_loop.py").read_text(encoding="utf-8"),
                "complete-patched-conversation-loop", "exec")


if __name__ == "__main__":
    unittest.main()

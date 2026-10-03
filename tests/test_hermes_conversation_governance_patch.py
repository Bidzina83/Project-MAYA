"""Test native loop exception dispatch; not a full conversation-loop harness."""

import ast
import copy
import hashlib
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/hermes_middleware"


class TestHermesConversationGovernancePatch(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.target = Path(temporary.name)
        for directory, names in (
            ("hermes_cli", ("middleware.py",)),
            ("agent", ("auxiliary_client.py", "plugin_llm.py", "conversation_loop.py")),
        ):
            destination = self.target / directory
            destination.mkdir()
            for name in names:
                shutil.copyfile(FIXTURE / name, destination / name)
        for name in (
            "0001-opt-in-mandatory-middleware.patch",
            "0002-governed-auxiliary-inference.patch",
            "0003-stop-main-loop-on-governance-failure.patch",
        ):
            result = subprocess.run(
                ["git", "apply", "--whitespace=error", str(ROOT / "patches/hermes" / name)],
                cwd=self.target, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        spec = importlib.util.spec_from_file_location(
            "_loop_test_middleware", self.target / "hermes_cli/middleware.py",
        )
        self.middleware = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.middleware
        self.addCleanup(sys.modules.pop, spec.name, None)
        spec.loader.exec_module(self.middleware)
        self.tree = ast.parse((self.target / "agent/conversation_loop.py").read_text(encoding="utf-8"))
        self.function = next(node for node in self.tree.body
                             if isinstance(node, ast.FunctionDef) and node.name == "run_conversation")
        self.boundaries = {}
        for node in ast.walk(self.function):
            if not isinstance(node, ast.Try):
                continue
            generic = next((handler for handler in node.handlers
                            if isinstance(handler.type, ast.Name) and handler.type.id == "Exception"), None)
            mandatory = any(isinstance(handler.type, ast.Name)
                            and handler.type.id == "MandatoryMiddlewareError" for handler in node.handlers)
            if generic and generic.name in ("api_error", "e") and mandatory:
                self.boundaries[generic.name] = node

    def run_handlers(self, boundary, error):
        # Compile the exact patched handler sequence. Unrelated original recovery
        # bodies are probes: they must never run for a mandatory denial.
        original = self.boundaries[boundary]
        handlers = copy.deepcopy(original.handlers)
        for handler in handlers:
            if not isinstance(handler.type, ast.Name) or handler.type.id != "MandatoryMiddlewareError":
                handler.body = ast.parse("recovery()\nbreak").body
        attempt = ast.Try(
            body=ast.parse("raise error").body, handlers=handlers, orelse=[], finalbody=[],
        )
        tree = ast.Module(body=[ast.While(test=ast.Constant(True), body=[attempt], orelse=[])], type_ignores=[])
        recovery = Mock()
        scope = {"error": error, "recovery": recovery,
                 "MandatoryMiddlewareError": self.middleware.MandatoryMiddlewareError}
        exec(compile(ast.fix_missing_locations(tree), "native-loop-handlers", "exec"), scope)
        return recovery

    def test_fixture_provenance(self):
        contents = (FIXTURE / "conversation_loop.py").read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(contents).hexdigest(),
                         "b32a7c2ef5f0f607488a92e6e513d267bd6f49f9a2564c1301c2e5dfea7ba4e8")

    def test_retry_handler_stops_every_mandatory_failure(self):
        for code in ("gate_missing", "callback_failed", "gate_bypassed", "binding_replaced",
                     "auxiliary_failed", "route_ambiguous"):
            with self.subTest(code=code):
                error = self.middleware.MandatoryMiddlewareError(code)
                with self.assertRaises(self.middleware.MandatoryMiddlewareError) as caught:
                    self.run_handlers("api_error", error)
                self.assertEqual(str(caught.exception), "mandatory_middleware." + code)
                self.assertTrue(caught.exception.__suppress_context__)

    def test_outer_handler_stops_tool_or_model_denial(self):
        error = self.middleware.MandatoryMiddlewareError("gate_missing")
        with self.assertRaises(self.middleware.MandatoryMiddlewareError):
            self.run_handlers("e", error)

    def test_tampered_exception_text_is_not_exposed(self):
        for boundary in ("api_error", "e"):
            with self.subTest(boundary=boundary):
                error = self.middleware.MandatoryMiddlewareError()
                error.args = ("synthetic-sensitive-provider-error",)
                with self.assertRaises(self.middleware.MandatoryMiddlewareError) as caught:
                    self.run_handlers(boundary, error)
                self.assertEqual(str(caught.exception), "mandatory_middleware.callback_failed")

    def test_ordinary_provider_errors_still_enter_existing_recovery(self):
        for boundary in ("api_error", "e"):
            with self.subTest(boundary=boundary):
                self.run_handlers(boundary, RuntimeError("synthetic transport failure")).assert_called_once()

    def test_interrupt_handling_remains_before_mandatory_handler(self):
        handlers = self.boundaries["api_error"].handlers
        self.assertEqual([handler.type.id for handler in handlers],
                         ["InterruptedError", "MandatoryMiddlewareError", "Exception"])

    def test_only_two_stop_handlers_and_import_change(self):
        original = ast.parse((FIXTURE / "conversation_loop.py").read_text(encoding="utf-8"))
        candidate = copy.deepcopy(self.tree)
        candidate.body = [node for node in candidate.body if not (
            isinstance(node, ast.ImportFrom) and node.module == "hermes_cli.middleware"
            and [alias.name for alias in node.names] == ["MandatoryMiddlewareError"]
        )]
        removed = 0
        for node in ast.walk(candidate):
            if isinstance(node, ast.Try):
                before = len(node.handlers)
                node.handlers = [handler for handler in node.handlers if not (
                    isinstance(handler.type, ast.Name) and handler.type.id == "MandatoryMiddlewareError"
                )]
                removed += before - len(node.handlers)
        self.assertEqual(removed, 2)
        self.assertEqual(ast.dump(candidate), ast.dump(original))


if __name__ == "__main__":
    unittest.main()

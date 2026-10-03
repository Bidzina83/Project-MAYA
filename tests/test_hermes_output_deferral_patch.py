"""Pinned native early-publication boundaries, not final-output qualification."""

import ast
import hashlib
import re
import shutil
import subprocess
import sys
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tests import test_hermes_conversation_governance_patch as loop_tests
from tests import test_hermes_summary_attempts_patch as attempt_tests


class TestHermesOutputDeferralPatch(unittest.TestCase):
    def setUp(self):
        self.host = attempt_tests.TestHermesSummaryAttemptsPatch()
        self.addCleanup(self.host.doCleanups)
        self.host.setUp()
        self.target = self.host.target
        self.engine = self.host.engine
        shutil.copyfile(loop_tests.FIXTURE / "run_agent.py", self.target / "run_agent.py")
        applied = subprocess.run(
            ["git", "apply", "--whitespace=error", str(loop_tests.ROOT / "patches/hermes/0009-defer-early-response-publication.patch")],
            cwd=self.target, capture_output=True, text=True, check=False,
        )
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.tree = ast.parse((self.target / "run_agent.py").read_text(encoding="utf-8"))
        self.loop = ast.parse((self.target / "agent/conversation_loop.py").read_text(encoding="utf-8"))
        agent_class = next(node for node in self.tree.body if isinstance(node, ast.ClassDef) and node.name == "AIAgent")
        names = {
            "_reset_stream_delivery_tracking", "_fire_stream_delta", "_fire_reasoning_delta",
            "_emit_interim_assistant_message", "_fire_tool_gen_started", "_record_streamed_assistant_text",
            "_normalize_interim_visible_text", "_interim_content_was_streamed",
        }
        methods = [node for node in agent_class.body if isinstance(node, ast.FunctionDef) and node.name in names]
        self.assertEqual(len(methods), len(names))
        isolated = ast.ClassDef(name="NativeDelivery", bases=[], keywords=[], body=methods, decorator_list=[])
        scope = {"re": re, "logger": Mock(), "sanitize_context": lambda text: text}
        module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), isolated], type_ignores=[])
        exec(compile(ast.fix_missing_locations(module), "native_delivery", "exec"), scope)
        self.agent = scope["NativeDelivery"]()
        self.scope = scope
        for name in ("stream_delta_callback", "_stream_callback", "reasoning_callback", "interim_assistant_callback", "tool_gen_callback"):
            setattr(self.agent, name, Mock())
        self.agent._strip_think_blocks = lambda text: text
        self.agent._stream_think_scrubber = Mock()
        self.agent._stream_think_scrubber.feed.side_effect = lambda text: text
        self.agent._stream_think_scrubber.flush.return_value = "private-think-tail"
        self.agent._stream_context_scrubber = Mock()
        self.agent._stream_context_scrubber.feed.side_effect = lambda text: text
        self.agent._stream_context_scrubber.flush.return_value = "private-context-tail"
        self.agent._current_streamed_assistant_text = ""

    def mandatory(self):
        self.host.install()

    def assert_no_delivery(self):
        for name in ("stream_delta_callback", "_stream_callback", "reasoning_callback", "interim_assistant_callback", "tool_gen_callback"):
            getattr(self.agent, name).assert_not_called()
        self.scope["logger"].debug.assert_not_called()

    def test_pinned_source_and_patched_modules_compile(self):
        content = (loop_tests.FIXTURE / "run_agent.py").read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(content).hexdigest(), "7a36be48ffdc0fe62b855263683d55c1c7138cc65acf597175920fcf86b45bd5")
        for path in (self.target / "run_agent.py", self.target / "agent/conversation_loop.py"):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_secret_split_across_chunks_is_never_published(self):
        self.mandatory()
        self.agent._stream_needs_break = True
        for chunk in ("sk-proj-", "synthetic", "credential0123456789", "\n"):
            self.agent._fire_stream_delta(chunk)
        self.assert_no_delivery()
        self.agent._stream_think_scrubber.feed.assert_not_called()
        self.agent._stream_context_scrubber.feed.assert_not_called()
        self.assertEqual(self.agent._current_streamed_assistant_text, "")

    def test_reasoning_interim_and_tool_names_are_withheld(self):
        self.mandatory()
        self.agent._fire_reasoning_delta("synthetic-private-reasoning")
        self.agent._emit_interim_assistant_message({"content": "synthetic-private-commentary"})
        self.agent._fire_tool_gen_started("synthetic-private-tool-name")
        self.assert_no_delivery()

    def test_tail_reset_discards_without_flushing_or_replaying(self):
        self.mandatory()
        think = self.agent._stream_think_scrubber
        context = self.agent._stream_context_scrubber
        self.agent._current_streamed_assistant_text = "stale private text"
        self.agent._reset_stream_delivery_tracking()
        self.agent._reset_stream_delivery_tracking()
        think.flush.assert_not_called()
        context.flush.assert_not_called()
        self.assertIsNone(self.agent._stream_think_scrubber)
        self.assertIsNone(self.agent._stream_context_scrubber)
        self.assertEqual(self.agent._current_streamed_assistant_text, "")
        self.assert_no_delivery()

    def test_provider_worker_cannot_publish_without_identity_context(self):
        self.mandatory()
        errors = []
        def worker():
            try:
                self.agent._fire_stream_delta("synthetic-private-worker-text")
                self.agent._fire_reasoning_delta("synthetic-private-worker-reasoning")
            except Exception as error:
                errors.append(error)
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assert_no_delivery()

    def test_gate_removal_does_not_reenable_live_publication(self):
        self.mandatory()
        self.host.base.manager._middleware["llm_execution"].clear()
        self.agent._fire_stream_delta("synthetic-private-after-removal")
        self.agent._emit_interim_assistant_message({"content": "synthetic-private-after-removal"})
        self.assert_no_delivery()

    def test_normal_mode_preserves_text_reasoning_interim_and_tool_callbacks(self):
        self.agent._fire_stream_delta("safe text")
        self.agent.stream_delta_callback.assert_called_once_with("safe text")
        self.agent._stream_callback.assert_called_once_with("safe text")
        self.agent._fire_reasoning_delta("safe reasoning")
        self.agent.reasoning_callback.assert_called_once_with("safe reasoning")
        self.agent._emit_interim_assistant_message({"content": "safe text"})
        self.agent.interim_assistant_callback.assert_called_once_with("safe text", already_streamed=True)
        self.agent._fire_tool_gen_started("read_file")
        self.agent.tool_gen_callback.assert_called_once_with("read_file")

    def test_normal_mode_preserves_tail_delivery_and_tracking_reset(self):
        self.agent._reset_stream_delivery_tracking()
        self.assertEqual([call.args[0] for call in self.agent.stream_delta_callback.call_args_list],
                         ["private-think-tail", "private-context-tail"])
        self.assertEqual(self.agent._current_streamed_assistant_text, "")

    def test_mandatory_mode_does_not_invoke_failing_callbacks(self):
        self.mandatory()
        self.agent.stream_delta_callback.side_effect = RuntimeError("synthetic-private-callback-error")
        self.agent.interim_assistant_callback.side_effect = RuntimeError("synthetic-private-callback-error")
        self.agent._fire_stream_delta("private text")
        self.agent._emit_interim_assistant_message({"content": "private text"})
        self.assert_no_delivery()

    def test_native_nonstreaming_message_builder_withholds_reasoning_delivery_and_log(self):
        for mandatory in (False, True):
            if mandatory:
                self.mandatory()
            logging = Mock()
            scope = self.host.compile("chat_completion_helpers.py", {"build_assistant_message"},
                                      logging=logging, _sanitize_surrogates=lambda text: text)
            agent = SimpleNamespace(
                _extract_reasoning=lambda message: "synthetic-private-reasoning",
                _strip_think_blocks=lambda text: text, verbose_logging=True,
                reasoning_callback=Mock(), stream_delta_callback=None, _stream_callback=None,
            )
            message = SimpleNamespace(content="safe content", tool_calls=None)
            with patch.dict(sys.modules, {"agent.redact": SimpleNamespace(redact_sensitive_text=lambda text: text)}):
                result = scope["build_assistant_message"](agent, message, "stop")
            self.assertEqual(result["reasoning"], "synthetic-private-reasoning")
            self.assertEqual(result["content"], "safe content")
            self.assertEqual(agent.reasoning_callback.called, not mandatory)
            self.assertEqual(logging.debug.called, not mandatory)

    def test_native_muted_stream_display_fallback_is_guarded(self):
        tree = ast.parse((self.target / "agent/chat_completion_helpers.py").read_text(encoding="utf-8"))
        guards = [node for node in ast.walk(tree) if isinstance(node, ast.If)
                  and ast.unparse(node.test) == "agent.stream_delta_callback and (not mandatory_middleware_enabled())"]
        self.assertEqual(len(guards), 1)
        for mandatory in (False, True):
            if mandatory:
                self.mandatory()
            agent = Mock()
            scope = {"agent": agent, "delta": SimpleNamespace(content="synthetic-private-muted-content"),
                     "mandatory_middleware_enabled": self.engine.mandatory_middleware_enabled}
            exec(compile(ast.fix_missing_locations(ast.Module(body=guards, type_ignores=[])), "native_muted_guard", "exec"), scope)
            self.assertEqual(agent.stream_delta_callback.called, not mandatory)
            self.assertEqual(agent._record_streamed_assistant_text.called, not mandatory)

    def test_native_loop_display_guards_block_and_normal_mode_preserves_sinks(self):
        # Execute the exact five changed native statements, not a replacement loop.
        guards = [node for node in ast.walk(self.loop) if isinstance(node, ast.If)
                  and "mandatory_middleware_enabled" in ast.unparse(node.test)
                  and any(token in ast.unparse(node.test) for token in (
                      "assistant_message.content", "_should_emit_quiet_tool_messages",
                      "stream_delta_callback", "final_response"))]
        self.assertEqual(len(guards), 5)
        for mandatory in (False, True):
            if mandatory:
                self.mandatory()
            for guard in guards:
                with self.subTest(mandatory=mandatory, line=guard.lineno):
                    agent = Mock(quiet_mode=False, verbose_logging=True, log_prefix="", _delegate_depth=1)
                    agent._strip_think_blocks.side_effect = lambda text: text
                    scope = {"agent": agent, "assistant_message": SimpleNamespace(content="synthetic-private-content"),
                             "turn_content": "synthetic-private-content", "final_response": "synthetic-private-content",
                             "mandatory_middleware_enabled": self.engine.mandatory_middleware_enabled, "re": re}
                    exec(compile(ast.fix_missing_locations(ast.Module(body=[guard], type_ignores=[])), "native_display_guard", "exec"), scope)
                    sinks = (agent._vprint, agent._safe_print, agent.tool_progress_callback, agent.stream_delta_callback)
                    self.assertEqual(any(sink.called for sink in sinks), not mandatory)


if __name__ == "__main__":
    unittest.main()

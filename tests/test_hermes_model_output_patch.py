"""Pinned native finalizer and Maya model-output policy, with inert effects."""

import ast
import hashlib
import os
import shutil
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.governance import bind_request_identity
from tests import test_hermes_conversation_governance_patch as loop_tests
from tests import test_hermes_output_deferral_patch as output_tests


class TestHermesModelOutputPatch(unittest.TestCase):
    def setUp(self):
        self.host = output_tests.TestHermesOutputDeferralPatch()
        self.addCleanup(self.host.doCleanups)
        self.host.setUp()
        self.target = self.host.target
        shutil.copyfile(loop_tests.FIXTURE / "turn_finalizer.py", self.target / "agent/turn_finalizer.py")
        applied = subprocess.run(
            ["git", "apply", "--whitespace=error", str(loop_tests.ROOT / "patches/hermes/0010-governed-final-model-disclosure.patch")],
            cwd=self.target, capture_output=True, text=True, check=False,
        )
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.engine = self.host.host.host.load("_disclosure_middleware", self.target / "hermes_cli/middleware.py")
        patcher = patch.dict(sys.modules, {"hermes_cli.middleware": self.engine})
        patcher.start()
        self.addCleanup(patcher.stop)
        tree = ast.parse((self.target / "agent/turn_finalizer.py").read_text(encoding="utf-8"))
        node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == "finalize_turn")
        scope = {"os": os, "_summarize_user_message_for_log": lambda message: str(message)}
        module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), node], type_ignores=[])
        exec(compile(ast.fix_missing_locations(module), "native_finalizer", "exec"), scope)
        self.finalize = scope["finalize_turn"]
        self.logger = Mock()
        patcher = patch.dict(sys.modules, {"agent.conversation_loop": SimpleNamespace(logger=self.logger)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.plugins = sys.modules["hermes_cli.plugins"]
        self.hook = Mock(side_effect=lambda name, **kwargs: [])
        patcher = patch.object(self.plugins, "invoke_hook", self.hook, create=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.manager = self.host.host.base.manager
        self.plugin = self.host.host.plugin
        self.plugin.gateway = PolicyAuthorizationGateway((
            PolicyRule("model.egress", target="model:openai", operation="infer", actor_id="alice"),
            PolicyRule("model.output", target="model:openai", operation="disclose", actor_id="alice"),
        ))
        self.agent = Mock()
        attrs = {
            "provider": "openai", "model": "test-model", "base_url": "https://api.openai.com/v1",
            "max_iterations": 3, "iteration_budget": SimpleNamespace(remaining=3, used=1, max_total=3),
            "quiet_mode": True, "session_id": "synthetic-session", "_turn_failed_file_mutations": {},
            "_tool_guardrail_halt_decision": None, "_response_was_previewed": False,
            "_skill_nudge_interval": 0, "_iters_since_skill": 0, "valid_tool_names": [],
            "_interrupt_message": None, "context_compressor": SimpleNamespace(last_prompt_tokens=0),
        }
        for name, value in attrs.items():
            setattr(self.agent, name, value)
        for name in ("session_input_tokens", "session_output_tokens", "session_cache_read_tokens",
                     "session_cache_write_tokens", "session_reasoning_tokens", "session_prompt_tokens",
                     "session_completion_tokens", "session_total_tokens"):
            setattr(self.agent, name, 0)
        self.agent.session_estimated_cost_usd = 0.0
        self.agent.session_cost_status = "available"
        self.agent.session_cost_source = "synthetic"
        self.agent._turn_completion_explainer_enabled.return_value = False
        self.agent._drain_pending_steer.return_value = None
        self.messages = [{"role": "user", "content": "synthetic question"},
                         {"role": "assistant", "content": "safe response"}]

    def install(self, output=None):
        for kind, callback in (
            ("llm_execution", self.plugin.model_execution),
            ("tool_execution", self.plugin.tool_execution),
            ("tool_result", self.plugin.tool_result),
            ("model_output", output or self.plugin.model_output),
        ):
            self.manager._middleware[kind] = [callback]
            self.engine.require_middleware(kind, callback)

    def run_turn(self):
        return self.finalize(
            self.agent, final_response="safe response", api_call_count=1,
            interrupted=False, failed=False, messages=self.messages,
            conversation_history=[], effective_task_id="synthetic-task",
            turn_id="synthetic-turn", user_message="synthetic question",
            original_user_message="synthetic question", _should_review_memory=False,
            _turn_exit_reason="text_response(stop)",
        )

    def test_pinned_source_and_candidate_compile(self):
        content = (loop_tests.FIXTURE / "turn_finalizer.py").read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(content).hexdigest(), "71ddf4e5245fe1302056290b95011aefc57909ad12485f8198a64ff46dbc709c")
        for path in (self.target / "agent/turn_finalizer.py", self.target / "hermes_cli/middleware.py"):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        self.assertFalse(hasattr(self.engine, "MAYA_GOVERNANCE_CONTRACT"))

    def test_allowed_response_is_checked_at_four_stages(self):
        self.install()
        with bind_request_identity("alice"):
            result = self.run_turn()
        self.assertEqual(result["final_response"], "safe response")
        self.assertEqual(self.agent._save_trajectory.call_count, 1)
        self.agent._persist_session.assert_called_once()
        self.assertEqual(self.hook.call_count, 3)  # transform, post, session-end
        self.assertEqual(self.plugin.audit.write.call_count, 8)

    def test_missing_identity_or_denied_actor_blocks_before_save(self):
        self.install()
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.run_turn()
        with bind_request_identity("mallory"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.run_turn()
        self.agent._save_trajectory.assert_not_called()
        self.agent._persist_session.assert_not_called()
        self.hook.assert_not_called()

    def test_original_secret_blocks_before_any_finalizer_sink(self):
        self.install()
        self.messages[-1]["content"] = "sk-proj-syntheticcredential0123456789"
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.run_turn()
        self.agent._save_trajectory.assert_not_called()
        self.agent._persist_session.assert_not_called()
        self.hook.assert_not_called()

    def test_transform_injected_secret_is_blocked_before_post_hook_or_return(self):
        self.install()
        self.hook.side_effect = lambda name, **kwargs: ["sk-proj-syntheticcredential0123456789"] if name == "transform_llm_output" else []
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.run_turn()
        self.assertEqual([call.args[0] for call in self.hook.call_args_list], ["transform_llm_output"])
        self.agent._persist_session.assert_called_once()  # original safe content only

    def test_gate_removed_after_trajectory_save_prevents_session_persistence(self):
        self.install()
        self.agent._save_trajectory.side_effect = lambda *args: self.manager._middleware["model_output"].clear()
        with bind_request_identity("alice"), self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "gate_missing"):
            self.run_turn()
        self.agent._persist_session.assert_not_called()
        self.hook.assert_not_called()

    def test_callback_mutation_and_audit_failure_cannot_return_output(self):
        self.install()
        self.manager._middleware["model_output"].insert(0, lambda **kwargs: {"final_response": "replacement"})
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.run_turn()
        self.agent._save_trajectory.assert_not_called()
        self.manager._middleware["model_output"].pop(0)
        self.plugin.audit.write.side_effect = RuntimeError("synthetic-private-audit-error")
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError) as caught:
            self.run_turn()
        self.assertNotIn("synthetic-private", str(caught.exception))
        self.agent._save_trajectory.assert_not_called()

    def test_unexpected_return_metadata_is_rejected_without_returning_result(self):
        self.install()
        self.agent.session_cost_source = object()
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.run_turn()
        self.agent._persist_session.assert_called_once()
        self.assertEqual(self.hook.call_count, 2)  # already validated transform/post

    def test_normal_mode_keeps_native_transform_persistence_and_return(self):
        self.hook.side_effect = lambda name, **kwargs: ["normal transformed"] if name == "transform_llm_output" else []
        result = self.run_turn()
        self.assertEqual(result["final_response"], "normal transformed")
        self.agent._persist_session.assert_called_once()
        self.assertEqual(self.hook.call_count, 3)


if __name__ == "__main__":
    unittest.main()

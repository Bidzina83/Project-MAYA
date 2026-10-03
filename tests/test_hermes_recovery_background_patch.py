"""Complete pinned recovery consumers; no provider, worker or customer state."""

import ast
import contextlib
import hashlib
import json
import shutil
import subprocess
import sys
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from project_maya.governance import PolicyAuthorizationGateway
from project_maya.hermes_plugins.governance import bind_request_identity
from tests import test_hermes_model_output_patch as output_tests
from tests.test_hermes_conversation_governance_patch import FIXTURE, ROOT


HASHES = {
    "context_compressor.py": "c83042885c66f13b9ffb3b94da763f8a4240c6bfdc81b9e5c98ff172a20d8733",
    "background_review.py": "afb05223518c3ea945bdb40da1af133431c1eb86146dd80c43054777a131170c",
    "plugins.py": "fb60534b86b403778232eb63842bba563448a15419b1a43c7fced2274b7601c4",
}


def native_method(path, class_name, method, scope):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    fn = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == method)
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), fn], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), scope)
    return scope[method]


class TestHermesRecoveryBackgroundPatch(unittest.TestCase):
    def setUp(self):
        self.host = output_tests.TestHermesModelOutputPatch()
        self.addCleanup(self.host.doCleanups)
        self.host.setUp()
        self.target = self.host.target
        self.engine = self.host.engine
        for name, directory in (("context_compressor.py", "agent"),
                                ("background_review.py", "agent"), ("plugins.py", "hermes_cli")):
            shutil.copyfile(FIXTURE / name, self.target / directory / name)
        result = subprocess.run(
            ["git", "apply", "--whitespace=error", str(ROOT / "patches/hermes/0011-recovery-and-background-denial.patch")],
            cwd=self.target, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.engine = self.host.host.host.host.load("_recovery_middleware", self.target / "hermes_cli/middleware.py")
        self.host.engine = self.engine
        middleware_patch = patch.dict(sys.modules, {"hermes_cli.middleware": self.engine})
        middleware_patch.start()
        self.addCleanup(middleware_patch.stop)
        finalizer_tree = ast.parse((self.target / "agent/turn_finalizer.py").read_text(encoding="utf-8"))
        finalizer = next(node for node in finalizer_tree.body if isinstance(node, ast.FunctionDef) and node.name == "finalize_turn")
        scope = self.host.finalize.__globals__.copy()
        module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), finalizer], type_ignores=[])
        exec(compile(ast.fix_missing_locations(module), "native_recovery_finalizer", "exec"), scope)
        self.host.finalize = scope["finalize_turn"]
        self.logger = Mock()
        self.call = Mock(return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="safe summary"))]))
        self.scope = {
            "time": time, "json": json, "logger": self.logger, "call_llm": self.call,
            "aux_interrupt_protection": contextlib.nullcontext,
            "redact_sensitive_text": lambda text: text, "_is_connection_error": lambda exc: False,
            "_SUMMARY_FAILURE_COOLDOWN_SECONDS": 300,
        }
        for name in ("HISTORICAL_TASK_HEADING", "HISTORICAL_IN_PROGRESS_HEADING",
                     "HISTORICAL_PENDING_ASKS_HEADING", "HISTORICAL_REMAINING_WORK_HEADING"):
            self.scope[name] = name
        self.summary = native_method(self.target / "agent/context_compressor.py", "ContextCompressor", "_generate_summary", self.scope)
        self.compressor = SimpleNamespace(
            _summary_failure_cooldown_until=0, _previous_summary="previous summary",
            _summary_model_fallen_back=False, _last_summary_error=None,
            _last_summary_auth_failure=False, _last_summary_network_failure=False,
            model="main", summary_model="auxiliary", provider="openai", base_url="http://127.0.0.1",
            api_key=None, api_mode="chat_completions", _compute_summary_budget=lambda turns: 100,
            _serialize_for_summary=lambda turns: "synthetic turns", _with_summary_prefix=lambda text: text,
            _fallback_to_main_for_compression=Mock(),
        )
        self.compressor._generate_summary = lambda turns, **kwargs: self.summary(self.compressor, turns, **kwargs)
        self.invoke = native_method(self.target / "hermes_cli/plugins.py", "PluginManager", "invoke_hook",
                                    {"logger": self.logger, "OBSERVER_SCHEMA_VERSION": 1})
        self.background = self.host.host.host.host.load("_candidate_background_review", self.target / "agent/background_review.py")

    def mandatory(self):
        self.host.install()

    def test_pinned_fixtures_full_series_and_no_production_marker(self):
        for name, digest in HASHES.items():
            self.assertEqual(hashlib.sha256((FIXTURE / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest(), digest)
        for path in self.target.rglob("*.py"):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        self.assertFalse(hasattr(self.engine, "MAYA_GOVERNANCE_CONTRACT"))

    def test_summary_denial_preserves_state_and_never_retries(self):
        self.mandatory()
        denial = self.engine.MandatoryMiddlewareError("mandatory.synthetic_denial")
        self.call.side_effect = denial
        before = vars(self.compressor).copy()
        with self.assertRaises(self.engine.MandatoryMiddlewareError) as caught:
            self.compressor._generate_summary([])
        self.assertIs(caught.exception, denial)
        self.assertEqual(vars(self.compressor), before)
        self.call.assert_called_once()
        self.compressor._fallback_to_main_for_compression.assert_not_called()
        self.logger.warning.assert_not_called()

    def test_summary_success_retains_native_behavior(self):
        for mandatory in (False, True):
            if mandatory:
                self.mandatory()
            self.assertEqual(self.compressor._generate_summary([]), "safe summary")
            self.assertEqual(self.compressor._previous_summary, "safe summary")

    def test_actual_maya_policy_denial_never_reaches_summary_transport(self):
        self.host.plugin.gateway = PolicyAuthorizationGateway(())
        self.mandatory()
        transport = Mock()
        config = self.host.plugin.config.llm
        def governed_summary(**kwargs):
            return self.engine.run_llm_execution_middleware(
                {"model": config.model, "messages": kwargs["messages"]}, transport,
                provider=config.provider, base_url=config.endpoint or "https://api.openai.com/v1",
            )
        self.call.side_effect = governed_summary
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.compressor._generate_summary([])
        transport.assert_not_called()
        self.call.assert_called_once()
        self.compressor._fallback_to_main_for_compression.assert_not_called()
        self.assertEqual(self.compressor._previous_summary, "previous summary")
        records = [call.args[0] for call in self.host.plugin.audit.write.call_args_list]
        self.assertTrue(any(record.event_type == "authorization.hermes_boundary"
                            and record.capability == "model.egress" and record.decision == "deny"
                            for record in records))

    def test_normal_mode_denial_retains_native_fallback(self):
        self.call.side_effect = [self.engine.MandatoryMiddlewareError("synthetic failure"), self.call.return_value]
        self.assertEqual(self.compressor._generate_summary([]), "safe summary")
        self.assertEqual(self.call.call_count, 2)
        self.compressor._fallback_to_main_for_compression.assert_called_once()

    def test_observer_denial_stops_before_later_callbacks_or_logging(self):
        self.mandatory()
        denial = self.engine.MandatoryMiddlewareError("mandatory.synthetic_denial")
        first, later = Mock(side_effect=denial), Mock(return_value="later")
        with self.assertRaises(self.engine.MandatoryMiddlewareError) as caught:
            self.invoke(SimpleNamespace(_hooks={"post_llm_call": [first, later]}), "post_llm_call")
        self.assertIs(caught.exception, denial)
        later.assert_not_called()
        self.logger.warning.assert_not_called()

    def test_normal_observers_keep_best_effort_behavior(self):
        first, later = Mock(side_effect=self.engine.MandatoryMiddlewareError("synthetic failure")), Mock(return_value="later")
        self.assertEqual(self.invoke(SimpleNamespace(_hooks={"event": [first, later]}), "event"), ["later"])
        self.logger.warning.assert_called_once()

    def test_ordinary_observer_error_remains_best_effort_in_mandatory_mode(self):
        self.mandatory()
        self.assertEqual(self.invoke(SimpleNamespace(_hooks={"event": [Mock(side_effect=ValueError("synthetic")), Mock(return_value="later")]}), "event"), ["later"])

    def test_background_factory_blocks_before_thread_construction(self):
        self.mandatory()
        thread = Mock()
        spawn = native_method(self.target / "run_agent.py", "AIAgent", "_spawn_background_review", {"threading": SimpleNamespace(Thread=thread)})
        with patch.dict(sys.modules, {"agent.background_review": self.background}):
            with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "mandatory_middleware.background_review_unqualified"):
                spawn(SimpleNamespace(), [], review_memory=True)
        thread.assert_not_called()

    def test_direct_worker_blocks_before_agent_or_approval_setup(self):
        self.mandatory()
        agent, approval = Mock(), Mock()
        with patch.dict(sys.modules, {"run_agent": SimpleNamespace(AIAgent=agent), "tools.terminal_tool": SimpleNamespace(set_approval_callback=approval)}):
            with self.assertRaises(self.engine.MandatoryMiddlewareError):
                self.background._run_review_in_thread(SimpleNamespace(), [], "synthetic")
        agent.assert_not_called()
        approval.assert_not_called()

    def test_prebuilt_target_is_blocked_if_mandatory_mode_activates(self):
        target, prompt = self.background.spawn_background_review_thread(SimpleNamespace(), [], review_memory=True)
        self.assertTrue(prompt)
        self.mandatory()
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            target()

    def trigger_finalizer_background_review(self):
        self.host.agent._skill_nudge_interval = 1
        self.host.agent._iters_since_skill = 1
        self.host.agent.valid_tool_names = ["skill_manage"]

    def test_complete_finalizer_propagates_background_readiness_denial(self):
        self.mandatory()
        self.trigger_finalizer_background_review()
        thread = Mock()
        spawn = native_method(self.target / "run_agent.py", "AIAgent", "_spawn_background_review", {"threading": SimpleNamespace(Thread=thread)})
        self.host.agent._spawn_background_review.side_effect = lambda **kwargs: spawn(self.host.agent, **kwargs)
        with patch.dict(sys.modules, {"agent.background_review": self.background}), bind_request_identity("alice"):
            with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "background_review_unqualified"):
                self.host.run_turn()
        thread.assert_not_called()
        self.host.agent._spawn_background_review.assert_called_once()

    def test_normal_finalizer_retains_best_effort_background_failure(self):
        self.trigger_finalizer_background_review()
        self.host.agent._spawn_background_review.side_effect = self.engine.MandatoryMiddlewareError("synthetic failure")
        self.assertEqual(self.host.run_turn()["final_response"], "safe response")
        self.host.agent._spawn_background_review.assert_called_once()

    def test_normal_background_factory_and_thread_behavior_preserved(self):
        agent, messages = SimpleNamespace(), []
        with patch.object(self.background, "_run_review_in_thread") as worker:
            target, prompt = self.background.spawn_background_review_thread(agent, messages, review_memory=True)
            target()
            worker.assert_called_once_with(agent, messages, prompt)
        thread = Mock()
        spawn = native_method(self.target / "run_agent.py", "AIAgent", "_spawn_background_review", {"threading": SimpleNamespace(Thread=thread)})
        with patch.dict(sys.modules, {"agent.background_review": self.background}):
            spawn(agent, messages, review_memory=True)
        thread.assert_called_once()
        thread.return_value.start.assert_called_once()


if __name__ == "__main__":
    unittest.main()

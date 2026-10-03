"""Complete native persistence helpers and observer dispatch, with inert sinks."""
import ast
from datetime import datetime
import json
import logging
import subprocess
import sys
import unittest
from unittest.mock import Mock

from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.governance import bind_request_identity
from tests import test_hermes_recovery_background_patch as recovery_tests


class TestHermesPersistenceObserverPatch(unittest.TestCase):
    def setUp(self):
        self.host = recovery_tests.TestHermesRecoveryBackgroundPatch()
        self.addCleanup(self.host.doCleanups)
        self.host.setUp()
        self.target = self.host.target
        self.engine = self.host.engine
        result = subprocess.run(
            ["git", "apply", "--whitespace=error", str(recovery_tests.ROOT / "patches/hermes/0012-native-persistence-and-raw-observer-boundaries.patch")],
            cwd=self.target, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        tree = ast.parse((self.target / "run_agent.py").read_text(encoding="utf-8"))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "AIAgent")
        names = {"_validate_persistence_payload", "_persist_session", "_flush_messages_to_session_db", "_save_session_log", "_save_trajectory"}
        methods = [node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name in names]
        self.assertEqual(len(methods), len(names))
        self.writer, self.trajectory_writer, self.logger = Mock(), Mock(), Mock()
        scope = {"datetime": datetime, "json": json, "logging": self.logger, "logger": self.logger,
                 "redact_sensitive_text": lambda value: value, "atomic_json_write": self.writer,
                 "_save_trajectory_to_file": self.trajectory_writer,
                 "_is_multimodal_tool_result": lambda value: False}
        native = ast.ClassDef(name="NativePersistence", bases=[], keywords=[], body=methods, decorator_list=[])
        module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), native], type_ignores=[])
        exec(compile(ast.fix_missing_locations(module), "native_persistence", "exec"), scope)
        self.agent = scope["NativePersistence"]()
        self.agent.model = "test-model"
        self.agent.provider = "openai"
        self.agent.base_url = "https://api.openai.com/v1"
        self.agent._drop_trailing_empty_response_scaffolding = Mock()
        self.agent._apply_persist_user_message_override = Mock()
        self.agent._session_messages = [{"role": "user", "content": "previous"}]
        self.agent._session_db = Mock()
        self.agent._session_db_created = True
        self.agent.session_id = "synthetic-session"
        self.agent._last_flushed_db_idx = 0
        self.agent._session_json_enabled = True
        self.agent.logs_dir = self.target / "sessions"
        self.agent.logs_dir.mkdir()
        self.agent._clean_session_content = lambda text: text
        self.agent._redact_message_content = lambda text: text
        self.agent.platform = "synthetic"
        self.agent.session_start = datetime(2026, 10, 2)
        self.agent._cached_system_prompt = "synthetic system prompt"
        self.agent.tools = []
        self.agent.verbose_logging = True
        self.agent.save_trajectories = True
        self.agent._convert_to_trajectory_format = Mock(side_effect=lambda messages, query, completed: messages)
        self.messages = [{"role": "user", "content": "synthetic question"},
                         {"role": "assistant", "content": "safe response", "reasoning": "safe reasoning"}]
        self.invoke = recovery_tests.native_method(self.target / "hermes_cli/plugins.py", "PluginManager", "invoke_hook",
                                                   {"logger": self.logger, "OBSERVER_SCHEMA_VERSION": 1})

    def mandatory(self, *, allowed=True):
        self.host.host.plugin.gateway = PolicyAuthorizationGateway((PolicyRule("model.output", target="model:openai", operation="disclose", actor_id="alice"),) if allowed else ())
        self.host.mandatory()

    def assert_no_store_effects(self):
        self.writer.assert_not_called()
        self.agent._session_db.append_message.assert_not_called()
        self.trajectory_writer.assert_not_called()
        self.assertEqual(list(self.agent.logs_dir.iterdir()), [])

    def test_full_series_compiles_without_production_marker(self):
        for name in ("run_agent.py", "hermes_cli/plugins.py"):
            compile((self.target / name).read_text(encoding="utf-8"), name, "exec")
        self.assertFalse(hasattr(self.engine, "MAYA_GOVERNANCE_CONTRACT"))

    def test_policy_denial_precedes_incremental_assignment_and_stores(self):
        self.mandatory(allowed=False)
        previous = self.agent._session_messages
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.agent._persist_session(self.messages, [])
        self.assertIs(self.agent._session_messages, previous)
        self.assert_no_store_effects()

    def test_override_is_validated_before_incremental_store(self):
        self.mandatory()
        self.agent._apply_persist_user_message_override.side_effect = lambda messages: messages[0].update(content="sk-proj-syntheticcredential0123456789")
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.agent._persist_session(self.messages, [])
        self.assert_no_store_effects()

    def test_direct_sqlite_denial_precedes_cursor_and_append(self):
        self.mandatory(allowed=False)
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.agent._flush_messages_to_session_db(self.messages, [])
        self.assertEqual(self.agent._last_flushed_db_idx, 0)
        self.assert_no_store_effects()

    def test_missing_identity_and_removed_gate_block_direct_writers(self):
        self.mandatory()
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.agent._flush_messages_to_session_db(self.messages, [])
        self.host.host.manager._middleware["model_output"].clear()
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.agent._save_trajectory(self.messages, "synthetic", True)
        self.assert_no_store_effects()

    def test_audit_failure_prevents_native_write(self):
        self.mandatory()
        self.host.host.plugin.audit.write.side_effect = RuntimeError("synthetic-private-audit-failure")
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError) as caught:
            self.agent._save_session_log(self.messages)
        self.assertNotIn("synthetic-private", str(caught.exception))
        self.assert_no_store_effects()

    def test_transformed_json_payload_is_checked_and_denial_not_logged(self):
        self.mandatory()
        self.agent._clean_session_content = lambda text: "sk-proj-syntheticcredential0123456789"
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.agent._save_session_log(self.messages)
        self.assert_no_store_effects()
        self.logger.warning.assert_not_called()

    def test_trajectory_source_denial_precedes_conversion(self):
        self.mandatory(allowed=False)
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.agent._save_trajectory(self.messages, "synthetic", True)
        self.agent._convert_to_trajectory_format.assert_not_called()
        self.assert_no_store_effects()

    def test_transformed_trajectory_is_checked_before_file_sink(self):
        self.mandatory()
        self.agent._convert_to_trajectory_format.return_value = None
        self.agent._convert_to_trajectory_format.side_effect = lambda *args: [{"content": "sk-proj-syntheticcredential0123456789"}]
        with bind_request_identity("alice"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.agent._save_trajectory(self.messages, "synthetic", True)
        self.assert_no_store_effects()

    def test_allowed_native_stores_and_sqlite_dedup_are_preserved(self):
        self.mandatory()
        with bind_request_identity("alice"):
            self.agent._persist_session(self.messages, [])
            self.agent._flush_messages_to_session_db(self.messages, [])
            self.agent._save_trajectory(self.messages, "synthetic", True)
        self.writer.assert_called_once()
        self.assertEqual(self.agent._session_db.append_message.call_count, 2)
        self.assertEqual(self.agent._last_flushed_db_idx, 2)
        self.trajectory_writer.assert_called_once()
        self.assertEqual(self.agent._session_db.append_message.call_args.kwargs["reasoning"], "safe reasoning")

    def test_normal_mode_retains_native_store_behavior_without_gates(self):
        self.agent._persist_session(self.messages, [])
        self.agent._save_trajectory(self.messages, "synthetic", True)
        self.writer.assert_called_once()
        self.assertEqual(self.agent._session_db.append_message.call_count, 2)
        self.trajectory_writer.assert_called_once()

    def test_disabled_optional_stores_remain_noops_without_identity(self):
        self.mandatory()
        self.agent._session_json_enabled = False
        self.agent.save_trajectories = False
        self.agent._session_db = None
        self.agent._save_session_log(self.messages)
        self.agent._save_trajectory(self.messages, "synthetic", True)
        self.agent._flush_messages_to_session_db(self.messages, [])
        self.writer.assert_not_called()
        self.trajectory_writer.assert_not_called()

    def test_raw_api_observers_are_suppressed_before_callbacks_in_mandatory_mode(self):
        self.mandatory()
        for name in ("pre_api_request", "post_api_request", "api_request_error"):
            callback = Mock(return_value="synthetic")
            manager = type("Hooks", (), {"_hooks": {name: [callback]}})()
            self.assertEqual(self.invoke(manager, name, request="synthetic raw body"), [])
            callback.assert_not_called()

    def test_normal_mode_raw_observers_still_receive_native_payloads(self):
        for name in ("pre_api_request", "post_api_request", "api_request_error"):
            callback = Mock(return_value="synthetic")
            manager = type("Hooks", (), {"_hooks": {name: [callback]}})()
            self.assertEqual(self.invoke(manager, name, request="synthetic raw body"), ["synthetic"])
            self.assertEqual(callback.call_args.kwargs["request"], "synthetic raw body")

    def test_other_observers_retain_typed_denial_propagation(self):
        self.mandatory()
        callback = Mock(side_effect=self.engine.MandatoryMiddlewareError("gate_missing"))
        manager = type("Hooks", (), {"_hooks": {"on_session_end": [callback]}})()
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.invoke(manager, "on_session_end")


if __name__ == "__main__":
    unittest.main()

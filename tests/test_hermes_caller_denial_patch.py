"""Scoped complete native callers; no provider, customer state or worker."""
import ast
import contextlib
from datetime import datetime
import hashlib
import os
import shutil
import subprocess
import sys
from types import SimpleNamespace
import unittest
import uuid
from unittest.mock import Mock, patch
from project_maya.hermes_plugins.governance import bind_request_identity

from tests import test_hermes_persistence_observer_patch as persistence

ROOT = persistence.recovery_tests.ROOT
FIXTURE = ROOT / "tests/fixtures/hermes_middleware"


def native_function(path, name, scope):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), node], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), scope)
    return scope[name]


class TestHermesCallerDenialPatch(unittest.TestCase):
    def setUp(self):
        self.host = persistence.TestHermesPersistenceObserverPatch()
        self.addCleanup(self.host.doCleanups)
        self.host.setUp()
        self.target = self.host.target
        self.engine = self.host.engine
        for name, path in (("cli.py", "cli.py"), ("conversation_compression.py", "agent/conversation_compression.py")):
            shutil.copyfile(FIXTURE / name, self.target / path)
        result = subprocess.run(["git", "apply", "--whitespace=error", str(ROOT / "patches/hermes/0013-outer-caller-denial-propagation.patch")],
                                cwd=self.target, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.logger = Mock()
        scope = {"logger": self.logger, "os": os, "datetime": datetime, "uuid": uuid,
                 "_compression_lock_holder": lambda agent: "synthetic-holder",
                 "estimate_request_tokens_rough": Mock(return_value=10),
                 "COMPACTION_STATUS": "synthetic-status"}
        self.compress = native_function(self.target / "agent/conversation_compression.py", "compress_context", scope)
        self.flush = native_function(self.target / "agent/tool_executor.py", "_flush_session_db_after_tool_progress", {"logger": self.logger})
        tree = ast.parse((self.target / "cli.py").read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and any(isinstance(f, ast.FunctionDef) and f.name == "new_session" for f in n.body))
        selected = {"new_session", "_notify_session_boundary", "_persist_active_session_before_close", "_manual_compress"}
        methods = [node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name in selected]
        module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *methods], type_ignores=[])
        scope = {"logger": self.logger, "os": os, "datetime": datetime}
        exec(compile(ast.fix_missing_locations(module), "native-cli-callers", "exec"), scope)
        self.cli = {name: scope[name] for name in selected}
        self.db = Mock()
        self.db.try_acquire_compression_lock.return_value = True
        self.db.get_session_title.return_value = None
        compressor = Mock(compression_count=1, _last_compress_aborted=False, _last_summary_error=None,
                          _last_aux_model_failure_model=None)
        compressor.compress.return_value = [{"role": "user", "content": "safe summary"}]
        self.agent = SimpleNamespace(_compression_feasibility_checked=True, compression_in_place=False,
            session_id="old-session", model="test-model", platform="cli", log_prefix="",
            context_compressor=compressor, _memory_manager=None, _session_db=self.db,
            _todo_store=Mock(), _invalidate_system_prompt=Mock(), _build_system_prompt=Mock(return_value="safe prompt"),
            _emit_status=Mock(), _emit_warning=Mock(), commit_memory_session=Mock(),
            _flush_messages_to_session_db=Mock(), _session_init_model_config={}, tools=[], event_callback=None)
        self.agent._todo_store.format_for_injection.return_value = ""
        self.messages = [{"role": "user", "content": "safe input"}]
        modules = {"tools.file_tools": SimpleNamespace(reset_file_dedup=Mock()),
                   "gateway.session_context": SimpleNamespace(set_current_session_id=Mock()),
                   "hermes_logging": SimpleNamespace(set_session_context=Mock()),
                   "hermes_cli.goals": SimpleNamespace(migrate_goal_to_session=Mock())}
        self.modules = modules
        patcher = patch.dict(sys.modules, modules)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.denial = self.engine.MandatoryMiddlewareError("callback_failed")

    def mandatory(self):
        self.host.mandatory()

    def test_series_compiles_and_fixtures_are_pinned(self):
        for name, digest in (("cli.py", "5b1f202b0eafe9028b79132bcac7911eb6755b74b2b335ce9f57902b22ddf728"),
                             ("conversation_compression.py", "956696cc13b349074eef3812902dc487af1a207c328218246c63b00c8bb9255f")):
            self.assertEqual(hashlib.sha256((FIXTURE / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest(), digest)
        for path in ("cli.py", "agent/conversation_compression.py", "agent/conversation_loop.py", "agent/tool_executor.py"):
            compile((self.target / path).read_text(encoding="utf-8"), path, "exec")
        self.assertFalse(hasattr(self.engine, "MAYA_GOVERNANCE_CONTRACT"))

    def test_tool_progress_denial_escapes_without_warning(self):
        self.mandatory()
        self.agent._flush_messages_to_session_db.side_effect = self.denial
        with self.assertRaises(self.engine.MandatoryMiddlewareError) as caught:
            self.flush(self.agent, self.messages, stage="synthetic")
        self.assertIs(caught.exception, self.denial)
        self.logger.warning.assert_not_called()

    def test_actual_maya_persistence_denial_crosses_tool_progress_caller(self):
        self.mandatory()
        self.agent._flush_messages_to_session_db = self.host.agent._flush_messages_to_session_db
        with bind_request_identity("denied-operator"), self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.flush(self.agent, self.messages, stage="synthetic")
        self.host.assert_no_store_effects()
        self.logger.warning.assert_not_called()

    def test_session_start_denial_stops_credits_and_prompt_write(self):
        self.mandatory()
        restore = native_function(self.target / "agent/conversation_loop.py", "_restore_or_build_system_prompt", {"logger": self.logger})
        credits = Mock()
        with patch.dict(sys.modules, {"agent.credits_tracker": SimpleNamespace(seed_credits_at_session_start=credits)}), \
             patch.object(sys.modules["hermes_cli.plugins"], "invoke_hook", side_effect=self.denial):
            with self.assertRaises(self.engine.MandatoryMiddlewareError):
                restore(self.agent, None, None)
        credits.assert_not_called()
        self.db.update_system_prompt.assert_not_called()
        self.logger.warning.assert_not_called()

    def test_normal_session_start_hook_failure_continues(self):
        restore = native_function(self.target / "agent/conversation_loop.py", "_restore_or_build_system_prompt", {"logger": self.logger})
        credits = Mock()
        with patch.dict(sys.modules, {"agent.credits_tracker": SimpleNamespace(seed_credits_at_session_start=credits)}), \
             patch.object(sys.modules["hermes_cli.plugins"], "invoke_hook", side_effect=self.denial):
            restore(self.agent, None, None)
        credits.assert_called_once()
        self.db.update_system_prompt.assert_called_once()
        self.logger.warning.assert_called_once()

    def test_ordinary_tool_progress_failure_remains_best_effort(self):
        self.agent._flush_messages_to_session_db.side_effect = self.denial
        self.flush(self.agent, self.messages, stage="synthetic")
        self.logger.warning.assert_called_once()

    def test_compression_flush_denial_stops_rotation_and_releases_lock(self):
        self.mandatory()
        self.agent._flush_messages_to_session_db.side_effect = self.denial
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.compress(self.agent, self.messages, None)
        self.assertEqual(self.agent.session_id, "old-session")
        self.db.end_session.assert_not_called()
        self.db.create_session.assert_not_called()
        self.db.update_system_prompt.assert_not_called()
        self.db.release_compression_lock.assert_called_once_with("old-session", "synthetic-holder")
        self.logger.warning.assert_not_called()

    def test_ordinary_compression_flush_failure_retains_rotation(self):
        self.agent._flush_messages_to_session_db.side_effect = RuntimeError("synthetic storage failure")
        self.assertEqual(self.compress(self.agent, self.messages, None)[0], self.agent.context_compressor.compress.return_value)
        self.db.end_session.assert_called_once()
        self.db.create_session.assert_called_once()
        self.db.release_compression_lock.assert_called_once()

    def test_precompression_memory_denial_stops_summary_and_releases_lock(self):
        self.mandatory()
        self.agent._memory_manager = Mock()
        self.agent._memory_manager.on_pre_compress.side_effect = self.denial
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.compress(self.agent, self.messages, None)
        self.agent.context_compressor.compress.assert_not_called()
        self.db.end_session.assert_not_called()
        self.db.release_compression_lock.assert_called_once()

    def test_context_boundary_denial_stops_memory_and_event_callbacks(self):
        self.mandatory()
        self.agent.compression_in_place = True
        self.agent.context_compressor.on_session_start.side_effect = self.denial
        self.agent._memory_manager = Mock()
        self.agent.event_callback = Mock()
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.compress(self.agent, self.messages, None)
        self.agent._memory_manager.on_session_switch.assert_not_called()
        self.agent.event_callback.assert_not_called()
        self.db.release_compression_lock.assert_called_once()
        self.logger.debug.assert_not_called()

    def test_memory_boundary_denial_stops_event_callback(self):
        self.mandatory()
        self.agent.compression_in_place = True
        self.agent._memory_manager = Mock()
        self.agent._memory_manager.on_session_switch.side_effect = self.denial
        self.agent.event_callback = Mock()
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.compress(self.agent, self.messages, None)
        self.agent.event_callback.assert_not_called()
        self.db.release_compression_lock.assert_called_once()

    def test_cli_new_session_flush_denial_stops_rotation(self):
        self.mandatory()
        self.agent._flush_messages_to_session_db.side_effect = self.denial
        cli = SimpleNamespace(agent=self.agent, conversation_history=self.messages,
                              session_id="old-session", _session_db=self.db, _notify_session_boundary=Mock())
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.cli["new_session"](cli)
        self.assertEqual(cli.session_id, "old-session")
        self.db.end_session.assert_not_called()

    def test_cli_close_denial_does_not_update_session_id(self):
        self.mandatory()
        self.agent._session_messages = self.messages
        self.agent._persist_session = Mock(side_effect=self.denial)
        cli = SimpleNamespace(agent=self.agent, conversation_history=self.messages, session_id="cli-session")
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.cli["_persist_active_session_before_close"](cli)
        self.assertEqual(cli.session_id, "cli-session")
        self.logger.debug.assert_not_called()

    def test_cli_boundary_denial_escapes(self):
        self.mandatory()
        plugins = sys.modules["hermes_cli.plugins"]
        with patch.object(plugins, "invoke_hook", side_effect=self.denial):
            with self.assertRaises(self.engine.MandatoryMiddlewareError):
                self.cli["_notify_session_boundary"](SimpleNamespace(agent=self.agent), "on_session_finalize")

    def test_cli_manual_compression_denial_is_not_printed(self):
        self.mandatory()
        self.agent.compression_enabled = True
        self.agent._compress_context = Mock(side_effect=self.denial)
        self.agent._cached_system_prompt = "safe prompt"
        cli = SimpleNamespace(agent=self.agent, conversation_history=self.messages * 4,
                              _busy_command=lambda text: contextlib.nullcontext())
        modules = {"hermes_cli.partial_compress": SimpleNamespace(parse_partial_compress_args=lambda text: (False, 2, ""),
                       rejoin_compressed_head_and_tail=Mock(), split_history_for_partial_compress=Mock()),
                   "agent.model_metadata": SimpleNamespace(estimate_request_tokens_rough=lambda *a, **kw: 10),
                   "agent.manual_compression_feedback": SimpleNamespace(summarize_manual_compression=Mock())}
        with patch.dict(sys.modules, modules), patch("builtins.print") as output:
            with self.assertRaises(self.engine.MandatoryMiddlewareError):
                self.cli["_manual_compress"](cli)
        self.assertFalse(any("Compression failed" in str(call) for call in output.call_args_list))

    def test_loop_persistence_catch_stops_following_dispatch(self):
        self.mandatory()
        tree = ast.parse((self.target / "agent/conversation_loop.py").read_text(encoding="utf-8"))
        boundary = next(node for node in ast.walk(tree) if isinstance(node, ast.Try)
                        and any(isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
                                and isinstance(statement.value.func, ast.Attribute)
                                and statement.value.func.attr == "_flush_messages_to_session_db" for statement in node.body))
        # Execute the unchanged native catch body; surrounding loop is not qualified.
        scope = {"error": self.denial, "logger": self.logger, "agent": self.agent, "dispatch": Mock()}
        attempt = ast.Try(body=ast.parse("raise error").body, handlers=boundary.handlers, orelse=[], finalbody=[])
        module = ast.Module(body=[attempt, *ast.parse("dispatch()").body], type_ignores=[])
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            exec(compile(ast.fix_missing_locations(module), "native-loop-catch", "exec"), scope)
        scope["dispatch"].assert_not_called()
        self.logger.warning.assert_not_called()


if __name__ == "__main__":
    unittest.main()

"""Execute pinned native dispatch/preflight functions with inert dependencies."""

import ast
import hashlib
import json
import logging
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch

from tests import test_hermes_conversation_governance_patch as conversation_tests

FIXTURE = conversation_tests.FIXTURE
ROOT = conversation_tests.ROOT
import shutil
import subprocess
import unittest


class TestHermesToolPreflightGovernancePatch(unittest.TestCase):
    def setUp(self):
        harness = conversation_tests.TestHermesConversationGovernancePatch()
        self.addCleanup(harness.doCleanups)
        harness.setUp()
        self.engine = harness.middleware
        self.target = harness.target
        for name in ("tool_executor.py", "turn_context.py", "memory_manager.py"):
            shutil.copyfile(FIXTURE / name, self.target / "agent" / name)
        result = subprocess.run(
            ["git", "apply", "--whitespace=error", str(ROOT / "patches/hermes/0004-tool-and-preflight-denial-propagation.patch")],
            cwd=self.target, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.manager = SimpleNamespace(_middleware={})
        modules = {
            "hermes_cli.middleware": self.engine,
            "hermes_cli.plugins": SimpleNamespace(
                get_plugin_manager=lambda: self.manager,
                get_pre_tool_call_block_message=Mock(return_value=None),
                invoke_hook=Mock(return_value=[]),
            ),
            "agent.auxiliary_client": SimpleNamespace(set_runtime_main=Mock()),
        }
        patcher = patch.dict(sys.modules, modules)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.modules = modules
        self.scope = dict(
            Any=Any, Dict=Dict, List=List, Optional=Optional, dataclass=dataclass,
            json=json, logging=logging, threading=threading, time=time, uuid=uuid,
            logger=Mock(), MandatoryMiddlewareError=self.engine.MandatoryMiddlewareError,
            mandatory_middleware_enabled=self.engine.mandatory_middleware_enabled,
            _budget_for_agent=Mock(return_value=None),
            _get_cute_tool_message_impl=Mock(return_value="completed"),
        )
        self.tools = self.compile_functions("tool_executor.py", {
            "execute_tool_calls_sequential", "execute_tool_calls_concurrent",
            "_apply_tool_request_middleware_for_agent", "_run_agent_tool_execution_middleware",
        })
        self.preflight = self.compile_functions("turn_context.py", {
            "TurnContext", "build_turn_context", "_compression_made_progress",
        }, IterationBudget=lambda count: count, estimate_request_tokens_rough=lambda *args, **kw: 100)
        tree = ast.parse((self.target / "agent/memory_manager.py").read_text(encoding="utf-8"))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "MemoryManager")
        functions = [node for node in cls.body if isinstance(node, ast.FunctionDef)
                     and node.name in ("prefetch_all", "on_turn_start")]
        namespace = self.scope.copy()
        exec(compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])), "memory_manager.py", "exec"), namespace)
        self.memory_type = type("NativeMemoryFunctions", (), {node.name: namespace[node.name] for node in functions})

    def compile_functions(self, name, selected, **extra):
        tree = ast.parse((self.target / "agent" / name).read_text(encoding="utf-8"))
        nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in selected]
        # Preserve postponed annotations from the original module.
        nodes.insert(0, ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0))
        scope = dict(self.scope, **extra)
        exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), name, "exec"), scope)
        return scope

    def agent(self):
        agent = Mock()
        for name, value in {
            "_interrupt_requested": False, "_skip_mcp_refresh": True,
            "_compression_warning": None, "_user_turn_count": 0,
            "_memory_nudge_interval": 0, "valid_tool_names": [],
            "_cached_system_prompt": "synthetic system", "quiet_mode": True,
            "compression_enabled": False, "session_id": "synthetic-session",
            "provider": "openai", "model": "synthetic-model", "platform": "test",
            "api_mode": "chat_completions", "max_iterations": 3,
            "_stream_context_scrubber": None, "_stream_think_scrubber": None,
            "_memory_manager": None, "_context_engine_tool_names": [],
            "tool_start_callback": None, "tool_progress_callback": None,
            "verbose_logging": False,
        }.items():
            setattr(agent, name, value)
        agent._cleanup_dead_connections.return_value = False
        agent._should_emit_quiet_tool_messages.return_value = False
        agent._should_start_quiet_spinner.return_value = False
        agent._tool_guardrails.before_call.return_value = SimpleNamespace(allows_execution=True)
        return agent

    def build(self, agent):
        return self.preflight["build_turn_context"](
            agent, "synthetic prompt", None, None, "task", None, None,
            restore_or_build_system_prompt=Mock(), install_safe_stdio=Mock(),
            sanitize_surrogates=lambda value: value,
            summarize_user_message_for_log=lambda value: value,
            set_session_context=Mock(), set_current_write_origin=Mock(),
            ra=lambda: SimpleNamespace(_set_interrupt=Mock()),
        )

    def install_gates(self, tool_callback):
        llm = lambda **kw: kw["next_call"](kw["request"])
        for kind, callback in (("llm_execution", llm), ("tool_execution", tool_callback)):
            self.manager._middleware[kind] = [callback]
            self.engine.require_middleware(kind, callback)

    def test_pinned_fixture_hashes(self):
        expected = {
            "tool_executor.py": "80a138e9ff2b7abc617adc528535e0271b4efe26ee3006daeb82c9c681b5574f",
            "turn_context.py": "09902a61baef2e0ef113ea72d8dcbdbc0f64d275020926214c7f1db6e8c70f31",
            "memory_manager.py": "3083e30b9532ad2fdb135de1b2de3cb43466d41a119a4e7679316fcaa35318fb",
        }
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256((FIXTURE / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest(), digest)

    def test_memory_provider_failures_are_fatal_only_in_mandatory_mode(self):
        cases = []
        for method in ("prefetch_all", "on_turn_start"):
            provider = Mock()
            getattr(provider, "prefetch" if method == "prefetch_all" else method).side_effect = RuntimeError("synthetic-sensitive-error")
            memory = self.memory_type()
            memory._providers = [provider]
            memory._strip_skill_scaffolding = lambda value: value
            args = ("query",) if method == "prefetch_all" else (1, "query")
            getattr(memory, method)(*args)  # Legacy optional-memory behavior.
            cases.append((memory, method, args))
        self.engine.enable_mandatory_middleware()
        self.scope["logger"].reset_mock()
        for memory, method, args in cases:
            with self.assertRaises(self.engine.MandatoryMiddlewareError) as caught:
                getattr(memory, method)(*args)
            self.assertEqual(str(caught.exception), "mandatory_middleware.callback_failed")
        self.scope["logger"].debug.assert_not_called()

    def test_full_preflight_stops_after_memory_turn_failure(self):
        agent = self.agent()
        agent._memory_manager = Mock()
        agent._memory_manager.on_turn_start.side_effect = self.engine.MandatoryMiddlewareError("gate_missing")
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.build(agent)
        agent._memory_manager.prefetch_all.assert_not_called()

    def test_full_preflight_stops_on_prefetch_failure(self):
        agent = self.agent()
        agent._memory_manager = Mock()
        agent._memory_manager.prefetch_all.side_effect = self.engine.MandatoryMiddlewareError("callback_failed")
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.build(agent)

    def test_full_preflight_stops_on_hook_denial(self):
        agent = self.agent()
        agent._memory_manager = Mock()
        self.modules["hermes_cli.plugins"].invoke_hook.side_effect = self.engine.MandatoryMiddlewareError()
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.build(agent)
        agent._memory_manager.on_turn_start.assert_not_called()

    def test_full_preflight_compression_denial_prevents_later_hooks(self):
        agent = self.agent()
        agent.compression_enabled = True
        agent.context_compressor = SimpleNamespace(
            protect_first_n=0, protect_last_n=-1, last_prompt_tokens=0,
            threshold_tokens=50, context_length=100,
            should_compress=lambda count: True,
        )
        agent._compress_context.side_effect = self.engine.MandatoryMiddlewareError("gate_missing")
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.build(agent)
        self.modules["hermes_cli.plugins"].invoke_hook.assert_not_called()

    def test_normal_preflight_still_returns_memory_context(self):
        agent = self.agent()
        agent._memory_manager = Mock()
        agent._memory_manager.prefetch_all.return_value = "synthetic business context"
        self.assertEqual(self.build(agent).ext_prefetch_cache, "synthetic business context")

    def test_full_serial_memory_dispatch_denial_stops_batch_without_result(self):
        def deny(**kw):
            raise RuntimeError("synthetic-sensitive-policy-error")
        self.install_gates(deny)
        agent = self.agent()
        agent._memory_manager = Mock()
        agent._memory_manager.has_tool.return_value = True
        call = SimpleNamespace(id="call", function=SimpleNamespace(name="maya_memory_search", arguments='{"query":"test"}'))
        messages = []
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.tools["execute_tool_calls_sequential"](agent, SimpleNamespace(tool_calls=[call, call]), messages, "task")
        agent._memory_manager.handle_tool_call.assert_not_called()
        self.assertEqual(messages, [])
        agent._touch_activity.assert_called_once()
        self.scope["logger"].error.assert_not_called()

    def test_context_engine_denial_is_not_a_tool_result(self):
        self.install_gates(lambda **kw: (_ for _ in ()).throw(RuntimeError("synthetic policy failure")))
        agent = self.agent()
        agent._context_engine_tool_names = ["lcm_grep"]
        call = SimpleNamespace(id="call", function=SimpleNamespace(name="lcm_grep", arguments="{}"))
        messages = []
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.tools["execute_tool_calls_sequential"](agent, SimpleNamespace(tool_calls=[call]), messages, "task")
        agent.context_compressor.handle_tool_call.assert_not_called()
        self.assertEqual(messages, [])
        self.scope["logger"].error.assert_not_called()

    def test_regular_tool_denial_propagates_in_quiet_and_verbose_paths(self):
        for quiet in (True, False):
            with self.subTest(quiet=quiet):
                agent = self.agent()
                agent.quiet_mode = quiet
                agent.tool_progress_mode = "off"
                runtime = SimpleNamespace(handle_function_call=Mock(side_effect=self.engine.MandatoryMiddlewareError("gate_missing")))
                self.tools["_ra"] = lambda: runtime
                call = SimpleNamespace(id="call", function=SimpleNamespace(name="read_file", arguments="{}"))
                messages = []
                with self.assertRaises(self.engine.MandatoryMiddlewareError):
                    self.tools["execute_tool_calls_sequential"](agent, SimpleNamespace(tool_calls=[call, call]), messages, "task")
                runtime.handle_function_call.assert_called_once()
                self.assertEqual(messages, [])
        self.scope["logger"].error.assert_not_called()

    def test_mandatory_concurrent_entry_uses_existing_serial_dispatch(self):
        self.engine.enable_mandatory_middleware()
        serial = Mock()
        self.tools["execute_tool_calls_sequential"] = serial
        args = (object(), object(), [], "task", 2)
        self.tools["execute_tool_calls_concurrent"](*args)
        serial.assert_called_once_with(*args)

    def test_tool_request_wrapper_does_not_swallow_typed_denial(self):
        with patch.object(self.engine, "apply_tool_request_middleware", side_effect=self.engine.MandatoryMiddlewareError()):
            with self.assertRaises(self.engine.MandatoryMiddlewareError):
                self.tools["_apply_tool_request_middleware_for_agent"](
                    self.agent(), function_name="read_file", function_args={}, effective_task_id="task", tool_call_id="call",
                )


if __name__ == "__main__":
    unittest.main()

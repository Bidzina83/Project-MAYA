"""Inert entry/sequence fixtures. No Hermes import, SDK or native execution."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1] / "src/project_maya/windows_runtime"
spec = importlib.util.spec_from_file_location("maya_construction_probe", SOURCE / "hermes_construction_check.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ConstructionTests(unittest.TestCase):
    def setUp(self):
        # Test doubles only; production resolves the real verified SDK/engine.
        class FixtureClient:
            def __init__(self):
                self._closed = False
                self.closure_queries = 0

            def is_closed(self):
                self.closure_queries += 1
                return self._closed

        self.sdk = FixtureClient
        self.engine = type("FixtureCompressor", (), {})
        self.addCleanup(patch.stopall)
        patch.dict(probe.sys.modules, {
            "openai": SimpleNamespace(OpenAI=self.sdk),
            "agent.context_compressor": SimpleNamespace(ContextCompressor=self.engine),
        }).start()

    def candidate(self):
        client = self.sdk()
        compressor = self.engine()
        compressor.context_length = 131072
        agent = SimpleNamespace(client=client, tools=[], valid_tool_names=set(),
            _memory_manager=None, _memory_store=None, _memory_enabled=False,
            _user_profile_enabled=False, context_compressor=compressor,
            compression_enabled=False, _environment_probe=False, _config_context_length=131072,
            _session_db=None, _checkpoint_mgr=SimpleNamespace(enabled=False), session_api_calls=0)
        agent.shutdown_memory_provider = Mock()
        def close():
            client._closed = True
            agent.client = None
        agent.close = Mock(side_effect=close)
        return agent, client

    def run_candidate(self, agent, report):
        factory = Mock(return_value=agent)
        with patch.object(probe, "save"):
            probe.construct_and_close(factory, "a" * 32, report)
        return factory

    def test_non_windows_never_imports_payload(self):
        with patch.object(probe.sys, "platform", "not-windows"), patch.object(probe.importlib, "import_module") as imported:
            self.assertEqual(probe.main(), 2)
            imported.assert_not_called()

    def test_real_contract_arguments_and_shutdown_sequence(self):
        agent, client = self.candidate()
        report = {}
        factory = self.run_candidate(agent, report)
        kwargs = factory.call_args.kwargs
        self.assertEqual(kwargs["enabled_toolsets"], [])
        self.assertEqual(kwargs["base_url"], probe.URL)
        self.assertEqual(kwargs["api_key"], probe.PLACEHOLDER)
        self.assertEqual(kwargs["session_id"], "maya-construction-" + "a" * 32)
        self.assertTrue(kwargs["skip_memory"])
        self.assertIsNone(kwargs["session_db"])
        agent.shutdown_memory_provider.assert_called_once_with([])
        agent.close.assert_called_once_with()
        self.assertTrue(report["constructor_completed"])
        self.assertTrue(report["client_closed"])
        self.assertEqual(client.closure_queries, 1)
        self.assertTrue(client.is_closed())

    def test_constructor_failure_never_claims_completion(self):
        report = {"constructor_completed": False}
        with patch.object(probe, "save"), self.assertRaises(RuntimeError):
            probe.construct_and_close(Mock(side_effect=RuntimeError("fixture")), "a" * 32, report)
        self.assertFalse(report["constructor_completed"])
        self.assertEqual(report["operation_failure_stage"], "constructor_entry")
        self.assertNotIn("close_returned", report)

    def test_failed_postcondition_still_closes(self):
        for field, value in (("tools", [{}]), ("_memory_manager", object()),
                             ("_environment_probe", True), ("session_api_calls", 1)):
            with self.subTest(field=field):
                agent, _ = self.candidate()
                setattr(agent, field, value)
                with patch.object(probe, "save"), self.assertRaises(ValueError):
                    probe.construct_and_close(Mock(return_value=agent), "a" * 32, {})
                agent.close.assert_called_once_with()

    def test_context_shutdown_failure_still_closes(self):
        agent, _ = self.candidate()
        agent.shutdown_memory_provider.side_effect = RuntimeError("fixture")
        report = {}
        with patch.object(probe, "save"), self.assertRaises(RuntimeError):
            probe.construct_and_close(Mock(return_value=agent), "a" * 32, report)
        agent.close.assert_called_once_with()
        self.assertEqual(report["operation_failure_stage"], "context_shutdown_entry")
        self.assertNotIn("context_shutdown_returned", report)

    def test_suppressed_close_failure_is_not_success(self):
        agent, _ = self.candidate()
        agent.close.side_effect = lambda: setattr(agent, "client", None)
        with patch.object(probe, "save"), self.assertRaisesRegex(ValueError, "shutdown_postconditions"):
            probe.construct_and_close(Mock(return_value=agent), "a" * 32, {})

    def test_closed_sdk_client_still_attached_is_not_success(self):
        agent, client = self.candidate()
        agent.close.side_effect = lambda: setattr(client, "_closed", True)
        with patch.object(probe, "save"), self.assertRaisesRegex(ValueError, "shutdown_postconditions"):
            probe.construct_and_close(Mock(return_value=agent), "a" * 32, {})

    def test_closure_query_failure_is_not_success(self):
        agent, client = self.candidate()
        client.is_closed = Mock(side_effect=OSError("fixture"))
        report = {"client_closed": False}
        with patch.object(probe, "save"), self.assertRaises(OSError):
            probe.construct_and_close(Mock(return_value=agent), "a" * 32, report)
        self.assertFalse(report["client_closed"])
        agent.close.assert_called_once_with()

    def test_boolean_property_cannot_substitute_for_sdk_method(self):
        agent, client = self.candidate()
        client.is_closed = True
        with patch.object(probe, "save"), self.assertRaises(TypeError):
            probe.construct_and_close(Mock(return_value=agent), "a" * 32, {})

    def test_non_boolean_closure_answer_cannot_pass(self):
        for value in (1, "True", None):
            with self.subTest(value=value):
                agent, client = self.candidate()
                client.is_closed = Mock(return_value=value)
                with patch.object(probe, "save"), self.assertRaisesRegex(ValueError, "shutdown_postconditions"):
                    probe.construct_and_close(Mock(return_value=agent), "a" * 32, {})

    def test_close_is_attempted_even_if_stage_write_fails(self):
        agent, _ = self.candidate()
        def save(report):
            if report["stage"] == "close_entry":
                raise OSError("fixture")
        with patch.object(probe, "save", side_effect=save), self.assertRaises(OSError):
            probe.construct_and_close(Mock(return_value=agent), "a" * 32, {})
        agent.close.assert_called_once_with()

    def test_oversized_report_never_writes(self):
        with patch("builtins.open") as opened, self.assertRaises(ValueError):
            probe.save({"x": "x" * probe.LIMIT})
        opened.assert_not_called()

    def test_effective_config_checks_leaves_not_unrelated_defaults(self):
        expected = {"tools": {"tool_search": {"enabled": "off"}}, "agent": {"environment_probe": False}}
        actual = {"tools": {"tool_search": {"enabled": "off", "threshold_pct": 10}},
                  "agent": {"environment_probe": False, "max_turns": 90}}
        self.assertTrue(probe.config_matches(expected, actual))
        actual["tools"]["tool_search"]["enabled"] = "auto"
        self.assertFalse(probe.config_matches(expected, actual))
        self.assertFalse(probe.config_matches({"a": False}, {"a": 0}))
        self.assertFalse(probe.config_matches(expected, {}))

    def test_no_conversation_fallback_or_broader_environment(self):
        text = (SOURCE / "hermes_construction_check.py").read_text()
        for forbidden in (".run_conversation(", ".chat(", "subprocess", "__new__(", "load_dotenv(", "site.addsitedir"):
            self.assertNotIn(forbidden, text)
        self.assertIn("time.monotonic() + 22", text)
        self.assertIn("get_managed_dir() is not None", text)
        self.assertEqual(probe.CONFIG["model"]["context_length"], 131072)


if __name__ == "__main__":
    unittest.main()

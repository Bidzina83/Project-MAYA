"""Inert import-probe checks; never import Hermes or a native dependency."""
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/project_maya/windows_runtime"
spec = importlib.util.spec_from_file_location("maya_import_probe", SOURCE / "hermes_import_check.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class HermesImportTests(unittest.TestCase):
    def test_non_windows_does_not_attempt_payload_import(self):
        with patch.object(probe.sys, "platform", "not-windows"), patch.object(probe.importlib, "import_module") as imported:
            self.assertEqual(probe.main(), 2)
            imported.assert_not_called()

    def test_output_limit_counts_bytes_without_retaining_text(self):
        capture = probe.Capture()
        self.assertEqual(capture.write("abc"), 3)
        self.assertEqual(capture.count, 3)
        with self.assertRaisesRegex(RuntimeError, "import_output_limit"):
            capture.write("x" * probe.LIMIT)
        self.assertTrue(capture.overflow)
        self.assertFalse(hasattr(capture, "getvalue"))

    def test_report_limit_prevents_file_write(self):
        with patch("builtins.open") as opened:
            with self.assertRaisesRegex(ValueError, "import_report_size"):
                probe.save({"x": "y" * probe.LIMIT})
            opened.assert_not_called()

    def test_actual_class_identity_not_a_callable_or_wrong_origin(self):
        expected = Path("runtime/hermes/run_agent.py")
        factory = type("AIAgent", (), {"__module__": "run_agent"})
        self.assertTrue(probe.class_matches(factory, expected, expected))
        self.assertFalse(probe.class_matches(lambda: None, expected, expected))
        self.assertFalse(probe.class_matches(factory, Path("elsewhere.py"), expected))
        factory.__module__ = "fake_runtime"
        self.assertFalse(probe.class_matches(factory, expected, expected))

    def test_profile_has_no_agent_construction_or_execution_call(self):
        text = (SOURCE / "hermes_import_check.py").read_text()
        for forbidden in ("factory(", ".chat(", ".run_conversation(", "subprocess", "site.addsitedir", "load_dotenv("):
            self.assertNotIn(forbidden, text)
        self.assertIn('importlib.import_module("run_agent")', text)
        self.assertIn('time.monotonic() + 22', text)
        self.assertIn('"HERMES_DISABLE_LAZY_INSTALLS"', text)
        self.assertIn('"pywin32_system32", "win32"', text)


if __name__ == "__main__":
    unittest.main()

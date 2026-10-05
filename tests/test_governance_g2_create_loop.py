"""Bind the blocked source-loop diagnostic to its unchanged reviewed parent."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestCreateLoopInputs(unittest.TestCase):
    def test_exact_blocked_inputs(self):
        data = json.loads((ROOT / "docs/architecture/governance-g2-create-loop.json").read_text())
        self.assertIs(data["production_qualified"], False)
        self.assertEqual(data["acceptance"], "blocked_lazy_session_recreation")
        self.assertEqual(data["expected_native_tests"], 5)
        for key, path in (
            ("parent_sha256", "docs/architecture/governance-g2-caller-qualification.json"),
            ("tests_sha256", "tests/hermes_g2_create_loop_native.py"),
        ):
            self.assertEqual(data[key], hashlib.sha256((ROOT / path).read_bytes()).hexdigest())

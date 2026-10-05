"""Restart qualification input checks; no native runtime acceptance."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    import verify_governance_g2_restart as candidate


class TestRestartInputs(unittest.TestCase):
    def test_separate_source_qualification(self):
        data = candidate.contract()
        self.assertIs(data["production_qualified"], False)
        self.assertEqual(data["expected_native_tests"], 4)
        self.assertEqual(set(data["fixture_sha256"]), candidate.FIXTURES)

    def test_tampering_rejected(self):
        data = candidate.contract()
        for key, value in (("schema_version", True), ("expected_native_tests", True),
                           ("production_qualified", True), ("acceptance", "accepted"),
                           ("qualification", "production"), ("parent_inputs_sha256", "0" * 64),
                           ("test_sha256", "0" * 64), ("fixture_sha256", {}),
                           ("native_inventory_sha256", "not-a-hash"), ("host_inventory_sha256", None)):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "input.json"
                path.write_text(json.dumps(data | {key: value}), encoding="utf-8")
                with patch.object(candidate, "INPUTS", path), self.assertRaises(ValueError):
                    candidate.contract()

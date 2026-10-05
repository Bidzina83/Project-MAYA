"""Final-profile qualification provenance, not production readiness."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    import verify_governance_g2_final_create as candidate


class TestFinalCreateInputs(unittest.TestCase):
    def test_frozen_qualification_inputs(self):
        data = candidate.contract()
        self.assertIs(data["production_qualified"], False)
        self.assertEqual(data["expected_native_tests"], 80)

    def test_tampering_denies(self):
        data = candidate.contract()
        for key, value in (("schema_version", True), ("production_qualified", True),
                           ("acceptance", "accepted"), ("expected_native_tests", True),
                           ("qualification", "production"), ("fixture_sha256", {}),
                           ("test_sha256", "0" * 64), ("parent_inputs_sha256", "0" * 64)):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "inputs.json"
                path.write_text(json.dumps(data | {key: value}), encoding="utf-8")
                with patch.object(candidate, "INPUTS", path), self.assertRaises(ValueError):
                    candidate.contract()

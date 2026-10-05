"""Recognition overlay provenance checks, not runtime acceptance."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    import prepare_governance_g2_recognition as candidate


class TestRecognitionInputs(unittest.TestCase):
    def test_reviewed_source_only_contract(self):
        data = candidate.contract()
        self.assertIs(data["production_qualified"], False)
        self.assertEqual(data["expected_native_tests"], 24)
        self.assertEqual(data["expected_ordinary_tests"], 3)
        self.assertEqual(set(data["effective_sha256"]), candidate.PATHS)

    def test_tampering_rejected(self):
        data = candidate.contract()
        for key, value in (("schema_version", True), ("expected_native_tests", True),
                           ("expected_ordinary_tests", True), ("design_sha256", "0" * 64),
                           ("production_qualified", True), ("acceptance", "accepted"),
                           ("parent_sha256", "0" * 64), ("loop_inputs_sha256", "0" * 64),
                           ("patch_sha256", "0" * 64), ("effective_sha256", {}), ("test_sha256", {})):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "inputs.json"
                path.write_text(json.dumps(data | {key: value}))
                with patch.object(candidate, "INPUTS", path):
                    with self.assertRaises(ValueError):
                        candidate.contract()

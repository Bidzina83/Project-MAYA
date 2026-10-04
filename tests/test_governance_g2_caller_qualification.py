"""Qualification-input provenance, not native acceptance."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    import prepare_governance_g2_caller_qualification as candidate


class TestQualificationInputs(unittest.TestCase):
    def test_exact_parent_is_preserved(self):
        data = candidate.qualification_contract()
        self.assertFalse(data["production_qualified"])
        self.assertEqual(data["expected_native_tests"], 12)

    def test_tampering_does_not_qualify_runtime(self):
        data = candidate.qualification_contract()
        for key, value in (("parent_sha256", "0" * 64), ("tests_sha256", "0" * 64),
                           ("restart_helper_sha256", "0" * 64), ("production_qualified", True),
                           ("acceptance", "accepted"), ("schema_version", True), ("expected_native_tests", True)):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "inputs.json"
                path.write_text(json.dumps(data | {key: value}))
                with patch.object(candidate, "INPUTS", path):
                    with self.assertRaises(ValueError):
                        candidate.qualification_contract()

"""Reader provenance controls, not production qualification."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    import prepare_governance_g2_reader as candidate


class TestReaderInputs(unittest.TestCase):
    def test_exact_inputs_preserve_parent(self):
        data = candidate.reader_contract()
        self.assertFalse(data["production_qualified"])
        self.assertEqual(data["expected_native_tests"], 22)
        candidate.create_contract()

    def test_tampered_inputs_denied(self):
        data = candidate.reader_contract()
        for key, value in (("maya_source_sha256", {}), ("patch_sha256", "0" * 64),
                           ("parent_contract_sha256", "0" * 64), ("production_qualified", True),
                           ("acceptance", "accepted"), ("expected_native_tests", True),
                           ("qualification", "production")):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "inputs.json"
                path.write_text(json.dumps(data | {key: value}))
                with patch.object(candidate, "INPUTS", path):
                    with self.assertRaisesRegex(ValueError, "g2.reader_contract_invalid"):
                        candidate.reader_contract()

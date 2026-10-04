"""Pinned create overlay inputs; not product/runtime qualification."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    import prepare_governance_g2_create as candidate


class TestCreateOverlayInputs(unittest.TestCase):
    def test_exact_create_inputs_preserve_g1_and_production_block(self):
        data = candidate.create_contract()
        self.assertFalse(data["production_qualified"])
        self.assertEqual(data["acceptance"], "pending_review")
        self.assertEqual(data["expected_native_tests"], 17)
        self.assertEqual(candidate.patch_paths(candidate.PATCH.read_bytes()), {"gateway/session.py"})
        candidate.full_caller_contract()

    def test_tampered_host_patch_parent_or_qualification_denies(self):
        data = candidate.create_contract()
        for key, value in (("maya_source_sha256", {}), ("patch_sha256", "0" * 64),
                           ("parent_contract_sha256", "0" * 64), ("production_qualified", True),
                           ("acceptance", "accepted"), ("expected_native_tests", True),
                           ("qualification", "production")):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "inputs.json"
                path.write_text(json.dumps(data | {key: value}))
                with patch.object(candidate, "CREATE_INPUTS", path):
                    with self.assertRaisesRegex(ValueError, "g2.create_contract_invalid"):
                        candidate.create_contract()

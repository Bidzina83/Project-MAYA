"""Reset preparation contract checks; no runtime acceptance implied."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    spec = importlib.util.spec_from_file_location("reset_preparation", ROOT / "scripts/prepare_governance_g2_reset.py")
    preparation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preparation)
finally:
    sys.path.pop(0)


class TestResetPreparation(unittest.TestCase):
    def test_current_hash_contract_is_valid_and_unqualified(self):
        data = preparation.contract()
        self.assertFalse(data["production_qualified"])
        self.assertEqual(data["acceptance"], "pending_review")

    def test_changed_contract_inputs_are_rejected(self):
        original = preparation.contract()
        for field, value in (("schema_version", True), ("production_qualified", True),
                ("acceptance", "accepted"), ("qualification", "production"),
                ("parent_sha256", "changed"), ("patch_sha256", "changed"),
                ("test_sha256", "changed"), ("effective_sha256", {})):
            with self.subTest(field=field):
                changed = copy.deepcopy(original)
                changed[field] = value
                with patch.object(preparation.json, "loads", return_value=changed):
                    with self.assertRaises(ValueError):
                        preparation.contract()

    def test_unverified_parent_cannot_be_copied(self):
        with patch.object(preparation, "verify_parent", side_effect=ValueError("invalid")), \
                patch.object(preparation.shutil, "copytree") as copy_tree:
            with self.assertRaises(ValueError):
                preparation.prepare(ROOT, ROOT / ".codex-build/reset-never-created")
            copy_tree.assert_not_called()

    def test_existing_output_is_not_overwritten(self):
        with patch.object(preparation, "verify_parent"), \
                patch.object(preparation.shutil, "copytree") as copy_tree:
            with self.assertRaises(ValueError):
                preparation.prepare(ROOT / ".codex-build/reset-parent", ROOT)
            copy_tree.assert_not_called()

    def test_nested_output_is_rejected(self):
        with patch.object(preparation, "verify_parent"), \
                patch.object(preparation.shutil, "copytree") as copy_tree:
            with self.assertRaises(ValueError):
                preparation.prepare(ROOT, ROOT / ".codex-build/reset-never-created")
            copy_tree.assert_not_called()

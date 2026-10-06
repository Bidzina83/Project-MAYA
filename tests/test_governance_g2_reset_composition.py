"""Composition input verification, not native/runtime acceptance."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    spec = importlib.util.spec_from_file_location("reset_composition_preparation", ROOT / "scripts/prepare_governance_g2_reset_composition.py")
    preparation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preparation)
finally:
    sys.path.pop(0)


class TestResetComposition(unittest.TestCase):
    def test_current_inputs_remain_unqualified(self):
        self.assertFalse(preparation.contract()["production_qualified"])

    def test_modified_security_fields_are_rejected(self):
        original = preparation.contract()
        for field, value in (("schema_version", True), ("production_qualified", True),
                ("acceptance", "accepted"), ("patch_sha256", "changed"),
                ("parent_sha256", "changed"), ("test_sha256", "changed"), ("effective_sha256", {})):
            with self.subTest(field=field), patch.object(preparation.json, "loads", return_value=dict(original, **{field: value})):
                with self.assertRaises(ValueError):
                    preparation.contract()

    def test_unverified_parent_is_not_copied(self):
        with patch.object(preparation, "verify_parent", side_effect=ValueError("invalid")), patch.object(preparation.shutil, "copytree") as copy:
            with self.assertRaises(ValueError):
                preparation.prepare(ROOT, ROOT, ROOT / ".codex-build/not-created")
            copy.assert_not_called()

    def test_existing_output_is_not_overwritten(self):
        with patch.object(preparation, "verify_parent"), patch.object(preparation.shutil, "copytree") as copy:
            with self.assertRaises(ValueError):
                preparation.prepare(ROOT / ".codex-build/parent", ROOT / ".codex-build/base", ROOT)
            copy.assert_not_called()

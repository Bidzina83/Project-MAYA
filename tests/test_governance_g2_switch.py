"""Switch candidate provenance checks, not native runtime acceptance."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    spec = importlib.util.spec_from_file_location("switch_preparation", ROOT / "scripts/prepare_governance_g2_switch.py")
    preparation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preparation)
finally:
    sys.path.pop(0)


class TestSwitchPreparation(unittest.TestCase):
    def test_current_contract_is_hash_pinned_and_unqualified(self):
        data = preparation.contract()
        self.assertFalse(data["production_qualified"])
        self.assertEqual(data["qualification"], "source_switch_atomic_only")
        self.assertEqual(data["acceptance"], "pending_review")

    def test_changed_inputs_or_test_count_are_rejected(self):
        original = preparation.contract()
        for field, value in (("schema_version", True), ("production_qualified", True),
                ("acceptance", "accepted"), ("qualification", "production"),
                ("parent_sha256", "changed"), ("patch_sha256", "changed"),
                ("test_sha256", "changed"), ("effective_sha256", {}),
                ("fixture_sha256", {}), ("expected_native_tests", True),
                ("expected_native_tests", 0)):
            with self.subTest(field=field):
                changed = copy.deepcopy(original)
                changed[field] = value
                with patch.object(preparation.json, "loads", return_value=changed):
                    with self.assertRaises(ValueError):
                        preparation.contract()

    def test_invalid_parent_is_never_copied(self):
        with patch.object(preparation, "verify_parent", side_effect=ValueError("invalid")), \
                patch.object(preparation.shutil, "copytree") as copy_tree:
            with self.assertRaises(ValueError):
                preparation.prepare(ROOT / ".codex-build/switch-never-created")
            copy_tree.assert_not_called()

    def test_existing_or_nested_output_is_never_overwritten(self):
        for path in (ROOT, preparation.PARENT_STAGE / "nested"):
            with self.subTest(path=path), patch.object(preparation, "verify_parent"), \
                    patch.object(preparation.shutil, "copytree") as copy_tree:
                with self.assertRaises(ValueError):
                    preparation.prepare(path)
                copy_tree.assert_not_called()

    def test_changed_manifest_blocks_stage(self):
        with patch.object(preparation, "verify_parent"), \
                patch.object(Path, "read_text", return_value="{}"):
            with self.assertRaises(ValueError):
                preparation.verify_stage(ROOT / ".codex-build/nonexistent-switch")

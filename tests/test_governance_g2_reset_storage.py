"""Reset authority evidence does not authorize reset or production activation."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    spec = importlib.util.spec_from_file_location("reset_storage_verifier", ROOT / "scripts/verify_governance_g2_reset_storage.py")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
finally:
    sys.path.pop(0)


class TestResetStorage(unittest.TestCase):
    def test_inputs_remain_unqualified(self):
        self.assertFalse(verifier.contract()["production_qualified"])

    def test_modified_inputs_rejected(self):
        data = verifier.contract()
        for field, value in (("schema_version", True), ("production_qualified", True),
                             ("acceptance", "accepted"), ("expected_native_tests", True),
                             ("qualification", "production"), ("parent_inputs_sha256", "changed"),
                             ("test_sha256", "changed"), ("fixture_sha256", {}),
                             ("host_inventory_sha256", "changed")):
            with self.subTest(field=field), patch.object(verifier.json, "loads", return_value=dict(data, **{field: value})):
                with self.assertRaises(ValueError):
                    verifier.contract()

    def test_parent_verification_precedes_inventory_checks(self):
        with patch.object(verifier, "verify_parent", side_effect=ValueError("invalid")), patch.object(verifier, "inventory_digest") as inventory:
            with self.assertRaises(ValueError):
                verifier.verify_stage(ROOT)
            inventory.assert_not_called()

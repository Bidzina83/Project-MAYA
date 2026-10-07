"""Frozen crash diagnostic contract, not reset acceptance."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    spec = importlib.util.spec_from_file_location("reset_crash_verifier", ROOT / "scripts/verify_governance_g2_reset_crash.py")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
finally:
    sys.path.pop(0)


class TestResetCrash(unittest.TestCase):
    def test_inputs_remain_unqualified(self):
        self.assertFalse(verifier.contract()["production_qualified"])

    def test_modified_inputs_rejected(self):
        data = verifier.contract()
        for field, value in (("schema_version", True), ("production_qualified", True),
                             ("acceptance", "accepted"), ("expected_native_tests", True),
                             ("parent_inputs_sha256", "changed"), ("test_sha256", "changed"),
                             ("fixture_sha256", {}), ("native_inventory_sha256", "changed")):
            with self.subTest(field=field), patch.object(verifier.json, "loads", return_value=dict(data, **{field: value})):
                with self.assertRaises(ValueError):
                    verifier.contract()

    def test_parent_verification_precedes_worker_checks(self):
        with patch.object(verifier, "verify_parent", side_effect=ValueError("invalid")), patch.object(verifier, "verify_worker_stage") as worker:
            with self.assertRaises(ValueError):
                verifier.verify_stage(ROOT)
            worker.assert_not_called()

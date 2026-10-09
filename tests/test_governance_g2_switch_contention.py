"""Contention inputs preserve Patch 37 and the closed production gate."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    spec = importlib.util.spec_from_file_location("switch_contention_verifier", ROOT / "scripts/verify_governance_g2_switch_contention.py")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
finally:
    sys.path.pop(0)


class TestSwitchContention(unittest.TestCase):
    def test_inputs_remain_pinned_and_unqualified(self):
        data = verifier.contract()
        self.assertIs(data["production_qualified"], False)
        self.assertEqual(data["cases"], list(verifier.CASES))
        self.assertEqual(data["expected_native_tests"], 8)

    def test_changed_inputs_rejected(self):
        data = verifier.contract()
        for field, value in (("schema_version", True), ("production_qualified", True),
                ("acceptance", "accepted"), ("qualification", "production"),
                ("expected_native_tests", True), ("cases", []),
                ("parent_inputs_sha256", "changed"), ("test_sha256", "changed"),
                ("fixture_sha256", {}), ("native_inventory_sha256", "changed"),
                ("host_inventory_sha256", "changed")):
            with self.subTest(field=field), patch.object(verifier.json, "loads", return_value=dict(data, **{field: value})):
                with self.assertRaises(ValueError):
                    verifier.contract()

    def test_parent_verification_precedes_worker_checks(self):
        with patch.object(verifier, "verify_parent", side_effect=ValueError("invalid")), \
                patch.object(verifier, "verify_worker_stage") as worker:
            with self.assertRaises(ValueError):
                verifier.verify_stage(ROOT)
            worker.assert_not_called()

    def test_changed_effective_inventory_rejected(self):
        data = verifier.contract()
        with patch.object(verifier, "verify_parent_worker", return_value=(ROOT, ROOT)), \
                patch.object(verifier, "inventory_digest", return_value="0" * 64):
            self.assertNotEqual(data["native_inventory_sha256"], "0" * 64)
            with self.assertRaises(ValueError):
                verifier.verify_worker_stage(ROOT)

"""Design consistency tests, never substitute for native enforcement tests."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    import validate_governance_g2_caller_contract as contract


class TestCallerDesign(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(contract.INPUTS.read_text())

    def test_design_preserves_parent_and_blocks_production(self):
        self.assertEqual(contract.validate(self.data), self.data)

    def test_no_legacy_or_pending_state_can_be_selectable(self):
        for state in self.data["blocked_states"]:
            with self.subTest(state=state):
                data = deepcopy(self.data)
                data["selectable_states"].append(state)
                with self.assertRaises(ValueError):
                    contract.validate(data)

    def test_tampered_contract_is_rejected(self):
        for key, value in (("runtime_enforced", True), ("production_qualified", True),
                           ("schema_version", True), ("status", "accepted"),
                           ("parent_reader_manifest_sha256", "0" * 64),
                           ("required_binding", []), ("required_cases", []),
                           ("invariants", {}), ("transitions", {}), ("scope", "arbitrary_async_caller")):
            with self.subTest(key=key):
                data = deepcopy(self.data)
                data[key] = value
                with self.assertRaises(ValueError):
                    contract.validate(data)

    def test_each_invariant_is_required(self):
        for key in self.data["invariants"]:
            with self.subTest(key=key):
                data = deepcopy(self.data)
                data["invariants"][key] = False
                with self.assertRaises(ValueError):
                    contract.validate(data)

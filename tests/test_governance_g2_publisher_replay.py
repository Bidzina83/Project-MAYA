"""Portable provenance checks for corrected-publisher Step 4 replay."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
try:
    import verify_governance_g2_publisher_replay as verifier
finally:
    sys.path.pop(0)


class TestPublisherReplay(unittest.TestCase):
    def test_unqualified_contract(self):
        data = verifier.contract()
        self.assertFalse(data['production_qualified'])
        self.assertEqual(sum(data['expected_tests'].values()), 33)

    def test_modified_contract_is_rejected(self):
        data = verifier.contract()
        for field, value in (('schema_version', True), ('production_qualified', True),
                             ('acceptance', 'accepted'), ('qualification', 'production'),
                             ('parent_sha256', 'changed'), ('test_sha256', {}),
                             ('fixture_sha256', {}), ('expected_tests', {})):
            with self.subTest(field=field), patch.object(verifier.json, 'loads', return_value=dict(data, **{field: value})):
                with self.assertRaises(ValueError):
                    verifier.contract()

    def test_contract_is_verified_before_parent(self):
        with patch.object(verifier, 'contract', side_effect=ValueError('invalid')), patch.object(verifier, 'verify_parent') as parent:
            with self.assertRaises(ValueError):
                verifier.verify_stage(ROOT)
            parent.assert_not_called()

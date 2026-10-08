"""Portable provenance checks for the separately versioned host-only correction."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
try:
    spec = importlib.util.spec_from_file_location('publisher_verifier', ROOT / 'scripts/prepare_governance_g2_publisher.py')
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
finally:
    sys.path.pop(0)


class TestPublisherCandidate(unittest.TestCase):
    def test_host_only_unqualified_contract(self):
        data = verifier.contract()
        self.assertFalse(data['production_qualified'])
        self.assertEqual(sum(data['expected_tests'].values()), 167)
        self.assertEqual(set(data['effective_sha256']), {verifier.PATH})

    def test_modified_contract_is_rejected(self):
        data = verifier.contract()
        for field, value in (('schema_version', True), ('production_qualified', True),
                             ('acceptance', 'accepted'), ('qualification', 'production'),
                             ('parent_sha256', 'changed'), ('patch_sha256', 'changed'),
                             ('effective_sha256', {}), ('test_sha256', {}),
                             ('fixture_sha256', {}), ('expected_tests', {})):
            with self.subTest(field=field), patch.object(verifier.json, 'loads', return_value=dict(data, **{field: value})):
                with self.assertRaises(ValueError):
                    verifier.contract()

    def test_parent_is_verified_before_candidate(self):
        with patch.object(verifier, 'verify_parent', side_effect=ValueError('invalid')), patch.object(verifier, 'verify_worker_stage') as candidate:
            with self.assertRaises(ValueError):
                verifier.verify_stage(ROOT)
            candidate.assert_not_called()

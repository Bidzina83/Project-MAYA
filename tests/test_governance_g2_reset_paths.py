"""Portable provenance checks for reset path/parity qualification."""
import sys
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
try:
    import verify_governance_g2_reset_paths as verifier
    import qualify_governance_g2_reset_parity as parity
finally:
    sys.path.pop(0)


class TestResetPaths(unittest.TestCase):
    def test_unqualified_contract(self):
        data = verifier.contract()
        self.assertFalse(data['production_qualified'])
        self.assertEqual(data['expected_path_tests'], 26)
        self.assertEqual(sum(data['ordinary_expected_counts'].values()), 331)

    def test_modified_contract_rejected(self):
        data = verifier.contract()
        for field, value in (('schema_version', True), ('production_qualified', True),
                             ('acceptance', 'accepted'), ('qualification', 'production'),
                             ('parent_sha256', 'changed'), ('expected_path_tests', True),
                             ('test_sha256', {}), ('fixture_sha256', {}),
                             ('ordinary_targets', []), ('ordinary_expected_counts', {}), ('cache_sha256', 'changed')):
            with self.subTest(field=field), patch.object(verifier.json, 'loads', return_value=dict(data, **{field: value})):
                with self.assertRaises(ValueError):
                    verifier.contract()

    def test_contract_precedes_parent(self):
        with patch.object(verifier, 'contract', side_effect=ValueError('invalid')), patch.object(verifier, 'verify_parent') as parent:
            with self.assertRaises(ValueError):
                verifier.verify_stage(ROOT)
            parent.assert_not_called()

    def test_parity_report_preserves_failed_outcome(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / 'report.xml'
            report.write_text('<testsuite><testcase classname="tests.Native" name="allowed"/>'
                              '<testcase classname="tests.Native" name="known"><failure/></testcase></testsuite>')
            self.assertEqual(parity.outcomes(report), {'Native::allowed': 'passed', 'Native::known': 'failed'})

    def test_parity_report_rejects_skip_error_duplicate_or_empty(self):
        for content in ('<testsuite/>', '<testsuite><testcase name="x"><skipped/></testcase></testsuite>',
                        '<testsuite><testcase name="x"><error/></testcase></testsuite>',
                        '<testsuite><testcase name="x"/><testcase name="x"/></testsuite>'):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                report = Path(directory) / 'report.xml'
                report.write_text(content)
                with self.assertRaises(ValueError):
                    parity.outcomes(report)

    def test_parity_removes_ambient_credentials(self):
        with patch.dict(parity.os.environ, {'OPENAI_API_KEY': 'synthetic', 'TELEGRAM_TOKEN': 'synthetic',
                                           'HERMES_SESSION_ID': 'old', 'PYTHONPATH': 'old',
                                           'PYTEST_ADDOPTS': '-k filter'}, clear=True):
            env = parity.clean_environment(Path('source'), Path('home'))
        self.assertNotIn('OPENAI_API_KEY', env)
        self.assertNotIn('TELEGRAM_TOKEN', env)
        self.assertNotIn('HERMES_SESSION_ID', env)
        self.assertNotIn('PYTEST_ADDOPTS', env)
        self.assertEqual(env['PYTHONPATH'], 'source')

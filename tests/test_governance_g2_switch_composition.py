"""Switch composition provenance and report checks, not runtime acceptance."""
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    spec = importlib.util.spec_from_file_location("switch_composition_preparation", ROOT / "scripts/prepare_governance_g2_switch_composition.py")
    preparation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preparation)
    spec = importlib.util.spec_from_file_location("switch_composition_qualification", ROOT / "scripts/qualify_governance_g2_switch_composition.py")
    qualification = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(qualification)
finally:
    sys.path.pop(0)


class TestSwitchComposition(unittest.TestCase):
    def test_contract_pins_parent_patch_tests_and_retains_closed_production_gate(self):
        data = preparation.contract()
        self.assertIs(data["production_qualified"], False)
        self.assertEqual(data["qualification"], "source_switch_composition_only")
        self.assertEqual(data["acceptance"], "pending_review")
        self.assertEqual(data["expected_tests"], preparation.TESTS)

    def test_changed_inputs_and_invalid_counts_are_rejected(self):
        original = preparation.contract()
        for field, value in (("schema_version", True), ("production_qualified", True),
                ("acceptance", "accepted"), ("qualification", "production"),
                ("parent_sha256", "changed"), ("patch_sha256", "changed"),
                ("test_sha256", {}), ("effective_sha256", {}),
                ("fixture_sha256", {}), ("expected_tests", {})):
            changed = copy.deepcopy(original)
            changed[field] = value
            with self.subTest(field=field), patch.object(preparation.json, "loads", return_value=changed):
                with self.assertRaises(ValueError):
                    preparation.contract()
        for value in (True, 0, -1, "41"):
            changed = copy.deepcopy(original)
            changed["expected_tests"]["tests/hermes_g2_switch_composition_native.py"] = value
            with self.subTest(value=value), patch.object(preparation.json, "loads", return_value=changed):
                with self.assertRaises(ValueError):
                    preparation.contract()

    def test_invalid_parent_never_reconstructs(self):
        with patch.object(preparation, "verify_parent", side_effect=ValueError("invalid")), \
                patch.object(preparation.shutil, "copytree") as copies:
            with self.assertRaises(ValueError):
                preparation.prepare(ROOT / ".codex-build/switch-composition-never-created")
            copies.assert_not_called()

    def test_existing_or_nested_output_never_overwrites(self):
        for path in (ROOT, preparation.PARENT_STAGE / "nested"):
            with self.subTest(path=path), patch.object(preparation, "verify_parent"), \
                    patch.object(preparation.shutil, "copytree") as copies:
                with self.assertRaises(ValueError):
                    preparation.prepare(path)
                copies.assert_not_called()

    def test_invalid_manifest_blocks_effective_stage(self):
        data = preparation.contract()
        with patch.object(preparation, "contract", return_value=data), \
                patch.object(preparation, "verify_parent"), \
                patch.object(Path, "read_text", return_value="{}"):
            with self.assertRaises(ValueError):
                preparation.verify_stage(ROOT / ".codex-build/invalid-composition")

    def test_report_cannot_accept_skips_partial_counts_or_duplicate_cases(self):
        reports = (
            ('<testsuites><testcase name="one"/></testsuites>', 0, 1, True),
            ('<testsuites><testcase name="one"><skipped/></testcase></testsuites>', 0, 1, False),
            ('<testsuites><testcase name="one"><error/></testcase></testsuites>', 0, 1, False),
            ('<testsuites><testcase name="one"><failure/></testcase></testsuites>', 1, 1, False),
            ('<testsuites><testcase name="one"/></testsuites>', 0, 2, False),
            ('<testsuites><testcase name="one"/><testcase name="one"/></testsuites>', 0, 2, False),
            ('<testsuites><testcase name="one"/></testsuites>', 1, 1, False),
        )
        for xml, code, count, valid in reports:
            with self.subTest(xml=xml, code=code), tempfile.TemporaryDirectory() as directory:
                report = Path(directory) / "report.xml"
                report.write_text(xml)
                if valid:
                    self.assertEqual(qualification.validate_report(report, code, count), count)
                else:
                    with self.assertRaises(ValueError):
                        qualification.validate_report(report, code, count)

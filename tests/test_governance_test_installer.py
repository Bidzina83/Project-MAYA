import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_governance_test_installer import candidate_template, inno_source, main
from project_maya.config import config_from_mapping
from project_maya.model_config import require_valid_model_config
from project_maya.hermes_plugins.candidate import CANDIDATE_SHA256, CANDIDATE_VERSION
from project_maya.hermes_plugins.candidate_qualification import SCENARIOS, qualify
from build_phase6_release import sha256_file
from verify_governance_test_installer import verify


class TestGovernanceTestInstaller(unittest.TestCase):
    def test_twelve_patch_artifact_binding_and_required_scenarios(self):
        self.assertEqual(CANDIDATE_VERSION, "0.17.0+maya.gov12.candidate.20261002")
        self.assertEqual(CANDIDATE_SHA256, "af979f8445e56e0379c7ad5252a228be5e7cf924c86f37c3c76a85ade867a323")
        self.assertEqual(len(SCENARIOS), 6)
        self.assertIn("compression-denial", SCENARIOS)
        self.assertIn("background-denial", SCENARIOS)

    def test_unknown_scenario_rejected_before_state_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "data"
            with self.assertRaisesRegex(ValueError, "scenario_invalid"):
                qualify(Path(temporary), root, scenario="unbounded-worker")
            self.assertFalse(root.exists())

    def test_candidate_template_validates_without_connector_credentials(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = candidate_template()
            data["deployment"]["data_dir"] = temporary
            data["governance"]["policy_file"] = str(Path(temporary) / "policy.json")
            config = config_from_mapping(data)
            require_valid_model_config(config)
            self.assertTrue(all(not i.enabled and i.credential_ref is None for i in config.integrations.values()))
            self.assertEqual(config.llm.mode, "local")
    def test_separate_identity_paths_shortcuts_and_scoped_uninstall(self):
        source = inno_source("0.1.0+test", False)
        self.assertIn("AD7D50D8-93F5-47B8-BA64-095429D67AA2", source)
        self.assertIn("Programs\\Maya Governance Test", source)
        self.assertIn("DefaultGroupName=Maya Governance Test", source)
        self.assertIn("qualify-governance.cmd", source)
        self.assertIn("Flags: unchecked", source)
        self.assertIn('Name: "{app}\\runtime"', source)
        self.assertNotIn('Type: filesandordirs; Name: "{localappdata}', source)
        self.assertNotIn("6D7C7B14", source)
        self.assertIn('IconFilename: "{app}\\assets\\maya.ico"', inno_source("0.1.0+test", True))

    def test_signing_required_without_explicit_unsigned_override(self):
        with self.assertRaisesRegex(SystemExit, "Signing is required"):
            main(["--out", "unused", "--managed-python-runtime", "unused",
                  "--python-wheelhouse-dir", "unused", "--hermes-wheel", "unused",
                  "--hermes-provenance", "unused", "--inno-compiler", "unused"])

    def test_verifier_rejects_thin_payload(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "payload").mkdir()
            files = root / "payload-files.json"
            files.write_text('{"files": []}', encoding="utf-8")
            (root / "governance-test-installer.json").write_text(json.dumps({
                "qualification": "test_only_unqualified", "production_qualified": False,
                "hermes_sha256": CANDIDATE_SHA256, "payload_manifest_sha256": sha256_file(files),
            }), encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "Missing real candidate component"):
                verify(root, allow_unsigned=True, run_payload=False)


if __name__ == "__main__":
    unittest.main()

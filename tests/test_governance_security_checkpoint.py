"""Provenance and tamper guards for the approved pre-G1 security overlay."""

import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    spec = importlib.util.spec_from_file_location("security_checkpoint", ROOT / "scripts/prepare_governance_security_checkpoint.py")
    checkpoint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checkpoint)


class TestSecurityCheckpoint(unittest.TestCase):
    def test_all_57_alerts_have_individual_dispositions(self):
        record = json.loads((ROOT / "docs/architecture/codeql-security-disposition-20261003.json").read_text())
        rows = record["dispositions"]
        self.assertEqual(len(rows), 57)
        self.assertEqual({r["alert"] for r in rows}, set(range(54, 111)))
        self.assertEqual(sum(r["disposition"] == "metadata_false_positive" for r in rows), 29)
        self.assertEqual(sum(r["disposition"] == "source_candidate_fix" for r in rows), 27)
        self.assertEqual([r["alert"] for r in rows if r["disposition"] == "excluded_frontend_needs_qualification"], [96])
        self.assertTrue(all(r["github_state"] == "open_not_dismissed" for r in rows))

    def test_linux_checkpoint_is_manual_and_keeps_all_required_controls(self):
        import yaml
        job = yaml.load((ROOT / ".github/workflows/governance-security-checkpoint.yml").read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(set(job["on"]), {"workflow_dispatch"})
        steps = job["jobs"]["checkpoint-linux"]["steps"]
        commands = "\n".join(s.get("run", "") for s in steps)
        self.assertIn("--mode security --security-checkpoint", commands)
        self.assertIn("--mode bounded --security-checkpoint", commands)
        self.assertIn("--ordinary-baseline", commands)
        self.assertIn("--extra bedrock", commands)
        self.assertIn("--locked", commands)
        self.assertNotIn("build_phase6_release", commands)

    def test_overlay_is_exact_and_does_not_rewrite_g0_patch_series(self):
        contract, candidate = checkpoint.security_contract()
        self.assertFalse(contract["production_qualified"])
        self.assertEqual(len(contract["effective_native_sha256"]), 10)
        self.assertEqual(checkpoint.digest(candidate.read_bytes()), contract["patch_sha256"])
        base = json.loads(checkpoint.CONTRACT.read_text())
        self.assertEqual([r["number"] for r in base["patches"]], list(range(1, 24)))
        self.assertNotIn("0024", json.dumps(base["patches"]))

    def test_base_inventory_identity_ignores_only_portable_tooling_metadata(self):
        base = {"effective_files": [{"path": "native.py", "sha256": "fixed", "mode": "100644"}],
                "tooling_sha256": {"runner": "windows-checkout"}}
        other = copy.deepcopy(base)
        other["tooling_sha256"]["runner"] = "linux-checkout"
        self.assertEqual(checkpoint.base_inventory_digest(base), checkpoint.base_inventory_digest(other))
        other["effective_files"][0]["sha256"] = "tampered"
        self.assertNotEqual(checkpoint.base_inventory_digest(base), checkpoint.base_inventory_digest(other))

    def test_altered_test_bytes_block_checkpoint_preparation(self):
        contract, _ = checkpoint.security_contract()
        contract["security_tests_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "contract.json"
            path.write_text(json.dumps(contract))
            with patch.object(checkpoint, "SECURITY_CONTRACT", path):
                with self.assertRaisesRegex(ValueError, "security.test_hash_mismatch"):
                    checkpoint.security_contract()

    def test_native_content_is_checked_against_contract_not_mutable_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            stage = Path(temp)
            source = stage / "source"
            source.mkdir()
            data = b"native = 1\n"
            (source / "native.py").write_bytes(data)
            base = {"effective_files": [{"path": "native.py", "sha256": "base", "mode": "100644"}]}
            contract = {"effective_native_sha256": {"native.py": checkpoint.digest(data)}}
            self.assertEqual(checkpoint.effective_files(stage, base, contract)[0]["sha256"], checkpoint.digest(data))
            (source / "native.py").write_bytes(b"tampered = 2\n")
            with self.assertRaisesRegex(ValueError, "security.stage_modified"):
                checkpoint.effective_files(stage, base, contract)

    def test_extra_files_and_changed_ordinary_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            stage = Path(temp)
            source = stage / "source"
            source.mkdir()
            data = b"native = 1\n"
            (source / "native.py").write_bytes(data)
            base = {"effective_files": [{"path": "native.py", "sha256": checkpoint.digest(data)}]}
            contract = {"effective_native_sha256": {}}
            checkpoint.effective_files(stage, base, contract)
            (source / "native.py").write_bytes(b"changed = 2\n")
            with self.assertRaisesRegex(ValueError, "security.stage_modified"):
                checkpoint.effective_files(stage, base, contract)
            (source / "extra.py").write_bytes(b"extra = True\n")
            with self.assertRaisesRegex(ValueError, "security.unexpected_stage_files"):
                checkpoint.effective_files(stage, base, contract)


if __name__ == "__main__":
    unittest.main()

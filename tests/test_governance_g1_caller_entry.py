"""G1 entry-patch provenance and runner profile guards, not loop qualification."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    spec = importlib.util.spec_from_file_location("g1_entry", ROOT / "scripts/prepare_governance_g1_caller_entry.py")
    candidate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(candidate)


class TestCallerEntryProvenance(unittest.TestCase):
    def test_exact_overlay_preserves_accepted_contracts(self):
        contract, artifact = candidate.caller_contract()
        self.assertFalse(contract["production_qualified"])
        self.assertEqual(set(contract["effective_native_sha256"]),
                         {"gateway/run.py", "gateway/slash_commands.py", "hermes_cli/middleware.py"})
        self.assertEqual(candidate.digest(artifact.read_bytes()), contract["patch_sha256"])
        base = json.loads(candidate.CONTRACT.read_text())
        self.assertEqual([p["number"] for p in base["patches"]], list(range(1, 24)))
        security, _ = candidate.security_contract()
        self.assertNotIn("0025", json.dumps(security))

    def test_changed_native_test_bytes_are_rejected(self):
        contract, _ = candidate.caller_contract()
        contract["native_tests_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.json"
            path.write_text(json.dumps(contract))
            with patch.object(candidate, "G1_CONTRACT", path):
                with self.assertRaisesRegex(ValueError, "g1.test_hash_mismatch"):
                    candidate.caller_contract()

    def test_changed_patch_identity_is_rejected(self):
        contract, _ = candidate.caller_contract()
        contract["patch_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.json"
            path.write_text(json.dumps(contract))
            with patch.object(candidate, "G1_CONTRACT", path):
                with self.assertRaisesRegex(ValueError, "g1.invalid_contract"):
                    candidate.caller_contract()

    def test_final_native_bytes_and_base_are_checked_not_receipt_claims(self):
        data = b"native = 1\n"
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            source = stage / "source"
            source.mkdir()
            (source / "native.py").write_bytes(data)
            base = {"effective_files": [{"path": "native.py", "sha256": candidate.digest(data)}],
                    "contract_sha256": candidate.digest(candidate.CONTRACT.read_bytes()),
                    "pin": candidate.PIN, "production_qualified": False, "patches_applied": True}
            (stage / "baseline-manifest.json").write_text(json.dumps(base))
            security = {"base_effective_inventory_sha256": candidate.base_inventory_digest(base),
                        "effective_native_sha256": {}}
            caller = {"effective_native_sha256": {"native.py": candidate.digest(data)}}
            with patch.object(candidate, "caller_contract", return_value=(caller, None)), \
                    patch.object(candidate, "security_contract", return_value=(security, None)):
                candidate.verify_caller_stage(stage)
                (source / "native.py").write_bytes(b"tampered = 2\n")
                with self.assertRaisesRegex(ValueError, "security.stage_modified"):
                    candidate.verify_caller_stage(stage)


if __name__ == "__main__":
    unittest.main()

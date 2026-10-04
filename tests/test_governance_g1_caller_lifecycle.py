"""Cleanup overlay provenance checks; no installed-product qualification."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    import prepare_governance_g1_caller_lifecycle as candidate


class TestCallerLifecycleProvenance(unittest.TestCase):
    def test_separate_overlay_preserves_entry_and_accepted_baseline(self):
        data, artifact = candidate.lifecycle_contract()
        self.assertFalse(data["production_qualified"])
        self.assertEqual(set(data["effective_native_sha256"]), {"gateway/run.py", "hermes_cli/middleware.py"})
        self.assertEqual(candidate.digest(artifact.read_bytes()), data["patch_sha256"])
        entry, _ = candidate.caller_contract()
        self.assertEqual(entry["patch"], "0025-trusted-native-caller-entry.patch")
        self.assertEqual([p["number"] for p in json.loads(candidate.CONTRACT.read_text())["patches"]], list(range(1, 24)))

    def test_tampered_patch_test_or_parent_contract_is_rejected(self):
        data, _ = candidate.lifecycle_contract()
        for field in ("patch_sha256", "native_tests_sha256", "entry_contract_sha256"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                changed = dict(data, **{field: "0" * 64})
                path = Path(directory) / "contract.json"
                path.write_text(json.dumps(changed))
                with patch.object(candidate, "LIFECYCLE_CONTRACT", path):
                    with self.assertRaisesRegex(ValueError, "lifecycle_contract_invalid"):
                        candidate.lifecycle_contract()

    def test_native_bytes_checked_independently_of_generated_receipt(self):
        raw = b"native = 1\n"
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "source").mkdir()
            source = stage / "source/native.py"
            source.write_bytes(raw)
            base = {"effective_files": [{"path": "native.py", "sha256": candidate.digest(raw)}],
                    "contract_sha256": candidate.digest(candidate.CONTRACT.read_bytes()),
                    "pin": candidate.PIN, "production_qualified": False, "patches_applied": True}
            (stage / "baseline-manifest.json").write_text(json.dumps(base))
            security = {"base_effective_inventory_sha256": candidate.base_inventory_digest(base),
                        "effective_native_sha256": {}}
            lifecycle = {"effective_native_sha256": {"native.py": candidate.digest(raw)}}
            with patch.object(candidate, "lifecycle_contract", return_value=(lifecycle, None)), \
                    patch.object(candidate, "caller_contract", return_value=({"effective_native_sha256": {}}, None)), \
                    patch.object(candidate, "security_contract", return_value=(security, None)):
                candidate.verify_lifecycle_stage(stage)
                source.write_bytes(b"changed = 2\n")
                with self.assertRaisesRegex(ValueError, "security.stage_modified"):
                    candidate.verify_lifecycle_stage(stage)

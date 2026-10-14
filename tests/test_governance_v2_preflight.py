"""Baseline validation tests; no Windows provisioning or native qualification."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.preflight_governance_v2_windows import PIN, validate_baseline


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.stage = Path(self.tmp.name)
        (self.stage / "source").mkdir()
        data = b"synthetic source\n"
        (self.stage / "source" / "run_agent.py").write_bytes(data)
        item = {"path": "run_agent.py", "mode": "100644",
                "sha256": hashlib.sha256(data).hexdigest(),
                "git_blob": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()}
        self.manifest = dict(pin=PIN, patches_applied=False, packaging_changes=[],
                             production_qualified=False, baseline_files=[item],
                             effective_files=[{k: item[k] for k in ("path", "mode", "sha256")}])
        self.save()

    def save(self):
        (self.stage / "baseline-manifest.json").write_text(json.dumps(self.manifest))

    def test_exact_ordinary_inventory(self):
        self.assertIn("manifest_sha256", validate_baseline(self.stage))

    def test_patched_manifest_refused(self):
        self.manifest["patches_applied"] = True
        self.save()
        with self.assertRaises(ValueError):
            validate_baseline(self.stage)

    def test_changed_bytes_refused(self):
        (self.stage / "source" / "run_agent.py").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            validate_baseline(self.stage)

    def test_unlisted_file_refused(self):
        (self.stage / "source" / "extra.py").write_bytes(b"extra")
        with self.assertRaises(ValueError):
            validate_baseline(self.stage)

    def test_changed_effective_inventory_refused(self):
        self.manifest["effective_files"][0]["sha256"] = "wrong"
        self.save()
        with self.assertRaises(ValueError):
            validate_baseline(self.stage)

    def test_path_escape_refused(self):
        self.manifest["baseline_files"][0]["path"] = "../escape"
        self.manifest["effective_files"][0]["path"] = "../escape"
        self.save()
        with self.assertRaises(ValueError):
            validate_baseline(self.stage)

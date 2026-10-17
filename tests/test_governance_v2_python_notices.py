"""Static notice integrity only; no runtime, native backend or network execution."""

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
NOTICES = ROOT / "docs/third-party/governance-v2-python-comparison"


class NoticeTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((NOTICES / "notices-manifest.json").read_text())

    def test_vendor_inventory_and_verbatim_hashes(self):
        entries = self.manifest["files"]
        names = [entry["path"] for entry in entries]
        self.assertEqual(len(names), 9)
        self.assertEqual(len(names), len(set(names)))
        actual = {path.name for path in NOTICES.iterdir() if path.is_file()}
        self.assertEqual(actual, set(names) | {"README.md", "notices-manifest.json"})
        for entry in entries:
            with self.subTest(notice=entry["path"]):
                self.assertEqual(Path(entry["path"]).name, entry["path"])
                data = (NOTICES / entry["path"]).read_bytes()
                self.assertEqual(len(data), entry["size_bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])
                self.assertTrue(entry.get("source_url") or entry.get("source_path"))

    def test_vendor_line_endings_are_not_converted_by_git(self):
        attributes = (ROOT / ".gitattributes").read_text()
        prefix = "/docs/third-party/governance-v2-python-comparison/"
        for suffix in ("*.txt -text", "*.rst -text"):
            self.assertIn(prefix + suffix, attributes.splitlines())

    def test_notice_collection_grants_no_operational_authority(self):
        for field in ("execution_authorized", "external_sharing_authorized",
                      "production_qualified", "redistribution_clearance_claimed"):
            self.assertIs(self.manifest[field], False)
        binding = self.manifest["runtime_binding"]
        self.assertEqual(binding["python_version"], "3.13.14")
        self.assertEqual(binding["reproduction_manifest_sha256"],
                         "17ad01535d3a70da86cc264b011cbb22528fdee5bf4b29203d9e7ed4daaeda60")
        self.assertEqual(binding["reference_commit"],
                         "8102bfc8dc3e244ec08e8204bd7d989e26a016e4")
        self.assertTrue(self.manifest["remaining_review"])


if __name__ == "__main__":
    unittest.main()

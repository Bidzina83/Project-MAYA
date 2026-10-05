"""Hash-pinned overlay provenance checks, not native acceptance."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    import prepare_governance_g2_prompt_cache as candidate


class TestPromptCacheInputs(unittest.TestCase):
    def test_source_only_contract(self):
        data = candidate.contract()
        self.assertIs(data["production_qualified"], False)
        self.assertEqual(data["mode"], "rebuild_without_snapshot")
        self.assertEqual(set(data["effective_sha256"]), candidate.PATHS)

    def test_tampering_rejected(self):
        data = candidate.contract()
        for key, value in (("schema_version", True), ("production_qualified", True),
                           ("mode", "snapshot"), ("acceptance", "accepted"),
                           ("parent_sha256", "0" * 64), ("patch_sha256", "0" * 64),
                           ("effective_sha256", {}), ("test_sha256", {})):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "inputs.json"
                path.write_text(json.dumps(data | {key: value}), encoding="utf-8")
                with patch.object(candidate, "INPUTS", path), self.assertRaises(ValueError):
                    candidate.contract()

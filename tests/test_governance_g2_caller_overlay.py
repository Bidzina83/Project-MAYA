"""Reviewed source overlay provenance, not production qualification."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    import prepare_governance_g2_caller as overlay


class TestCallerOverlay(unittest.TestCase):
    def test_exact_inputs_preserve_parent(self):
        data = overlay.overlay_contract()
        self.assertFalse(data["production_qualified"])
        overlay.reader_contract()

    def test_tampered_inputs_are_denied(self):
        data = overlay.overlay_contract()
        for key, value in (("production_qualified", True), ("acceptance", "accepted"),
                           ("design_sha256", "0" * 64), ("patch_sha256", "0" * 64),
                           ("maya_source_sha256", {}), ("effective_sha256", {}), ("schema_version", True),
                           ("host_inventory_sha256", "0" * 64)):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "inputs.json"
                altered = deepcopy(data)
                altered[key] = value
                path.write_text(json.dumps(altered))
                with patch.object(overlay, "INPUTS", path):
                    with self.assertRaises(ValueError):
                        overlay.overlay_contract()

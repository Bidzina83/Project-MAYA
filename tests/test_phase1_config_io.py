import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from project_maya import config_from_mapping, config_to_mapping
from project_maya.cli import main as maya_cli
from tests.test_phase0_contracts import valid_config_mapping


class TestPhase1ConfigIO(unittest.TestCase):
    def test_config_to_mapping_normalizes_enums_paths_and_secret_refs(self):
        config_data = valid_config_mapping()
        config = config_from_mapping(config_data)

        exported = config_to_mapping(config)

        self.assertEqual(exported["schema_version"], 2)
        self.assertEqual(exported["product"]["edition"], "standard")
        self.assertIn("maya-core", exported["runtime"]["enabled_profiles"])
        self.assertEqual(
            exported["integrations"]["google"]["credential_ref"],
            "secret://integrations/google",
        )
        self.assertNotIn("token", json.dumps(exported).lower())

    def test_export_config_cli_prints_normalized_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "maya.json"
            config_path.write_text(
                json.dumps(valid_config_mapping()),
                encoding="utf-8",
            )

            with patch("builtins.print") as printed:
                exit_code = maya_cli(["export-config", "--config", str(config_path)])

        self.assertEqual(exit_code, 0)
        exported = json.loads(printed.call_args.args[0])
        self.assertEqual(exported["schema_version"], 2)
        self.assertEqual(exported["product"]["edition"], "standard")

    def test_export_config_cli_accepts_utf8_bom_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "maya.json"
            config_path.write_text(
                json.dumps(valid_config_mapping()),
                encoding="utf-8-sig",
            )

            with patch("builtins.print") as printed:
                exit_code = maya_cli(["export-config", "--config", str(config_path)])

        self.assertEqual(exit_code, 0)
        exported = json.loads(printed.call_args.args[0])
        self.assertEqual(exported["schema_version"], 2)
        self.assertEqual(exported["product"]["edition"], "standard")

    def test_doctor_cli_reports_invalid_config_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "maya.json"
            config_path.write_text(
                '{"secret": "raw-value", ',
                encoding="utf-8",
            )

            with patch("builtins.print") as printed:
                exit_code = maya_cli(["doctor", "--config", str(config_path)])

        self.assertEqual(exit_code, 1)
        output = printed.call_args.args[0]
        self.assertEqual(output, "fail\tconfig\tconfiguration invalid")
        self.assertNotIn("Traceback", output)
        self.assertNotIn("raw-value", output)

    def test_import_config_cli_is_dry_run_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "source.json"
            destination_path = Path(tmp) / "dest" / "maya.json"
            source_path.write_text(
                json.dumps(valid_config_mapping()),
                encoding="utf-8",
            )

            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    [
                        "import-config",
                        "--from",
                        str(source_path),
                        "--to",
                        str(destination_path),
                    ]
                )

        self.assertEqual(exit_code, 0)
        self.assertFalse(destination_path.exists())
        output = json.loads(printed.call_args.args[0])
        self.assertEqual(output["status"], "dry_run")
        self.assertTrue(output["valid"])

    def test_import_config_cli_applies_normalized_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "source.json"
            destination_path = Path(tmp) / "dest" / "maya.json"
            source_path.write_text(
                json.dumps(valid_config_mapping()),
                encoding="utf-8",
            )

            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    [
                        "import-config",
                        "--from",
                        str(source_path),
                        "--to",
                        str(destination_path),
                        "--apply",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue(destination_path.is_file())
            written = json.loads(destination_path.read_text(encoding="utf-8"))
            self.assertEqual(written["schema_version"], 2)
            self.assertEqual(
                json.loads(printed.call_args.args[0])["status"],
                "imported",
            )

    def test_import_config_cli_requires_overwrite_consent(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "source.json"
            destination_path = Path(tmp) / "maya.json"
            source_path.write_text(
                json.dumps(valid_config_mapping()),
                encoding="utf-8",
            )
            destination_path.write_text("existing", encoding="utf-8")

            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    [
                        "import-config",
                        "--from",
                        str(source_path),
                        "--to",
                        str(destination_path),
                        "--apply",
                    ]
                )

            self.assertEqual(exit_code, 1)
            self.assertEqual(destination_path.read_text(encoding="utf-8"), "existing")
            output = printed.call_args.args[0]
            self.assertIn('"code": "config_import_failed"', output)
            self.assertNotIn("secret://", output)


if __name__ == "__main__":
    unittest.main()

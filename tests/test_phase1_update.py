import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from project_maya import (
    UpdateError,
    check_updates,
    config_from_mapping,
    rollback_update,
)
from project_maya.cli import main as maya_cli
from tests.test_phase0_contracts import valid_config_mapping


class TestPhase1Update(unittest.TestCase):
    def test_check_updates_reports_unavailable_without_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._config(Path(tmp) / "maya-data")

            result = check_updates(config)

            self.assertEqual(result.operation, "check")
            self.assertFalse(result.supported)
            self.assertEqual(result.status, "unavailable")
            self.assertFalse(result.network_used)
            self.assertFalse(result.mutation)

    def test_check_updates_accepts_signed_local_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            updates_dir = data_dir / "updates"
            updates_dir.mkdir(parents=True)
            (updates_dir / "update-manifest.json").write_text(
                json.dumps(
                    {
                        "signed": True,
                        "current_version": "1.0.0",
                        "available_version": "1.0.1",
                    }
                ),
                encoding="utf-8",
            )
            config = self._config(data_dir)

            result = check_updates(config)

            self.assertTrue(result.supported)
            self.assertEqual(result.status, "available")
            self.assertEqual(result.current_version, "1.0.0")
            self.assertEqual(result.available_version, "1.0.1")
            self.assertTrue(result.signed_manifest)
            self.assertFalse(result.mutation)

    def test_check_updates_rejects_unsigned_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            updates_dir = data_dir / "updates"
            updates_dir.mkdir(parents=True)
            (updates_dir / "update-manifest.json").write_text(
                json.dumps({"signed": False, "available_version": "1.0.1"}),
                encoding="utf-8",
            )
            config = self._config(data_dir)

            result = check_updates(config)

            self.assertFalse(result.supported)
            self.assertEqual(result.status, "unsigned_manifest_rejected")
            self.assertFalse(result.network_used)
            self.assertFalse(result.mutation)

    def test_rollback_update_reports_ready_for_signed_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            updates_dir = data_dir / "updates"
            updates_dir.mkdir(parents=True)
            (updates_dir / "rollback.json").write_text(
                json.dumps(
                    {
                        "signed": True,
                        "current_version": "1.0.1",
                        "rollback_version": "1.0.0",
                    }
                ),
                encoding="utf-8",
            )
            config = self._config(data_dir)

            result = rollback_update(config)

            self.assertEqual(result.operation, "rollback")
            self.assertTrue(result.supported)
            self.assertEqual(result.status, "ready")
            self.assertEqual(result.rollback_version, "1.0.0")
            self.assertFalse(result.network_used)
            self.assertFalse(result.mutation)

    def test_update_metadata_must_be_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            updates_dir = data_dir / "updates"
            updates_dir.mkdir(parents=True)
            (updates_dir / "update-manifest.json").write_text(
                json.dumps(["bad"]),
                encoding="utf-8",
            )
            config = self._config(data_dir)

            with self.assertRaisesRegex(UpdateError, "JSON object"):
                check_updates(config)

    def test_maya_update_check_cli_reports_local_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            config_path = self._write_config(Path(tmp), data_dir)

            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    ["update", "--config", str(config_path), "--check"]
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(printed.call_args.args[0])
            self.assertEqual(payload["operation"], "check")
            self.assertEqual(payload["status"], "unavailable")
            self.assertFalse(payload["network_used"])

    def test_maya_update_rollback_cli_reports_local_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            config_path = self._write_config(Path(tmp), data_dir)

            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    ["update", "--config", str(config_path), "--rollback"]
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(printed.call_args.args[0])
            self.assertEqual(payload["operation"], "rollback")
            self.assertEqual(payload["status"], "unavailable")
            self.assertFalse(payload["network_used"])

    def test_maya_update_cli_reports_secret_safe_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            updates_dir = data_dir / "updates"
            updates_dir.mkdir(parents=True)
            (updates_dir / "update-manifest.json").write_text(
                json.dumps(["bad"]),
                encoding="utf-8",
            )
            config_path = self._write_config(Path(tmp), data_dir)

            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    ["update", "--config", str(config_path), "--check"]
                )

            self.assertEqual(exit_code, 1)
            output = printed.call_args.args[0]
            self.assertIn('"code": "update_status_failed"', output)
            self.assertNotIn(str(data_dir), output)

    def _config(self, data_dir: Path):
        config_data = valid_config_mapping()
        config_data["deployment"]["data_dir"] = str(data_dir)
        return config_from_mapping(config_data)

    def _write_config(self, root: Path, data_dir: Path) -> Path:
        config_data = valid_config_mapping()
        config_data["deployment"]["data_dir"] = str(data_dir)
        path = root / "maya-config.json"
        path.write_text(json.dumps(config_data), encoding="utf-8")
        return path


if __name__ == "__main__":
    unittest.main()

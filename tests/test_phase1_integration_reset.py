import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from project_maya import (
    IntegrationResetError,
    config_from_mapping,
    reset_integration_state,
)
from project_maya.cli import main as maya_cli
from tests.test_phase0_contracts import valid_config_mapping


class TestPhase1IntegrationReset(unittest.TestCase):
    def test_reset_integration_is_dry_run_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            state_dir = data_dir / "integrations" / "google"
            state_file = state_dir / "state.json"
            state_dir.mkdir(parents=True)
            state_file.write_text("{}", encoding="utf-8")
            config = self._config(data_dir)

            result = reset_integration_state(config, "google")

            self.assertTrue(result.dry_run)
            self.assertTrue(result.local_state_exists)
            self.assertEqual(result.files, 1)
            self.assertTrue(result.credential_ref_present)
            self.assertFalse(result.external_revocation_performed)
            self.assertTrue(state_file.exists())

    def test_reset_integration_apply_removes_only_local_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            state_dir = data_dir / "integrations" / "google"
            other_dir = data_dir / "integrations" / "telegram"
            state_dir.mkdir(parents=True)
            other_dir.mkdir(parents=True)
            (state_dir / "state.json").write_text("{}", encoding="utf-8")
            (other_dir / "state.json").write_text("{}", encoding="utf-8")
            config = self._config(data_dir)

            result = reset_integration_state(config, "google", apply=True)

            self.assertFalse(result.dry_run)
            self.assertFalse(result.local_state_exists)
            self.assertEqual(result.files, 1)
            self.assertFalse(state_dir.exists())
            self.assertTrue(other_dir.is_dir())

    def test_reset_integration_rejects_unknown_or_unsafe_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._config(Path(tmp) / "maya-data")

            with self.assertRaisesRegex(IntegrationResetError, "not configured"):
                reset_integration_state(config, "slack")
            with self.assertRaisesRegex(IntegrationResetError, "configured name"):
                reset_integration_state(config, "../google")

    def test_maya_reset_integration_cli_defaults_to_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            state_dir = data_dir / "integrations" / "google"
            state_dir.mkdir(parents=True)
            (state_dir / "state.json").write_text("{}", encoding="utf-8")
            config_path = self._write_config(Path(tmp), data_dir)

            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    ["reset-integration", "google", "--config", str(config_path)]
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(printed.call_args.args[0])
            self.assertEqual(payload["status"], "dry_run")
            self.assertEqual(payload["integration"], "google")
            self.assertTrue(payload["credential_ref_present"])
            self.assertFalse(payload["external_revocation_performed"])
            self.assertNotIn("secret://integrations/google", printed.call_args.args[0])
            self.assertTrue(state_dir.is_dir())

    def test_maya_reset_integration_cli_applies_local_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            state_dir = data_dir / "integrations" / "google"
            state_dir.mkdir(parents=True)
            (state_dir / "state.json").write_text("{}", encoding="utf-8")
            config_path = self._write_config(Path(tmp), data_dir)

            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    [
                        "reset-integration",
                        "google",
                        "--config",
                        str(config_path),
                        "--apply",
                    ]
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(printed.call_args.args[0])
            self.assertEqual(payload["status"], "reset")
            self.assertFalse(state_dir.exists())

    def test_maya_reset_integration_cli_reports_secret_safe_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            config_path = self._write_config(Path(tmp), data_dir)

            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    ["reset-integration", "../google", "--config", str(config_path)]
                )

            self.assertEqual(exit_code, 1)
            output = printed.call_args.args[0]
            self.assertIn('"code": "integration_reset_failed"', output)
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

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from project_maya import (
    ProviderRevocationStatus,
    config_from_mapping,
    reset_integration_state,
)
from project_maya.cli import main as maya_cli
from tests.test_phase0_contracts import valid_config_mapping


class TestPhase2ResetRevocation(unittest.TestCase):
    def test_local_reset_reports_provider_revocation_not_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            state_dir = data_dir / "integrations" / "google"
            state_dir.mkdir(parents=True)
            (state_dir / "state.json").write_text("{}", encoding="utf-8")
            config = self._config(data_dir)

            result = reset_integration_state(config, "google", apply=True)

            self.assertFalse(result.external_revocation_performed)
            self.assertFalse(result.provider_revocation_requested)
            self.assertEqual(
                result.provider_revocation_status,
                ProviderRevocationStatus.NOT_REQUESTED,
            )
            self.assertIn("not requested", result.provider_revocation_reason)

    def test_requested_provider_revocation_reports_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            config = self._config(data_dir)

            result = reset_integration_state(
                config,
                "google",
                revoke_provider=True,
            )

            self.assertFalse(result.external_revocation_performed)
            self.assertTrue(result.provider_revocation_requested)
            self.assertEqual(
                result.provider_revocation_status,
                ProviderRevocationStatus.UNAVAILABLE,
            )
            self.assertIn("provider-specific revoker", result.provider_revocation_reason)

    def test_reset_cli_reports_revocation_contract_without_secret_values(self):
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
                        "--revoke-provider",
                    ]
                )

            self.assertEqual(exit_code, 0)
            output = printed.call_args.args[0]
            payload = json.loads(output)
            self.assertTrue(payload["provider_revocation_requested"])
            self.assertEqual(payload["provider_revocation_status"], "unavailable")
            self.assertFalse(payload["external_revocation_performed"])
            self.assertNotIn("secret://integrations/google", output)
            self.assertTrue(state_dir.exists())

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

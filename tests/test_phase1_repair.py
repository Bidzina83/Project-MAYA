import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from project_maya import RepairError, config_from_mapping, repair_local_state
from project_maya.cli import main as maya_cli
from project_maya.repair import REQUIRED_DIRECTORIES
from tests.test_phase0_contracts import valid_config_mapping


class TestPhase1Repair(unittest.TestCase):
    def test_repair_local_state_is_dry_run_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            config = self._config(data_dir)

            result = repair_local_state(config)

            self.assertTrue(result.dry_run)
            self.assertFalse(data_dir.exists())
            actions = {action.path: action for action in result.actions}
            self.assertEqual(actions[data_dir].status, "planned")
            self.assertEqual(actions[data_dir].action, "create_directory")

    def test_repair_local_state_creates_missing_directories_when_applied(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            config = self._config(data_dir)

            result = repair_local_state(config, apply=True)

            self.assertFalse(result.dry_run)
            self.assertTrue(data_dir.is_dir())
            for relative_name in REQUIRED_DIRECTORIES:
                self.assertTrue((data_dir / relative_name).is_dir(), relative_name)
            self.assertTrue(
                any(action.status == "created" for action in result.actions)
            )

    def test_repair_local_state_rejects_blocked_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            data_dir.mkdir()
            (data_dir / "backups").write_text("blocked", encoding="utf-8")
            config = self._config(data_dir)

            with self.assertRaisesRegex(RepairError, "not a directory"):
                repair_local_state(config, apply=True)

    def test_maya_repair_cli_defaults_to_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            config_path = self._write_config(Path(tmp), data_dir)

            with patch("builtins.print") as printed:
                exit_code = maya_cli(["repair", "--config", str(config_path)])

            self.assertEqual(exit_code, 0)
            payload = json.loads(printed.call_args.args[0])
            self.assertEqual(payload["status"], "dry_run")
            self.assertFalse(data_dir.exists())

    def test_maya_repair_cli_applies_directory_repairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            config_path = self._write_config(Path(tmp), data_dir)

            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    ["repair", "--config", str(config_path), "--apply"]
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(printed.call_args.args[0])
            self.assertEqual(payload["status"], "repaired")
            self.assertTrue((data_dir / "backups").is_dir())
            self.assertTrue((data_dir / "migrations").is_dir())

    def test_maya_repair_cli_reports_secret_safe_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "missing-parent" / "maya-data"
            config_path = self._write_config(Path(tmp), data_dir)

            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    ["repair", "--config", str(config_path), "--apply"]
                )

            self.assertEqual(exit_code, 1)
            output = printed.call_args.args[0]
            self.assertIn('"code": "repair_failed"', output)
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

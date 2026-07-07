import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from project_maya import (
    config_from_mapping,
    plan_restore_backup,
    plan_setup,
    restore_local_backup,
)
from project_maya.cli import main as maya_cli
from tests.test_phase0_contracts import valid_config_mapping
from tests.test_phase1_backup import TestPhase1Backup
from tests.test_phase2_model_config import enterprise_broker_disabled_mapping


class FakeMemoryProvider:
    def shutdown(self):
        return None


class FakeMemoryManager:
    def __init__(self):
        self.provider = FakeMemoryProvider()


class FakeAIAgent:
    def __init__(self, **kwargs):
        self.session_id = "phase4-health"
        self._memory_manager = FakeMemoryManager()

    def chat(self, message):
        return "ok"

    def shutdown_memory_provider(self):
        self._memory_manager.provider.shutdown()


class TestPhase4SetupHealth(unittest.TestCase):
    def test_setup_plan_is_dry_run_and_secret_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            config = self._config(data_dir)

            result = plan_setup(config)

            self.assertTrue(result.dry_run)
            self.assertFalse(data_dir.exists())
            payload = json.dumps(result.redacted_summary(), sort_keys=True)
            self.assertIn("maya-data", payload)
            self.assertIn("component", payload)
            self.assertIn("next_command", payload)
            self.assertIn("manual_action", payload)
            self.assertIn("broker_pending", payload)
            self.assertNotIn(str(data_dir), payload)
            self.assertNotIn("secret://", payload)

    def test_enterprise_setup_reports_broker_disabled_customer_owned_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            mapping = enterprise_broker_disabled_mapping()
            mapping["deployment"]["data_dir"] = str(Path(tmp) / "maya-data")
            mapping["runtime"]["enabled_profiles"] = [
                "maya-core",
                "maya-messaging",
                "maya-local-models",
            ]
            config = config_from_mapping(mapping)

            result = plan_setup(config)

            payload = json.dumps(result.redacted_summary(), sort_keys=True)
            self.assertIn("enterprise", payload)
            self.assertIn("broker is disabled", payload)
            self.assertIn("customer_owned", payload)
            self.assertIn("local-models", payload)
            self.assertNotIn("secret://", payload)

    def test_setup_init_apply_creates_only_repair_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            config = self._config(data_dir)

            result = plan_setup(config, apply=True)

            self.assertFalse(result.dry_run)
            self.assertTrue((data_dir / "memory" / "registry").is_dir())
            self.assertTrue((data_dir / "governance" / "audit").is_dir())
            self.assertTrue((data_dir / "documents" / "outputs").is_dir())
            self.assertTrue((data_dir / "metabase" / "provisioning").is_dir())
            self.assertTrue((data_dir / "updates").is_dir())
            self.assertFalse((data_dir / "analytics" / "sources").exists())

    def test_setup_cli_text_output_is_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            config_path = self._write_config(Path(tmp), data_dir)

            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    [
                        "setup",
                        "plan",
                        "--config",
                        str(config_path),
                        "--format",
                        "text",
                    ]
                )

            self.assertEqual(exit_code, 0)
            output = printed.call_args.args[0]
            self.assertIn("operation: plan", output)
            self.assertNotIn(str(data_dir), output)
            self.assertNotIn("secret://", output)

    def test_health_summary_cli_reports_operator_categories(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            data_dir.mkdir()
            config_path = self._write_config(Path(tmp), data_dir)

            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    ["health", "summary", "--config", str(config_path)]
                )

            self.assertIn(exit_code, {0, 1})
            payload = json.loads(printed.call_args.args[0])
            category_names = {item["name"] for item in payload["categories"]}
            self.assertIn("setup", category_names)
            self.assertIn("platform", category_names)
            self.assertIn("recovery", category_names)
            self.assertIn("configuration", category_names)
            self.assertIn("runtime", category_names)
            self.assertIn("backup", category_names)
            self.assertIn("restore", category_names)
            self.assertIn("migration", category_names)
            self.assertIn("update", category_names)
            self.assertIn("skills", category_names)
            self.assertFalse(payload["network_used"])
            self.assertNotIn("secret://", printed.call_args.args[0])

    def test_restore_plan_reports_conflicts_without_extracting(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = TestPhase1Backup()._make_backup_archive(Path(tmp))
            destination = Path(tmp) / "restore"
            existing = destination / "memory" / "records.json"
            existing.parent.mkdir(parents=True)
            existing.write_text("existing", encoding="utf-8")

            plan = plan_restore_backup(archive_path, destination)

            self.assertTrue(plan.dry_run)
            self.assertEqual(plan.conflicts, 1)
            self.assertTrue(plan.overwrite_required)
            self.assertEqual(plan.manifest_status, "valid")
            payload = json.dumps(plan.redacted_summary(), sort_keys=True)
            self.assertNotIn(str(destination), payload)

            with self.assertRaisesRegex(Exception, "existing files"):
                restore_local_backup(archive_path, destination, apply=True)

    def test_restore_cli_reports_conflict_safely(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = TestPhase1Backup()._make_backup_archive(Path(tmp))
            destination = Path(tmp) / "restore"
            existing = destination / "memory" / "records.json"
            existing.parent.mkdir(parents=True)
            existing.write_text("existing", encoding="utf-8")

            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    [
                        "restore",
                        "--from",
                        str(archive_path),
                        "--to",
                        str(destination),
                    ]
                )

            self.assertEqual(exit_code, 1)
            output = printed.call_args.args[0]
            self.assertIn('"code": "restore_failed"', output)
            self.assertNotIn(str(destination), output)
            self.assertEqual(existing.read_text(encoding="utf-8"), "existing")

    def _config(self, data_dir: Path):
        return config_from_mapping(self._mapping(data_dir))

    def _write_config(self, root: Path, data_dir: Path) -> Path:
        path = root / "maya-config.json"
        path.write_text(json.dumps(self._mapping(data_dir)), encoding="utf-8")
        return path

    def _mapping(self, data_dir: Path):
        config_data = valid_config_mapping()
        config_data["deployment"]["data_dir"] = str(data_dir)
        config_data["runtime"]["enabled_profiles"] = ["maya-core"]
        config_data["runtime"]["hermes_factory"] = (
            "tests.test_phase4_setup_health:FakeAIAgent"
        )
        config_data["runtime"]["hermes_runtime_version"] = "test-hermes"
        config_data["memory"]["retriever"] = "local_json"
        config_data["metabase"]["enabled"] = False
        config_data["metabase"]["application_database"] = None
        config_data["metabase"]["analytics_sources"] = []
        return config_data


if __name__ == "__main__":
    unittest.main()

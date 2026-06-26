import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from project_maya import (
    BackupError,
    RestoreError,
    config_from_mapping,
    create_local_backup,
    restore_local_backup,
)
from project_maya.cli import main as maya_cli
from tests.test_phase0_contracts import valid_config_mapping


class TestPhase1Backup(unittest.TestCase):
    def test_create_local_backup_archives_state_and_normalized_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            memory_path = data_dir / "memory" / "records.json"
            backup_cache_path = data_dir / "backups" / "old.zip"
            memory_path.parent.mkdir(parents=True)
            backup_cache_path.parent.mkdir(parents=True)
            memory_path.write_text(
                json.dumps([{"id": "note-1", "text": "hello"}]),
                encoding="utf-8",
            )
            backup_cache_path.write_text("old backup", encoding="utf-8")
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            config = config_from_mapping(config_data)
            destination = Path(tmp) / "backup.zip"

            result = create_local_backup(config, destination=destination)

            with zipfile.ZipFile(result.archive_path) as archive:
                names = set(archive.namelist())
                config_export = json.loads(
                    archive.read("maya-config.json").decode("utf-8")
                )

        self.assertEqual(result.archive_path, destination.resolve())
        self.assertEqual(result.files, 2)
        self.assertIn("maya-config.json", names)
        self.assertIn("maya-data/memory/records.json", names)
        self.assertNotIn("maya-data/backups/old.zip", names)
        self.assertEqual(config_export["schema_version"], 2)
        self.assertNotIn("token", json.dumps(config_export).lower())

    def test_create_local_backup_rejects_existing_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            data_dir.mkdir()
            destination = Path(tmp) / "backup.zip"
            destination.write_text("existing", encoding="utf-8")
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            config = config_from_mapping(config_data)

            with self.assertRaises(BackupError):
                create_local_backup(config, destination=destination)

            self.assertEqual(destination.read_text(encoding="utf-8"), "existing")

    def test_backup_cli_reports_archive_without_printing_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            memory_path = data_dir / "memory" / "records.json"
            memory_path.parent.mkdir(parents=True)
            memory_path.write_text(
                json.dumps([{"id": "note-1", "text": "sensitive memory"}]),
                encoding="utf-8",
            )
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            config_path = Path(tmp) / "maya.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")
            destination = Path(tmp) / "backup.zip"

            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    [
                        "backup",
                        "--config",
                        str(config_path),
                        "--to",
                        str(destination),
                    ]
                )

            self.assertEqual(exit_code, 0)
            output = printed.call_args.args[0]
            payload = json.loads(output)
            self.assertEqual(payload["status"], "backed_up")
            self.assertEqual(payload["archive"], str(destination.resolve()))
            self.assertTrue(destination.is_file())
            self.assertNotIn("sensitive memory", output)
            self.assertNotIn("secret://", output)

    def test_backup_cli_reports_secret_safe_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(Path(tmp) / "missing")
            config_path = Path(tmp) / "maya.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            with patch("builtins.print") as printed:
                exit_code = maya_cli(["backup", "--config", str(config_path)])

        self.assertEqual(exit_code, 1)
        output = printed.call_args.args[0]
        self.assertIn('"code": "backup_failed"', output)
        self.assertNotIn("missing", output)
        self.assertNotIn("secret://", output)

    def test_restore_local_backup_is_dry_run_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = self._make_backup_archive(Path(tmp))
            destination = Path(tmp) / "restore"

            result = restore_local_backup(archive_path, destination)

            self.assertTrue(result.dry_run)
            self.assertEqual(result.files, 2)
            self.assertFalse((destination / "memory" / "records.json").exists())

    def test_restore_local_backup_applies_files_and_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = self._make_backup_archive(Path(tmp))
            destination = Path(tmp) / "restore"

            result = restore_local_backup(archive_path, destination, apply=True)

            self.assertFalse(result.dry_run)
            self.assertEqual(result.files, 2)
            self.assertEqual(
                json.loads(
                    (destination / "memory" / "records.json").read_text(
                        encoding="utf-8"
                    )
                )[0]["id"],
                "note-1",
            )
            self.assertEqual(
                json.loads(
                    (destination / "config" / "maya-config.json").read_text(
                        encoding="utf-8"
                    )
                )["schema_version"],
                2,
            )

    def test_restore_local_backup_rejects_existing_files_without_consent(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = self._make_backup_archive(Path(tmp))
            destination = Path(tmp) / "restore"
            existing = destination / "memory" / "records.json"
            existing.parent.mkdir(parents=True)
            existing.write_text("existing", encoding="utf-8")

            with self.assertRaises(RestoreError):
                restore_local_backup(archive_path, destination, apply=True)

            self.assertEqual(existing.read_text(encoding="utf-8"), "existing")

    def test_restore_local_backup_rejects_unsafe_archive_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "unsafe.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("maya-config.json", "{}")
                archive.writestr("maya-data/../escape.txt", "bad")

            with self.assertRaises(RestoreError):
                restore_local_backup(archive_path, Path(tmp) / "restore")

    def test_restore_cli_dry_run_and_apply_are_secret_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = self._make_backup_archive(Path(tmp))
            destination = Path(tmp) / "restore"

            with patch("builtins.print") as printed:
                dry_run_code = maya_cli(
                    [
                        "restore",
                        "--from",
                        str(archive_path),
                        "--to",
                        str(destination),
                    ]
                )
            self.assertEqual(dry_run_code, 0)
            dry_run_output = printed.call_args.args[0]
            self.assertEqual(json.loads(dry_run_output)["status"], "dry_run")
            self.assertFalse((destination / "memory" / "records.json").exists())

            with patch("builtins.print") as printed:
                apply_code = maya_cli(
                    [
                        "restore",
                        "--from",
                        str(archive_path),
                        "--to",
                        str(destination),
                        "--apply",
                    ]
                )
            self.assertEqual(apply_code, 0)
            output = printed.call_args.args[0]
            self.assertEqual(json.loads(output)["status"], "restored")
            self.assertTrue((destination / "memory" / "records.json").is_file())
            self.assertNotIn("hello", output)
            self.assertNotIn("secret://", output)

    def test_restore_cli_reports_secret_safe_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("builtins.print") as printed:
                exit_code = maya_cli(
                    [
                        "restore",
                        "--from",
                        str(Path(tmp) / "missing.zip"),
                        "--to",
                        str(Path(tmp) / "restore"),
                    ]
                )

        self.assertEqual(exit_code, 1)
        output = printed.call_args.args[0]
        self.assertIn('"code": "restore_failed"', output)
        self.assertNotIn("missing.zip", output)

    def _make_backup_archive(self, root: Path) -> Path:
        data_dir = root / "maya-data"
        memory_path = data_dir / "memory" / "records.json"
        memory_path.parent.mkdir(parents=True)
        memory_path.write_text(
            json.dumps([{"id": "note-1", "text": "hello"}]),
            encoding="utf-8",
        )
        config_data = valid_config_mapping()
        config_data["deployment"]["data_dir"] = str(data_dir)
        config = config_from_mapping(config_data)
        archive_path = root / "backup.zip"
        create_local_backup(config, destination=archive_path)
        return archive_path


if __name__ == "__main__":
    unittest.main()

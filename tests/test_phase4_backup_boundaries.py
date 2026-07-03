import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from project_maya import config_from_mapping, create_local_backup
from tests.test_phase0_contracts import valid_config_mapping


class TestPhase4BackupBoundaries(unittest.TestCase):
    def test_default_backup_includes_maya_phase4_artifacts_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "maya-data"
            included_files = (
                data_dir / "documents" / "outputs" / "summary.pdf",
                data_dir / "documents" / "cache" / "preview.json",
                data_dir / "metabase" / "provisioning" / "plan.json",
                data_dir / "audit" / "runtime.jsonl",
            )
            excluded_files = (
                data_dir / "analytics" / "sources" / "customer.sqlite",
                data_dir / "metabase" / "application" / "metabase.db",
            )
            for path in included_files + excluded_files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({"path": path.name}), encoding="utf-8")

            config_data = valid_config_mapping()
            config_data["deployment"]["data_dir"] = str(data_dir)
            archive_path = Path(tmp) / "backup.zip"

            result = create_local_backup(
                config_from_mapping(config_data),
                destination=archive_path,
            )

            with zipfile.ZipFile(result.archive_path) as archive:
                names = set(archive.namelist())

        self.assertIn("maya-config.json", names)
        self.assertIn("maya-data/documents/outputs/summary.pdf", names)
        self.assertIn("maya-data/documents/cache/preview.json", names)
        self.assertIn("maya-data/metabase/provisioning/plan.json", names)
        self.assertIn("maya-data/audit/runtime.jsonl", names)
        self.assertNotIn("maya-data/analytics/sources/customer.sqlite", names)
        self.assertNotIn("maya-data/metabase/application/metabase.db", names)


if __name__ == "__main__":
    unittest.main()

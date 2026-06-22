import hashlib
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from scripts.migrate import migrate


def _make_legacy_db(path: Path) -> None:
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("CREATE TABLE memory_kv (key TEXT PRIMARY KEY, value TEXT)")
        conn.executemany(
            "INSERT INTO memory_kv(key, value) VALUES(?, ?)",
            [
                ("vec1", json.dumps([0.1, 0.2, 0.3])),
                ("obj1", json.dumps({"note": "not a vector"})),
                ("txt1", "just a legacy note"),
            ],
        )
        conn.commit()


class TestMigrationSafetyContract(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "legacy.sqlite"
        self.destination = self.root / "migrated.sqlite"
        _make_legacy_db(self.source)

    def tearDown(self):
        self.temporary.cleanup()

    def test_dry_run_is_default_and_does_not_create_destination(self):
        result = migrate(str(self.source), str(self.destination))

        self.assertTrue(result["dry_run"])
        self.assertEqual(result["source_rows"], 3)
        self.assertFalse(self.destination.exists())

    def test_apply_requires_explicit_modify_consent(self):
        with self.assertRaisesRegex(PermissionError, "allow_modify"):
            migrate(str(self.source), str(self.destination), dry_run=False)

    def test_registry_migration_writes_vectors_provenance_and_report(self):
        result = migrate(
            str(self.source),
            str(self.destination),
            dry_run=False,
            allow_modify=True,
        )

        self.assertEqual(result["migrated"], 3)
        self.assertEqual(result["validation_errors"], [])
        self.assertTrue(Path(result["report_path"]).is_file())
        with closing(sqlite3.connect(self.destination)) as conn:
            vector_row = conn.execute(
                "SELECT chunk_id, vector, vector_dim, score_meta "
                "FROM entries WHERE embedding_id='vec1'"
            ).fetchone()
            text_row = conn.execute(
                "SELECT chunk_id, vector, vector_dim, score_meta "
                "FROM entries WHERE embedding_id='txt1'"
            ).fetchone()
            embedding_row = conn.execute(
                "SELECT source_hash, extractor_version FROM embeddings "
                "WHERE chunk_id='vec1'"
            ).fetchone()

        self.assertEqual(vector_row[:3], ("vec1", "[0.1,0.2,0.3]", 3))
        vector_meta = json.loads(vector_row[3])
        expected_hash = hashlib.sha256(json.dumps([0.1, 0.2, 0.3]).encode()).hexdigest()
        self.assertEqual(vector_meta["original_sha256"], expected_hash)
        self.assertEqual(text_row[:3], (None, None, None))
        self.assertEqual(
            json.loads(text_row[3])["legacy_value"], "just a legacy note"
        )
        self.assertEqual(embedding_row, (expected_hash, "legacy-migration"))

    def test_existing_destination_is_backed_up_and_conflicts_are_skipped(self):
        migrate(
            str(self.source),
            str(self.destination),
            dry_run=False,
            allow_modify=True,
        )
        backup = self.root / "migrated.backup.sqlite"

        result = migrate(
            str(self.source),
            str(self.destination),
            dry_run=False,
            allow_modify=True,
            backup_path=str(backup),
        )

        self.assertTrue(backup.is_file())
        self.assertEqual(result["migrated"], 0)
        self.assertEqual(result["skipped_keys"], ["vec1", "obj1", "txt1"])

    def test_existing_destination_without_backup_is_rejected(self):
        self.destination.touch()

        with self.assertRaisesRegex(PermissionError, "backup_path"):
            migrate(
                str(self.source),
                str(self.destination),
                dry_run=False,
                allow_modify=True,
            )


if __name__ == "__main__":
    unittest.main()

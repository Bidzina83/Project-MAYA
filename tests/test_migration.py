import unittest
import tempfile
import os
import sqlite3
import importlib.util

# load scripts/migrate.py as a module
migrate_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "migrate.py")
migrate_path = os.path.normpath(migrate_path)
spec = importlib.util.spec_from_file_location("migrate", migrate_path)
migrate_module = importlib.util.module_from_spec(spec)
loader = spec.loader
assert loader is not None
loader.exec_module(migrate_module)

class TestMigration(unittest.TestCase):
    def setUp(self):
        # create legacy sqlite with memory_kv
        fd, self.src = tempfile.mkstemp(prefix="legacy_", suffix=".db")
        os.close(fd)
        src_conn = sqlite3.connect(self.src)
        cur = src_conn.cursor()
        cur.execute(
            "CREATE TABLE memory_kv (key TEXT PRIMARY KEY, value TEXT)"
        )
        cur.execute("INSERT INTO memory_kv(key, value) VALUES(?, ?)", ("k1", "v1"))
        cur.execute("INSERT INTO memory_kv(key, value) VALUES(?, ?)", ("k2", "v2"))
        src_conn.commit()
        src_conn.close()

        fd, self.dst = tempfile.mkstemp(prefix="new_", suffix=".db")
        os.close(fd)
        # remove dst file so migrate creates it
        os.remove(self.dst)

    def tearDown(self):
        for p in (self.src, self.dst):
            try:
                os.remove(p)
            except Exception:
                pass

    def test_dry_run_reports(self):
        res = migrate_module.migrate(self.src, self.dst, dry_run=True, target_schema="registry")
        self.assertEqual(res.get("source_rows"), 2)
        self.assertIn("Would copy", res.get("actions")[1])
        self.assertFalse(os.path.exists(self.dst))

    def test_apply_migration_registry(self):
        res = migrate_module.migrate(self.src, self.dst, dry_run=False, target_schema="registry")
        # inspect destination DB
        dst_conn = sqlite3.connect(self.dst)
        cur = dst_conn.cursor()
        cur.execute("SELECT embedding_id, chunk_id, vector, source_path FROM entries ORDER BY embedding_id")
        rows = cur.fetchall()
        dst_conn.close()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], "k1")
        self.assertEqual(rows[0][2], "v1")

    def test_apply_migration_memory_entries(self):
        # remove dst and test memory_entries target
        if os.path.exists(self.dst):
            os.remove(self.dst)
        res = migrate_module.migrate(self.src, self.dst, dry_run=False, target_schema="memory_entries")
        dst_conn = sqlite3.connect(self.dst)
        cur = dst_conn.cursor()
        cur.execute("SELECT key, value, migrated_from FROM memory_entries ORDER BY key")
        rows = cur.fetchall()
        dst_conn.close()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], "k1")
        self.assertEqual(rows[0][1], "v1")

if __name__ == '__main__':
    unittest.main()

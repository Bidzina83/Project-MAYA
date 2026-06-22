import unittest
import sqlite3
import json
from pathlib import Path
from scripts.migrate import migrate


def _make_legacy_db(path: str):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE memory_kv (key TEXT PRIMARY KEY, value TEXT)")
    # vector-like value (JSON array string)
    cur.execute("INSERT INTO memory_kv(key, value) VALUES(?, ?)", ("vec1", json.dumps([0.1, 0.2, 0.3])))
    # non-vector JSON object
    cur.execute("INSERT INTO memory_kv(key, value) VALUES(?, ?)", ("obj1", json.dumps({"note": "not a vector"})))
    # plain legacy string
    cur.execute("INSERT INTO memory_kv(key, value) VALUES(?, ?)", ("txt1", "just a legacy note"))
    conn.commit()
    conn.close()


class TestMigrationSafeHandling(unittest.TestCase):

    def test_migrate_registry_safe_handling(self):
        tmp = Path.cwd() / "tmp_test_migrate"
        tmp.mkdir(exist_ok=True)
        src = tmp / "legacy.sqlite"
        dst = tmp / "migrated.sqlite"
        if src.exists():
            src.unlink()
        if dst.exists():
            dst.unlink()
        _make_legacy_db(str(src))

        # perform migration (not dry-run)
        res = migrate(str(src), str(dst), dry_run=False, target_schema="registry")
        self.assertEqual(res["migrated"], 3)

        # open destination and validate semantics
        conn = sqlite3.connect(str(dst))
        cur = conn.cursor()
        cur.execute("SELECT embedding_id, chunk_id, vector, vector_dim, created_at, source_path, score_meta FROM entries ORDER BY embedding_id")
        rows = cur.fetchall()
        self.assertEqual(len(rows), 3)

        # vec1 should have vector JSON and vector_dim=3
        r_vec = [r for r in rows if r[0] == 'vec1'][0]
        self.assertIsNotNone(r_vec[2])
        parsed = json.loads(r_vec[2])
        self.assertIsInstance(parsed, list)
        self.assertEqual(len(parsed), 3)
        self.assertEqual(r_vec[3], 3)

        # obj1 should NOT place object into vector; vector must be NULL and legacy content in score_meta
        r_obj = [r for r in rows if r[0] == 'obj1'][0]
        self.assertIsNone(r_obj[2])
        meta_obj = json.loads(r_obj[6])
        self.assertIn('legacy_value', meta_obj)
        self.assertIsInstance(meta_obj['legacy_value'], dict)

        # txt1 should also be stored in score_meta legacy_value and vector NULL
        r_txt = [r for r in rows if r[0] == 'txt1'][0]
        self.assertIsNone(r_txt[2])
        meta_txt = json.loads(r_txt[6])
        self.assertEqual(meta_txt['legacy_value'], 'just a legacy note')

        conn.close()


if __name__ == '__main__':
    unittest.main()

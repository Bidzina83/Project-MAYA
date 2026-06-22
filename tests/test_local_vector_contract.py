import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from plugins.memory.adapters.local_vector_adapter import LocalVectorAdapter
from plugins.memory.indexer import LocalVectorStore
from project_maya.memory import MemoryRetriever


class TestLocalVectorContract(unittest.TestCase):
    def test_adapter_upsert_persists_normalized_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "vectors.sqlite"
            store = LocalVectorStore(str(database))
            try:
                adapter = LocalVectorAdapter(store)
                memory = MemoryRetriever(adapter)
                memory.remember(
                    {
                        "id": "fact-1",
                        "content": "Project MAYA uses normalized vectors",
                        "embedding": [3.0, 4.0],
                    }
                )
            finally:
                store.close()

            with closing(sqlite3.connect(database)) as connection:
                row = connection.execute(
                    "SELECT normalized_vector, normalized_vector_dim, "
                    "normalized_vector_algo, normalized_version "
                    "FROM entries WHERE embedding_id='fact-1'"
                ).fetchone()

        normalized = json.loads(row[0])
        self.assertAlmostEqual(normalized[0], 0.6)
        self.assertAlmostEqual(normalized[1], 0.8)
        self.assertEqual(row[1:], (2, "l2-v1", 1))


if __name__ == "__main__":
    unittest.main()

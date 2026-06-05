import json
from plugins.memory.indexer import LocalVectorStore


def test_query_by_vector_basic(tmp_path):
    dbpath = str(tmp_path / "vecstore" / "vs.sqlite")
    store = LocalVectorStore(dbpath)
    try:
        # Add three entries with simple vectors
        store.add_entry("emb-a", "chunk-a", [1.0, 0.0], source_path="/tmp/a.txt")
        store.add_entry("emb-b", "chunk-b", [0.0, 1.0], source_path="/tmp/b.txt")
        store.add_entry("emb-c", "chunk-c", [1.0, 1.0], source_path="/tmp/c.txt")

        # Query with a vector similar to chunk-a
        res = store.query_by_vector([1.0, 0.0], top_k=3)
        assert len(res) >= 1
        # Top result should be chunk-a (highest cosine similarity)
        assert res[0]["chunk_id"] == "chunk-a"

        # Query with vector [1,1] should return chunk-c first
        res2 = store.query_by_vector([1.0, 1.0], top_k=3)
        assert res2[0]["chunk_id"] == "chunk-c"

    finally:
        store.close()

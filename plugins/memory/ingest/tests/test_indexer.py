import os
import tempfile
import json
from ...indexer import Indexer, LocalVectorStore


def test_indexer_atomic_write(tmp_path):
    idx = Indexer(base_dir=str(tmp_path / "index"))
    entry = {
        "embedding_id": "emb-test-1",
        "chunk_id": "a" * 64,
        "vector_dim": 3,
        "source_path": "/tmp/example.txt",
        "score_meta": {"score": 0.5},
    }
    path = idx.write_index_entry(entry)
    assert os.path.isfile(path)
    with open(path, "r", encoding="utf-8") as f:
        content = json.load(f)
    assert content["chunk_id"] == entry["chunk_id"]
    assert content["source_path"] == entry["source_path"]


def test_local_vector_store_basic(tmp_path):
    dbpath = str(tmp_path / "vecstore" / "vs.sqlite")
    store = LocalVectorStore(dbpath)
    try:
        store.add_entry("emb-1", "chunk-1", [0.1, 0.2, 0.3], source_path="/tmp/s.txt", score_meta={"s": 1.0})
        got = store.get_by_chunk_id("chunk-1")
        assert got is not None
        assert got["embedding_id"] == "emb-1"
        assert got["vector"] == [0.1, 0.2, 0.3]
        assert got["vector_dim"] == 3
    finally:
        store.close()

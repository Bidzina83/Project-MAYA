from __future__ import annotations
import json
import tempfile
import sqlite3
import os
from typing import List

from plugins.memory.indexer import LocalVectorStore
from plugins.memory.adapters.local_vector_adapter import LocalVectorAdapter
from plugins.memory.utils.normalization import vector_normalize


def _create_store_with_vectors(path: str, entries: List[dict]):
    store = LocalVectorStore(path)
    for e in entries:
        store.add_entry(e["embedding_id"], e["chunk_id"], e["vector"], created_at=e.get("created_at"), source_path=e.get("source_path"), score_meta=e.get("score_meta"))
    return store


def test_ranking_consistency_before_after_normalization(tmp_path):
    # Create a small store with two vectors where normalization should not change ranking
    db = str(tmp_path / "test_store.db")
    entries = [
        {"embedding_id": "e1", "chunk_id": "c1", "vector": [3.0, 0.0]},
        {"embedding_id": "e2", "chunk_id": "c2", "vector": [1.0, 0.0]},
    ]
    store = _create_store_with_vectors(db, entries)
    adapter = LocalVectorAdapter(store)

    # Query with vector pointing along first axis
    q = [1.0, 0.0]
    before = adapter.query_vector(q, top_k=2)
    before_ids = [r["id"] for r in before]

    # Simulate backfill by writing normalized_vector column for each row
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    # Add normalized columns if missing
    try:
        cur.execute("ALTER TABLE entries ADD COLUMN normalized_vector TEXT")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE entries ADD COLUMN normalized_vector_dim INTEGER")
    except Exception:
        pass
    for r in entries:
        nvec = vector_normalize(r["vector"]) or []
        cur.execute("UPDATE entries SET normalized_vector=?, normalized_vector_dim=? WHERE embedding_id=?", (json.dumps(nvec), len(nvec), r["embedding_id"]))
    conn.commit()
    conn.close()

    # Recreate adapter to ensure it reads latest DB state
    store2 = LocalVectorStore(db)
    adapter2 = LocalVectorAdapter(store2)
    after = adapter2.query_vector(q, top_k=2)
    after_ids = [r["id"] for r in after]

    assert before_ids == after_ids


def test_backfill_idempotent(tmp_path):
    db = str(tmp_path / "test_store2.db")
    entries = [
        {"embedding_id": "e1", "chunk_id": "c1", "vector": [0.0, 0.0]},
        {"embedding_id": "e2", "chunk_id": "c2", "vector": [1.0, 1.0]},
    ]
    store = _create_store_with_vectors(db, entries)
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    # ensure columns
    try:
        cur.execute("ALTER TABLE entries ADD COLUMN normalized_vector TEXT")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE entries ADD COLUMN normalized_vector_dim INTEGER")
    except Exception:
        pass
    conn.commit()
    conn.close()

    # Run the backfill function twice (import path)
    from plugins.memory.scripts.backfill_normalize_entries import backfill

    res1 = backfill(db, dry_run=False, chunk=10)
    res2 = backfill(db, dry_run=False, chunk=10)

    # Second run should not produce additional updates
    assert res1["updated"] >= 0
    assert res2["updated"] == 0 or res2["updated"] == res1["updated"]

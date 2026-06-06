#!/usr/bin/env python3
"""Backfill script to normalize existing LocalVectorStore entries.

Usage:
  python plugins/memory/scripts/backfill_normalize_entries.py /path/to/store.db

What it does:
- For each row in entries:
  - ensure score_meta contains content_normalized (text_normalize)
  - normalize vector with L2 normalization and update vector and vector_dim

This script is idempotent and writes updates in-place.
"""
from __future__ import annotations
import sys
import json
import sqlite3
from typing import Optional
from plugins.memory.utils.normalization import text_normalize, vector_normalize


def backfill(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT embedding_id, chunk_id, vector, vector_dim, created_at, source_path, score_meta FROM entries")
    rows = cur.fetchall()
    updated = 0
    for row in rows:
        embedding_id = row[0]
        chunk_id = row[1]
        vec_json = row[2] or "[]"
        try:
            vec = json.loads(vec_json)
        except Exception:
            vec = []
        score_meta_json = row[6] or "{}"
        try:
            score_meta = json.loads(score_meta_json)
        except Exception:
            score_meta = {}
        # compute normalized values
        changed = False
        if score_meta.get("content") and not score_meta.get("content_normalized"):
            score_meta["content_normalized"] = text_normalize(score_meta.get("content"))
            changed = True
        nvec = vector_normalize(vec)
        if nvec != vec:
            changed = True
        if changed:
            cur.execute(
                "UPDATE entries SET vector = ?, vector_dim = ?, score_meta = ? WHERE embedding_id = ?",
                (json.dumps(nvec), len(nvec), json.dumps(score_meta), embedding_id),
            )
            updated += 1
    conn.commit()
    conn.close()
    print(f"Backfill complete. Updated {updated} rows.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: backfill_normalize_entries.py /path/to/store.db")
        sys.exit(2)
    db = sys.argv[1]
    backfill(db)

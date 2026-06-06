#!/usr/bin/env python3
"""Backfill script to compute and store L2-normalized vectors into a separate
column while preserving original vectors for audit and re-indexing.

Usage:
  python plugins/memory/scripts/backfill_normalize_entries.py --db /path/to/store.db [--algo l2-v1] [--chunk 1000] [--dry-run]

Behavior (safe, idempotent):
- Ensures normalized columns exist (adds them if missing):
  normalized_vector, normalized_vector_dim, normalized_vector_algo, normalized_at, normalized_version
- For rows where normalized_vector is NULL or normalized_vector_algo/version differs from the requested algo/version,
  computes normalized_vector = vector_normalize(original_vector) and writes the normalized fields.
- Commits in batches (chunk) to limit transaction size.
- Does not delete or overwrite the original vector column.

IMPORTANT: This script modifies the SQLite DB in-place. Please back up the DB before running.

This file is the implementation artifact; DO NOT run it until the migration plan is reviewed/approved.
"""
from __future__ import annotations
import argparse
import json
import sqlite3
import time
from datetime import datetime, timezone
from typing import Optional

from plugins.memory.utils.normalization import vector_normalize

CURRENT_NORMALIZED_ALGO = "l2-v1"
CURRENT_NORMALIZED_VERSION = 1


def ensure_normalized_columns(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    # Get existing columns
    cur.execute("PRAGMA table_info('entries')")
    cols = {r[1] for r in cur.fetchall()}
    adds = []
    if "normalized_vector" not in cols:
        adds.append("ALTER TABLE entries ADD COLUMN normalized_vector TEXT")
    if "normalized_vector_dim" not in cols:
        adds.append("ALTER TABLE entries ADD COLUMN normalized_vector_dim INTEGER")
    if "normalized_vector_algo" not in cols:
        adds.append("ALTER TABLE entries ADD COLUMN normalized_vector_algo TEXT")
    if "normalized_at" not in cols:
        adds.append("ALTER TABLE entries ADD COLUMN normalized_at TEXT")
    if "normalized_version" not in cols:
        adds.append("ALTER TABLE entries ADD COLUMN normalized_version INTEGER")
    for s in adds:
        cur.execute(s)
    if adds:
        conn.commit()


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def backfill(db_path: str, algo: str = CURRENT_NORMALIZED_ALGO, version: int = CURRENT_NORMALIZED_VERSION, chunk: int = 1000, dry_run: bool = False) -> dict:
    result = {"scanned": 0, "updated": 0, "skipped": 0, "errors": 0}
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # Ensure normalized columns are present
        ensure_normalized_columns(conn)
        cur = conn.cursor()
        # Select rows that need normalization
        q = (
            "SELECT embedding_id, chunk_id, vector, vector_dim, score_meta, normalized_vector, normalized_vector_algo, normalized_version "
            "FROM entries "
            "WHERE normalized_vector IS NULL OR normalized_vector_algo != ? OR normalized_version != ?"
        )
        cur.execute(q, (algo, version))
        rows = cur.fetchall()
        total = len(rows)
        result["scanned"] = total
        if dry_run:
            conn.close()
            return result
        batch = []
        count = 0
        start = time.time()
        for r in rows:
            count += 1
            embedding_id = r["embedding_id"]
            try:
                vec = json.loads(r["vector"]) if r["vector"] else []
            except Exception:
                vec = []
            try:
                nvec = vector_normalize(vec)
            except Exception:
                nvec = []
            # Prepare update
            if nvec is None:
                nvec = []
            normalized_json = json.dumps(nvec)
            normalized_dim = len(nvec)
            normalized_at = now_utc_iso()
            batch.append((normalized_json, normalized_dim, algo, normalized_at, version, embedding_id))
            # Commit in chunks
            if len(batch) >= chunk:
                _apply_batch_update(conn, batch)
                result["updated"] += len(batch)
                batch = []
        # final batch
        if batch:
            _apply_batch_update(conn, batch)
            result["updated"] += len(batch)
        elapsed = time.time() - start
        result["time_sec"] = elapsed
    except Exception as e:
        result["errors"] += 1
        result["error_detail"] = str(e)
    finally:
        conn.close()
    return result


def _apply_batch_update(conn: sqlite3.Connection, batch: list) -> None:
    cur = conn.cursor()
    cur.executemany(
        "UPDATE entries SET normalized_vector = ?, normalized_vector_dim = ?, normalized_vector_algo = ?, normalized_at = ?, normalized_version = ? WHERE embedding_id = ?",
        batch,
    )
    conn.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill normalized vectors for LocalVectorStore entries")
    parser.add_argument("--db", required=True, help="Path to SQLite DB file")
    parser.add_argument("--algo", default=CURRENT_NORMALIZED_ALGO, help="Normalization algorithm id (default l2-v1)")
    parser.add_argument("--version", type=int, default=CURRENT_NORMALIZED_VERSION, help="Normalization version (default 1)")
    parser.add_argument("--chunk", type=int, default=1000, help="Commit chunk size")
    parser.add_argument("--dry-run", action="store_true", help="Do everything except write updates")
    args = parser.parse_args()
    print("Dry-run:" if args.dry_run else "Executing backfill:")
    print(f"DB: {args.db}  algo: {args.algo}  version: {args.version}  chunk: {args.chunk}")
    res = backfill(args.db, algo=args.algo, version=args.version, chunk=args.chunk, dry_run=args.dry_run)
    print("Result:", res)

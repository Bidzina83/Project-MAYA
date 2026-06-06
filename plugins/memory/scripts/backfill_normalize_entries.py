#!/usr/bin/env python3
"""Backfill normalized vectors as first-class fields.

Usage:
  backfill_normalize_entries.py --db /path/to/store.db [--chunk N] [--dry-run] [--algo l2-v1] [--version 1]

What it does:
- Adds normalized_vector, normalized_vector_dim, normalized_vector_algo, normalized_at, normalized_version columns if missing
- For each row in entries, computes L2-normalized vector from the stored vector column and writes into normalized_vector* fields
- Idempotent: only writes when normalized_vector is NULL or algorithm/version mismatches
- Preserves original vector column unchanged

This script is conservative by default: use --dry-run to preview changes.
"""
from __future__ import annotations
import argparse
import json
import sqlite3
from datetime import datetime
from typing import List

from plugins.memory.utils.normalization import vector_normalize, text_normalize


def ensure_columns(conn: sqlite3.Connection, dry_run: bool=False):
    cur = conn.cursor()
    # Check existing columns
    cur.execute("PRAGMA table_info(entries)")
    cols = [r[1] for r in cur.fetchall()]
    to_add = []
    if 'normalized_vector' not in cols:
        to_add.append("ALTER TABLE entries ADD COLUMN normalized_vector TEXT")
    if 'normalized_vector_dim' not in cols:
        to_add.append("ALTER TABLE entries ADD COLUMN normalized_vector_dim INTEGER")
    if 'normalized_vector_algo' not in cols:
        to_add.append("ALTER TABLE entries ADD COLUMN normalized_vector_algo TEXT")
    if 'normalized_at' not in cols:
        to_add.append("ALTER TABLE entries ADD COLUMN normalized_at TEXT")
    if 'normalized_version' not in cols:
        to_add.append("ALTER TABLE entries ADD COLUMN normalized_version INTEGER")
    if to_add:
        if dry_run:
            print('dry-run: would add columns:', to_add)
        else:
            for stmt in to_add:
                cur.execute(stmt)
            conn.commit()


def rows_to_process(conn: sqlite3.Connection, chunk: int):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) FROM entries")
    total = cur.fetchone()[0]
    for offset in range(0, total, chunk):
        cur.execute("SELECT embedding_id, chunk_id, vector, vector_dim, normalized_vector, normalized_vector_algo, normalized_version, score_meta FROM entries LIMIT ? OFFSET ?", (chunk, offset))
        yield cur.fetchall()


def backfill(db_path: str, chunk: int=100, dry_run: bool=False, algo: str='l2-v1', version: int=1):
    conn = sqlite3.connect(db_path)
    ensure_columns(conn, dry_run)
    updated = 0
    for batch in rows_to_process(conn, chunk):
        updates = []
        for row in batch:
            embedding_id, chunk_id, vec_json, vec_dim, nvec_json, nvec_algo, nvec_version, score_meta_json = row
            # parse existing
            try:
                vec = json.loads(vec_json) if vec_json else []
            except Exception:
                vec = []
            try:
                score_meta = json.loads(score_meta_json) if score_meta_json else {}
            except Exception:
                score_meta = {}
            # compute normalized vector
            nvec = vector_normalize(vec)
            # decide whether to write: if normalized_vector missing or algorithm/version mismatch
            need_write = False
            if not nvec_json:
                need_write = True
            else:
                try:
                    if (nvec_algo != algo) or (nvec_version != version):
                        need_write = True
                except Exception:
                    need_write = True
            if need_write:
                updates.append((json.dumps(nvec), len(nvec), algo, datetime.utcnow().isoformat() + 'Z', version, embedding_id))
        if updates:
            if dry_run:
                updated += len(updates)
                continue
            cur = conn.cursor()
            for u in updates:
                cur.execute(
                    "UPDATE entries SET normalized_vector = ?, normalized_vector_dim = ?, normalized_vector_algo = ?, normalized_at = ?, normalized_version = ? WHERE embedding_id = ?",
                    u
                )
            conn.commit()
            updated += len(updates)
    conn.close()
    print(f"Backfill complete. Updated {updated} rows (dry_run={dry_run}).")
    return {"updated": updated}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', required=True, help='Path to SQLite DB')
    parser.add_argument('--chunk', type=int, default=100, help='Batch size')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--algo', default='l2-v1')
    parser.add_argument('--version', type=int, default=1)
    args = parser.parse_args()
    res = backfill(args.db, chunk=args.chunk, dry_run=args.dry_run, algo=args.algo, version=args.version)
    print(res)

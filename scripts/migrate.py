"""Migration helper for legacy persistence adapters.

This script provides two modes:
- If Alembic is available, it will prefer to invoke Alembic programmatically (scaffolding
  files are added under alembic/ but alembic is optional at runtime).
- Fallback: a simple programmatic migration that reads the legacy sqlite `memory_kv`
  table and writes to a destination that can be either the project-maya registry schema
  (entries + embeddings) or the simpler memory_entries table used by earlier prototypes.

The migrate(from_src, to_dest, dry_run, target_schema) function is importable and unit-testable.
"""
from __future__ import annotations
import argparse
import sqlite3
import os
import json
from typing import Optional
from datetime import datetime, timezone


def _ensure_registry_schema(conn: sqlite3.Connection):
    """Ensure destination has the Project-MAYA registry schema (entries + embeddings).
    This is idempotent: it creates tables only if they don't already exist.
    """
    cur = conn.cursor()
    # embeddings table (observed in live registry)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS embeddings (
            chunk_id TEXT PRIMARY KEY,
            embedding_path TEXT,
            source_path TEXT,
            source_hash TEXT,
            model TEXT,
            extractor_version TEXT,
            embedding_timestamp TEXT,
            updated_at TEXT
        )
        """
    )
    # entries table (observed in live registry)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY,
            embedding_id TEXT UNIQUE,
            chunk_id TEXT,
            vector TEXT,
            vector_dim INTEGER,
            created_at TEXT,
            source_path TEXT,
            score_meta TEXT
        )
        """
    )
    conn.commit()


def _insert_into_registry(conn: sqlite3.Connection, key: str, value: str, migrated_from: str):
    cur = conn.cursor()
    # created_at as ISO UTC
    created_at = datetime.now(timezone.utc).isoformat()
    # score_meta: record provenance
    score_meta = json.dumps({"migrated_from": migrated_from})
    # Use key as embedding_id/chunk_id to preserve original key material.
    cur.execute(
        "INSERT OR REPLACE INTO entries(embedding_id, chunk_id, vector, vector_dim, created_at, source_path, score_meta) VALUES(?, ?, ?, ?, ?, ?, ?)",
        (str(key), str(key), str(value), None, created_at, "legacy_kv", score_meta),
    )


def migrate(from_src: str, to_dest: str, dry_run: bool = True, target_schema: str = "registry") -> dict:
    """Migrate data from a legacy sqlite memory_kv schema to a destination DB.

    - from_src: path to legacy sqlite DB file
    - to_dest: path for destination sqlite DB file (will be created unless dry_run)
    - dry_run: if True, don't write the destination, only report what would happen
    - target_schema: either 'registry' to target the Project-MAYA registry schema
      (entries + embeddings) or 'memory_entries' to use the simple memory_entries table.

    Returns a dict with summary information.
    """
    summary = {"migrated": 0, "source_rows": 0, "to_path": to_dest, "actions": [], "target_schema": target_schema}

    if not os.path.exists(from_src):
        raise FileNotFoundError(f"legacy source DB not found: {from_src}")

    src_conn = sqlite3.connect(from_src)
    src_cur = src_conn.cursor()

    # Discover whether legacy table exists
    src_cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_kv'"
    )
    if not src_cur.fetchone():
        raise RuntimeError("legacy table 'memory_kv' not found in source DB")

    src_cur.execute("SELECT key, value FROM memory_kv")
    rows = src_cur.fetchall()
    summary["source_rows"] = len(rows)

    summary["actions"].append(f"Discovered {len(rows)} rows in source {from_src}")

    if dry_run:
        summary["actions"].append(f"Would copy {len(rows)} rows from {from_src} to {to_dest} using target_schema={target_schema}")
        src_conn.close()
        return summary

    # Create destination DB and desired schema
    dst_conn = sqlite3.connect(to_dest)

    if target_schema == "registry":
        _ensure_registry_schema(dst_conn)
    else:
        dst_cur = dst_conn.cursor()
        dst_cur.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_entries (
                key TEXT PRIMARY KEY,
                value TEXT,
                migrated_from TEXT
            )
            """
        )
        dst_conn.commit()

    for key, value in rows:
        if target_schema == "registry":
            _insert_into_registry(dst_conn, key, value, os.path.abspath(from_src))
        else:
            dst_cur = dst_conn.cursor()
            dst_cur.execute(
                "INSERT OR REPLACE INTO memory_entries(key, value, migrated_from) VALUES(?, ?, ?)",
                (key, value, os.path.abspath(from_src)),
            )
            summary["migrated"] += 1
        summary["migrated"] += 1 if target_schema == "registry" else 0

    dst_conn.commit()
    dst_conn.close()
    src_conn.close()
    summary["actions"].append(f"Copied {summary['migrated']} rows into {to_dest} using schema {target_schema}")
    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Show migration plan only")
    p.add_argument("--from", dest="from_src", required=True, help="Legacy sqlite source path")
    p.add_argument("--to", dest="to_dest", required=True, help="Destination sqlite path")
    p.add_argument("--target-schema", dest="target_schema", choices=["registry", "memory_entries"], default="registry", help="Target schema for the migration")
    args = p.parse_args()

    try:
        res = migrate(args.from_src, args.to_dest, dry_run=args.dry_run, target_schema=args.target_schema)
    except Exception as e:
        print("Migration failed:", e)
        raise
    else:
        print("Migration result:", res)


if __name__ == "__main__":
    main()

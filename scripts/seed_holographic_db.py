#!/usr/bin/env python3
"""Create a minimal holographic SQLite store for local testing.

This script is intentionally explicit: it requires --confirm to make any on-disk changes.
It creates a MemoryStore at the given path (default: ./holographic_test.db) and inserts
a few sample facts so the HolographicAdapter/FactRetriever can be exercised in CI/local.

Usage:
  python3 scripts/seed_holographic_db.py --db /tmp/holographic_test.db --confirm
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", dest="db_path", default="./holographic_test.db", help="Path to sqlite DB to create")
    p.add_argument("--confirm", action="store_true", help="Confirm creation of the DB and sample data")
    args = p.parse_args(argv)

    if not args.confirm:
        print("This script will create or overwrite the holographic DB. Pass --confirm to proceed.")
        return 2

    db_path = Path(args.db_path).expanduser().resolve()
    print(f"Creating holographic memory DB at: {db_path}")

    # Import MemoryStore lazily so the script can run even when holographic package missing
    try:
        from plugins.memory.holographic.store import MemoryStore
    except Exception as e:
        print("Failed to import MemoryStore from plugins.memory.holographic.store:", e)
        return 3

    store = MemoryStore(db_path=db_path)

    # Insert a few sample facts
    samples = [
        ("The sky is blue.", "general", "test"),
        ("Python is a programming language.", "tech", "tests"),
        ("Alice went to the market.", "narrative", "test"),
    ]

    for content, category, tags in samples:
        try:
            fid = store.add_fact(content, category=category, tags=tags)
            print(f"Inserted fact id={fid} '"+content[:40]+("..." if len(content)>40 else "") + "'")
        except Exception as e:
            print(f"Failed to add fact: {e}")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

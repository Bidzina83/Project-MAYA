#!/usr/bin/env python3
"""Registry control CLI: list/get/migrate-sqlite

Examples:
  registry_ctl.py list --storage-root /opt/data/maya-memory-repo
  registry_ctl.py get abc123 --storage-root /opt/data/maya-memory-repo
  registry_ctl.py migrate-sqlite --storage-root /opt/data/maya-memory-repo
"""
import argparse
import json
import os
import sys

from plugins.memory.ingest.registry import MemoryRegistry
from plugins.memory.ingest.sqlite_registry import SQLiteMemoryRegistry


def cmd_list(args):
    reg = MemoryRegistry(args.storage_root)
    data = reg.list_entries()
    print(json.dumps(data, indent=2))


def cmd_get(args):
    reg = MemoryRegistry(args.storage_root)
    e = reg.get_entry(args.chunk_id)
    if e is None:
        print(f"Not found: {args.chunk_id}", file=sys.stderr)
        return 2
    print(json.dumps(e, indent=2))
    return 0


def cmd_migrate_sqlite(args):
    reg = MemoryRegistry(args.storage_root)
    data = reg.list_entries()
    # convert nested dict-of-dicts to mapping chunk_id->metadata
    to_import = {k: v for k, v in data.items()}
    s = SQLiteMemoryRegistry(args.storage_root)
    s.bulk_import(to_import)
    print(f"Migrated {len(to_import)} entries to {s.db_path}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--storage-root", required=True)
    sub = p.add_subparsers(dest="cmd")
    sub.required = True
    sub.add_parser("list")
    getp = sub.add_parser("get")
    getp.add_argument("chunk_id")
    sub.add_parser("migrate-sqlite")
    args = p.parse_args(argv)

    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "get":
        return cmd_get(args)
    if args.cmd == "migrate-sqlite":
        return cmd_migrate_sqlite(args)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/opt/hermes/.venv/bin/python
"""Registry monitor: record JSON registry size and entry count, and SQLite counts if present.
Appends a JSON line to STORAGE_ROOT/registry/monitor.log
Usage: python3 registry_monitor.py --storage-root /opt/data/maya-memory-repo
This script is intentionally robust: it runs under the project venv and ensures the data shim path is available on sys.path.
"""
import argparse
import json
import os
import sys
from datetime import datetime
import sqlite3

# Ensure shim is available so imports that rely on /opt/hermes path succeed in varied environments
shim = '/opt/data/.hermes_shim'
if os.path.isdir(shim) and shim not in sys.path:
    sys.path.insert(0, shim)

p = argparse.ArgumentParser()
p.add_argument("--storage-root", required=False, default="/opt/data/maya-memory-repo")
args = p.parse_args()

storage = args.storage_root
reg_dir = os.path.join(storage, "registry")
os.makedirs(reg_dir, exist_ok=True)
json_path = os.path.join(reg_dir, "memory_registry.json")
log_path = os.path.join(reg_dir, "monitor.log")
sqlite_path = os.path.join(reg_dir, "memory_registry.sqlite")

report = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "storage_root": storage,
    "json_exists": False,
    "json_bytes": 0,
    "json_entries": 0,
    "sqlite_exists": False,
    "sqlite_rows": None,
    "sqlite_path": sqlite_path,
}

if os.path.exists(json_path):
    report["json_exists"] = True
    try:
        report["json_bytes"] = os.path.getsize(json_path)
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                report["json_entries"] = len(data)
            else:
                try:
                    report["json_entries"] = len(data)
                except Exception:
                    report["json_entries"] = 0
    except Exception as e:
        report["json_error"] = str(e)

if os.path.exists(sqlite_path):
    report["sqlite_exists"] = True
    try:
        conn = sqlite3.connect(sqlite_path)
        cur = conn.cursor()
            # Check for known table names used by different LocalVectorStore implementations
        cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name IN ('embeddings','entries');")
        tbl_count = cur.fetchone()[0]
        if tbl_count > 0:
            # prefer entries table (likely authoritative), otherwise fall back to embeddings
            cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='entries';")
            if cur.fetchone()[0] == 1:
                cur.execute("SELECT count(*) FROM entries;")
            else:
                cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='embeddings';")
                if cur.fetchone()[0] == 1:
                    cur.execute("SELECT count(*) FROM embeddings;")
                else:
                    report["sqlite_rows"] = 0
            report["sqlite_rows"] = cur.fetchone()[0]
        else:
            report["sqlite_rows"] = 0
        conn.close()
    except Exception as e:
        report["sqlite_error"] = str(e)

# append JSON line to log
with open(log_path, "a", encoding="utf-8") as f:
    f.write(json.dumps(report, ensure_ascii=False) + "\n")

# also print report to stdout
print(json.dumps(report, indent=2, ensure_ascii=False))

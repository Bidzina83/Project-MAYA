#!/usr/bin/env python3
"""Simple alert checker for registry monitor.log

Reads STORAGE_ROOT/registry/monitor.log and checks the latest entry against thresholds.
Usage:
  registry_alert.py --storage-root /opt/data/maya-memory-repo --max-bytes 100000 --max-entries 1000
Exit code 0 -> OK; 2 -> alert; 1 -> error
"""
import argparse
import json
import os
import sys

p = argparse.ArgumentParser()
p.add_argument("--storage-root", required=False, default="/opt/data/maya-memory-repo")
p.add_argument("--max-bytes", type=int, default=100000)
p.add_argument("--max-entries", type=int, default=1000)
args = p.parse_args()

logp = os.path.join(args.storage_root, "registry", "monitor.log")
if not os.path.exists(logp):
    print("monitor.log not found; no data yet")
    sys.exit(0)

try:
    with open(logp, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    if not lines:
        print("monitor.log empty")
        sys.exit(0)
    last = json.loads(lines[-1])
except Exception as e:
    print("error reading monitor.log:", e, file=sys.stderr)
    sys.exit(1)

alerts = []
jb = last.get("json_bytes", 0) or 0
je = last.get("json_entries", 0) or 0
if jb >= args.max_bytes:
    alerts.append(f"json_bytes {jb} >= threshold {args.max_bytes}")
if je >= args.max_entries:
    alerts.append(f"json_entries {je} >= threshold {args.max_entries}")

print("latest monitor entry:\n", json.dumps(last, indent=2))
if alerts:
    print("ALERTS:")
    for a in alerts:
        print(" -", a)
    sys.exit(2)
else:
    print("OK: thresholds not exceeded")
    sys.exit(0)

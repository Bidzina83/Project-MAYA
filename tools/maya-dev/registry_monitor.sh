#!/bin/sh
# registry_monitor wrapper for CI/dev repo (copy target for scheduler)
/opt/hermes/.venv/bin/python /opt/hermes/plugins/memory/ingest/bin/registry_monitor.py --storage-root /opt/data/maya-memory-repo

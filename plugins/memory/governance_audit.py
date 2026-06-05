from __future__ import annotations
import json
import os
from datetime import datetime
from typing import Optional
from plugins.memory.governance_validator import GovernanceReportV2
import uuid

DEFAULT_AUDIT_DIR = "/opt/data/maya-memory-repo/governance_audit"


def persist_report(report: GovernanceReportV2, dirpath: Optional[str] = None) -> str:
    """Persist a GovernanceReportV2 to disk as a JSON file.

    Returns the absolute path to the written file.

    This is a simple file-backed audit sink suitable for local deployments and CI.
    File name format: governance_report_v2-<iso_ts>-<uuid4>.json
    """
    d = dirpath or DEFAULT_AUDIT_DIR
    os.makedirs(d, exist_ok=True)
    iso = datetime.utcnow().isoformat().replace(":", "-")
    fname = f"governance_report_v2-{iso}-{uuid.uuid4().hex}.json"
    path = os.path.join(d, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report.to_json())
    return os.path.abspath(path)


def load_report(path: str) -> dict:
    """Load and return a persisted report as a dict."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

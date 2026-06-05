import json
import tempfile
import os

from plugins.memory.governance_validator import GovernanceValidator, GovernancePolicy
from plugins.memory.governance_audit import persist_report, load_report


def _make_retrieval(chunk_id: str, trust: float = 0.1):
    return {
        "id": f"id-{chunk_id}",
        "chunk_id": chunk_id,
        "content": "sensitive info",
        "score": 0.9,
        "trust_score": trust,
        "similarity": 0.9,
        "provider": "local",
        "source_path": f"/data/{chunk_id}.txt",
        "created_at": "2026-01-01T00:00:00Z",
        "meta": {},
    }


def test_persist_and_load_governance_report(tmp_path):
    policy = GovernancePolicy(min_trust=0.5)
    gv = GovernanceValidator(policy=policy)

    r1 = _make_retrieval("a", trust=0.1)
    r2 = _make_retrieval("b", trust=1.0)

    gv.validate([r1, r2])
    v2 = gv.last_report_v2()
    assert v2 is not None

    # persist to tmp dir
    out_path = persist_report(v2, dirpath=str(tmp_path))
    assert os.path.exists(out_path)

    # load and check
    loaded = load_report(out_path)
    assert loaded["version"] == "v2"
    assert loaded["total"] == 2
    assert "annotations" in loaded

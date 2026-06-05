import pytest
from typing import Optional
from datetime import datetime, timezone, timedelta

from plugins.memory.governance_validator import GovernanceValidator, GovernancePolicy


def make_retrieval(chunk_id: str, trust: float = 1.0, days_old: Optional[int] = None, provider: str = "local", meta=None, content="hello world"):
    if days_old is not None:
        created_at = (datetime.now(timezone.utc) - timedelta(days=days_old)).isoformat()
    else:
        created_at = datetime.now(timezone.utc).isoformat()
    return {
        "chunk_id": chunk_id,
        "content": content,
        "trust_score": trust,
        "score": 0.5,
        "created_at": created_at,
        "provider": provider,
        "meta": meta or {},
    }


def test_validator_generates_warnings_for_low_trust_and_old_entries():
    policy = GovernancePolicy(min_trust=0.8, max_age_days=30)
    gv = GovernanceValidator(policy=policy)

    r1 = make_retrieval("c1", trust=0.5, days_old=1)
    r2 = make_retrieval("c2", trust=0.9, days_old=40)
    r3 = make_retrieval("c3", trust=0.95, days_old=5)

    report = gv.validate([r1, r2, r3])

    assert report.total == 3
    # expect warnings for r1 (low_trust) and r2 (too_old)
    reasons = [rc for a in report.warnings for rc in a.reasons]
    assert "low_trust" in reasons
    assert any("too_old" in a.reasons for a in report.warnings)
    assert report.summary.get("kept", 0) >= 0


def test_validator_provider_allowlist_and_missing_provenance():
    policy = GovernancePolicy(provider_allowlist=["trusted"], required_provenance_fields=["source_url"])
    gv = GovernanceValidator(policy=policy)

    r1 = make_retrieval("c1", provider="untrusted")
    r2 = make_retrieval("c2", provider="trusted", meta={})
    r3 = make_retrieval("c3", provider="trusted", meta={"source_url": "http://x"})

    report = gv.validate([r1, r2, r3])
    # c1 should be provider_not_allowed
    assert any(a.chunk_id == "c1" and "provider_not_allowed" in a.reasons for a in report.warnings)
    # c2 should be missing_provenance
    assert any(a.chunk_id == "c2" and any(r.startswith("missing_provenance") for r in a.reasons) for a in report.warnings)
    # c3 should have no warnings
    assert not any(a.chunk_id == "c3" for a in report.warnings)

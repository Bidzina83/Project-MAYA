from plugins.memory.governance_validator import GovernanceValidator, GovernancePolicy


def _make_retrieval(chunk_id: str, content: str, trust: float = 1.0, created_at: str = "2026-01-01T00:00:00Z", provider: str = "local"):
    return {
        "id": f"id-{chunk_id}",
        "chunk_id": chunk_id,
        "content": content,
        "score": 0.9,
        "trust_score": trust,
        "similarity": 0.9,
        "provider": provider,
        "source_path": f"/data/{chunk_id}.txt",
        "created_at": created_at,
        "meta": {},
    }


def test_governance_v2_report_and_annotations():
    policy = GovernancePolicy(min_trust=0.5, max_age_days=365)
    gv = GovernanceValidator(policy=policy)

    # r1 low trust
    r1 = _make_retrieval("a", "some text", trust=0.1)
    # r2 ok
    r2 = _make_retrieval("b", "other text", trust=1.0)

    gv.validate([r1, r2])
    v2 = gv.last_report_v2()
    assert v2 is not None
    assert v2.version == "v2"
    assert v2.total == 2
    # annotations should include two entries
    assert len(v2.annotations) == 2
    # find annotation for r1 and assert low_trust reason present and severity is warning or error
    a1 = next(a for a in v2.annotations if a.chunk_id == "a")
    assert "low_trust" in a1.reasons
    assert a1.severity in ("warning", "error")

    # summary should include low_trust count
    assert v2.summary.get("low_trust", 0) >= 1

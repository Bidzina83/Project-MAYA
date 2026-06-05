from plugins.memory.governance_validator import GovernanceValidator, GovernancePolicy


def _make_retrieval(chunk_id: str, trust: float = 0.1):
    return {
        "id": f"id-{chunk_id}",
        "chunk_id": chunk_id,
        "content": "some content",
        "score": 0.9,
        "trust_score": trust,
        "similarity": 0.9,
        "provider": "local",
        "source_path": f"/data/{chunk_id}.txt",
        "created_at": "2026-01-01T00:00:00Z",
        "meta": {},
    }


def test_explain_returns_audit_entry_and_none():
    policy = GovernancePolicy(min_trust=0.5)
    gv = GovernanceValidator(policy=policy)

    r1 = _make_retrieval("a", trust=0.1)
    gv.validate([r1])

    ae = gv.explain("a")
    assert ae is not None
    assert ae.chunk_id == "a"
    # explain should surface reasons that include low_trust for this input
    assert any("low_trust" in r for r in ae.reasons) or ae.action == "warning"

    # explain for unknown chunk should return None
    assert gv.explain("does-not-exist") is None

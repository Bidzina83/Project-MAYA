import json
import jsonschema

from plugins.memory.governance_validator import GovernanceValidator, GovernancePolicy


def _make_retrieval(chunk_id: str, content: str, trust: float = 1.0):
    return {
        "id": f"id-{chunk_id}",
        "chunk_id": chunk_id,
        "content": content,
        "score": 0.9,
        "trust_score": trust,
        "similarity": 0.9,
        "provider": "local",
        "source_path": f"/data/{chunk_id}.txt",
        "created_at": "2026-01-01T00:00:00Z",
        "meta": {},
    }


def test_privacy_block_triggers_redaction_hint():
    # privacy regex to match the literal 'SSN' token in content
    policy = GovernancePolicy(min_trust=0.0)
    policy.privacy_blocking_regexes = [r"SSN"]

    gv = GovernanceValidator(policy=policy)

    r = _make_retrieval("p1", "This text contains an SSN 123-45-6789 that should be redacted.")
    gv.validate([r])
    v2 = gv.last_report_v2()
    assert v2 is not None
    a = next((a for a in v2.annotations if a.chunk_id == "p1"), None)
    assert a is not None
    # enforcement_hints should suggest redaction for privacy_block
    eh = a.enforcement_hints
    assert eh is not None
    # either redact list present or block_flag True as per policy or fallback
    assert (eh.redact is not None and len(eh.redact) > 0) or (eh.block_flag is True)

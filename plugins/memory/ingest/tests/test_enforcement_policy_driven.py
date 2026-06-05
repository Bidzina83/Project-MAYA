import json
import jsonschema

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


def test_policy_driven_enforcement_hints_and_schema():
    # Define a policy that maps reason codes to enforcement rules
    policy = GovernancePolicy(min_trust=0.5)
    # inject a simple rule set via attribute to avoid changing constructor (policy is a dataclass)
    policy.enforcement_rules = {
        "low_trust": {"score_adjust": 0.6, "note": "policy: reduce by derived trust"},
        "privacy_block": {"block_flag": True, "redact": [{"reason": "privacy_block"}], "note": "policy: redact/ban"},
    }

    gv = GovernanceValidator(policy=policy)

    r1 = _make_retrieval("a", "some text", trust=0.1)
    r2 = _make_retrieval("b", "other text", trust=1.0)

    gv.validate([r1, r2])
    v2 = gv.last_report_v2()
    assert v2 is not None
    # find annotation for low-trust chunk
    a1 = next(a for a in v2.annotations if a.chunk_id == "a")
    assert a1 is not None
    hints = a1.enforcement_hints
    assert hints is not None
    # policy rule should have applied (score_adjust roughly 0.6 or derived trust)
    assert hints.score_adjust is not None

    # Validate enforcement_hint JSON schema
    schema_path = "docs/enforcement_hint_schema.json"
    with open(schema_path, "r") as f:
        schema = json.load(f)

    # enforcement_hints is serializable
    eh = a1.enforcement_hints.to_dict()
    jsonschema.validate(instance=eh, schema=schema)

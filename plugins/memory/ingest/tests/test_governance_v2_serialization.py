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


def test_governance_v2_serialization_matches_schema():
    policy = GovernancePolicy(min_trust=0.5, max_age_days=365)
    gv = GovernanceValidator(policy=policy)

    r1 = _make_retrieval("a", "some text", trust=0.1)
    r2 = _make_retrieval("b", "other text", trust=1.0)

    gv.validate([r1, r2])
    v2 = gv.last_report_v2()
    assert v2 is not None

    # Serialize to dict and JSON
    payload = v2.to_dict()
    text = v2.to_json()
    parsed = json.loads(text)
    assert parsed["version"] == "v2"
    assert parsed["total"] == 2

    # Validate against JSON Schema
    schema_path = "docs/governance_report_v2_schema.json"
    with open(schema_path, "r") as f:
        schema = json.load(f)

    jsonschema.validate(instance=payload, schema=schema)

import json

from plugins.memory.governance_validator import REASON_CODE_CATALOG


def test_reason_code_catalog_is_well_formed():
    # load the canonical docs file and compare
    with open("docs/reason_code_catalog.json", "r") as f:
        docs_catalog = json.load(f)

    # Ensure every code in the docs file appears in the in-code catalog and vice versa
    doc_keys = set(docs_catalog.keys())
    code_keys = set(REASON_CODE_CATALOG.keys())

    assert doc_keys <= code_keys or code_keys <= doc_keys

    # Check each entry for required fields and valid severity
    allowed_severities = {"info", "warning", "error"}
    for k, v in REASON_CODE_CATALOG.items():
        assert isinstance(k, str) and k
        assert isinstance(v, dict)
        assert "description" in v and isinstance(v["description"], str)
        assert "severity" in v and v["severity"] in allowed_severities

    # Validate docs file entries too
    for k, v in docs_catalog.items():
        assert "description" in v and "severity" in v
        assert v["severity"] in allowed_severities

"""Verify bounded reset authority evidence on frozen Patch 34."""
import json

from verify_governance_g2_reset_crash import inventory_digest, digest, ROOT, PARENT, verify_parent, FIXTURES as BASE_FIXTURES

INPUTS = ROOT / "docs/architecture/governance-g2-reset-combined-faults.json"
TEST = "tests/hermes_g2_reset_combined_faults_native.py"
FIXTURES = BASE_FIXTURES | {"tests/hermes_g2_reset_contention_native.py"}


def contract():
    data = json.loads(INPUTS.read_text(encoding="utf-8"))
    if (type(data.get("schema_version")) is not int or data["schema_version"] != 1
            or data.get("production_qualified") is not False or data.get("acceptance") != "pending_review"
            or data.get("qualification") != "source_reset_combined_faults_only"
            or type(data.get("expected_native_tests")) is not int or data["expected_native_tests"] != 13
            or data.get("parent_inputs_sha256") != digest(PARENT.read_bytes())
            or data.get("test_sha256") != digest((ROOT / TEST).read_bytes())
            or set(data.get("fixture_sha256", {})) != FIXTURES
            or any(data["fixture_sha256"][name] != digest((ROOT / name).read_bytes()) for name in FIXTURES)
            or any(type(data.get(name)) is not str or len(data[name]) != 64
                   or any(char not in "0123456789abcdef" for char in data[name])
                   for name in ("native_inventory_sha256", "host_inventory_sha256"))):
        raise ValueError("g2.reset_combined_faults_contract_invalid")
    return data


def verify_stage(stage):
    data = contract()
    verify_parent(stage, ROOT / ".codex-build/governance-g2-reset-composition-20261006-final",
                  ROOT / ".codex-build/governance-g2-prompt-cache-20261005-final-c")
    if (json.loads((stage / "g2-reset-gate-manifest.json").read_text(encoding="utf-8"))
            != json.loads(PARENT.read_text(encoding="utf-8"))
            or inventory_digest(stage / "source") != data["native_inventory_sha256"]
            or inventory_digest(stage / "host") != data["host_inventory_sha256"]):
        raise ValueError("g2.reset_combined_faults_inventory_invalid")
    return stage / "source", stage / "host/src"

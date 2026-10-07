"""Verify independent process-crash evidence over unchanged Patch 34 source."""
import json

from prepare_governance_g2_reset_gate import ROOT, INPUTS as PARENT, verify_stage as verify_parent, inventory
from prepare_governance_g2_caller import digest

INPUTS = ROOT / "docs/architecture/governance-g2-reset-crash.json"
TEST = "tests/hermes_g2_reset_crash_native.py"
FIXTURES = {"tests/hermes_g2_reset_gate_native.py", "tests/hermes_g2_reset_composition_native.py",
            "tests/hermes_g2_prompt_cache_native.py", "tests/hermes_g2_recognition_native.py",
            "tests/hermes_g2_create_loop_native.py", "tests/hermes_g2_caller_native.py",
            "tests/hermes_g2_create_native.py", "tests/hermes_g2_restart_loop_native.py"}


def inventory_digest(path):
    return digest(json.dumps(inventory(path), sort_keys=True, separators=(",", ":")).encode())


def contract():
    data = json.loads(INPUTS.read_text(encoding="utf-8"))
    if (type(data.get("schema_version")) is not int or data["schema_version"] != 1
            or data.get("production_qualified") is not False or data.get("acceptance") != "pending_review"
            or data.get("qualification") != "source_reset_process_crash_only"
            or type(data.get("expected_native_tests")) is not int or data["expected_native_tests"] != 8
            or data.get("parent_inputs_sha256") != digest(PARENT.read_bytes())
            or data.get("test_sha256") != digest((ROOT / TEST).read_bytes())
            or set(data.get("fixture_sha256", {})) != FIXTURES
            or any(data["fixture_sha256"][name] != digest((ROOT / name).read_bytes()) for name in FIXTURES)
            or any(type(data.get(name)) is not str or len(data[name]) != 64
                   or any(char not in "0123456789abcdef" for char in data[name])
                   for name in ("native_inventory_sha256", "host_inventory_sha256"))):
        raise ValueError("g2.reset_crash_contract_invalid")
    return data


def verify_worker_stage(stage):
    data = contract()
    if (json.loads((stage / "g2-reset-gate-manifest.json").read_text(encoding="utf-8"))
            != json.loads(PARENT.read_text(encoding="utf-8"))
            or inventory_digest(stage / "source") != data["native_inventory_sha256"]
            or inventory_digest(stage / "host") != data["host_inventory_sha256"]):
        raise ValueError("g2.reset_crash_inventory_invalid")
    return stage / "source", stage / "host/src"


def verify_stage(stage):
    verify_parent(stage, ROOT / ".codex-build/governance-g2-reset-composition-20261006-final",
                  ROOT / ".codex-build/governance-g2-prompt-cache-20261005-final-c")
    return verify_worker_stage(stage)

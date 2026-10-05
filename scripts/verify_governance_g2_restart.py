"""Verify separate process-restart evidence over the frozen Patch 31 source."""
import json
from pathlib import Path

from prepare_governance_g2_prompt_cache import INPUTS as PARENT, verify_stage as verify_parent
from prepare_governance_g2_recognition import ROOT, inventory
from prepare_governance_g2_caller import digest

INPUTS = ROOT / "docs/architecture/governance-g2-restart-loop.json"
TEST = "tests/hermes_g2_restart_loop_native.py"
FIXTURES = {
    "tests/hermes_g2_prompt_cache_native.py", "tests/hermes_g2_recognition_native.py",
    "tests/hermes_g2_create_loop_native.py", "tests/hermes_g2_caller_native.py",
    "tests/hermes_g2_create_native.py",
}


def inventory_digest(path):
    return digest(json.dumps(inventory(path), sort_keys=True, separators=(",", ":")).encode())


def contract():
    data = json.loads(INPUTS.read_text(encoding="utf-8"))
    if (type(data["schema_version"]) is not int or data["schema_version"] != 1
            or data["production_qualified"] is not False or data["acceptance"] != "pending_review"
            or data["qualification"] != "source_process_restart_loop_only"
            or type(data["expected_native_tests"]) is not int or data["expected_native_tests"] != 4
            or data["parent_inputs_sha256"] != digest(PARENT.read_bytes())
            or data["test_sha256"] != digest((ROOT / TEST).read_bytes())
            or set(data["fixture_sha256"]) != FIXTURES
            or any(digest((ROOT / path).read_bytes()) != sha for path, sha in data["fixture_sha256"].items())
            or any(type(data[name]) is not str or len(data[name]) != 64
                   or any(char not in "0123456789abcdef" for char in data[name])
                   for name in ("native_inventory_sha256", "host_inventory_sha256"))):
        raise ValueError("g2.restart_contract_invalid")
    return data


def verify_worker_stage(stage):
    """Each new process checks complete effective trees against reviewed hashes."""
    data = contract()
    if (json.loads((stage / "g2-prompt-cache-manifest.json").read_text(encoding="utf-8"))
            != json.loads(PARENT.read_text(encoding="utf-8"))
            or inventory_digest(stage / "source") != data["native_inventory_sha256"]
            or inventory_digest(stage / "host") != data["host_inventory_sha256"]):
        raise ValueError("g2.restart_inventory_invalid")
    return stage / "source", stage / "host/src"


def verify_stage(stage):
    # The supervisor validates the frozen ancestry as well as effective bytes.
    verify_parent(stage)
    return verify_worker_stage(stage)

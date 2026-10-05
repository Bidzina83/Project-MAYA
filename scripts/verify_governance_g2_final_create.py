"""Independent qualification contract for unchanged final Patch 31 source."""
import json

from prepare_governance_g2_caller import digest
from prepare_governance_g2_recognition import ROOT
from verify_governance_g2_restart import INPUTS as PARENT, verify_stage as verify_parent

INPUTS = ROOT / "docs/architecture/governance-g2-final-create.json"
TEST = "tests/hermes_g2_final_create_native.py"
FIXTURES = {
    "tests/hermes_g2_create_native.py", "tests/hermes_g2_caller_native.py",
    "tests/hermes_g2_caller_qualification_native.py", "tests/hermes_g2_create_authority_loss_native.py",
    "tests/hermes_g2_create_failures_native.py", "tests/hermes_g2_reader_native.py",
    "tests/hermes_g2_create_crash_native.py",
}


def contract():
    data = json.loads(INPUTS.read_text(encoding="utf-8"))
    if (type(data.get("schema_version")) is not int or data["schema_version"] != 1
            or data.get("production_qualified") is not False
            or data.get("acceptance") != "pending_review"
            or data.get("qualification") != "source_final_create_matrix_only"
            or type(data.get("expected_native_tests")) is not int or data["expected_native_tests"] != 80
            or data.get("parent_inputs_sha256") != digest(PARENT.read_bytes())
            or data.get("test_sha256") != digest((ROOT / TEST).read_bytes())
            or set(data.get("fixture_sha256", {})) != FIXTURES
            or any(digest((ROOT / path).read_bytes()) != sha
                   for path, sha in data["fixture_sha256"].items())):
        raise ValueError("g2.final_create_contract_invalid")
    return data


def verify_stage(stage):
    contract()
    return verify_parent(stage)

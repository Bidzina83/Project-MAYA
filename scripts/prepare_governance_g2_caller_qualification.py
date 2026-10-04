"""Pin native caller failure diagnostics over the unchanged source overlay."""
import argparse
import json
from pathlib import Path

from prepare_governance_g2_caller import ROOT, INPUTS as PARENT, overlay_contract, prepare, verify_caller_stage, digest

INPUTS = ROOT / "docs/architecture/governance-g2-caller-qualification.json"
TEST = ROOT / "tests/hermes_g2_caller_qualification_native.py"


def qualification_contract():
    overlay_contract()
    data = json.loads(INPUTS.read_text())
    if (data["schema_version"] != 1 or type(data["schema_version"]) is not int
            or data["production_qualified"] is not False or data["acceptance"] != "pending_review"
            or data["qualification"] != "source_caller_failure_matrix_only"
            or type(data["expected_native_tests"]) is not int or data["expected_native_tests"] != 12
            or data["parent_sha256"] != digest(PARENT.read_bytes())
            or data["tests_sha256"] != digest(TEST.read_bytes())
            or data["restart_helper_sha256"] != digest((ROOT / "tests/hermes_g2_create_crash_native.py").read_bytes())):
        raise ValueError("g2.caller_qualification_invalid")
    return data


def verify_stage(stage):
    data = qualification_contract()
    if json.loads((stage / "g2-caller-qualification-manifest.json").read_text()) != data:
        raise ValueError("g2.caller_qualification_stage_invalid")
    return verify_caller_stage(stage)


def prepare_qualification(repo, output):
    data = qualification_contract()
    prepare(repo, output)
    raw = (json.dumps(data, sort_keys=True, indent=2) + "\n").encode()
    (output / "g2-caller-qualification-manifest.json").write_bytes(raw)
    verify_stage(output)
    return digest(raw)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        sha = prepare_qualification(args.source_repo, args.output.resolve())
    except (ValueError, OSError, KeyError, SyntaxError):
        print(json.dumps({"status": "blocked", "reason_code": "g2.caller_qualification_preparation_failed"}))
        raise SystemExit(1)
    print(json.dumps({"status": "reconstructed", "manifest_sha256": sha, "production_qualified": False}))

"""Reconstruct the source-only native cleanup overlay, not a product wheel."""
import argparse
import json
from pathlib import Path

from prepare_governance_baseline import CONTRACT, PIN, ROOT, digest, git, patch_paths
from prepare_governance_g1_caller_entry import caller_contract, prepare_caller
from prepare_governance_security_checkpoint import base_inventory_digest, effective_files, security_contract

LIFECYCLE_CONTRACT = ROOT / "docs/architecture/governance-g1-caller-lifecycle.json"
FULL_CALLER_CONTRACT = ROOT / "docs/architecture/governance-g1-full-caller.json"


def lifecycle_contract():
    caller_contract()
    data = json.loads(LIFECYCLE_CONTRACT.read_text())
    patch = ROOT / "patches/hermes" / data["patch"]
    if (data["pin"] != PIN or data["production_qualified"] is not False
            or digest(patch.read_bytes()) != data["patch_sha256"]
            or patch_paths(patch.read_bytes()) != set(data["effective_native_sha256"])
            or data["entry_contract_sha256"] != digest((ROOT / "docs/architecture/governance-g1-caller-entry.json").read_bytes())
            or digest((ROOT / data["native_tests"]).read_bytes()) != data["native_tests_sha256"]):
        raise ValueError("g1.lifecycle_contract_invalid")
    return data, patch


def full_caller_contract():
    lifecycle_contract()
    data = json.loads(FULL_CALLER_CONTRACT.read_text())
    host_paths = {
        "src/project_maya/hermes_plugins/governance.py",
        "src/project_maya/hermes_plugins/session_requests.py",
        "src/project_maya/hermes_plugins/session_handoff.py",
    }
    if (data["schema_version"] != 1 or data["pin"] != PIN
            or data["production_qualified"] is not False
            or data["acceptance"] != "pending_review"
            or data["qualification"] != "source_full_caller_g1_review_pending"
            or data["lifecycle_contract_sha256"] != digest(LIFECYCLE_CONTRACT.read_bytes())
            or data["native_tests"] != "tests/hermes_g1_full_caller_native.py"
            or digest((ROOT / data["native_tests"]).read_bytes()) != data["native_tests_sha256"]
            or type(data["expected_tests"]) is not int or data["expected_tests"] != 14
            or set(data["maya_source_sha256"]) != host_paths
            or any(digest((ROOT / path).read_bytes()) != sha
                   for path, sha in data["maya_source_sha256"].items())):
        raise ValueError("g1.full_caller_contract_invalid")
    return data


def verify_lifecycle_stage(stage):
    data, _ = lifecycle_contract()
    entry, _ = caller_contract()
    security, _ = security_contract()
    base = json.loads((stage / "baseline-manifest.json").read_text())
    if (base_inventory_digest(base) != security["base_effective_inventory_sha256"]
            or base["contract_sha256"] != digest(CONTRACT.read_bytes())
            or base["pin"] != PIN or base["production_qualified"] is not False
            or base["patches_applied"] is not True):
        raise ValueError("g1.base_changed")
    rows = effective_files(stage, base, {"effective_native_sha256":
        security["effective_native_sha256"] | entry["effective_native_sha256"] | data["effective_native_sha256"]})
    return stage / "source", rows


def prepare_lifecycle(repo, output):
    data, patch = lifecycle_contract()
    prepare_caller(repo, output)
    git(output / "source", "apply", "--no-index", "--whitespace=error", str(patch))
    _, rows = verify_lifecycle_stage(output)
    manifest = {"pin": PIN, "production_qualified": False, "qualification": "source_only_not_run",
                "contract_sha256": digest(LIFECYCLE_CONTRACT.read_bytes()),
                "patch_sha256": data["patch_sha256"], "effective_files": rows}
    raw = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    (output / "g1-caller-lifecycle-manifest.json").write_bytes(raw)
    return digest(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        sha = prepare_lifecycle(args.source_repo, args.output.resolve())
    except (ValueError, OSError, KeyError, SyntaxError):
        print(json.dumps({"status": "blocked", "reason_code": "g1.lifecycle_preparation_failed", "production_qualified": False}))
        return 1
    print(json.dumps({"status": "reconstructed", "manifest_sha256": sha, "production_qualified": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

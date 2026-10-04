"""Build a separate source-only create overlay; never a production wheel."""
import argparse
import json
from pathlib import Path

from prepare_governance_baseline import ROOT, PIN, CONTRACT, digest, git, patch_paths
from prepare_governance_g1_caller_lifecycle import (
    LIFECYCLE_CONTRACT, caller_contract, full_caller_contract, lifecycle_contract,
    prepare_lifecycle, security_contract,
)
from prepare_governance_security_checkpoint import effective_files, base_inventory_digest

PATCH = ROOT / "patches/hermes/0027-owned-session-create-entry.patch"
CREATE_INPUTS = ROOT / "docs/architecture/governance-g2-create.json"
HOST_PATHS = {"src/project_maya/hermes_plugins/session_creation.py",
              "src/project_maya/hermes_plugins/session_transitions.py", "tests/hermes_g2_create_native.py"}


def create_contract():
    full_caller_contract()
    data = json.loads(CREATE_INPUTS.read_text())
    if (data["schema_version"] != 1 or data["pin"] != PIN or data["production_qualified"] is not False
            or data["qualification"] != "source_create_candidate_only" or data["acceptance"] != "pending_review"
            or type(data["expected_native_tests"]) is not int or data["expected_native_tests"] != 17
            or data["patch_sha256"] != digest(PATCH.read_bytes())
            or patch_paths(PATCH.read_bytes()) != {"gateway/session.py"}
            or data["parent_contract_sha256"] != digest(LIFECYCLE_CONTRACT.read_bytes())
            or set(data["maya_source_sha256"]) != HOST_PATHS
            or any(digest((ROOT / path).read_bytes()) != sha for path, sha in data["maya_source_sha256"].items())):
        raise ValueError("g2.create_contract_invalid")
    return data


def verify_create_stage(stage):
    data = create_contract()
    base = json.loads((stage / "baseline-manifest.json").read_text())
    security, _ = security_contract()
    entry, _ = caller_contract()
    lifecycle, _ = lifecycle_contract()
    manifest = json.loads((stage / "g2-create-manifest.json").read_text())
    if (base_inventory_digest(base) != security["base_effective_inventory_sha256"]
            or base["contract_sha256"] != digest(CONTRACT.read_bytes()) or base["pin"] != PIN
            or base["production_qualified"] is not False or base["patches_applied"] is not True
            or manifest != {key: data[key] for key in manifest}
            or set(manifest) != {"pin", "production_qualified", "qualification", "patch_sha256",
                                 "parent_contract_sha256", "native_session_sha256", "maya_source_sha256"}):
        raise ValueError("g2.create_contract_invalid")
    expected = security["effective_native_sha256"] | entry["effective_native_sha256"] | lifecycle["effective_native_sha256"]
    expected["gateway/session.py"] = manifest["native_session_sha256"]
    rows = effective_files(stage, base, {"effective_native_sha256": expected})
    for path, sha in manifest["maya_source_sha256"].items():
        if digest((ROOT / path).read_bytes()) != sha:
            raise ValueError("g2.create_host_changed")
    return stage / "source", rows


def prepare_create(repo, output):
    create_contract()
    prepare_lifecycle(repo, output)
    git(output / "source", "apply", "--no-index", "--whitespace=error", str(PATCH))
    paths = ["src/project_maya/hermes_plugins/session_creation.py",
             "src/project_maya/hermes_plugins/session_transitions.py",
             "tests/hermes_g2_create_native.py"]
    manifest = {"pin": PIN, "production_qualified": False,
                "qualification": "source_create_candidate_only",
                "parent_contract_sha256": digest(LIFECYCLE_CONTRACT.read_bytes()),
                "patch_sha256": digest(PATCH.read_bytes()),
                "native_session_sha256": digest((output / "source/gateway/session.py").read_bytes()),
                "maya_source_sha256": {path: digest((ROOT / path).read_bytes()) for path in paths}}
    raw = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    (output / "g2-create-manifest.json").write_bytes(raw)
    verify_create_stage(output)
    return digest(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        sha = prepare_create(args.source_repo, args.output.resolve())
    except (ValueError, OSError, KeyError, SyntaxError):
        print(json.dumps({"status": "blocked", "reason_code": "g2.create_preparation_failed", "production_qualified": False}))
        return 1
    print(json.dumps({"status": "reconstructed", "manifest_sha256": sha, "production_qualified": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

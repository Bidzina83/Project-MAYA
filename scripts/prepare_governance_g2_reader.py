"""Reconstruct a separate source-only published-reader overlay over Patch 27."""
import argparse
import json
from pathlib import Path

from prepare_governance_g2_create import (
    ROOT, PIN, CONTRACT, CREATE_INPUTS,
    base_inventory_digest, caller_contract, create_contract, digest, effective_files,
    git, lifecycle_contract, patch_paths, prepare_create, security_contract,
)

PATCH = ROOT / "patches/hermes/0028-published-session-reader.patch"
INPUTS = ROOT / "docs/architecture/governance-g2-reader.json"
READER_PATHS = {"src/project_maya/hermes_plugins/session_readers.py", "tests/hermes_g2_reader_native.py"}


def reader_contract():
    create_contract()
    data = json.loads(INPUTS.read_text())
    if (data["schema_version"] != 1 or data["pin"] != PIN or data["production_qualified"] is not False
            or data["qualification"] != "source_reader_candidate_only" or data["acceptance"] != "pending_review"
            or data["parent_contract_sha256"] != digest(CREATE_INPUTS.read_bytes())
            or data["patch_sha256"] != digest(PATCH.read_bytes())
            or patch_paths(PATCH.read_bytes()) != {"gateway/session.py"}
            or set(data["maya_source_sha256"]) != READER_PATHS
            or type(data["expected_native_tests"]) is not int or data["expected_native_tests"] != 22
            or any(digest((ROOT / path).read_bytes()) != sha for path, sha in data["maya_source_sha256"].items())):
        raise ValueError("g2.reader_contract_invalid")
    return data


def verify_reader_stage(stage):
    data = reader_contract()
    base = json.loads((stage / "baseline-manifest.json").read_text())
    security, _ = security_contract()
    entry, _ = caller_contract()
    lifecycle, _ = lifecycle_contract()
    if (base_inventory_digest(base) != security["base_effective_inventory_sha256"]
            or base["contract_sha256"] != digest(CONTRACT.read_bytes()) or base["pin"] != PIN
            or base["production_qualified"] is not False or base["patches_applied"] is not True
            or json.loads((stage / "g2-reader-manifest.json").read_text()) != data):
        raise ValueError("g2.reader_stage_invalid")
    expected = security["effective_native_sha256"] | entry["effective_native_sha256"] | lifecycle["effective_native_sha256"]
    expected["gateway/session.py"] = data["native_session_sha256"]
    return stage / "source", effective_files(stage, base, {"effective_native_sha256": expected})


def prepare_reader(repo, output):
    data = reader_contract()
    prepare_create(repo, output)
    git(output / "source", "apply", "--no-index", "--whitespace=error", str(PATCH))
    raw = (json.dumps(data, sort_keys=True, indent=2) + "\n").encode()
    (output / "g2-reader-manifest.json").write_bytes(raw)
    verify_reader_stage(output)
    return digest(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        sha = prepare_reader(args.source_repo, args.output.resolve())
    except (ValueError, OSError, KeyError, SyntaxError):
        print(json.dumps({"status": "blocked", "reason_code": "g2.reader_preparation_failed", "production_qualified": False}))
        return 1
    print(json.dumps({"status": "reconstructed", "manifest_sha256": sha, "production_qualified": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

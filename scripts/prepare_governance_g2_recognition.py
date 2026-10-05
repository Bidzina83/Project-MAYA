"""Reconstruct a separate, source-only existing-session recognition overlay."""
import argparse
import json
from pathlib import Path
import shutil

from prepare_governance_g2_caller_qualification import (
    ROOT, INPUTS as PARENT, prepare_qualification, verify_stage as verify_parent,
)
from prepare_governance_g2_caller import digest, git, patch_paths

INPUTS = ROOT / "docs/architecture/governance-g2-recognition.json"
PATCH = ROOT / "patches/hermes/0030-existing-session-recognition.patch"
LOOP_INPUTS = ROOT / "docs/architecture/governance-g2-create-loop.json"
DESIGN = ROOT / "docs/architecture/governance_g2_existing_session_recognition.md"
PATHS = {"source/run_agent.py", "host/src/project_maya/hermes_plugins/session_readers.py"}


def contract():
    data = json.loads(INPUTS.read_text())
    loop = json.loads(LOOP_INPUTS.read_text())
    if (type(data["schema_version"]) is not int or data["schema_version"] != 1
            or data["production_qualified"] is not False or data["acceptance"] != "pending_review"
            or data["qualification"] != "source_existing_session_recognition_only"
            or type(data["expected_native_tests"]) is not int or data["expected_native_tests"] != 24
            or type(data["expected_ordinary_tests"]) is not int or data["expected_ordinary_tests"] != 3
            or data["parent_sha256"] != digest(PARENT.read_bytes())
            or data["design_sha256"] != digest(DESIGN.read_bytes())
            or data["loop_inputs_sha256"] != digest(LOOP_INPUTS.read_bytes())
            or loop["tests_sha256"] != digest((ROOT / "tests/hermes_g2_create_loop_native.py").read_bytes())
            or data["patch_sha256"] != digest(PATCH.read_bytes())
            or patch_paths(PATCH.read_bytes()) != PATHS
            or set(data["effective_sha256"]) != PATHS
            or set(data["test_sha256"]) != {"tests/hermes_g2_recognition_native.py", "tests/hermes_g2_recognition_ordinary.py"}
            or any(digest((ROOT / path).read_bytes()) != sha for path, sha in data["test_sha256"].items())):
        raise ValueError("g2.recognition_contract_invalid")
    return data


def inventory(root):
    if any(path.is_symlink() for path in root.rglob("*")):
        raise ValueError("g2.recognition_symlink_invalid")
    return {path.relative_to(root).as_posix(): digest(path.read_bytes())
            for path in root.rglob("*") if path.is_file()}


def verify_stage(stage):
    data = contract()
    if json.loads((stage / "g2-recognition-manifest.json").read_text()) != data:
        raise ValueError("g2.recognition_stage_invalid")
    verify_parent(stage / "parent")
    for name in ("source", "host"):
        expected = inventory(stage / "parent" / name)
        for path, sha in data["effective_sha256"].items():
            if path.startswith(name + "/"):
                expected[path[len(name) + 1:]] = sha
        if inventory(stage / name) != expected:
            raise ValueError("g2.recognition_inventory_invalid")
    return stage / "source", stage / "host/src"


def prepare(repo, output):
    data = contract()
    prepare_qualification(repo, output / "parent")
    for name in ("source", "host"):
        shutil.copytree(output / "parent" / name, output / name)
    git(output, "apply", "--no-index", "--unidiff-zero", "--whitespace=error", str(PATCH))
    raw = (json.dumps(data, sort_keys=True, indent=2) + "\n").encode()
    (output / "g2-recognition-manifest.json").write_bytes(raw)
    verify_stage(output)
    return digest(raw)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        sha = prepare(args.source_repo, args.output.resolve())
    except (ValueError, OSError, KeyError, SyntaxError):
        print(json.dumps({"status": "blocked", "reason_code": "g2.recognition_preparation_failed"}))
        raise SystemExit(1)
    print(json.dumps({"status": "reconstructed", "manifest_sha256": sha, "production_qualified": False}))

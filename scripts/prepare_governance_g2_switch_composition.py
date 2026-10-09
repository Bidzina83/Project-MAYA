"""Reconstruct the source-only switch caller/reader over frozen Patch 36."""
import argparse
import json
from pathlib import Path
import shutil

from prepare_governance_g2_switch import (
    ROOT, INPUTS as PARENT, TEST as PARENT_TEST, FIXTURES as PARENT_FIXTURES,
    digest, git, inventory, verify_stage as verify_parent,
)

INPUTS = ROOT / "docs/architecture/governance-g2-switch-composition.json"
PATCH = ROOT / "patches/hermes/0037-switch-publication-caller-reader.patch"
PARENT_STAGE = ROOT / ".codex-build/governance-g2-switch-20261008-b"
PATHS = {"source/gateway/session.py", "source/gateway/run.py",
         "host/src/project_maya/hermes_plugins/session_readers.py",
         "host/src/project_maya/hermes_plugins/switch_publication.py"}
TESTS = {"tests/hermes_g2_switch_composition_native.py": 42,
         "tests/hermes_g2_switch_atomic_replay.py": 43,
         "tests/hermes_g2_switch_create_replay.py": 80,
         "tests/hermes_g2_switch_reset_replay.py": 34}
FIXTURES = PARENT_FIXTURES | {PARENT_TEST}


def contract():
    data = json.loads(INPUTS.read_text(encoding="utf-8"))
    paths = {line.split()[3][2:] for line in PATCH.read_text().splitlines()
             if line.startswith("diff --git ")}
    if (type(data.get("schema_version")) is not int or data["schema_version"] != 1
            or data.get("production_qualified") is not False
            or data.get("acceptance") != "pending_review"
            or data.get("qualification") != "source_switch_composition_only"
            or data.get("parent_sha256") != digest(PARENT.read_bytes())
            or data.get("patch_sha256") != digest(PATCH.read_bytes()) or paths != PATHS
            or set(data.get("effective_sha256", {})) != PATHS
            or any(not isinstance(sha, str) or len(sha) != 64
                   or any(c not in "0123456789abcdef" for c in sha)
                   for sha in data.get("effective_sha256", {}).values())
            or data.get("expected_tests") != TESTS
            or any(type(n) is not int or n <= 0 for n in data.get("expected_tests", {}).values())
            or set(data.get("test_sha256", {})) != set(TESTS)
            or any(data["test_sha256"][p] != digest((ROOT / p).read_bytes()) for p in TESTS)
            or set(data.get("fixture_sha256", {})) != FIXTURES
            or any(data["fixture_sha256"][p] != digest((ROOT / p).read_bytes()) for p in FIXTURES)):
        raise ValueError("g2.switch_composition_contract_invalid")
    return data


def verify_worker_stage(stage):
    data = contract()
    if json.loads((stage / "g2-switch-composition-manifest.json").read_text()) != data:
        raise ValueError("g2.switch_composition_manifest_invalid")
    for tree in ("source", "host"):
        expected = inventory(PARENT_STAGE / tree)
        for path, sha in data["effective_sha256"].items():
            if path.startswith(tree + "/"):
                expected[path[len(tree) + 1:]] = sha
        if inventory(stage / tree) != expected:
            raise ValueError("g2.switch_composition_inventory_invalid")
    return stage / "source", stage / "host/src"


def verify_stage(stage):
    verify_parent(PARENT_STAGE)
    return verify_worker_stage(stage)


def prepare(output):
    data = contract()
    verify_parent(PARENT_STAGE)
    if output.exists() or output.is_relative_to(PARENT_STAGE) or PARENT_STAGE.is_relative_to(output):
        raise ValueError("g2.switch_composition_output_invalid")
    for tree in ("source", "host"):
        shutil.copytree(PARENT_STAGE / tree, output / tree)
    git(output, "apply", "--no-index", "--whitespace=error", str(PATCH))
    (output / "g2-switch-composition-manifest.json").write_text(
        json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    verify_worker_stage(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.output.resolve())
    print(json.dumps({"status": "reconstructed", "production_qualified": False}))

"""Reconstruct a source-only atomic switch over the accepted Patch 35 profile."""
import argparse
import json
from pathlib import Path
import shutil

from prepare_governance_g2_publisher import (
    ROOT, INPUTS as PARENT, FIXTURES, digest, git, inventory, verify_stage as verify_parent,
)

INPUTS = ROOT / "docs/architecture/governance-g2-switch.json"
PATCH = ROOT / "patches/hermes/0036-owned-session-switch.patch"
PARENT_STAGE = ROOT / ".codex-build/governance-g2-publisher-20261008-a"
PATHS = {"source/gateway/session.py", "host/src/project_maya/hermes_plugins/session_switch.py"}
TEST = "tests/hermes_g2_switch_native.py"
EXPECTED = 43


def contract():
    data = json.loads(INPUTS.read_text(encoding="utf-8"))
    paths = {line.split()[3][2:] for line in PATCH.read_text().splitlines()
             if line.startswith("diff --git ")}
    if (type(data.get("schema_version")) is not int or data["schema_version"] != 1
            or data.get("production_qualified") is not False
            or data.get("acceptance") != "pending_review"
            or data.get("qualification") != "source_switch_atomic_only"
            or data.get("parent_sha256") != digest(PARENT.read_bytes())
            or data.get("patch_sha256") != digest(PATCH.read_bytes()) or paths != PATHS
            or set(data.get("effective_sha256", {})) != PATHS
            or any(not isinstance(sha, str) or len(sha) != 64
                   or any(c not in "0123456789abcdef" for c in sha)
                   for sha in data.get("effective_sha256", {}).values())
            or type(data.get("expected_native_tests")) is not int
            or data["expected_native_tests"] != EXPECTED
            or data.get("test_sha256") != digest((ROOT / TEST).read_bytes())
            or set(data.get("fixture_sha256", {})) != FIXTURES
            or any(data["fixture_sha256"][p] != digest((ROOT / p).read_bytes()) for p in FIXTURES)):
        raise ValueError("g2.switch_contract_invalid")
    return data


def verify_worker_stage(stage):
    data = contract()
    if json.loads((stage / "g2-switch-manifest.json").read_text()) != data:
        raise ValueError("g2.switch_manifest_invalid")
    for tree in ("source", "host"):
        expected = inventory(PARENT_STAGE / tree)
        for path, sha in data["effective_sha256"].items():
            if path.startswith(tree + "/"):
                expected[path[len(tree) + 1:]] = sha
        if inventory(stage / tree) != expected:
            raise ValueError("g2.switch_inventory_invalid")
    return stage / "source", stage / "host/src"


def verify_stage(stage):
    verify_parent(PARENT_STAGE)
    return verify_worker_stage(stage)


def prepare(output):
    data = contract()
    verify_parent(PARENT_STAGE)
    if output.exists() or output.is_relative_to(PARENT_STAGE) or PARENT_STAGE.is_relative_to(output):
        raise ValueError("g2.switch_output_invalid")
    for tree in ("source", "host"):
        shutil.copytree(PARENT_STAGE / tree, output / tree)
    git(output, "apply", "--no-index", "--whitespace=error", str(PATCH))
    (output / "g2-switch-manifest.json").write_text(
        json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    verify_worker_stage(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.output.resolve())
    print(json.dumps({"status": "reconstructed", "production_qualified": False}))

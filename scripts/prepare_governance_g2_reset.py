"""Reconstruct a source-only reset overlay over verified prepared Patch 31."""
import argparse
import json
from pathlib import Path
import shutil

from prepare_governance_g2_recognition import ROOT, inventory
from prepare_governance_g2_caller import digest, git
from verify_governance_g2_final_create import INPUTS as PARENT, verify_stage as verify_parent

INPUTS = ROOT / "docs/architecture/governance-g2-reset.json"
PATCH = ROOT / "patches/hermes/0032-owned-session-reset.patch"
PATHS = {"source/gateway/session.py", "host/src/project_maya/hermes_plugins/session_reset.py"}


def contract():
    data = json.loads(INPUTS.read_text(encoding="utf-8"))
    if (data.get("schema_version") != 1 or type(data.get("schema_version")) is not int
            or data.get("production_qualified") is not False
            or data.get("qualification") != "source_reset_atomic_only"
            or data.get("acceptance") != "pending_review"
            or type(data.get("expected_native_tests")) is not int or data["expected_native_tests"] != 22
            or data.get("parent_sha256") != digest(PARENT.read_bytes())
            or data.get("patch_sha256") != digest(PATCH.read_bytes())
            or {line.split()[3][2:] for line in PATCH.read_text().splitlines()
                if line.startswith("diff --git ")} != PATHS
            or set(data.get("effective_sha256", {})) != PATHS
            or data.get("test_sha256") != digest((ROOT / "tests/hermes_g2_reset_native.py").read_bytes())):
        raise ValueError("g2.reset_contract_invalid")
    return data


def verify_stage(stage, parent):
    data = contract()
    verify_parent(parent)
    if json.loads((stage / "g2-reset-manifest.json").read_text()) != data:
        raise ValueError("g2.reset_stage_invalid")
    for tree in ("source", "host"):
        expected = inventory(parent / tree)
        for name, sha in data["effective_sha256"].items():
            if name.startswith(tree + "/"):
                expected[name[len(tree) + 1:]] = sha
        if inventory(stage / tree) != expected:
            raise ValueError("g2.reset_inventory_invalid")
    return stage / "source", stage / "host/src"


def prepare(parent, output):
    data = contract()
    verify_parent(parent)
    if output.exists() or output.is_relative_to(parent) or parent.is_relative_to(output):
        raise ValueError("g2.reset_output_invalid")
    for tree in ("source", "host"):
        shutil.copytree(parent / tree, output / tree)
    git(output, "apply", "--no-index", "--whitespace=error", str(PATCH))
    (output / "g2-reset-manifest.json").write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
    verify_stage(output, parent)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-stage", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        prepare(args.parent_stage.resolve(), args.output.resolve())
    except (ValueError, OSError, KeyError):
        print(json.dumps({"status": "blocked", "reason_code": "g2.reset_preparation_failed"}))
        raise SystemExit(1)
    print(json.dumps({"status": "reconstructed", "production_qualified": False}))

"""Reconstruct the approved source-only reset eligibility/approval restriction."""
import argparse
import json
import shutil
from pathlib import Path

from prepare_governance_g2_reset_composition import (
    ROOT, INPUTS as PARENT, verify_stage as verify_parent, inventory,
)
from prepare_governance_g2_caller import digest, git

INPUTS = ROOT / "docs/architecture/governance-g2-reset-gate.json"
PATCH = ROOT / "patches/hermes/0034-reset-confirmation-approval-gate.patch"
PATHS = {"source/gateway/run.py", "source/tools/approval.py", "source/tools/slash_confirm.py",
         "host/src/project_maya/hermes_plugins/reset_publication.py",
         "host/src/project_maya/hermes_plugins/session_readers.py"}
TESTS = {"tests/hermes_g2_reset_gate_native.py", "tests/hermes_g2_reset_gate_atomic_native.py"}


def contract():
    data = json.loads(INPUTS.read_text(encoding="utf-8"))
    if (type(data.get("schema_version")) is not int or data["schema_version"] != 1
            or data.get("production_qualified") is not False
            or data.get("acceptance") != "pending_review"
            or data.get("qualification") != "source_reset_gate_only"
            or type(data.get("expected_gate_tests")) is not int or data["expected_gate_tests"] != 34
            or type(data.get("expected_atomic_tests")) is not int or data["expected_atomic_tests"] != 22
            or data.get("parent_sha256") != digest(PARENT.read_bytes())
            or data.get("patch_sha256") != digest(PATCH.read_bytes())
            or {line.split()[3][2:] for line in PATCH.read_text().splitlines()
                if line.startswith("diff --git ")} != PATHS
            or set(data.get("effective_sha256", {})) != PATHS
            or set(data.get("test_sha256", {})) != TESTS
            or any(data["test_sha256"][name] != digest((ROOT / name).read_bytes()) for name in TESTS)):
        raise ValueError("g2.reset_gate_contract_invalid")
    return data


def verify_stage(stage, parent, baseline):
    data = contract()
    verify_parent(parent, ROOT / ".codex-build/governance-g2-reset-20261006-final-b", baseline)
    if json.loads((stage / "g2-reset-gate-manifest.json").read_text()) != data:
        raise ValueError("g2.reset_gate_stage_invalid")
    for tree in ("source", "host"):
        expected = inventory(parent / tree)
        expected.update({name[len(tree) + 1:]: sha for name, sha in data["effective_sha256"].items()
                         if name.startswith(tree + "/")})
        if inventory(stage / tree) != expected:
            raise ValueError("g2.reset_gate_inventory_invalid")
    return stage / "source", stage / "host/src"


def prepare(parent, baseline, output):
    data = contract()
    verify_parent(parent, ROOT / ".codex-build/governance-g2-reset-20261006-final-b", baseline)
    if (output.exists() or any(output.is_relative_to(path) or path.is_relative_to(output)
                              for path in (parent, baseline))):
        raise ValueError("g2.reset_gate_output_invalid")
    for tree in ("source", "host"):
        shutil.copytree(parent / tree, output / tree)
    git(output, "apply", "--no-index", "--whitespace=error", str(PATCH))
    (output / "g2-reset-gate-manifest.json").write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
    verify_stage(output, parent, baseline)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-stage", type=Path, required=True)
    parser.add_argument("--baseline-stage", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        prepare(args.parent_stage.resolve(), args.baseline_stage.resolve(), args.output.resolve())
    except (ValueError, OSError, KeyError):
        print(json.dumps({"status": "blocked", "reason_code": "g2.reset_gate_preparation_failed"}))
        raise SystemExit(1)
    print(json.dumps({"status": "reconstructed", "production_qualified": False}))

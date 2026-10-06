"""Reconstruct source-only reset caller/reader composition over frozen Patch 32."""
import argparse
import json
import shutil
from pathlib import Path

from prepare_governance_g2_reset import ROOT, INPUTS as PARENT, verify_stage as verify_parent, inventory
from prepare_governance_g2_caller import digest, git

INPUTS = ROOT / "docs/architecture/governance-g2-reset-composition.json"
PATCH = ROOT / "patches/hermes/0033-reset-publication-caller-reader.patch"
PATHS = {"source/gateway/session.py", "host/src/project_maya/hermes_plugins/session_reset.py",
         "host/src/project_maya/hermes_plugins/session_readers.py",
         "host/src/project_maya/hermes_plugins/reset_publication.py"}


def contract():
    data = json.loads(INPUTS.read_text(encoding="utf-8"))
    if (type(data.get("schema_version")) is not int or data["schema_version"] != 1
            or data.get("production_qualified") is not False or data.get("acceptance") != "pending_review"
            or data.get("qualification") != "source_reset_composition_only"
            or data.get("expected_composition_tests") != 15 or type(data.get("expected_composition_tests")) is not int
            or data.get("expected_atomic_regression_tests") != 22
            or type(data.get("expected_atomic_regression_tests")) is not int
            or data.get("atomic_regression_sha256") != digest((ROOT / "tests/hermes_g2_reset_step2_regression_native.py").read_bytes())
            or data.get("parent_sha256") != digest(PARENT.read_bytes())
            or data.get("patch_sha256") != digest(PATCH.read_bytes())
            or {line.split()[3][2:] for line in PATCH.read_text().splitlines()
                if line.startswith("diff --git ")} != PATHS
            or set(data.get("effective_sha256", {})) != PATHS
            or data.get("test_sha256") != digest((ROOT / "tests/hermes_g2_reset_composition_native.py").read_bytes())):
        raise ValueError("g2.reset_composition_contract_invalid")
    return data


def verify_stage(stage, parent, baseline):
    data = contract()
    verify_parent(parent, baseline)
    if json.loads((stage / "g2-reset-composition-manifest.json").read_text()) != data:
        raise ValueError("g2.reset_composition_stage_invalid")
    for tree in ("source", "host"):
        expected = inventory(parent / tree)
        expected.update({name[len(tree) + 1:]: sha for name, sha in data["effective_sha256"].items()
                         if name.startswith(tree + "/")})
        if inventory(stage / tree) != expected:
            raise ValueError("g2.reset_composition_inventory_invalid")
    return stage / "source", stage / "host/src"


def prepare(parent, baseline, output):
    data = contract()
    verify_parent(parent, baseline)
    if (output.exists() or any(output.is_relative_to(path) or path.is_relative_to(output)
                              for path in (parent, baseline))):
        raise ValueError("g2.reset_composition_output_invalid")
    for tree in ("source", "host"):
        shutil.copytree(parent / tree, output / tree)
    git(output, "apply", "--no-index", "--whitespace=error", str(PATCH))
    (output / "g2-reset-composition-manifest.json").write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
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
        print(json.dumps({"status": "blocked", "reason_code": "g2.reset_composition_preparation_failed"}))
        raise SystemExit(1)
    print(json.dumps({"status": "reconstructed", "production_qualified": False}))

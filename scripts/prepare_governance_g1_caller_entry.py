"""Reconstruct the source-only G1 caller-entry candidate after the security overlay."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prepare_governance_baseline import CONTRACT, PIN, ROOT, digest, git, patch_paths
from prepare_governance_security_checkpoint import (
    base_inventory_digest, effective_files, prepare_security, security_contract,
)

G1_CONTRACT = ROOT / "docs/architecture/governance-g1-caller-entry.json"


def caller_contract():
    contract = json.loads(G1_CONTRACT.read_text())
    patch = ROOT / "patches/hermes" / contract["patch"]
    if (contract["pin"] != PIN or contract["production_qualified"] is not False
            or digest(patch.read_bytes()) != contract["patch_sha256"]
            or patch_paths(patch.read_bytes()) != set(contract["effective_native_sha256"])):
        raise ValueError("g1.invalid_contract")
    if digest((ROOT / contract["native_tests"]).read_bytes()) != contract["native_tests_sha256"]:
        raise ValueError("g1.test_hash_mismatch")
    return contract, patch


def verify_caller_stage(stage):
    contract, _ = caller_contract()
    security, _ = security_contract()
    base = json.loads((stage / "baseline-manifest.json").read_text())
    if (base_inventory_digest(base) != security["base_effective_inventory_sha256"]
            or base["contract_sha256"] != digest(CONTRACT.read_bytes())
            or base["pin"] != PIN or base["production_qualified"] is not False
            or base["patches_applied"] is not True):
        raise ValueError("g1.base_changed")
    expected = {"effective_native_sha256": security["effective_native_sha256"] | contract["effective_native_sha256"]}
    rows = effective_files(stage, base, expected)
    return stage / "source", rows


def prepare_caller(repo, output):
    contract, patch = caller_contract()
    prepare_security(repo, output)
    git(output / "source", "apply", "--no-index", "--whitespace=error", str(patch))
    _, rows = verify_caller_stage(output)
    manifest = {"pin": PIN, "production_qualified": False, "qualification": "source_only_not_run",
                "contract_sha256": digest(G1_CONTRACT.read_bytes()),
                "patch_sha256": contract["patch_sha256"], "effective_files": rows}
    data = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    (output / "g1-caller-entry-manifest.json").write_bytes(data)
    return digest(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        sha = prepare_caller(args.source_repo, args.output.resolve())
    except (ValueError, OSError, KeyError, SyntaxError):
        print(json.dumps({"status": "blocked", "reason_code": "g1.preparation_failed", "production_qualified": False}))
        return 1
    print(json.dumps({"status": "reconstructed", "manifest_sha256": sha, "production_qualified": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

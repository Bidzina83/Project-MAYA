"""Apply the approved security overlay without rewriting the accepted G0 baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from prepare_governance_baseline import CONTRACT, PIN, ROOT, digest, git, patch_paths, prepare

SECURITY_CONTRACT = ROOT / "docs/architecture/governance-security-checkpoint.json"


def security_contract():
    contract = json.loads(SECURITY_CONTRACT.read_text())
    if contract["pin"] != PIN or contract["production_qualified"] is not False:
        raise ValueError("security.invalid_contract")
    patch = ROOT / "patches/hermes" / contract["patch"]
    if digest(patch.read_bytes()) != contract["patch_sha256"]:
        raise ValueError("security.patch_hash_mismatch")
    if patch_paths(patch.read_bytes()) != set(contract["effective_native_sha256"]):
        raise ValueError("security.patch_inventory_mismatch")
    test = ROOT / contract["security_tests"]
    if digest(test.read_bytes()) != contract["security_tests_sha256"]:
        raise ValueError("security.test_hash_mismatch")
    return contract, patch


def effective_files(stage, base, contract):
    source = stage / "source"
    expected = {row["path"]: row for row in base["effective_files"]}
    actual = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    if actual != set(expected) or any(p.is_symlink() for p in source.rglob("*")):
        raise ValueError("security.unexpected_stage_files")
    rows = []
    for name, row in expected.items():
        sha = digest((source / name).read_bytes())
        wanted = contract["effective_native_sha256"].get(name, row["sha256"])
        if sha != wanted:
            raise ValueError("security.stage_modified")
        if name in contract["effective_native_sha256"]:
            compile((source / name).read_bytes(), name, "exec")
        rows.append({**row, "sha256": sha})
    return rows


def base_inventory_digest(base):
    # Source identity is portable; tooling byte hashes can vary with checkout
    # line endings and must not make Linux and Windows source contracts diverge.
    return digest(json.dumps(base["effective_files"], sort_keys=True,
                             separators=(",", ":")).encode())


def prepare_security(repo, output):
    contract, patch = security_contract()
    prepare(repo, output)
    base_bytes = (output / "baseline-manifest.json").read_bytes()
    base = json.loads(base_bytes)
    if base_inventory_digest(base) != contract["base_effective_inventory_sha256"]:
        raise ValueError("security.base_manifest_changed")
    git(output / "source", "apply", "--no-index", "--whitespace=error", str(patch))
    manifest = {
        "schema": contract["schema"], "pin": PIN,
        "production_qualified": False, "assessment_only": True,
        "base_manifest_sha256": digest(base_bytes),
        "security_contract_sha256": digest(SECURITY_CONTRACT.read_bytes()),
        "patch_sha256": contract["patch_sha256"],
        "security_tests_sha256": contract["security_tests_sha256"],
        "effective_files": effective_files(output, base, contract),
    }
    data = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    (output / "security-checkpoint-manifest.json").write_bytes(data)
    return digest(data)


def verify_security_stage(stage):
    contract, _ = security_contract()
    base_bytes = (stage / "baseline-manifest.json").read_bytes()
    base = json.loads(base_bytes)
    manifest = json.loads((stage / "security-checkpoint-manifest.json").read_text())
    if (base_inventory_digest(base) != contract["base_effective_inventory_sha256"] or
            base["contract_sha256"] != digest(CONTRACT.read_bytes()) or
            base["pin"] != PIN or base["production_qualified"] is not False or
            not base["patches_applied"] or
            manifest["pin"] != PIN or manifest["production_qualified"] is not False or
            manifest["base_manifest_sha256"] != digest(base_bytes) or
            manifest["security_contract_sha256"] != digest(SECURITY_CONTRACT.read_bytes()) or
            manifest["patch_sha256"] != contract["patch_sha256"] or
            manifest["security_tests_sha256"] != contract["security_tests_sha256"]):
        raise ValueError("security.invalid_stage")
    if manifest["effective_files"] != effective_files(stage, base, contract):
        raise ValueError("security.invalid_manifest")
    return stage / "source"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        sha = prepare_security(args.source_repo, args.output.resolve())
    except (ValueError, OSError, KeyError, SyntaxError) as exc:
        reason = str(exc) if str(exc).startswith(("security.", "baseline.")) else "security.preparation_failed"
        print(json.dumps({"status": "blocked", "reason_code": reason, "production_qualified": False}))
        return 1
    print(json.dumps({"status": "reconstructed", "manifest_sha256": sha,
                      "production_qualified": False, "qualification": "not_run"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

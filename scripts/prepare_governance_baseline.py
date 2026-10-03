"""Reconstruct an assessment-only Hermes stage from pinned Git objects, offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[1]
PIN = "b13e2fd6948a59eeb59fe618914147d97a2ee90a"
CONTRACT = ROOT / "docs/architecture/governance-g0-baseline.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git_env():
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_TERMINAL_PROMPT="0", GIT_NO_REPLACE_OBJECTS="1")
    return env


def git(repo, *args):
    env = git_env()
    if args and args[0] == "apply":
        # Exported trees must not inherit an enclosing repository's path prefix.
        env["GIT_CEILING_DIRECTORIES"] = str(Path(repo).resolve().parent)
    result = subprocess.run(["git", "-C", str(repo), *args], env=env,
                            capture_output=True)
    if result.returncode:
        raise ValueError("baseline.git_command_failed")
    return result.stdout


def safe_path(name):
    path = PurePosixPath(name)
    if (path.is_absolute() or ".." in path.parts or "\\" in name or
            ":" in name or any(p.lower() == ".git" for p in path.parts)):
        raise ValueError("baseline.unsafe_path")
    return path


def tree(repo, pin):
    records = []
    for entry in git(repo, "ls-tree", "-rz", pin).split(b"\0"):
        if not entry:
            continue
        meta, raw_name = entry.split(b"\t", 1)
        mode, kind, oid = meta.decode("ascii").split()
        name = raw_name.decode("utf-8")
        safe_path(name)
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError("baseline.unsupported_tree_entry")
        records.append((name, mode, oid))
    return sorted(records)


def export_objects(repo, records, destination):
    result = []
    # Read object bytes directly: checkout filters, line endings and dirty files
    # must not influence the reconstructed source.
    with subprocess.Popen(["git", "-C", str(repo), "cat-file", "--batch"],
                          env=git_env(), stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as process:
        try:
            for name, mode, oid in records:
                process.stdin.write((oid + "\n").encode("ascii"))
                process.stdin.flush()
                header = process.stdout.readline().decode("ascii").split()
                if len(header) != 3 or header[:2] != [oid, "blob"]:
                    raise ValueError("baseline.object_missing")
                data = process.stdout.read(int(header[2]))
                if process.stdout.read(1) != b"\n":
                    raise ValueError("baseline.object_truncated")
                if hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() != oid:
                    raise ValueError("baseline.object_hash_mismatch")
                target = destination / safe_path(name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                if mode == "100755" and os.name != "nt":
                    target.chmod(0o755)
                result.append({"path": name, "mode": mode, "git_blob": oid,
                               "sha256": digest(data)})
        finally:
            process.stdin.close()
            process.wait()
    if process.returncode:
        raise ValueError("baseline.object_export_failed")
    return result


def patch_paths(data):
    paths = re.findall(rb"^--- a/([^\r\n]+)\r?\n\+\+\+ b/([^\r\n]+)\r?$", data, re.MULTILINE)
    if not paths:
        raise ValueError("baseline.empty_patch")
    names = set()
    for old, new in paths:
        if old != new:
            raise ValueError("baseline.patch_rename_not_reviewed")
        name = new.decode("utf-8")
        safe_path(name)
        names.add(name)
    return names


def validate_contract(contract):
    if contract["pin"] != PIN or contract["production_qualified"] is not False:
        raise ValueError("baseline.invalid_contract")
    if [p["number"] for p in contract["patches"]] != list(range(1, 24)):
        raise ValueError("baseline.invalid_patch_order")
    ids = set()
    for boundary in contract["coverage"]:
        if boundary["id"] in ids or boundary["status"] not in {"supported", "blocked", "unresolved"}:
            raise ValueError("baseline.invalid_coverage")
        ids.add(boundary["id"])
        if not all(boundary[k] for k in ("entrypoints", "sink", "evidence", "next_gate")):
            raise ValueError("baseline.incomplete_coverage")
        for module in boundary["tests"]:
            if not (ROOT / (module.replace(".", "/") + ".py")).is_file():
                raise ValueError("baseline.missing_test")
    if contract["profile"]["unknown_roots"] != "deny_and_block_acceptance":
        raise ValueError("baseline.unknown_root_fallback")


def prepare(repo, output, contract_path=CONTRACT, *, apply_patches=True):
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    validate_contract(contract)
    output = output.resolve()
    if output.exists():
        raise ValueError("baseline.output_must_be_new")
    records = tree(repo, PIN)
    patch_records, changed, combined = [], set(), bytearray()
    for item in contract["patches"]:
        path = ROOT / "patches/hermes" / item["filename"]
        data = path.read_bytes()
        if digest(data) != item["sha256"]:
            raise ValueError("baseline.patch_hash_mismatch")
        changed.update(patch_paths(data))
        combined.extend(data)
        patch_records.append(item)
    if digest(combined) != contract["patch_series_sha256"]:
        raise ValueError("baseline.series_hash_mismatch")
    output.mkdir(parents=True)
    source = output / "source"
    source.mkdir()
    blobs = export_objects(repo, records, source)
    locks = {}
    for name, expected in contract["dependency_inputs"].items():
        data = (source / name).read_bytes()
        if digest(data) != expected:
            raise ValueError("baseline.dependency_input_changed")
        locks[name] = expected
    locked = tomllib.loads((source / "uv.lock").read_text(encoding="utf-8"))
    for package in locked["package"]:
        if "registry" not in package["source"]:
            if package["source"] != {"editable": "."}:
                raise ValueError("baseline.unreviewed_dependency_source")
            continue
        artifacts = package.get("wheels", []) + ([package["sdist"]] if "sdist" in package else [])
        if not artifacts or any(not re.fullmatch(r"sha256:[0-9a-f]{64}", a.get("hash", "")) for a in artifacts):
            raise ValueError("baseline.unhashed_dependency")
    if apply_patches:
        # --no-index applies to this complete exported tree, without creating a
        # Git checkout or allowing unrelated working-tree state into the stage.
        for item in patch_records:
            git(source, "apply", "--no-index", "--whitespace=error",
                str((ROOT / "patches/hermes" / item["filename"]).resolve()))
    expected_paths = {r["path"] for r in blobs}
    actual_paths = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    if actual_paths != expected_paths:
        raise ValueError("baseline.unexpected_stage_files")
    effective = []
    for row in blobs:
        data = (source / row["path"]).read_bytes()
        sha = digest(data)
        if sha != row["sha256"] and row["path"] not in changed:
            raise ValueError("baseline.unreviewed_source_change")
        if row["path"] in changed and row["path"].endswith(".py"):
            compile(data, row["path"], "exec")
        effective.append({"path": row["path"], "sha256": sha, "mode": row["mode"]})
    for test in contract["ordinary_regressions"]:
        if not (source / test["path"]).is_file():
            raise ValueError("baseline.missing_native_regression")
    manifest = {"schema": "maya.governance-baseline.v1", "pin": PIN,
                "source_tree": git(repo, "rev-parse", PIN + "^{tree}").decode().strip(),
                "production_qualified": False, "assessment_only": True,
                "patches_applied": apply_patches, "patches": patch_records,
                "contract_sha256": digest(contract_path.read_bytes()),
                "tooling_sha256": {name: digest((ROOT / "scripts" / name).read_bytes())
                                   for name in ("prepare_governance_baseline.py", "run_governance_native_regressions.py")},
                "packaging_changes": [], "dependency_inputs": locks,
                "dependency_packages": len(locked["package"]),
                "baseline_files": blobs, "effective_files": effective}
    encoded = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    (output / "baseline-manifest.json").write_bytes(encoded)
    return digest(encoded)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ordinary-baseline", action="store_true")
    args = parser.parse_args()
    try:
        sha = prepare(args.source_repo, args.output, apply_patches=not args.ordinary_baseline)
    except (ValueError, OSError, KeyError, SyntaxError) as exc:
        code = str(exc) if str(exc).startswith("baseline.") else "baseline.preparation_failed"
        print(json.dumps({"status": "blocked", "reason_code": code, "production_qualified": False}))
        return 1
    print(json.dumps({"status": "reconstructed", "manifest_sha256": sha,
                      "production_qualified": False, "runtime_qualification": "not_run"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Prepare an isolated native/Maya caller overlay, never an installed runtime."""
import argparse
import json
from pathlib import Path

from prepare_governance_g2_reader import (
    ROOT, PIN, CONTRACT, base_inventory_digest, caller_contract, digest, effective_files,
    git, lifecycle_contract, patch_paths, prepare_reader, reader_contract, security_contract,
)
from validate_governance_g2_caller_contract import INPUTS as DESIGN, validate

PATCH = ROOT / "patches/hermes/0029-create-caller-acknowledgement.patch"
INPUTS = ROOT / "docs/architecture/governance-g2-caller-overlay.json"
PATCH_PATHS = {"source/gateway/session.py", "host/src/project_maya/hermes_plugins/session_creation.py",
               "host/src/project_maya/hermes_plugins/session_readers.py"}
SOURCE_PATHS = {"src/project_maya/hermes_plugins/caller_preparation.py", "tests/hermes_g2_caller_native.py"}


def overlay_contract():
    reader_contract()
    validate(json.loads(DESIGN.read_text()))
    data = json.loads(INPUTS.read_text())
    if (data["pin"] != PIN or data["production_qualified"] is not False
            or data["qualification"] != "source_caller_overlay_only"
            or data["acceptance"] != "pending_review" or type(data["schema_version"]) is not int or data["schema_version"] != 1
            or data["design_sha256"] != digest(DESIGN.read_bytes())
            or data["patch_sha256"] != digest(PATCH.read_bytes())
            or patch_paths(PATCH.read_bytes()) != PATCH_PATHS
            or set(data["effective_sha256"]) != PATCH_PATHS
            or data["host_inventory_sha256"] != host_inventory_digest(data)
            or set(data["maya_source_sha256"]) != SOURCE_PATHS
            or any(digest((ROOT / name).read_bytes()) != sha for name, sha in data["maya_source_sha256"].items())):
        raise ValueError("g2.caller_overlay_invalid")
    return data


def host_paths():
    return sorted(name for name in git(ROOT, "ls-files", "src/project_maya").decode().splitlines()
                  if not name.endswith(".pyc") and "__pycache__" not in name.split("/"))


def host_inventory_digest(data):
    inventory = {name: data["effective_sha256"].get("host/" + name, digest(source_bytes(name)))
                 for name in set(host_paths()) | {"src/project_maya/hermes_plugins/caller_preparation.py"}}
    return digest(json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode())


def source_bytes(name):
    raw = (ROOT / name).read_bytes()
    if Path(name).suffix in {".py", ".json", ".md", ".yaml", ".yml", ".toml", ".txt", ".cfg", ".ini", ".sql"}:
        raw = raw.replace(b"\r\n", b"\n")
    return raw


def verify_caller_stage(stage):
    data = overlay_contract()
    if json.loads((stage / "g2-caller-manifest.json").read_text()) != data:
        raise ValueError("g2.caller_stage_invalid")
    base = json.loads((stage / "baseline-manifest.json").read_text())
    security, _ = security_contract()
    entry, _ = caller_contract()
    lifecycle, _ = lifecycle_contract()
    if (base_inventory_digest(base) != security["base_effective_inventory_sha256"]
            or base["contract_sha256"] != digest(CONTRACT.read_bytes()) or base["pin"] != PIN
            or base["production_qualified"] is not False or base["patches_applied"] is not True):
        raise ValueError("g2.caller_stage_invalid")
    expected = security["effective_native_sha256"] | entry["effective_native_sha256"] | lifecycle["effective_native_sha256"]
    expected["gateway/session.py"] = data["effective_sha256"]["source/gateway/session.py"]
    effective_files(stage, base, {"effective_native_sha256": expected})
    names = set(host_paths()) | {"src/project_maya/hermes_plugins/caller_preparation.py"}
    tree = stage / "host"
    actual = {p.relative_to(tree).as_posix() for p in tree.rglob("*") if p.is_file()}
    if actual != names or any(p.is_symlink() for p in tree.rglob("*")):
        raise ValueError("g2.caller_host_inventory_invalid")
    for name in names:
        wanted = data["effective_sha256"].get("host/" + name, digest(source_bytes(name)))
        if digest((tree / name).read_bytes()) != wanted:
            raise ValueError("g2.caller_host_modified")
    return stage / "source", tree / "src"


def prepare(repo, output):
    data = overlay_contract()
    prepare_reader(repo, output)
    for name in set(host_paths()) | {"src/project_maya/hermes_plugins/caller_preparation.py"}:
        target = output / "host" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source_bytes(name))
    git(output, "apply", "--no-index", "--unidiff-zero", "--whitespace=error", str(PATCH))
    raw = (json.dumps(data, sort_keys=True, indent=2) + "\n").encode()
    (output / "g2-caller-manifest.json").write_bytes(raw)
    verify_caller_stage(output)
    return digest(raw)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        sha = prepare(args.source_repo, args.output.resolve())
    except (ValueError, OSError, KeyError, SyntaxError):
        print(json.dumps({"status": "blocked", "reason_code": "g2.caller_preparation_failed", "production_qualified": False}))
        raise SystemExit(1)
    print(json.dumps({"status": "reconstructed", "manifest_sha256": sha, "production_qualified": False}))

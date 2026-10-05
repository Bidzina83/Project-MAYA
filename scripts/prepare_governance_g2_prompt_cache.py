"""Reconstruct the approved source-only fixed no-snapshot overlay."""
import argparse
import json
from pathlib import Path
import shutil

from prepare_governance_g2_recognition import (
    ROOT, INPUTS as PARENT, prepare as prepare_parent, verify_stage as verify_parent, inventory,
)
from prepare_governance_g2_caller import digest, git, patch_paths

INPUTS = ROOT / "docs/architecture/governance-g2-prompt-cache.json"
PATCH = ROOT / "patches/hermes/0031-prompt-cache-mode.patch"
PATHS = {"source/agent/conversation_loop.py", "source/agent/turn_context.py",
         "host/src/project_maya/hermes_plugins/session_readers.py"}
TESTS = {"tests/hermes_g2_prompt_cache_native.py", "tests/hermes_g2_prompt_cache_ordinary.py"}


def contract():
    data = json.loads(INPUTS.read_text(encoding="utf-8"))
    if (type(data["schema_version"]) is not int or data["schema_version"] != 1
            or data["production_qualified"] is not False or data["acceptance"] != "pending_review"
            or data["qualification"] != "source_prompt_cache_mode_only"
            or data["mode"] != "rebuild_without_snapshot"
            or data["parent_sha256"] != digest(PARENT.read_bytes())
            or data["patch_sha256"] != digest(PATCH.read_bytes())
            or patch_paths(PATCH.read_bytes()) != PATHS
            or set(data["effective_sha256"]) != PATHS
            or set(data["test_sha256"]) != TESTS
            or any(digest((ROOT / name).read_bytes()) != sha for name, sha in data["test_sha256"].items())):
        raise ValueError("g2.prompt_cache_contract_invalid")
    return data


def verify_stage(stage):
    data = contract()
    if json.loads((stage / "g2-prompt-cache-manifest.json").read_text(encoding="utf-8")) != data:
        raise ValueError("g2.prompt_cache_stage_invalid")
    verify_parent(stage / "parent")
    for name in ("source", "host"):
        expected = inventory(stage / "parent" / name)
        for path, sha in data["effective_sha256"].items():
            if path.startswith(name + "/"):
                expected[path[len(name) + 1:]] = sha
        if inventory(stage / name) != expected:
            raise ValueError("g2.prompt_cache_inventory_invalid")
    return stage / "source", stage / "host/src"


def prepare(repo, output):
    data = contract()
    prepare_parent(repo, output / "parent")
    for name in ("source", "host"):
        shutil.copytree(output / "parent" / name, output / name)
    git(output, "apply", "--no-index", "--whitespace=error", str(PATCH))
    raw = (json.dumps(data, sort_keys=True, indent=2) + "\n").encode()
    (output / "g2-prompt-cache-manifest.json").write_bytes(raw)
    verify_stage(output)
    return digest(raw)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        sha = prepare(args.source_repo, args.output.resolve())
    except (ValueError, OSError, KeyError, SyntaxError):
        print(json.dumps({"status": "blocked", "reason_code": "g2.prompt_cache_preparation_failed"}))
        raise SystemExit(1)
    print(json.dumps({"status": "reconstructed", "manifest_sha256": sha, "production_qualified": False}))

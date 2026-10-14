"""Prepare ignored Gate A runtime artifacts; never provisions Windows security."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.preflight_governance_v2_windows import validate_baseline

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".codex-build/governance-v2-lpac-stage"


def copy_tree(source: Path, destination: Path) -> None:
    if source.is_symlink():
        raise ValueError("stage.link_input")
    destination.mkdir(parents=True)
    for item in source.iterdir():
        if item.is_symlink():
            raise ValueError("stage.link_input")
        if item.name in {"__pycache__", "tests", "test", "site-packages"}:
            continue
        if item.suffix in {".pth", ".pyc", ".pyo", ".egg-link"}:
            continue
        target = destination / item.name
        if item.is_dir():
            copy_tree(item, target)
        elif item.is_file():
            shutil.copyfile(item, target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--python-root", type=Path, required=True)
    parser.add_argument("--dependencies", type=Path, required=True)
    parser.add_argument("--refresh-worker", action="store_true")
    args = parser.parse_args()
    if args.refresh_worker:
        report = json.loads((OUTPUT / "runtime-manifest.json").read_text(encoding="utf-8"))
        for item in report["files"]:
            path = OUTPUT / item["path"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                raise ValueError("stage.artifact_changed")
        target = OUTPUT / "runtime/worker.py"
        shutil.copyfile(ROOT / "scripts/governance_v2_worker.py", target)
        for item in report["files"]:
            if item["path"] == "runtime/worker.py":
                item["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        (OUTPUT / "runtime-manifest.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "bootstrap_refreshed_before_qualification", "production_qualified": False}))
        return 0
    if OUTPUT.exists():
        raise ValueError("stage.output_must_be_new")
    baseline = validate_baseline(args.baseline)
    runtime = OUTPUT / "runtime"
    python = runtime / "python"
    python.mkdir(parents=True)
    for name in ("python.exe", "python313.dll", "python3.dll", "vcruntime140.dll", "vcruntime140_1.dll"):
        source = args.python_root / name
        if source.is_symlink() or not source.is_file():
            raise ValueError("stage.python_artifact_missing")
        shutil.copyfile(source, python / name)
    for name in ("Lib", "DLLs"):
        copy_tree(args.python_root / name, python / name)
    copy_tree(args.dependencies, runtime / "dependencies")
    # Keep every pinned source byte for provenance, including native tests. This
    # is an assessment stage, never a production installer payload.
    shutil.copytree(args.baseline / "source", runtime / "hermes")
    shutil.copyfile(ROOT / "scripts/governance_v2_worker.py", runtime / "worker.py")
    (OUTPUT / "state").mkdir()
    (OUTPUT / "host").mkdir()
    records = [{"path": p.relative_to(OUTPUT).as_posix(),
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
               for p in sorted(runtime.rglob("*")) if p.is_file()]
    report = {"schema": "maya.gate_a.runtime.v1", "pin": baseline["manifest"]["pin"],
              "baseline_manifest_sha256": baseline["manifest_sha256"],
              "patches_applied": False, "files": records,
              "dependencies": "copied_existing_native_test_environment_not_release_qualified",
              "security_provisioned": False, "production_qualified": False}
    (OUTPUT / "runtime-manifest.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "prepared", "file_count": len(records), "production_qualified": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

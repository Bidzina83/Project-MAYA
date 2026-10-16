"""Prepare a local-only Python startup reproduction; never executes its payload."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat


ROOT = Path(__file__).resolve().parents[1]
FROZEN_RUNTIME = "0ed977a4f7269ec86d01468e19820d616fc4e74cacd21b2919131d88457a5b32"
FROZEN_HELPER = "e72f101bea8222d14e908c2f39e7fecdca122b2f13b2abe9d5293490b7856f63"
PIN = "b13e2fd6948a59eeb59fe618914147d97a2ee90a"
STAGE_NAME = ".codex-build/governance-v2-lpac-stage"
HELPER_NAME = ".codex-build/governance-v2-native-tools/GateANative.exe"
CONTRACT = ROOT / "docs/architecture/governance-v2-python-comparison.json"
RUNBOOK = ROOT / "docs/architecture/governance_v2_python_comparison.md"
PROBE = ROOT / "scripts/governance_v2_python_probe.py"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def plain_path(path: Path) -> None:
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if (stat.S_ISLNK(info.st_mode) or
                getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
            raise ValueError("repro.reparse_path")


def inventory_name(value: str) -> PurePosixPath:
    if not isinstance(value, str):
        raise ValueError("repro.invalid_inventory")
    name = PurePosixPath(value)
    if (not name.parts or name.is_absolute() or ".." in name.parts or
            "\\" in value or ":" in value or name.as_posix() != value):
        raise ValueError("repro.invalid_inventory")
    return name


def prepare(stage: Path, helper: Path, output: Path) -> dict:
    for path in (stage, helper, output):
        plain_path(path.absolute())
    stage, helper, output = stage.resolve(), helper.resolve(), output.resolve()
    if output.exists():
        raise ValueError("repro.output_must_be_new")
    if output.is_relative_to(stage) or stage.is_relative_to(output) or helper.is_relative_to(output):
        raise ValueError("repro.overlapping_output")
    manifest_path = stage / "runtime-manifest.json"
    plain_path(manifest_path)
    raw = manifest_path.read_bytes()
    helper_bytes = helper.read_bytes()
    if digest(raw) != FROZEN_RUNTIME or digest(helper_bytes) != FROZEN_HELPER:
        raise ValueError("repro.frozen_input_changed")
    manifest = json.loads(raw)
    if manifest.get("pin") != PIN or manifest.get("patches_applied") is not False:
        raise ValueError("repro.invalid_baseline")
    python = stage / "runtime/python"
    records, seen = [], set()
    for item in manifest["files"]:
        name = inventory_name(item["path"])
        if str(name) in seen:
            raise ValueError("repro.duplicate_inventory")
        seen.add(str(name))
        if name.parts[:2] != ("runtime", "python"):
            continue
        source = stage.joinpath(*name.parts)
        plain_path(source)
        if source.suffix.lower() in {".pyc", ".pyo", ".pth", ".egg-link"}:
            raise ValueError("repro.generated_or_startup_file")
        if digest(source.read_bytes()) != item["sha256"]:
            raise ValueError("repro.python_changed")
        records.append((source, f"{STAGE_NAME}/{name}", item["sha256"]))
    expected = {source.relative_to(python).as_posix() for source, _, _ in records}
    actual = set()
    for source in python.rglob("*"):
        plain_path(source)
        if source.is_file():
            actual.add(source.relative_to(python).as_posix())
    if actual != expected or not {"python.exe", "python313.dll", "python3.dll",
                                 "vcruntime140.dll", "vcruntime140_1.dll"} <= actual:
        raise ValueError("repro.python_inventory_changed")
    contract_bytes, runbook_bytes, probe_bytes = CONTRACT.read_bytes(), RUNBOOK.read_bytes(), PROBE.read_bytes()
    contract = json.loads(contract_bytes)
    if contract["execution_authorized"] is not False or [c["id"] for c in contract["cases"]] != list("ABCD"):
        raise ValueError("repro.invalid_contract")
    # Do not place operator-specific source paths, prior state or raw logs in the bundle.
    extra = [(HELPER_NAME, helper_bytes), (f"{STAGE_NAME}/runtime/worker.py", probe_bytes),
             ("comparison-contract.json", contract_bytes), ("COMPARISON.md", runbook_bytes)]
    output.mkdir(parents=True)
    files = []
    for source, name, expected_hash in records:
        data = source.read_bytes()
        if digest(data) != expected_hash:
            raise ValueError("repro.input_changed_during_copy")
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
        if digest(target.read_bytes()) != expected_hash:
            raise ValueError("repro.copy_changed")
        files.append({"path": name, "sha256": expected_hash})
    for name, data in extra:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        files.append({"path": name, "sha256": digest(data)})
    for folder in ("state", "host"):
        (output / STAGE_NAME / folder).mkdir()
    report = {"schema": "maya.python_repro.v1", "status": "prepared_not_executed",
              "execution_authorized": False, "production_qualified": False,
              "gate_a_accepted": False, "external_sharing_authorized": False,
              "source_runtime_manifest_sha256": digest(raw), "source_helper_sha256": digest(helper_bytes),
              "python_artifacts_modified": False, "hermes_included": False,
              "original_worker_replaced_only_in_derived_bundle": True,
              "reference": contract["reference"],
              "remaining": ["vm_impact_and_permission", "reference_build_and_binary_hash",
                            "execution_manifest_and_token_observer", "capability_permission",
                            "python_license_review_before_external_sharing", "four_case_execution"],
              "files": sorted(files, key=lambda item: item["path"])}
    with (output / "reproduction-manifest.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, default=ROOT / STAGE_NAME)
    parser.add_argument("--helper", type=Path, default=ROOT / HELPER_NAME)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        plain_path(args.output.absolute())
        if not args.output.resolve().is_relative_to((ROOT / ".codex-build").resolve()):
            raise ValueError("repro.output_must_be_ignored")
        report = prepare(args.stage, args.helper, args.output)
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps({"status": "blocked", "reason_code": "repro.preparation_failed",
                          "production_qualified": False}))
        return 1
    print(json.dumps({"status": report["status"], "files": len(report["files"]),
                      "execution_authorized": False, "production_qualified": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Qualify separate switch storage/audit/path faults on unchanged Patch 37."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from prepare_governance_g2_switch_composition import (
    ROOT, INPUTS as PARENT, FIXTURES as PARENT_FIXTURES, digest,
    verify_stage as verify_parent, verify_worker_stage as verify_parent_worker,
)
from verify_governance_g2_switch_crash import inventory_digest
from qualify_governance_g2_reset_parity import clean_environment
from qualify_governance_g2_switch import validate_report

INPUTS = ROOT / "docs/architecture/governance-g2-switch-storage-paths.json"
TESTS = {"tests/hermes_g2_switch_storage_native.py": 17,
         "tests/hermes_g2_switch_paths_native.py": 42}
FIXTURES = PARENT_FIXTURES | {"tests/hermes_g2_switch_composition_native.py",
                            "tests/hermes_g2_switch_uncertainty_native.py", "tests/hermes_g2_reset_paths_native.py"}


def contract():
    data = json.loads(INPUTS.read_text(encoding="utf-8"))
    if (type(data.get("schema_version")) is not int or data["schema_version"] != 1
            or data.get("production_qualified") is not False or data.get("acceptance") != "pending_review"
            or data.get("qualification") != "source_switch_storage_audit_paths_only"
            or data.get("expected_tests") != TESTS
            or any(type(n) is not int for n in data.get("expected_tests", {}).values())
            or data.get("parent_inputs_sha256") != digest(PARENT.read_bytes())
            or set(data.get("test_sha256", {})) != set(TESTS)
            or any(data["test_sha256"][p] != digest((ROOT / p).read_bytes()) for p in TESTS)
            or set(data.get("fixture_sha256", {})) != FIXTURES
            or any(data["fixture_sha256"][p] != digest((ROOT / p).read_bytes()) for p in FIXTURES)
            or any(type(data.get(name)) is not str or len(data[name]) != 64
                   or any(c not in "0123456789abcdef" for c in data[name])
                   for name in ("native_inventory_sha256", "host_inventory_sha256"))):
        raise ValueError("g2.switch_storage_paths_contract_invalid")
    return data


def verify_worker_stage(stage):
    data = contract()
    source, host = verify_parent_worker(stage)
    if (inventory_digest(stage / "source") != data["native_inventory_sha256"]
            or inventory_digest(stage / "host") != data["host_inventory_sha256"]):
        raise ValueError("g2.switch_storage_paths_inventory_invalid")
    return source, host


def verify_stage(stage):
    verify_parent(stage)
    return verify_worker_stage(stage)


def qualify(stage, python, output):
    contract()
    source, host = verify_stage(stage)
    if output.exists() or not output.is_relative_to(ROOT / ".codex-build"):
        raise ValueError("g2.switch_storage_paths_report_output_invalid")
    output.mkdir(parents=True)
    outcomes = {}
    for number, (test, count) in enumerate(TESTS.items()):
        env = clean_environment(source, output / ("home-" + str(number)))
        env["PYTHONPATH"] = os.pathsep.join((str(host), str(source)))
        report = output / ("suite-" + str(number) + ".xml")
        process = subprocess.run([str(python), "-B", "-m", "pytest", str(ROOT / test),
                                  "--rootdir=" + str(source), "-p", "no:cacheprovider",
                                  "--junitxml=" + str(report), "-q"],
                                 cwd=output, env=env, timeout=900)
        outcomes[test] = validate_report(report, process.returncode, count)
    verify_stage(stage)
    result = {"passed": sum(outcomes.values()), "tests": outcomes,
              "qualification": "source_switch_storage_audit_paths_only",
              "production_qualified": False, "acceptance": "pending_review",
              "inputs_sha256": digest(INPUTS.read_bytes())}
    (output / "qualification.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(qualify(args.stage.resolve(), args.python.resolve(), args.output.resolve())))

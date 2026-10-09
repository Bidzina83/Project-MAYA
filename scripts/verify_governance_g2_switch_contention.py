"""Verify bounded process contention on unchanged Patch 37; not acceptance."""
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

INPUTS = ROOT / "docs/architecture/governance-g2-switch-contention.json"
TEST = "tests/hermes_g2_switch_contention_native.py"
FIXTURES = PARENT_FIXTURES | {"tests/hermes_g2_switch_composition_native.py"}
CASES = ("projection_lock", "prepared_sink_lock", "sqlite_writer_lock", "active_request",
         "native_commit", "publication", "pending_and_acknowledged", "unconfirmed_hosts")


def contract():
    data = json.loads(INPUTS.read_text(encoding="utf-8"))
    if (type(data.get("schema_version")) is not int or data["schema_version"] != 1
            or data.get("production_qualified") is not False or data.get("acceptance") != "pending_review"
            or data.get("qualification") != "source_switch_process_contention_only"
            or type(data.get("expected_native_tests")) is not int or data["expected_native_tests"] != len(CASES)
            or data.get("cases") != list(CASES)
            or data.get("parent_inputs_sha256") != digest(PARENT.read_bytes())
            or data.get("test_sha256") != digest((ROOT / TEST).read_bytes())
            or set(data.get("fixture_sha256", {})) != FIXTURES
            or any(data["fixture_sha256"][p] != digest((ROOT / p).read_bytes()) for p in FIXTURES)
            or any(type(data.get(name)) is not str or len(data[name]) != 64
                   or any(c not in "0123456789abcdef" for c in data[name])
                   for name in ("native_inventory_sha256", "host_inventory_sha256"))):
        raise ValueError("g2.switch_contention_contract_invalid")
    return data


def verify_worker_stage(stage):
    data = contract()
    source, host = verify_parent_worker(stage)
    if (inventory_digest(stage / "source") != data["native_inventory_sha256"]
            or inventory_digest(stage / "host") != data["host_inventory_sha256"]):
        raise ValueError("g2.switch_contention_inventory_invalid")
    return source, host


def verify_stage(stage):
    verify_parent(stage)
    return verify_worker_stage(stage)


def qualify(stage, python, output):
    data = contract()
    source, host = verify_stage(stage)
    if output.exists() or not output.is_relative_to(ROOT / ".codex-build"):
        raise ValueError("g2.switch_contention_report_output_invalid")
    output.mkdir(parents=True)
    env = clean_environment(source, output / "home")
    env["PYTHONPATH"] = os.pathsep.join((str(host), str(source)))
    report = output / "native.xml"
    process = subprocess.run([str(python), "-B", "-m", "pytest", str(ROOT / TEST),
                              "--rootdir=" + str(source), "-p", "no:cacheprovider",
                              "--junitxml=" + str(report), "-q"],
                             cwd=output, env=env, timeout=900)
    passed = validate_report(report, process.returncode, data["expected_native_tests"])
    verify_stage(stage)
    result = {"passed": passed, "qualification": "source_switch_process_contention_only",
              "production_qualified": False, "acceptance": "pending_review",
              "inputs_sha256": digest(INPUTS.read_bytes()), "cases": data["cases"]}
    (output / "qualification.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(qualify(args.stage.resolve(), args.python.resolve(), args.output.resolve())))

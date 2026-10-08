"""Run the bounded atomic-switch native matrix on verified source artifacts."""
import argparse
import json
from pathlib import Path
import os
import subprocess
import xml.etree.ElementTree as ET

from prepare_governance_g2_switch import ROOT, TEST, contract, verify_stage
from qualify_governance_g2_reset_parity import clean_environment


def validate_report(report, returncode, expected):
    cases = ET.parse(report).findall(".//testcase")
    names = [(c.get("classname"), c.get("name")) for c in cases]
    if (returncode != 0 or len(cases) != expected or len(set(names)) != expected
            or any(not c.get("name") or c.find("failure") is not None
                   or c.find("error") is not None or c.find("skipped") is not None for c in cases)):
        raise ValueError("g2.switch_native_matrix_failed")
    return len(cases)


def qualify(stage, python, output):
    data = contract()
    source, host = verify_stage(stage)
    if output.exists() or not output.is_relative_to(ROOT / ".codex-build"):
        raise ValueError("g2.switch_report_output_invalid")
    output.mkdir(parents=True)
    env = clean_environment(source, output / "home")
    env["PYTHONPATH"] = os.pathsep.join((str(host), str(source)))
    report = output / "native.xml"
    process = subprocess.run([str(python), "-B", "-m", "pytest", str(ROOT / TEST),
                              "--rootdir=" + str(source), "-p", "no:cacheprovider",
                              "--junitxml=" + str(report), "-q"],
                             cwd=output, env=env, timeout=600)
    passed = validate_report(report, process.returncode, data["expected_native_tests"])
    # Verify ancestry and full source inventories again before recording success.
    verify_stage(stage)
    result = {"passed": passed, "qualification": "source_switch_atomic_only",
              "production_qualified": False, "acceptance": "pending_review"}
    (output / "qualification.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(qualify(args.stage.resolve(), args.python.resolve(), args.output.resolve())))

"""Qualify bounded switch composition and unchanged create/reset/atomic replays."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from prepare_governance_g2_switch_composition import ROOT, INPUTS, contract, digest, inventory, verify_stage
from qualify_governance_g2_switch import validate_report
from qualify_governance_g2_reset_parity import clean_environment


def qualify(stage, python, output):
    data = contract()
    source, host = verify_stage(stage)
    if output.exists() or not output.is_relative_to(ROOT / ".codex-build"):
        raise ValueError("g2.switch_composition_report_output_invalid")
    output.mkdir(parents=True)
    env = clean_environment(source, output / "home")
    env["PYTHONPATH"] = os.pathsep.join((str(host), str(source)))
    passed = {}
    for test, expected in data["expected_tests"].items():
        report = output / (Path(test).stem + ".xml")
        process = subprocess.run([str(python), "-B", "-m", "pytest", str(ROOT / test),
                                  "--rootdir=" + str(source), "-p", "no:cacheprovider",
                                  "--junitxml=" + str(report), "-q"],
                                 cwd=output, env=env, timeout=600)
        passed[test] = validate_report(report, process.returncode, expected)
    verify_stage(stage)
    result = {"passed": passed, "qualification": "source_switch_composition_only",
              "production_qualified": False, "acceptance": "pending_review"}
    (output / "qualification.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    return result


def qualify_ordinary(stage, python, repo, output):
    from prepare_governance_baseline import PIN, prepare
    from qualify_governance_g2_reset_parity import ORDINARY, KNOWN_WINDOWS_FAILURES, run_profile
    contract()
    source, _ = verify_stage(stage)
    if output.exists() or not output.is_relative_to(ROOT / ".codex-build"):
        raise ValueError("g2.switch_composition_report_output_invalid")
    output.mkdir(parents=True)
    prepare(repo, output / "unpatched", apply_patches=False)
    baseline = json.loads((output / "unpatched/baseline-manifest.json").read_text())
    unpatched = output / "unpatched/source"
    expected = {row["path"]: row["sha256"] for row in baseline["baseline_files"]}
    if baseline["pin"] != PIN or baseline["patches_applied"] is not False or inventory(unpatched) != expected:
        raise ValueError("g2.switch_ordinary_baseline_invalid")
    for test in (*ORDINARY, "tests/conftest.py"):
        if digest((source / test).read_bytes()) != expected[test]:
            raise ValueError("g2.switch_ordinary_native_test_changed")
    original = inventory(source)
    control = run_profile(python, unpatched, output / "unpatched-work")
    candidate = run_profile(python, source, output / "candidate-work")
    if inventory(unpatched) != expected or inventory(source) != original or control != candidate:
        raise ValueError("g2.switch_ordinary_outcome_mismatch")
    failures = {name for cases in control.values() for name, status in cases.items() if status == "failed"}
    if failures != (KNOWN_WINDOWS_FAILURES if os.name == "nt" else set()):
        raise ValueError("g2.switch_ordinary_unexpected_failures")
    verify_stage(stage)
    count = sum(len(cases) for cases in control.values())
    result = {"status": "bounded_parity_passed", "production_qualified": False,
              "qualification": "source_switch_ordinary_parity_only", "acceptance": "pending_review",
              "inputs_sha256": digest(INPUTS.read_bytes()), "pin": PIN,
              "per_profile": {"tests": count, "passed": count - len(failures),
                              "failed": len(failures), "skipped": 0},
              "unchanged_windows_failures": sorted(failures), "ordinary_outcomes": control}
    (output / "parity-report.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    return {k: result[k] for k in ("status", "production_qualified", "qualification", "per_profile", "unchanged_windows_failures")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ordinary-source-repo", type=Path,
                        help="Compare unchanged ordinary cases with unpatched pinned Git objects instead.")
    args = parser.parse_args()
    if args.ordinary_source_repo:
        result = qualify_ordinary(args.stage.resolve(), args.python.resolve(),
                                  args.ordinary_source_repo.resolve(), args.output.resolve())
    else:
        result = qualify(args.stage.resolve(), args.python.resolve(), args.output.resolve())
    print(json.dumps(result))

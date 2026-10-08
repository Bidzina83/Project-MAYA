"""Run ordinary controls on disposable corrected and pinned-unpatched sources."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

from prepare_governance_baseline import PIN, prepare
from prepare_governance_g2_reset_gate import inventory
from verify_governance_g2_reset_paths import ROOT, ORDINARY, CACHE, COUNTS, INPUTS, digest, contract, verify_stage

KNOWN_WINDOWS_FAILURES = {
    'TestTeePattern::test_tee_absolute_home_bashrc',
    'TestHermesConfigWriteProtection::test_sed_in_place_absolute_hermes_home_config',
    'TestHermesConfigWriteProtection::test_sed_in_place_absolute_hermes_home_env',
    'TestHermesConfigWriteProtection::test_perl_in_place_absolute_hermes_home_config',
    'TestHermesConfigWriteProtection::test_ruby_in_place_absolute_hermes_home_env',
    'TestSensitiveRedirectPattern::test_append_to_absolute_home_ssh_authorized_keys',
    'TestSensitiveRedirectPattern::test_redirect_to_absolute_home_bashrc',
    'TestSensitiveRedirectPattern::test_redirect_to_home_set_after_import',
    'TestSensitiveInPlaceEditPattern::test_ruby_in_place_absolute_home_zshrc',
}


def outcomes(path):
    result = {}
    for case in ET.parse(path).getroot().iter('testcase'):
        name = case.get('classname', '').rsplit('.', 1)[-1] + '::' + case.get('name', '')
        if name in result or case.find('error') is not None or case.find('skipped') is not None:
            raise ValueError('g2.parity_incomplete_or_skipped')
        result[name] = 'failed' if case.find('failure') is not None else 'passed'
    if not result:
        raise ValueError('g2.parity_empty_report')
    return result


def clean_environment(source, home):
    suffixes = ('_KEY', '_TOKEN', '_SECRET', '_PASSWORD', '_CREDENTIALS')
    env = {k: v for k, v in os.environ.items()
           if not k.upper().endswith(suffixes) and not k.startswith('HERMES_SESSION_')
           and k.upper() not in {'PYTEST_ADDOPTS', 'PYTEST_PLUGINS', 'PYTHONHOME', 'PYTHONSTARTUP'}}
    env.update(PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1',
               HERMES_HOME=str(home), PYTHONHASHSEED='0', TZ='UTC')
    return env


def run_profile(python, source, work):
    work.mkdir()
    result = {}
    for number, target in enumerate((*ORDINARY, CACHE)):
        test = ROOT / target if target == CACHE else source / target
        report = work / ('suite-' + str(number) + '.xml')
        process = subprocess.run([str(python), '-B', '-m', 'pytest', str(test),
                                  '--rootdir=' + str(source), '-p', 'no:cacheprovider',
                                  '--junitxml=' + str(report), '-q'],
                                 cwd=work, env=clean_environment(source, work / 'home'),
                                 capture_output=True, timeout=300)
        if process.returncode not in {0, 1} or not report.is_file():
            raise ValueError('g2.parity_test_process_failed')
        cases = outcomes(report)
        if len(cases) != COUNTS[target]:
            raise ValueError('g2.parity_incomplete_case_count')
        if process.returncode != int('failed' in cases.values()):
            raise ValueError('g2.parity_exit_report_mismatch')
        result[target] = cases
    return result


def qualify(stage, repo, python, output):
    contract()
    source, _ = verify_stage(stage)
    if output.exists() or not output.is_relative_to(ROOT / '.codex-build'):
        raise ValueError('g2.parity_output_invalid')
    output.mkdir(parents=True)
    prepare(repo, output / 'unpatched', apply_patches=False)
    baseline = json.loads((output / 'unpatched/baseline-manifest.json').read_text())
    unpatched = output / 'unpatched/source'
    expected = {row['path']: row['sha256'] for row in baseline['baseline_files']}
    if baseline['pin'] != PIN or baseline['patches_applied'] is not False or inventory(unpatched) != expected:
        raise ValueError('g2.parity_baseline_invalid')
    copied = output / 'candidate/source'
    shutil.copytree(source, copied)
    corrected = inventory(source)
    if inventory(copied) != corrected:
        raise ValueError('g2.parity_copy_invalid')
    for target in (*ORDINARY, 'tests/conftest.py'):
        if digest((copied / target).read_bytes()) != expected[target]:
            raise ValueError('g2.parity_changed_native_tests')
    control = run_profile(python, unpatched, output / 'unpatched-work')
    candidate = run_profile(python, copied, output / 'candidate-work')
    if inventory(unpatched) != expected or inventory(copied) != corrected:
        raise ValueError('g2.parity_source_changed_during_tests')
    if control != candidate:
        raise ValueError('g2.parity_outcome_mismatch')
    failures = {name for cases in control.values() for name, state in cases.items() if state == 'failed'}
    known = KNOWN_WINDOWS_FAILURES if os.name == 'nt' else set()
    if failures != known:
        raise ValueError('g2.parity_unexpected_failures')
    count = sum(len(cases) for cases in control.values())
    report = dict(status='bounded_parity_passed', production_qualified=False,
                  qualification='source_reset_paths_parity_only', acceptance='pending_review',
                  pin=PIN, inputs_sha256=digest(INPUTS.read_bytes()),
                  per_profile=dict(tests=count, passed=count - len(failures), failed=len(failures), skipped=0),
                  unchanged_windows_failures=sorted(failures), ordinary_outcomes=control,
                  native_test_sha256={p: expected[p] for p in ORDINARY},
                  baseline_inventory_sha256=digest(json.dumps(expected, sort_keys=True).encode()),
                  candidate_inventory_sha256=digest(json.dumps(corrected, sort_keys=True).encode()))
    (output / 'parity-report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--source-repo', type=Path, required=True)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = qualify(args.stage.resolve(), args.source_repo.resolve(), args.python.resolve(), args.output.resolve())
    except Exception:
        print(json.dumps({'status': 'blocked', 'reason_code': 'g2.reset_parity_failed', 'production_qualified': False}))
        raise SystemExit(1) from None
    print(json.dumps({k: result[k] for k in ('status', 'production_qualified', 'qualification', 'per_profile', 'unchanged_windows_failures')}, sort_keys=True))

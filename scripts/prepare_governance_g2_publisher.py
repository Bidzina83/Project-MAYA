"""Reconstruct an approved host-only publisher correction over frozen Patch 34."""
import argparse
import json
from pathlib import Path
import shutil

from prepare_governance_g2_reset_gate import ROOT, INPUTS as PARENT, verify_stage as verify_parent, inventory
from prepare_governance_g2_caller import digest, git

INPUTS = ROOT / 'docs/architecture/governance-g2-publisher.json'
PATCH = ROOT / 'patches/hermes/0035-complete-projection-publication.patch'
PATH = 'host/src/project_maya/hermes_plugins/session_creation.py'
PARENT_STAGE = ROOT / '.codex-build/governance-g2-reset-gate-20261007-final-c'
COMPOSITION = ROOT / '.codex-build/governance-g2-reset-composition-20261006-final'
BASELINE = ROOT / '.codex-build/governance-g2-prompt-cache-20261005-final-c'
TESTS = {'tests/hermes_g2_publisher_create_native.py': 80,
         'tests/hermes_g2_publisher_reset_native.py': 34,
         'tests/hermes_g2_publisher_atomic_native.py': 22,
         'tests/hermes_g2_publisher_storage_native.py': 12,
         'tests/hermes_g2_publisher_combined_native.py': 13,
         'tests/hermes_g2_publisher_integrity_native.py': 6}
FIXTURES = {'tests/hermes_g2_' + name + '.py' for name in (
    'create_native', 'caller_native', 'recognition_ordinary', 'create_loop_native',
    'recognition_native', 'create_failures_native', 'reader_native', 'create_crash_native',
    'create_authority_loss_native', 'caller_qualification_native', 'prompt_cache_ordinary',
    'prompt_cache_native', 'final_create_native', 'create_preflight_native',
    'reset_gate_diagnostic_native', 'reset_native', 'reset_gate_atomic_native',
    'reset_storage_native', 'reset_late_executor_native', 'reset_descriptors_native',
    'reset_step2_regression_native', 'reset_crash_native', 'reset_gate_native',
    'reset_contention_native', 'reset_composition_native', 'reset_combined_faults_native',
    'restart_loop_native')}


def contract():
    data = json.loads(INPUTS.read_text(encoding='utf-8'))
    paths = {line.split()[3][2:] for line in PATCH.read_text().splitlines() if line.startswith('diff --git ')}
    if (type(data.get('schema_version')) is not int or data['schema_version'] != 1
            or data.get('production_qualified') is not False or data.get('acceptance') != 'pending_review'
            or data.get('qualification') != 'source_complete_publisher_only'
            or data.get('parent_sha256') != digest(PARENT.read_bytes())
            or data.get('patch_sha256') != digest(PATCH.read_bytes()) or paths != {PATH}
            or set(data.get('effective_sha256', {})) != {PATH}
            or data.get('expected_tests') != TESTS
            or any(type(value) is not int for value in data.get('expected_tests', {}).values())
            or set(data.get('test_sha256', {})) != set(TESTS)
            or any(data['test_sha256'][p] != digest((ROOT / p).read_bytes()) for p in TESTS)
            or set(data.get('fixture_sha256', {})) != FIXTURES
            or any(not p.startswith('tests/hermes_g2_') or not p.endswith('.py')
                   or sha != digest((ROOT / p).read_bytes()) for p, sha in data['fixture_sha256'].items())):
        raise ValueError('g2.publisher_contract_invalid')
    return data


def verify_worker_stage(stage):
    data = contract()
    if json.loads((stage / 'g2-publisher-manifest.json').read_text()) != data:
        raise ValueError('g2.publisher_manifest_invalid')
    for tree in ('source', 'host'):
        expected = inventory(PARENT_STAGE / tree)
        if tree == 'host':
            expected[PATH[len('host/'):]] = data['effective_sha256'][PATH]
        if inventory(stage / tree) != expected:
            raise ValueError('g2.publisher_inventory_invalid')
    return stage / 'source', stage / 'host/src'


def verify_stage(stage):
    verify_parent(PARENT_STAGE, COMPOSITION, BASELINE)
    return verify_worker_stage(stage)


def prepare(output):
    data = contract()
    verify_parent(PARENT_STAGE, COMPOSITION, BASELINE)
    if output.exists() or output.is_relative_to(PARENT_STAGE) or PARENT_STAGE.is_relative_to(output):
        raise ValueError('g2.publisher_output_invalid')
    for tree in ('source', 'host'):
        shutil.copytree(PARENT_STAGE / tree, output / tree)
    git(output, 'apply', '--no-index', '--whitespace=error', str(PATCH))
    (output / 'g2-publisher-manifest.json').write_text(json.dumps(data, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    verify_worker_stage(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.output.resolve())
    print(json.dumps({'status': 'reconstructed', 'production_qualified': False}))

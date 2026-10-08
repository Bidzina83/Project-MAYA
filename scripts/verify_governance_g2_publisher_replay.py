"""Bind unchanged Step 4 test bodies to the corrected publisher candidate."""
import json
from prepare_governance_g2_publisher import ROOT, INPUTS as PARENT, FIXTURES, digest, verify_stage as verify_parent, verify_worker_stage as verify_parent_worker

INPUTS = ROOT / 'docs/architecture/governance-g2-publisher-replay.json'
TESTS = {'tests/hermes_g2_publisher_crash_native.py': 8,
         'tests/hermes_g2_publisher_contention_native.py': 4,
         'tests/hermes_g2_publisher_descriptors_native.py': 18,
         'tests/hermes_g2_publisher_late_native.py': 3}


def contract():
    data = json.loads(INPUTS.read_text())
    if (type(data.get('schema_version')) is not int or data['schema_version'] != 1
            or data.get('production_qualified') is not False or data.get('acceptance') != 'pending_review'
            or data.get('qualification') != 'source_publisher_step4_replay_only'
            or data.get('parent_sha256') != digest(PARENT.read_bytes())
            or data.get('expected_tests') != TESTS
            or any(type(value) is not int for value in data.get('expected_tests', {}).values())
            or set(data.get('test_sha256', {})) != set(TESTS)
            or any(data['test_sha256'][p] != digest((ROOT / p).read_bytes()) for p in TESTS)
            or set(data.get('fixture_sha256', {})) != FIXTURES
            or any(data['fixture_sha256'][p] != digest((ROOT / p).read_bytes()) for p in FIXTURES)):
        raise ValueError('g2.publisher_replay_contract_invalid')
    return data


def verify_stage(stage):
    contract()
    return verify_parent(stage)


def verify_worker_stage(stage):
    contract()
    return verify_parent_worker(stage)

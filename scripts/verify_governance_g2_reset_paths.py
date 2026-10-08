"""Verify bounded reset path/parity inputs without changing runtime qualification."""
import json
from prepare_governance_g2_publisher import ROOT, INPUTS as PARENT, FIXTURES, digest, verify_stage as verify_parent

INPUTS = ROOT / 'docs/architecture/governance-g2-reset-paths.json'
TEST = 'tests/hermes_g2_reset_paths_native.py'
ORDINARY = ('tests/gateway/test_session.py', 'tests/tools/test_approval.py',
            'tests/tools/test_slash_confirm.py')
CACHE = 'tests/hermes_g2_prompt_cache_ordinary.py'
COUNTS = dict(zip((*ORDINARY, CACHE), (88, 225, 16, 2)))


def contract():
    data = json.loads(INPUTS.read_text(encoding='utf-8'))
    if (type(data.get('schema_version')) is not int or data['schema_version'] != 1
            or data.get('production_qualified') is not False
            or data.get('acceptance') != 'pending_review'
            or data.get('qualification') != 'source_reset_paths_parity_only'
            or data.get('parent_sha256') != digest(PARENT.read_bytes())
            or type(data.get('expected_path_tests')) is not int or data['expected_path_tests'] != 26
            or data.get('test_sha256') != {TEST: digest((ROOT / TEST).read_bytes())}
            or set(data.get('fixture_sha256', {})) != FIXTURES
            or any(data['fixture_sha256'][p] != digest((ROOT / p).read_bytes()) for p in FIXTURES)
            or data.get('ordinary_targets') != list(ORDINARY)
            or data.get('ordinary_expected_counts') != COUNTS
            or any(type(value) is not int for value in data.get('ordinary_expected_counts', {}).values())
            or data.get('cache_sha256') != digest((ROOT / CACHE).read_bytes())):
        raise ValueError('g2.reset_paths_contract_invalid')
    return data


def verify_stage(stage):
    contract()
    return verify_parent(stage)

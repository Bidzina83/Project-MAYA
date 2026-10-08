"""Unchanged bounded reset gate replay; parent evidence remains frozen."""
import importlib.util
from pathlib import Path
import sys
import pytest
import hermes_state

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publisher_reset_parent', ROOT / 'tests/hermes_g2_reset_gate_native.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
for name in ('host', 'caller_host', 'loop_host', 'recognition_host', 'cache_host', 'reset_host'):
    globals()[name] = getattr(base, name)
for name in vars(base):
    if name.startswith('test_'):
        globals()[name] = getattr(base, name)


def verify_source(worker=False):
    sys.path.insert(0, str(ROOT / 'scripts'))
    from prepare_governance_g2_publisher import verify_stage, verify_worker_stage
    stage = Path(hermes_state.__file__).resolve().parent.parent
    (verify_worker_stage if worker else verify_stage)(stage)


@pytest.fixture(scope='module', autouse=True)
def verified_source():
    verify_source()


def restart_probe(directory):
    verify_source(worker=True)
    base.restart_probe(directory)


base.__file__ = __file__

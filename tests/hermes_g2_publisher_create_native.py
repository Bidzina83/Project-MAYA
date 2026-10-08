"""Unchanged final create cases replayed against the verified publisher candidate."""
import importlib.util
from pathlib import Path
import sys
import pytest
import hermes_state

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publisher_create_parent', ROOT / 'tests/hermes_g2_final_create_native.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
host, caller_host, reader_host = base.host, base.caller_host, base.reader_host
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


# Route unchanged subprocess test bodies to this independently verified test host.
base.__file__ = __file__
base.verify_source = lambda: verify_source(worker=True)

if __name__ == '__main__':
    assert len(sys.argv) == 4 and sys.argv[1] == '--worker'
    base.worker(sys.argv[2], sys.argv[3])

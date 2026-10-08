"""Frozen process-crash cases with an explicit corrected-profile worker host."""
from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import io
import json
from pathlib import Path
import sys
import pytest
import hermes_state

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publisher_crash_parent', ROOT / 'tests/hermes_g2_reset_crash_native.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
for name in vars(base):
    if name.startswith('test_'):
        globals()[name] = getattr(base, name)
base.__file__ = __file__


def verify(worker=False):
    sys.path.insert(0, str(ROOT / 'scripts'))
    from verify_governance_g2_publisher_replay import verify_stage, verify_worker_stage
    stage = Path(hermes_state.__file__).resolve().parent.parent
    return (verify_worker_stage if worker else verify_stage)(stage)


@pytest.fixture(scope='module', autouse=True)
def verified_source():
    verify()


def worker_verifier(stage):
    sys.path.insert(0, str(ROOT / 'scripts'))
    from verify_governance_g2_publisher_replay import verify_worker_stage
    return verify_worker_stage(stage)


base.stage_verifier = lambda: worker_verifier

if __name__ == '__main__':
    try:
        operation, stage, directory, scenario = sys.argv[1:]
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            if operation == 'crash':
                base.crash_worker(Path(stage), Path(directory), scenario)
            elif operation == 'restart' and scenario in {'source', 'reset'}:
                report = base.restart_worker(Path(stage), Path(directory), scenario == 'source')
            else:
                raise ValueError('invalid scenario')
    except Exception:
        print(json.dumps({'status': 'blocked', 'reason_code': 'g2.publisher_crash_failed'}))
        raise SystemExit(1)
    print(json.dumps(report, sort_keys=True))

"""Frozen contention bodies; newly verified worker profile, no native changes."""
from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publisher_contention_parent', ROOT / 'tests/hermes_g2_reset_contention_native.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
reset_host = base.reset_host
for name in vars(base):
    if name.startswith('test_'):
        globals()[name] = getattr(base, name)
base.__file__ = __file__
spec = importlib.util.spec_from_file_location('publisher_contention_verification', ROOT / 'tests/hermes_g2_publisher_crash_native.py')
verification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verification)
verified_source = verification.verified_source


if __name__ == '__main__':
    try:
        stage, directory, name, operation = sys.argv[1:]
        assert name in {'busy', 'commit', 'first', 'second', 'pending'}
        sys.path.insert(0, str(ROOT / 'scripts'))
        from verify_governance_g2_publisher_replay import verify_worker_stage
        # Only test-profile verification is rebound; native authority is untouched.
        import verify_governance_g2_reset_contention as legacy_verifier
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            verify_worker_stage(Path(stage))
            legacy_verifier.verify_worker_stage = verify_worker_stage
            result = base.worker(Path(stage), Path(directory), name, operation)
    except BaseException:
        print(json.dumps({'status': 'failed', 'reason_code': 'g2.publisher_contention_failed'}))
        raise SystemExit(1) from None
    print(json.dumps(result, sort_keys=True))

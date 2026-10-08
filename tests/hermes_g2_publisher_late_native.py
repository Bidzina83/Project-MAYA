"""Unchanged actual late-executor cases against corrected publisher bytes."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publisher_late_parent', ROOT / 'tests/hermes_g2_reset_late_executor_native.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
reset_host, late_host = base.reset_host, base.late_host
for name in vars(base):
    if name.startswith('test_'):
        globals()[name] = getattr(base, name)
spec = importlib.util.spec_from_file_location('publisher_late_verification', ROOT / 'tests/hermes_g2_publisher_crash_native.py')
verification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verification)
verified_source = verification.verified_source

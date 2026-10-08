"""Frozen atomic reset cases on the publisher candidate."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publisher_atomic_parent', ROOT / 'tests/hermes_g2_reset_gate_atomic_native.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
host, caller_host, reset_host = base.host, base.caller_host, base.reset_host
for name in vars(base):
    if name.startswith('test_'):
        globals()[name] = getattr(base, name)
spec = importlib.util.spec_from_file_location('publisher_atomic_verification', ROOT / 'tests/hermes_g2_publisher_reset_native.py')
verification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verification)
verified_source = verification.verified_source

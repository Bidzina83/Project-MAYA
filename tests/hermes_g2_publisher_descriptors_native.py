"""Replay exact descriptor cases with corrected-profile subprocess verification."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publisher_descriptor_parent', ROOT / 'tests/hermes_g2_reset_descriptors_native.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
reset_host = base.reset_host
for name in vars(base):
    if name.startswith('test_'):
        globals()[name] = getattr(base, name)
base.fixtures.__file__ = str(ROOT / 'tests/hermes_g2_publisher_contention_native.py')
spec = importlib.util.spec_from_file_location('publisher_descriptor_verification', ROOT / 'tests/hermes_g2_publisher_crash_native.py')
verification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verification)
verified_source = verification.verified_source

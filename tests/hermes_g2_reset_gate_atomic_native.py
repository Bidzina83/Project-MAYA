"""Unchanged atomic reset cases against the approved gate correction."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gate_atomic_parent", ROOT / "tests/hermes_g2_reset_step2_regression_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
host = base.host
caller_host = base.caller_host
reset_host = base.reset_host
for name in vars(base):
    if name.startswith("test_"):
        globals()[name] = getattr(base, name)

spec = importlib.util.spec_from_file_location("gate_verifier", ROOT / "tests/hermes_g2_reset_gate_native.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
verified_source = gate.verified_source

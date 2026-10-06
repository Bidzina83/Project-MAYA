"""Unchanged Step 2 cases against the composed source, with its own verifier."""
import importlib.util
from pathlib import Path
import sys

import hermes_state
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reset_atomic_regression", ROOT / "tests/hermes_g2_reset_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
host = base.host
caller_host = base.caller_host
reset_host = base.reset_host
for name in vars(base):
    if name.startswith("test_"):
        globals()[name] = getattr(base, name)


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_reset_composition import verify_stage
        verify_stage(Path(hermes_state.__file__).resolve().parent.parent,
                     ROOT / ".codex-build/governance-g2-reset-20261006-final-b",
                     ROOT / ".codex-build/governance-g2-prompt-cache-20261005-final-c")
    finally:
        sys.path.pop(0)

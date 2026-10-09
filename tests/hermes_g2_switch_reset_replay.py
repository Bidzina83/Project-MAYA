"""Replay frozen reset composition assertions on the verified switch candidate."""
import importlib.util
from pathlib import Path
import sys
import hermes_state
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("switch_reset_replay_parent", ROOT / "tests/hermes_g2_reset_gate_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
for name in ("host", "caller_host", "loop_host", "recognition_host", "cache_host", "reset_host"):
    globals()[name] = getattr(base, name)
for name in vars(base):
    if name.startswith("test_"):
        globals()[name] = getattr(base, name)


def verify_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_switch_composition import verify_worker_stage
        verify_worker_stage(Path(hermes_state.__file__).resolve().parent.parent)
    finally:
        sys.path.pop(0)


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    verify_source()


def restart_probe(directory):
    verify_source()
    base.restart_probe(directory)


base.__file__ = __file__

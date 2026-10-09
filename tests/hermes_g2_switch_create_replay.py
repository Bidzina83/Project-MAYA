"""Replay frozen final create assertions on the verified switch candidate."""
import importlib.util
from pathlib import Path
import sys
import hermes_state
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("switch_create_replay_parent", ROOT / "tests/hermes_g2_final_create_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
host, caller_host, reader_host = base.host, base.caller_host, base.reader_host
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


base.__file__ = __file__
base.verify_source = verify_source

if __name__ == "__main__":
    assert len(sys.argv) == 4 and sys.argv[1] == "--worker"
    base.worker(sys.argv[2], sys.argv[3])

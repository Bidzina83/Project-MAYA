"""Real-process crash diagnostics; no recovery or production activation."""
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import portalocker
import pytest
import hermes_state

ROOT = Path(__file__).resolve().parents[1]


def fixture_module():
    spec = importlib.util.spec_from_file_location("create_fixture", ROOT / "tests/hermes_g2_create_native.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def crash_worker(directory, boundary):
    module = fixture_module()
    monkeypatch = pytest.MonkeyPatch()
    fixture = module.host.__wrapped__(Path(directory), monkeypatch)
    host = next(fixture)
    coordinator = host[3]
    if boundary in {"before_commit", "after_commit"}:
        original = coordinator._commit
        def crash(conn):
            if boundary == "after_commit":
                original(conn)
            os._exit(73)
        coordinator._commit = crash
    else:
        original = coordinator._publish
        def crash(raw):
            if boundary == "after_replace":
                original(raw)
            os._exit(73)
        coordinator._publish = crash
    module.create(host)
    raise RuntimeError("crash boundary not reached")


@pytest.mark.parametrize("boundary", ["before_commit", "after_commit", "before_replace", "after_replace"])
def test_process_crash_preserves_transaction_and_quarantines_publication(tmp_path, boundary):
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_reader import verify_reader_stage
        source = Path(hermes_state.__file__).resolve().parent
        verified, _ = verify_reader_stage(source.parent)
        assert source == verified.resolve()
    finally:
        sys.path.pop(0)
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((str(source), str(ROOT / "src")))
    result = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()),
                             "--crash-worker", str(tmp_path), boundary],
                            cwd=source, env=environment, capture_output=True, timeout=60)
    assert result.returncode == 73, "worker did not reach selected crash boundary"
    # New connections after actual process exit observe SQLite recovery, not
    # an in-process rollback or a replacement persistence implementation.
    with sqlite3.connect(tmp_path / "native.db") as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchone() is None
        count = conn.execute("SELECT count(*) FROM sessions").fetchone()[0]
        receipts = conn.execute("SELECT state FROM maya_session_transitions_v1").fetchall()
        generation = conn.execute("SELECT generation FROM maya_session_projection_v1").fetchone()[0]
        assert count == generation == (0 if boundary == "before_commit" else 1)
        assert receipts == ([] if boundary == "before_commit" else [("committed_pending_projection",)])
        assert conn.execute("SELECT count(*) FROM maya_session_owners_v1").fetchone()[0] == count
        assert conn.execute("SELECT count(*) FROM maya_session_routes_v1").fetchone()[0] == count
    projection = json.loads((tmp_path / "sessions/sessions.json").read_bytes())
    assert projection["generation"] == (1 if boundary == "after_replace" else 0)
    assert len(projection["routes"]) == projection["generation"]
    # Kernel exclusion must be released by process termination, without repair.
    with portalocker.Lock(tmp_path / "sessions/maya-session-projection.lock", mode="r+b",
                          timeout=0, fail_when_locked=True):
        pass
    audit = [json.loads(line) for line in (tmp_path / "audit.jsonl").read_text().splitlines()]
    assert not any(row.get("event_type") == "outcome.session_transition" for row in audit)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--crash-worker":
        crash_worker(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit("explicit crash-worker invocation required")

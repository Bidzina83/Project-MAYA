"""Native acknowledgement, caller and unsafe-path diagnostics; no activation."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import hermes_state
from hermes_cli import middleware

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("failure_fixture", ROOT / "tests/hermes_g2_create_native.py")
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
host = parent.host


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_reader import verify_reader_stage
        source = Path(hermes_state.__file__).resolve().parent
        verified, _ = verify_reader_stage(source.parent)
        assert source == verified.resolve()
    finally:
        sys.path.pop(0)


@pytest.mark.parametrize("state", ["projection_verified", "published"])
def test_native_receipt_update_failure_quarantines_without_replay(host, state):
    store, db, _, coordinator = host
    db._conn.execute("CREATE TRIGGER fixture_receipt_failure BEFORE UPDATE ON maya_session_transitions_v1 "
                     f"WHEN NEW.state='{state}' BEGIN SELECT RAISE(ABORT,'synthetic-private-value'); END")
    db._conn.commit()
    with pytest.raises(middleware.MandatoryMiddlewareError) as error:
        parent.create(host)
    assert "synthetic-private-value" not in str(error.value)
    expected = "committed_pending_projection" if state == "projection_verified" else "projection_verified"
    assert db._conn.execute("SELECT state FROM maya_session_transitions_v1").fetchone()[0] == expected
    assert json.loads(coordinator.index.read_bytes())["generation"] == 1
    assert db._conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 1
    before = parent.snapshot(host)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        parent.create(host)
    assert parent.snapshot(host) == before and not store._entries
    assert not db._conn.in_transaction
    outcomes = [json.loads(line) for line in (store.sessions_dir.parent / "audit.jsonl").read_text().splitlines()]
    assert sum(row.get("event_type") == "outcome.session_transition" for row in outcomes) == int(state == "published")
    with coordinator._exclusive():
        pass


def test_caller_failure_after_receipt_does_not_dispatch_or_compensate(host):
    store, db, binding, _ = host
    body_entries = []
    with pytest.raises(RuntimeError, match="fixture caller failure"):
        with binding.authenticated_create(binding.owner) as authority:
            receipt = store.create_owned_session_candidate(authority)
            assert not receipt["dispatch_allowed"]
            raise RuntimeError("fixture caller failure")
        body_entries.append("unreachable")
    assert not body_entries and not store._entries
    assert db._conn.execute("SELECT state FROM maya_session_transitions_v1").fetchone()[0] == "published"
    before = parent.snapshot(host)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        parent.create(host)
    assert parent.snapshot(host) == before
    # This source entry does not durably quarantine a later caller exception.
    # No subsequent reader scope is granted or tested by this diagnostic.


def replace_directory_with_link(directory):
    target = directory.with_name("fixture-relocated-sessions")
    directory.rename(target)
    if os.name == "nt":
        result = subprocess.run(["cmd.exe", "/c", "mklink", "/J", str(directory), str(target)],
                                capture_output=True, timeout=15)
        assert result.returncode == 0, "fixture junction creation failed"
    else:
        directory.symlink_to(target, target_is_directory=True)
    return target


@pytest.mark.parametrize("boundary", ["before_attempt", "after_commit"])
def test_actual_directory_link_replacement_blocks_native_publication(host, monkeypatch, boundary):
    store, db, _, coordinator = host
    old = coordinator.index.read_bytes()
    if boundary == "before_attempt":
        replace_directory_with_link(store.sessions_dir)
    else:
        original = coordinator._commit
        def commit(conn):
            original(conn)
            replace_directory_with_link(store.sessions_dir)
        monkeypatch.setattr(coordinator, "_commit", commit)
    before = list(db._conn.iterdump())
    with pytest.raises(middleware.MandatoryMiddlewareError):
        parent.create(host)
    assert coordinator.index.read_bytes() == old and not store._entries
    assert not db._conn.in_transaction
    if boundary == "before_attempt":
        assert list(db._conn.iterdump()) == before
    else:
        assert db._conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 1
        assert db._conn.execute("SELECT state FROM maya_session_transitions_v1").fetchone()[0] == "committed_pending_projection"
    assert db._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert db._conn.execute("PRAGMA foreign_key_check").fetchone() is None

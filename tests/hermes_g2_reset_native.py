"""Native reset atomic sink, not publication/caller/product qualification."""
from dataclasses import replace
import importlib.util
from pathlib import Path
import sys

import hermes_state
import pytest
from hermes_cli import middleware
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.session_reset import CandidateNativeSessionReset
from project_maya.hermes_plugins.governance import GovernanceBoundaryError
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / ".codex-build/governance-g2-prompt-cache-20261005-final-c"
spec = importlib.util.spec_from_file_location("reset_caller_fixture", ROOT / "tests/hermes_g2_caller_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
host = base.host
caller_host = base.caller_host


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_reset import verify_stage
        source = Path(hermes_state.__file__).resolve().parent
        native, maya = verify_stage(source.parent, PARENT)
        assert native.resolve() == source
        import project_maya.hermes_plugins.session_reset as module
        assert Path(module.__file__).resolve().is_relative_to(maya.resolve())
    finally:
        sys.path.pop(0)


PERMISSIONS = (("session.read", "route_state"), ("session.transition", "reset"),
               ("session.write", "end"), ("session.write", "create"))


def policy(binding, missing=None):
    binding.gateway = PolicyAuthorizationGateway(tuple(PolicyRule(cap, operation=op, actor_id="alice")
        for cap, op in PERMISSIONS if (cap, op) != missing))


@pytest.fixture
def reset_host(caller_host):
    native, _, reader = caller_host
    store, db, binding, create = native
    with store.prepare_owned_session_candidate(binding.owner) as receipt:
        pass
    # Explicit fixture content, not a granted conversation write.
    db._conn.execute("INSERT INTO messages(session_id,role,content,timestamp) VALUES (?,'user','retained fixture',1)",
                     (receipt["session_id"],))
    db._conn.commit()
    policy(binding)
    reset = CandidateNativeSessionReset(create, acknowledgement=ACKNOWLEDGEMENT)
    return native, reset, reader, receipt["session_id"]


def snapshot(native):
    return list(native[1]._conn.iterdump()), native[3].index.read_bytes()


def execute(native, reset):
    with reset.authenticated_reset(native[2].owner) as authority:
        return native[0].reset_owned_session_candidate(authority)


def test_allowed_atomic_reset_retains_transcript_and_blocks_reader(reset_host):
    native, reset, reader, source = reset_host
    store, db, binding, create = native
    old = create.index.read_bytes()
    messages = db._conn.execute("SELECT * FROM messages").fetchall()
    result = execute(native, reset)
    target = result["session_id"]
    assert result["state"] == "committed_pending_projection" and not result["dispatch_allowed"]
    assert create.index.read_bytes() == old and not store._entries
    assert db._conn.execute("SELECT * FROM messages").fetchall() == messages
    assert db._conn.execute("SELECT count(*) FROM messages WHERE session_id=?", (target,)).fetchone()[0] == 0
    assert tuple(db._conn.execute("SELECT parent_session_id,user_id FROM sessions WHERE id=?", (target,)).fetchone()) == (source, "alice")
    assert tuple(db._conn.execute("SELECT lifecycle_status,parent_session_id FROM maya_session_owners_v1 WHERE session_id=?", (target,)).fetchone()) == ("active", source)
    assert db._conn.execute("SELECT ended_at FROM sessions WHERE id=?", (source,)).fetchone()[0] is not None
    assert tuple(db._conn.execute("SELECT session_id,route_version FROM maya_session_routes_v1").fetchone()) == (target, 2)
    assert db._conn.execute("SELECT state FROM maya_session_transitions_v1 WHERE operation='reset'").fetchone()[0] == "committed_pending_projection"
    with pytest.raises(middleware.MandatoryMiddlewareError):
        store.read_owned_session_candidate(binding.owner)
    assert reader._active is None and reset._active is None and not db._conn.in_transaction
    assert db._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert db._conn.execute("PRAGMA foreign_key_check").fetchone() is None


@pytest.mark.parametrize("missing", PERMISSIONS)
def test_each_independent_permission_is_required(reset_host, missing):
    native, reset, _, _ = reset_host
    policy(native[2], missing)
    before = snapshot(native)
    with pytest.raises((GovernanceBoundaryError, middleware.MandatoryMiddlewareError)) as error:
        execute(native, reset)
    assert isinstance(error.value, (GovernanceBoundaryError, middleware.MandatoryMiddlewareError))
    assert snapshot(native) == before and reset._active is None


@pytest.mark.parametrize("failure", ["sql", "revoked", "expired", "foreign", "stale", "outside", "replay"])
def test_reset_denials_and_rollback(reset_host, monkeypatch, failure):
    native, reset, _, source = reset_host
    store, db, binding, _ = native
    if failure == "sql":
        db._conn.execute("CREATE TRIGGER reject_reset BEFORE INSERT ON sessions BEGIN SELECT RAISE(ABORT,'private-fixture'); END")
        db._conn.commit()
    before = snapshot(native)
    if failure == "outside":
        with reset.authenticated_reset(binding.owner) as authority:
            pass
        with pytest.raises(middleware.MandatoryMiddlewareError):
            store.reset_owned_session_candidate(authority)
    elif failure == "foreign":
        with pytest.raises(GovernanceBoundaryError):
            with reset.authenticated_reset(replace(binding.owner, actor_id="mallory")):
                pytest.fail("foreign owner was bound")
    else:
        with reset.authenticated_reset(binding.owner) as authority:
            if failure == "revoked":
                authority.revoke()
            elif failure == "expired":
                authority.deadline = 0
            elif failure == "stale":
                authority.descriptor = replace(authority.descriptor, expected_route_version=99)
            elif failure == "replay":
                authority.attempted = True
            with pytest.raises(middleware.MandatoryMiddlewareError) as error:
                store.reset_owned_session_candidate(authority)
            assert "private-fixture" not in str(error.value)
    assert snapshot(native) == before and not db._conn.in_transaction
    assert reset._active is None


def test_ordinary_reset_stays_blocked(reset_host):
    native, _, _, _ = reset_host
    before = snapshot(native)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        native[0].reset_session(native[2].route_slot)
    assert snapshot(native) == before


def test_unknown_commit_retains_blocked_reset(reset_host, monkeypatch):
    native, reset, _, _ = reset_host
    old = native[3].index.read_bytes()
    def commit_then_error(conn):
        conn.commit()
        raise OSError("private-fixture")
    monkeypatch.setattr(reset, "_commit", commit_then_error)
    with pytest.raises(middleware.MandatoryMiddlewareError) as error:
        execute(native, reset)
    assert "private-fixture" not in str(error.value)
    assert native[1]._conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 2
    assert native[3].index.read_bytes() == old
    assert native[1]._conn.execute("SELECT state FROM maya_session_transitions_v1 WHERE operation='reset'").fetchone()[0] == "committed_pending_projection"
    assert not native[1]._conn.in_transaction and reset._active is None


@pytest.mark.parametrize("table", ["sessions", "maya_session_owners_v1"])
def test_ignored_source_finalization_rolls_back(reset_host, table):
    native, reset, _, _ = reset_host
    native[1]._conn.execute(f"CREATE TRIGGER ignore_end BEFORE UPDATE ON {table} BEGIN SELECT RAISE(IGNORE); END")
    native[1]._conn.commit()
    before = snapshot(native)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        execute(native, reset)
    assert snapshot(native) == before


@pytest.mark.parametrize("change", ["ended", "archived", "legacy", "pending", "classification"])
def test_invalid_source_never_allocates(reset_host, change):
    native, reset, _, source = reset_host
    conn = native[1]._conn
    statements = {
        "ended": "UPDATE sessions SET ended_at=1",
        "archived": "UPDATE sessions SET archived=1",
        "legacy": "UPDATE maya_session_transitions_v1 SET operation='legacy'",
        "pending": "UPDATE maya_session_transitions_v1 SET state='published_pending_caller'",
        "classification": "UPDATE maya_session_owners_v1 SET classification='untrusted'",
    }
    conn.execute(statements[change])
    conn.commit()
    before = snapshot(native)
    with pytest.raises(GovernanceBoundaryError):
        execute(native, reset)
    assert snapshot(native) == before and reset._active is None


def test_revocation_at_precommit_rolls_back(reset_host, monkeypatch):
    native, reset, _, _ = reset_host
    before = snapshot(native)
    with reset.authenticated_reset(native[2].owner) as authority:
        authorize = reset.authorize
        def revoke_after_mutation(*args, **kwargs):
            authorize(*args, **kwargs)
            if native[1]._conn.in_transaction:
                authority.revoke()
        monkeypatch.setattr(reset, "authorize", revoke_after_mutation)
        with pytest.raises(middleware.MandatoryMiddlewareError):
            native[0].reset_owned_session_candidate(authority)
    assert snapshot(native) == before and not native[1]._conn.in_transaction

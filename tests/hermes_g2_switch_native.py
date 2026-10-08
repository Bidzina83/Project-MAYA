"""Native switch atomic sink only; no publication, frontend or product qualification."""
from dataclasses import replace
import importlib.util
from pathlib import Path
import sys
from threading import Thread

import hermes_state
import pytest
from hermes_cli import middleware
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.governance import GovernanceBoundaryError
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT
from project_maya.hermes_plugins.session_switch import CandidateNativeSessionSwitch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("switch_parent_fixture", ROOT / "tests/hermes_g2_reset_gate_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
for name in ("host", "caller_host", "loop_host", "recognition_host", "cache_host", "reset_host"):
    globals()[name] = getattr(base, name)


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_switch import verify_stage
        native, maya = verify_stage(Path(hermes_state.__file__).resolve().parent.parent)
        assert native.resolve() == Path(hermes_state.__file__).resolve().parent
        import project_maya.hermes_plugins.session_switch as module
        assert Path(module.__file__).resolve().is_relative_to(maya.resolve())
    finally:
        sys.path.pop(0)


PERMISSIONS = (("session.read", "route_state"), ("session.read", "transition_state"),
               ("session.transition", "switch"), ("session.write", "end"),
               ("session.write", "reopen"))


def policy(h, missing=None):
    h.binding.gateway = PolicyAuthorizationGateway(tuple(
        PolicyRule(cap, operation=op, actor_id="alice") for cap, op in PERMISSIONS if (cap, op) != missing))


@pytest.fixture
def switch_host(reset_host):
    h = reset_host
    receipt = base.base.prepare(h)
    h.child = receipt["session_id"]
    # Explicit synthetic fixture content, not product conversation authority.
    h.db._conn.execute("INSERT INTO messages(session_id,role,content,timestamp) VALUES (?,'user','SYNTHETIC_CHILD_HISTORY',2)", (h.child,))
    h.db._conn.commit()
    h.switch = CandidateNativeSessionSwitch(h.preparation, acknowledgement=ACKNOWLEDGEMENT)
    policy(h)
    return h


def snapshot(h):
    return list(h.db._conn.iterdump()), h.original[3].index.read_bytes()


def execute(h):
    with h.switch.authenticated_switch(h.binding.owner, h.source) as authority:
        return h.store.switch_owned_session_candidate(authority)


def test_allowed_switch_preserves_both_histories_and_blocks_reader(switch_host):
    h = switch_host
    messages = h.db._conn.execute("SELECT * FROM messages").fetchall()
    receipts = h.db._conn.execute("SELECT * FROM maya_session_transitions_v1 ORDER BY correlation_id").fetchall()
    before = h.original[3].index.read_bytes()
    result = execute(h)
    assert result["session_id"] == h.source and result["source_session"] == h.child
    assert result["state"] == "committed_pending_projection" and result["dispatch_allowed"] is False
    assert h.db._conn.execute("SELECT * FROM messages").fetchall() == messages
    assert h.db._conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 2
    assert tuple(h.db._conn.execute("SELECT ended_at,end_reason FROM sessions WHERE id=?", (h.source,)).fetchone()) == (None, None)
    assert h.db._conn.execute("SELECT end_reason FROM sessions WHERE id=?", (h.child,)).fetchone()[0] == "session_switch"
    assert h.db._conn.execute("SELECT lifecycle_status FROM maya_session_owners_v1 WHERE session_id=?", (h.source,)).fetchone()[0] == "active"
    assert h.db._conn.execute("SELECT lifecycle_status FROM maya_session_owners_v1 WHERE session_id=?", (h.child,)).fetchone()[0] == "ended"
    assert tuple(h.db._conn.execute("SELECT session_id,route_version FROM maya_session_routes_v1").fetchone()) == (h.source, 3)
    assert h.db._conn.execute("SELECT * FROM maya_session_transitions_v1 WHERE operation<>'switch' ORDER BY correlation_id").fetchall() == receipts
    assert h.original[3].index.read_bytes() == before
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.read_owned_session_candidate(h.binding.owner)
    assert not h.agents and not h.requests and not h.db._conn.in_transaction
    assert h.switch._active is None
    assert h.db._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert h.db._conn.execute("PRAGMA foreign_key_check").fetchone() is None


@pytest.mark.parametrize("missing", PERMISSIONS)
def test_each_permission_required(switch_host, missing):
    h = switch_host
    policy(h, missing)
    before = snapshot(h)
    with pytest.raises((GovernanceBoundaryError, middleware.MandatoryMiddlewareError)):
        execute(h)
    assert snapshot(h) == before and h.switch._active is None


@pytest.mark.parametrize("failure", ["revoked", "expired", "stale", "forged", "foreign", "outside", "replay", "thread", "target", "same"])
def test_invalid_authority_has_zero_effects(switch_host, failure):
    h = switch_host
    before = snapshot(h)
    if failure in {"foreign", "target", "same"}:
        identity = replace(h.binding.owner, actor_id="mallory") if failure == "foreign" else h.binding.owner
        target = "unknown" if failure == "target" else h.child if failure == "same" else h.source
        with pytest.raises(GovernanceBoundaryError):
            with h.switch.authenticated_switch(identity, target):
                pytest.fail("invalid selector accepted")
    elif failure == "outside":
        with h.switch.authenticated_switch(h.binding.owner, h.source) as authority:
            pass
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.store.switch_owned_session_candidate(authority)
    else:
        with h.switch.authenticated_switch(h.binding.owner, h.source) as authority:
            if failure == "revoked":
                authority.revoke()
            elif failure == "expired":
                authority.deadline = 0
            elif failure == "stale":
                authority.descriptor = replace(authority.descriptor, expected_route_version=99)
            elif failure == "forged":
                authority.descriptor = replace(authority.descriptor, prior_reset_correlation="forged")
            elif failure == "replay":
                authority.attempted = True
            if failure == "thread":
                caught = []
                def run():
                    try:
                        h.store.switch_owned_session_candidate(authority)
                    except middleware.MandatoryMiddlewareError as error:
                        caught.append(error)
                thread = Thread(target=run)
                thread.start()
                thread.join(timeout=10)
                assert not thread.is_alive() and len(caught) == 1
            else:
                with pytest.raises(middleware.MandatoryMiddlewareError):
                    h.store.switch_owned_session_candidate(authority)
    assert snapshot(h) == before and not h.db._conn.in_transaction and h.switch._active is None


@pytest.mark.parametrize("damage", ["foreign", "classification", "ended", "archived", "parent", "receipt", "version", "projection", "confirmation", "target_active"])
def test_invalid_lineage_not_adopted(switch_host, damage):
    h = switch_host
    statements = {
        "foreign": "UPDATE maya_session_owners_v1 SET principal='mallory' WHERE lifecycle_status='ended'",
        "classification": "UPDATE maya_session_owners_v1 SET classification='internal' WHERE lifecycle_status='ended'",
        "ended": "UPDATE sessions SET ended_at=1 WHERE parent_session_id IS NOT NULL",
        "archived": "UPDATE sessions SET archived=1 WHERE parent_session_id IS NULL",
        "parent": "UPDATE maya_session_owners_v1 SET parent_session_id=NULL WHERE parent_session_id IS NOT NULL",
        "receipt": "UPDATE maya_session_transitions_v1 SET operation='legacy' WHERE operation='reset'",
        "version": "UPDATE maya_session_routes_v1 SET route_version=99",
        "target_active": "UPDATE sessions SET ended_at=NULL WHERE parent_session_id IS NULL",
    }
    if damage in statements:
        if damage == "foreign":
            h.db._conn.execute("PRAGMA foreign_keys=OFF")
        h.db._conn.execute(statements[damage])
        h.db._conn.commit()
        if damage == "foreign":
            h.db._conn.execute("PRAGMA foreign_keys=ON")
    elif damage == "projection":
        h.original[3].index.write_bytes(b"{}")
    else:
        h.preparation._confirmed = None
    before = snapshot(h)
    with pytest.raises(GovernanceBoundaryError):
        execute(h)
    assert snapshot(h) == before and not h.agents and not h.requests


@pytest.mark.parametrize("effect", ["end", "reopen", "owner", "route", "receipt"])
def test_native_transaction_failure_rolls_back_every_effect(switch_host, effect):
    h = switch_host
    triggers = {
        "end": "BEFORE UPDATE ON sessions WHEN NEW.end_reason='session_switch'",
        "reopen": "BEFORE UPDATE ON sessions WHEN NEW.ended_at IS NULL",
        "owner": "BEFORE UPDATE ON maya_session_owners_v1",
        "route": "BEFORE UPDATE ON maya_session_routes_v1",
        "receipt": "BEFORE INSERT ON maya_session_transitions_v1",
    }
    action = "RAISE(ABORT,'SYNTHETIC_PRIVATE_MARKER')" if effect == "receipt" else "RAISE(IGNORE)"
    h.db._conn.execute("CREATE TRIGGER reject_switch " + triggers[effect] + " BEGIN SELECT " + action + "; END")
    h.db._conn.commit()
    before = snapshot(h)
    with pytest.raises(middleware.MandatoryMiddlewareError) as error:
        execute(h)
    assert "SYNTHETIC_PRIVATE_MARKER" not in str(error.value)
    assert snapshot(h) == before and not h.db._conn.in_transaction


def test_ordinary_mandatory_switch_remains_denied(switch_host):
    h = switch_host
    before = snapshot(h)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.switch_session(h.binding.route_slot, h.source)
    assert snapshot(h) == before


@pytest.mark.parametrize("kind", ["conversation", "projection_lock"])
def test_busy_authority_cannot_be_upgraded(switch_host, kind):
    h = switch_host
    before = snapshot(h)
    policy(h)
    # Existing reader uses additional read permissions, not transition authority.
    if kind == "conversation":
        h.binding.gateway = PolicyAuthorizationGateway(tuple(PolicyRule(cap, operation=op, actor_id="alice")
            for cap, op in (*PERMISSIONS, ("session.read", "history"))))
        scope = h.store.authenticated_owned_session_candidate(h.binding.owner)
    else:
        scope = h.original[3]._exclusive()
    with scope:
        with pytest.raises(GovernanceBoundaryError):
            execute(h)
    assert snapshot(h) == before


def test_unknown_commit_retains_committed_but_blocked_state(switch_host, monkeypatch):
    h = switch_host
    before = h.original[3].index.read_bytes()
    def commit_then_error(conn):
        conn.commit()
        raise OSError("SYNTHETIC_PRIVATE_MARKER")
    monkeypatch.setattr(h.switch, "_commit", commit_then_error)
    with pytest.raises(middleware.MandatoryMiddlewareError) as error:
        execute(h)
    assert "SYNTHETIC_PRIVATE_MARKER" not in str(error.value)
    assert h.db._conn.execute("SELECT state FROM maya_session_transitions_v1 WHERE operation='switch'").fetchone()[0] == "committed_pending_projection"
    assert h.original[3].index.read_bytes() == before and not h.db._conn.in_transaction
    assert not h.requests and not h.agents


def test_revocation_before_commit_rolls_back(switch_host, monkeypatch):
    h = switch_host
    before = snapshot(h)
    authorize = h.switch.authorize
    with h.switch.authenticated_switch(h.binding.owner, h.source) as authority:
        def revoke(*args, **kwargs):
            authorize(*args, **kwargs)
            if h.db._conn.in_transaction:
                authority.revoke()
        monkeypatch.setattr(h.switch, "authorize", revoke)
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.store.switch_owned_session_candidate(authority)
    assert snapshot(h) == before and not h.db._conn.in_transaction


@pytest.mark.parametrize("failure", ["policy", "audit"])
def test_unavailable_authorization_denies_secret_safely(switch_host, monkeypatch, failure):
    h = switch_host
    target = h.binding.gateway if failure == "policy" else h.binding.audit
    method = "authorize" if failure == "policy" else "write"
    monkeypatch.setattr(target, method, lambda *args: (_ for _ in ()).throw(OSError("SYNTHETIC_PRIVATE_MARKER")))
    before = snapshot(h)
    with pytest.raises(GovernanceBoundaryError) as error:
        execute(h)
    assert "SYNTHETIC_PRIVATE_MARKER" not in str(error.value)
    assert snapshot(h) == before


@pytest.mark.parametrize("gate", ["disabled", "missing", "replaced"])
def test_native_entry_rejects_unbound_or_broken_gates(switch_host, monkeypatch, gate):
    h = switch_host
    before = snapshot(h)
    if gate == "disabled":
        monkeypatch.setattr(middleware, "_mandatory_enabled", False)
    elif gate == "missing":
        monkeypatch.setattr(h.store, "_maya_switch_coordinator", None)
    else:
        monkeypatch.setattr(middleware, "validate_mandatory_middleware", lambda: False)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.switch_owned_session_candidate(None)
    assert snapshot(h) == before

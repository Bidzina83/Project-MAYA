"""Approved reset gate correction; actual native state and synthetic transport."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import hermes_state
import pytest
from hermes_cli import middleware
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.reset_publication import CandidateResetPreparation
from project_maya.hermes_plugins.session_reset import CandidateNativeSessionReset
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reset_gate_parent", ROOT / "tests/hermes_g2_reset_composition_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
host = base.host
caller_host = base.caller_host
loop_host = base.loop_host
recognition_host = base.recognition_host
cache_host = base.cache_host
for name in vars(base):
    if name.startswith("test_"):
        globals()[name] = getattr(base, name)


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from prepare_governance_g2_reset_gate import verify_stage
        verify_stage(Path(hermes_state.__file__).resolve().parent.parent,
                     ROOT / ".codex-build/governance-g2-reset-composition-20261006-final",
                     ROOT / ".codex-build/governance-g2-prompt-cache-20261005-final-c")
    finally:
        sys.path.pop(0)


@pytest.fixture
def reset_host(cache_host):
    h = cache_host
    with h.store.prepare_owned_session_candidate(h.binding.owner) as receipt:
        pass
    h.source = receipt["session_id"]
    h.db._conn.execute("INSERT INTO messages(session_id,role,content,timestamp) VALUES (?,'user','SYNTHETIC_OLD_HISTORY',1)", (h.source,))
    h.db._conn.commit()
    rules = [("session.read", op) for op in ("route_state", "history", "existing_session", "prompt_cache_rebuild_without_snapshot")]
    rules += [("session.transition", op) for op in ("reset", "acknowledge_reset")]
    rules += [("session.write", op) for op in ("end", "create")]
    h.binding.gateway = PolicyAuthorizationGateway(tuple(PolicyRule(cap, operation=op, actor_id="alice") for cap, op in rules))
    h.reset = CandidateNativeSessionReset(h.original[3], acknowledgement=ACKNOWLEDGEMENT)
    h.preparation = CandidateResetPreparation(h.reset, acknowledgement=ACKNOWLEDGEMENT, gateway_runner=h.runner)
    return h


def seed_approvals(h, monkeypatch):
    from tools import approval, slash_confirm
    key = h.binding.route_slot
    # Explicit old ordinary-state provisioning, never conversation authority.
    with monkeypatch.context() as provision:
        provision.setattr(middleware, "mandatory_middleware_enabled", lambda: False)
        approval.approve_session(key, "synthetic-old-pattern")
        approval.enable_session_yolo(key)
        approval.submit_pending(key, {"command": "synthetic"})
        slash_confirm.register(key, "old-confirm", "synthetic", lambda choice: None)
    waiter = approval._ApprovalEntry({"command": "synthetic"})
    with approval._lock:
        approval._gateway_queues[key] = [waiter]
    approval.register_gateway_notify(key, lambda data: None)
    for name in ("_pending_approvals", "_update_prompt_pending", "_pending_skills_reload_notes"):
        setattr(h.runner, name, {key: {"synthetic": True}, "other-route": {"preserved": True}})
    return waiter


def test_native_approvals_are_cleared_before_confirmation(reset_host, monkeypatch):
    from tools import approval, slash_confirm
    h = reset_host
    waiter = seed_approvals(h, monkeypatch)
    key = h.binding.route_slot
    try:
        receipt = base.prepare(h)
        assert not approval.is_approved(key, "synthetic-old-pattern")
        assert not approval.is_session_yolo_enabled(key)
        assert not approval.has_blocking_approval(key)
        assert waiter.event.is_set() and waiter.result == "deny"
        assert key not in approval._pending and key not in approval._gateway_notify_cbs
        assert slash_confirm.get_pending(key) is None
        for name in ("_pending_approvals", "_update_prompt_pending", "_pending_skills_reload_notes"):
            assert getattr(h.runner, name) == {"other-route": {"preserved": True}}
        assert h.store.read_owned_session_candidate(h.binding.owner).session_id == receipt["session_id"]
    finally:
        approval.clear_session(key)
        approval.unregister_gateway_notify(key)
        slash_confirm.clear(key)


@pytest.mark.parametrize("failure", ["raise", "noop", "invalid_gateway_state"])
def test_security_cleanup_failure_blocks(reset_host, monkeypatch, failure):
    from tools import approval, slash_confirm
    h = reset_host
    seed_approvals(h, monkeypatch)
    key = h.binding.route_slot
    if failure == "raise":
        monkeypatch.setattr(slash_confirm, "clear", lambda key: (_ for _ in ()).throw(OSError("synthetic")))
    elif failure == "noop":
        monkeypatch.setattr(approval, "clear_session", lambda key: None)
    else:
        h.runner._pending_approvals = []
    try:
        with pytest.raises(middleware.MandatoryMiddlewareError):
            base.prepare(h)
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.store.read_owned_session_candidate(h.binding.owner)
        assert h.preparation._confirmed is None
        assert not h.requests and not h.agents
    finally:
        monkeypatch.undo()
        approval.clear_session(key)
        approval.unregister_gateway_notify(key)
        slash_confirm.clear(key)


def test_uncertain_commit_with_failed_quarantine_cannot_dispatch(reset_host, monkeypatch):
    h = reset_host
    original = h.preparation._commit
    def commit(conn):
        original(conn)
        if base.state(h) == "caller_acknowledged":
            raise OSError("synthetic uncertain commit")
    monkeypatch.setattr(h.preparation, "_commit", commit)
    monkeypatch.setattr(h.preparation, "_quarantine", lambda authority: (_ for _ in ()).throw(OSError("synthetic quarantine")))
    old = h.db.get_messages(h.source)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        base.prepare(h)
    assert base.state(h) == "caller_acknowledged"  # Honest committed outcome, not rollback.
    assert h.preparation._confirmed is None
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.read_owned_session_candidate(h.binding.owner)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        with h.store.authenticated_owned_session_candidate(h.binding.owner):
            pytest.fail("unconfirmed route dispatched")
    assert h.db.get_messages(h.source) == old and not h.requests and not h.agents


def test_reported_final_cleanup_failure_does_not_confirm(reset_host):
    h = reset_host
    lock = h.preparation._lock
    class FailedRelease:
        def acquire(self, **kwargs):
            return lock.acquire(**kwargs)

        def release(self):
            lock.release()
            raise OSError("synthetic cleanup failure")
    h.preparation._lock = FailedRelease()
    with pytest.raises(middleware.MandatoryMiddlewareError) as error:
        base.prepare(h)
    assert "synthetic" not in str(error.value)
    assert base.state(h) == "caller_acknowledged"
    assert h.preparation._confirmed is None
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.read_owned_session_candidate(h.binding.owner)
    assert not h.requests and not h.agents


@pytest.mark.parametrize("damage", ["missing", "receipt", "pid", "runner"])
def test_confirmation_cannot_be_adopted(reset_host, damage):
    h = reset_host
    base.prepare(h)
    if damage == "missing":
        h.preparation._confirmed = None
    elif damage == "receipt":
        h.preparation._confirmed = ("foreign",)
    elif damage == "pid":
        h.preparation._pid = -1
    else:
        h.runner._maya_reset_preparation = None
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.read_owned_session_candidate(h.binding.owner)
    assert not h.requests and not h.agents


@pytest.mark.parametrize("operation", ["approve", "yolo", "pending", "resolve", "permanent", "wait", "slash_register"])
def test_late_approval_entry_is_denied(reset_host, operation):
    from tools import approval, slash_confirm
    h = reset_host
    base.prepare(h)
    key = h.binding.route_slot
    actions = {
        "approve": lambda: approval.approve_session(key, "synthetic"),
        "yolo": lambda: approval.enable_session_yolo(key),
        "pending": lambda: approval.submit_pending(key, {}),
        "resolve": lambda: approval.resolve_gateway_approval(key, "always"),
        "permanent": lambda: approval.approve_permanent("synthetic"),
        "wait": lambda: approval._await_gateway_decision(key, lambda data: pytest.fail("notify"), {}),
        "slash_register": lambda: slash_confirm.register(key, "late", "synthetic", lambda choice: None),
    }
    with pytest.raises(middleware.MandatoryMiddlewareError):
        actions[operation]()
    assert not approval.has_blocking_approval(key) and slash_confirm.get_pending(key) is None
    assert not h.requests and not h.agents


@pytest.mark.asyncio
async def test_late_slash_resolution_is_denied(reset_host):
    from tools import slash_confirm
    h = reset_host
    base.prepare(h)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        await slash_confirm.resolve(h.binding.route_slot, "old-confirm", "always")
    assert not h.requests and not h.agents


def restart_probe(directory):
    spec = importlib.util.spec_from_file_location("reset_restart_fixture", ROOT / "tests/hermes_g2_restart_loop_native.py")
    restart = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(restart)
    patcher = pytest.MonkeyPatch()
    original, _, _ = restart.resume_host(directory, patcher)
    store, db, binding, _ = original
    binding.gateway = PolicyAuthorizationGateway((PolicyRule("session.read", operation="route_state", actor_id="alice"),))
    before = list(db._conn.iterdump())
    try:
        with pytest.raises(middleware.MandatoryMiddlewareError):
            store.read_owned_session_candidate(binding.owner)
        assert list(db._conn.iterdump()) == before
        assert db._conn.execute("SELECT state FROM maya_session_transitions_v1 WHERE operation='reset'").fetchone()[0] == "caller_acknowledged"
        print(json.dumps({"status": "blocked", "qualification": "reset_confirmation_absent"}))
    finally:
        patcher.undo()
        db.close()


def test_new_process_does_not_adopt_acknowledged_reset(reset_host):
    h = reset_host
    base.prepare(h)
    directory = Path(h.db.db_path).parent
    code = ("import importlib.util,pathlib; "
            "s=importlib.util.spec_from_file_location('gate'," + repr(str(Path(__file__).resolve())) + "); "
            "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
            "m.restart_probe(pathlib.Path(" + repr(str(directory)) + "))")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run([sys.executable, "-c", code], cwd=Path(hermes_state.__file__).parent,
                            env=env, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, "isolated restart probe failed"
    assert '"qualification": "reset_confirmation_absent"' in result.stdout
    assert not h.requests and not h.agents

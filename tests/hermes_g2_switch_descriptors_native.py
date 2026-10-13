"""Bounded switch authority faults; actual native SQLite, no runtime overlay."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import importlib.util
from pathlib import Path
import socket
import sys

import hermes_state
import pytest
from hermes_cli import middleware
from project_maya.governance import PolicyAuthorizationGateway
from project_maya.hermes_plugins.governance import _session_write

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("switch_descriptor_parent", ROOT / "tests/hermes_g2_switch_composition_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
for name in ("host", "caller_host", "loop_host", "recognition_host", "cache_host", "reset_host", "switch_host", "composed_host"):
    globals()[name] = getattr(base, name)


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_governance_g2_switch_callers import verify_worker_stage
    verify_worker_stage(Path(hermes_state.__file__).resolve().parent.parent)


def guard_sockets(patcher):
    def forbidden(*args, **kwargs):
        raise AssertionError("g2.switch_callers_unexpected_socket")
    patcher.setattr(socket, "create_connection", forbidden)
    patcher.setattr(socket.socket, "connect", forbidden)
    patcher.setattr(socket.socket, "connect_ex", forbidden)
    patcher.setattr(socket.socket, "sendto", forbidden)


def snapshot(h):
    return list(h.db._conn.iterdump()), h.original[3].index.read_bytes()


def retained(h):
    return (list(h.db._conn.execute("SELECT * FROM messages ORDER BY id")),
            list(h.db._conn.execute("SELECT * FROM maya_session_transitions_v1 WHERE operation<>'switch' ORDER BY correlation_id")))


def committed(h, state):
    conn = h.db._conn
    assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert conn.execute("PRAGMA foreign_key_check").fetchone() is None
    assert conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 2
    assert conn.execute("SELECT count(*) FROM maya_session_transitions_v1 WHERE operation='switch'").fetchone()[0] == 1
    assert conn.execute("SELECT state FROM maya_session_transitions_v1 WHERE operation='switch'").fetchone()[0] == state
    assert tuple(conn.execute("SELECT session_id,route_version FROM maya_session_routes_v1").fetchone()) == (h.source, 3)
    assert conn.execute("SELECT generation FROM maya_session_projection_v1").fetchone()[0] == 3
    assert tuple(conn.execute("SELECT ended_at,end_reason FROM sessions WHERE id=?", (h.source,)).fetchone()) == (None, None)
    assert conn.execute("SELECT end_reason FROM sessions WHERE id=? AND ended_at IS NOT NULL", (h.child,)).fetchone()[0] == "session_switch"
    assert h.switch._active is h.switch_preparation._current is None and not conn.in_transaction
    assert not h.agents and not h.requests and not h.wire


def invalidate(authority, mode):
    if mode == "revoked":
        authority.revoke()
    else:
        authority.deadline = 0


@pytest.mark.parametrize("mode", ["revoked", "expired"])
@pytest.mark.parametrize("phase", ["before_atomic", "before_commit", "before_publication", "pending_caller"])
def test_authority_loss_at_switch_boundaries(composed_host, monkeypatch, phase, mode):
    h = composed_host
    guard_sockets(monkeypatch)
    before, keep = snapshot(h), retained(h)
    if phase in {"before_atomic", "before_commit"}:
        with h.switch.authenticated_switch(h.binding.owner, h.source) as authority:
            if phase == "before_atomic":
                invalidate(authority, mode)
            else:
                authorize = h.switch.authorize
                def lost(*args, **kwargs):
                    authorize(*args, **kwargs)
                    if h.db._conn.in_transaction:
                        invalidate(authority, mode)
                monkeypatch.setattr(h.switch, "authorize", lost)
            with pytest.raises(middleware.MandatoryMiddlewareError):
                h.store.switch_owned_session_candidate(authority)
        assert snapshot(h) == before and not authority.active
        assert h.store.read_owned_session_candidate(h.binding.owner).session_id == h.child
    elif phase == "before_publication":
        publish = h.switch_preparation._publish
        def lost(authority):
            invalidate(authority, mode)
            return publish(authority)
        monkeypatch.setattr(h.switch_preparation, "_publish", lost)
        with pytest.raises(middleware.MandatoryMiddlewareError):
            with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source):
                pytest.fail("invalid authority reached caller")
        committed(h, "committed_pending_projection")
        assert snapshot(h)[1] == before[1]
        base.blocked(h)
    else:
        with pytest.raises(middleware.MandatoryMiddlewareError):
            with h.store.prepare_owned_switch_candidate(h.binding.owner, h.source):
                invalidate(h.switch_preparation._current, mode)
        committed(h, "caller_quarantined")
        assert h.original[3].index.read_bytes() == h.original[3]._state(h.db._conn)[2]
        base.blocked(h)
    assert retained(h) == keep and not h.db._conn.in_transaction
    assert h.switch._active is h.switch_preparation._current is h.reader._active is None
    assert not h.agents and not h.requests


@pytest.mark.parametrize("field", ["principal", "database", "instance_id", "route_slot", "binding_version",
    "target_binding_version", "target_session", "source_session", "operation", "contract", "classification",
    "expected_route_version", "prior_reset_correlation", "request_id", "correlation_id"])
def test_changed_sealed_descriptor_has_zero_effects(composed_host, monkeypatch, field):
    h = composed_host
    guard_sockets(monkeypatch)
    before = snapshot(h)
    with h.switch.authenticated_switch(h.binding.owner, h.source) as authority:
        descriptor = authority.descriptor
        value = getattr(descriptor, field)
        authority.descriptor = replace(descriptor, **{field: value + 1 if type(value) is int else "foreign"})
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.store.switch_owned_session_candidate(authority)
    assert snapshot(h) == before and not h.db._conn.in_transaction
    assert not h.agents and not h.requests


def test_consumed_descriptor_cannot_replay(composed_host, monkeypatch):
    h = composed_host
    guard_sockets(monkeypatch)
    keep, old_projection = retained(h), snapshot(h)[1]
    with h.switch.authenticated_switch(h.binding.owner, h.source) as authority:
        h.store.switch_owned_session_candidate(authority)
        before = snapshot(h)
        assert authority.active and authority.attempted
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.store.switch_owned_session_candidate(authority)
        assert snapshot(h) == before
    committed(h, "committed_pending_projection")
    assert retained(h) == keep and snapshot(h)[1] == old_projection
    base.blocked(h)


def test_exited_descriptor_cannot_borrow_fresh_authority(composed_host, monkeypatch):
    h = composed_host
    guard_sockets(monkeypatch)
    with h.switch.authenticated_switch(h.binding.owner, h.source) as old:
        pass
    before = snapshot(h)
    with h.switch.authenticated_switch(h.binding.owner, h.source) as fresh:
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.store.switch_owned_session_candidate(old)
        assert fresh.active and not fresh.attempted
    assert snapshot(h) == before and not old.active


def test_descriptor_cannot_transfer_to_thread(composed_host, monkeypatch):
    h = composed_host
    guard_sockets(monkeypatch)
    before = snapshot(h)
    with h.switch.authenticated_switch(h.binding.owner, h.source) as authority:
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = executor.submit(h.store.switch_owned_session_candidate, authority)
            with pytest.raises(middleware.MandatoryMiddlewareError):
                result.result(timeout=30)
        assert authority.active and not authority.attempted
    assert snapshot(h) == before


@pytest.mark.asyncio
async def test_descriptor_cannot_transfer_to_async_task(composed_host, monkeypatch):
    h = composed_host
    # Asyncio's Windows wake-up socket is initialized before this guard.
    with pytest.MonkeyPatch.context() as guards:
        guard_sockets(guards)
        before = snapshot(h)
        with h.switch.authenticated_switch(h.binding.owner, h.source) as authority:
            async def foreign():
                h.store.switch_owned_session_candidate(authority)
            with pytest.raises(middleware.MandatoryMiddlewareError):
                await asyncio.create_task(foreign())
            assert authority.active and not authority.attempted
        assert snapshot(h) == before


def test_old_descriptor_cannot_borrow_target_conversation(composed_host, monkeypatch):
    h = composed_host
    guard_sockets(monkeypatch)
    with h.switch.authenticated_switch(h.binding.owner, h.source) as old:
        pass
    base.prepare(h)
    before = snapshot(h)
    with h.store.authenticated_owned_session_candidate(h.binding.owner) as entry:
        fresh = _session_write.get()
        assert fresh.session_id == entry.session_id == h.source and fresh.lease.is_active
        cache = dict(h.store._entries)
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.store.switch_owned_session_candidate(old)
        assert snapshot(h) == before and h.store._entries == cache and fresh.lease.is_active
        assert h.reader._active is fresh
    committed(h, "caller_acknowledged")


def test_policy_revoked_after_preparation_stops_atomic_sink(composed_host, monkeypatch):
    h = composed_host
    guard_sockets(monkeypatch)
    before = snapshot(h)
    with h.switch.authenticated_switch(h.binding.owner, h.source) as authority:
        h.binding.gateway = PolicyAuthorizationGateway(())
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.store.switch_owned_session_candidate(authority)
    assert snapshot(h) == before and not h.db._conn.in_transaction
    assert not h.agents and not h.requests

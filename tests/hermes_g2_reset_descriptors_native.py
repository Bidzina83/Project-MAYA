"""Bounded reset authority qualification against unchanged native Patch 34."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("descriptor_contention", ROOT / "tests/hermes_g2_reset_contention_native.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
reset_host = fixtures.reset_host


@pytest.fixture(scope="module", autouse=True)
def verified_source():
    import hermes_state
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_governance_g2_reset_descriptors import verify_stage
    verify_stage(Path(hermes_state.__file__).resolve().parent.parent)


def invalidate(authority, mode):
    if mode == "revoked":
        authority.revoke()
    else:
        authority.deadline = 0


def blocked_reader(h):
    from hermes_cli import middleware
    with pytest.raises(middleware.MandatoryMiddlewareError):
        h.store.read_owned_session_candidate(h.binding.owner)
    assert h.preparation._confirmed is None
    assert not h.agents and not h.requests and not h.db._conn.in_transaction


@pytest.mark.parametrize("mode", ["revoked", "expired"])
@pytest.mark.parametrize("phase", ["before_atomic", "before_publication", "pending_caller"])
def test_authority_loss_at_reset_boundaries(reset_host, tmp_path, monkeypatch, phase, mode):
    from hermes_cli import middleware
    h = reset_host
    before = fixtures.persisted(tmp_path)
    if phase == "before_atomic":
        with h.reset.authenticated_reset(h.binding.owner) as authority:
            invalidate(authority, mode)
            with pytest.raises(middleware.MandatoryMiddlewareError):
                h.store.reset_owned_session_candidate(authority)
        assert fixtures.persisted(tmp_path) == before
        assert h.store.read_owned_session_candidate(h.binding.owner).session_id == h.source
    elif phase == "before_publication":
        publish = h.preparation._publish
        def lost(authority):
            invalidate(authority, mode)
            return publish(authority)
        monkeypatch.setattr(h.preparation, "_publish", lost)
        with pytest.raises(middleware.MandatoryMiddlewareError):
            with h.store.prepare_owned_reset_candidate(h.binding.owner):
                pytest.fail("invalid authority reached caller")
        fixtures.committed_once(h, "committed_pending_projection")
        assert fixtures.persisted(tmp_path)[1] == before[1]
        blocked_reader(h)
    else:
        with pytest.raises(middleware.MandatoryMiddlewareError):
            with h.store.prepare_owned_reset_candidate(h.binding.owner):
                invalidate(h.preparation._current, mode)
        fixtures.committed_once(h, "caller_quarantined")
        blocked_reader(h)
    assert h.reset._active is None and h.preparation._current is None
    assert not h.agents and not h.requests and not h.db._conn.in_transaction


@pytest.mark.parametrize("field", ["principal", "database", "instance_id", "route_slot",
                                   "binding_version", "target_session", "source_session", "operation"])
def test_changed_descriptor_cannot_allocate(reset_host, tmp_path, field):
    from hermes_cli import middleware
    h = reset_host
    before = fixtures.persisted(tmp_path)
    with h.reset.authenticated_reset(h.binding.owner) as authority:
        descriptor = authority.descriptor
        value = getattr(descriptor, field)
        authority.descriptor = replace(descriptor, **{field: value + 1 if type(value) is int else "foreign"})
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.store.reset_owned_session_candidate(authority)
    assert fixtures.persisted(tmp_path) == before
    assert not h.agents and not h.requests and not h.db._conn.in_transaction


def test_successfully_consumed_authority_cannot_replay(reset_host, tmp_path):
    from hermes_cli import middleware
    h = reset_host
    with h.reset.authenticated_reset(h.binding.owner) as authority:
        h.store.reset_owned_session_candidate(authority)
        before = fixtures.persisted(tmp_path)
        assert authority.active and authority.attempted
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.store.reset_owned_session_candidate(authority)
        assert fixtures.persisted(tmp_path) == before
    fixtures.committed_once(h, "committed_pending_projection")
    blocked_reader(h)


def test_exited_authority_cannot_be_reused(reset_host, tmp_path):
    from hermes_cli import middleware
    h = reset_host
    with h.reset.authenticated_reset(h.binding.owner) as authority:
        pass
    before = fixtures.persisted(tmp_path)
    with h.reset.authenticated_reset(h.binding.owner):
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.store.reset_owned_session_candidate(authority)
    assert fixtures.persisted(tmp_path) == before


def test_authority_does_not_transfer_to_thread(reset_host, tmp_path):
    from hermes_cli import middleware
    h = reset_host
    before = fixtures.persisted(tmp_path)
    with h.reset.authenticated_reset(h.binding.owner) as authority:
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = executor.submit(h.store.reset_owned_session_candidate, authority)
            with pytest.raises(middleware.MandatoryMiddlewareError):
                result.result(timeout=30)
        assert authority.active and not authority.attempted
    assert fixtures.persisted(tmp_path) == before


def test_live_descriptor_stales_after_other_process_acknowledges(reset_host, tmp_path):
    from hermes_cli import middleware
    h = reset_host
    with h.reset.authenticated_reset(h.binding.owner) as authority:
        with fixtures.child(tmp_path, "first") as process:
            fixtures.release(tmp_path, "first")
            assert fixtures.report(process)["status"] == "acknowledged"
        assert authority.active and not authority.attempted
        before = fixtures.persisted(tmp_path)
        with pytest.raises(middleware.MandatoryMiddlewareError):
            h.store.reset_owned_session_candidate(authority)
        assert fixtures.persisted(tmp_path) == before
    # The acknowledging process exited: durable state cannot replace host confirmation.
    blocked_reader(h)
    assert h.db._conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 2
    assert h.db._conn.execute("SELECT state FROM maya_session_transitions_v1 WHERE operation='reset'").fetchone()[0] == "caller_acknowledged"

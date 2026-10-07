"""Read-only qualification diagnostic of frozen Patch 33; synthetic state only."""
import importlib.util
from pathlib import Path

import pytest
from hermes_cli import middleware

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "reset_gate_composition", ROOT / "tests/hermes_g2_reset_composition_native.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
host = base.host
caller_host = base.caller_host
loop_host = base.loop_host
recognition_host = base.recognition_host
cache_host = base.cache_host
reset_host = base.reset_host
verified_source = base.verified_source


def test_committed_acknowledgement_and_failed_quarantine_exposes_route(reset_host, monkeypatch):
    h = reset_host
    original_commit = h.preparation._commit

    def uncertain_commit(conn):
        original_commit(conn)
        if base.state(h) == "caller_acknowledged":
            raise OSError("synthetic uncertain acknowledgement")

    def failed_quarantine(authority):
        raise OSError("synthetic unavailable quarantine")

    monkeypatch.setattr(h.preparation, "_commit", uncertain_commit)
    monkeypatch.setattr(h.preparation, "_quarantine", failed_quarantine)
    before = h.db.get_messages(h.source)
    with pytest.raises(middleware.MandatoryMiddlewareError):
        with h.store.prepare_owned_reset_candidate(h.binding.owner) as receipt:
            target = receipt["session_id"]
    # This assertion records the defect, not an acceptable product outcome.
    assert base.state(h) == "caller_acknowledged"
    assert h.store.read_owned_session_candidate(h.binding.owner).session_id == target
    assert h.db.get_messages(h.source) == before
    assert not h.requests and not h.agents


def test_reset_does_not_clear_native_route_approval(reset_host):
    from tools import approval
    h = reset_host
    key = h.binding.route_slot
    pattern = "synthetic-reset-gate-command"
    approval.approve_session(key, pattern)
    try:
        assert approval.is_approved(key, pattern)
        base.prepare(h)
        # Demonstrates retained state, not a governed tool execution bypass.
        assert approval.is_approved(key, pattern)
        assert not h.requests and not h.agents
    finally:
        approval.clear_session(key)

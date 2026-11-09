from dataclasses import replace
from threading import Barrier, Thread

import pytest

from project_maya.bridge.final_output_inert import (
    DESTINATION, PROFILE, Consent, FakeSink, FinalOutput, Receipt,
)
from project_maya.bridge.service import HostBinding


HOST = HostBinding("S-1-5-21-500", "a" * 32, "b" * 64)
RECEIPT = Receipt(HOST, "c" * 64, "d" * 64, "e" * 32)
OUTPUT = b"fixed synthetic output"


class Fixture:
    def __init__(self, *, lose_ack=False):
        self.tick = 0
        self.events = []
        self.on_audit = lambda _: None
        self.sink = FakeSink(lose_ack=lose_ack)
        self.owner = FinalOutput(HOST, OUTPUT, profile=PROFILE, clock=lambda: self.tick,
                                 pending_ticks=10, release_ticks=3,
                                 audit=self.audit, sink=self.sink)
        self.owner.set_policy(True)

    def audit(self, event, intent):
        self.on_audit(event)
        self.events.append((event, intent))

    def admit(self, *, expires=20):
        binding = self.owner.admit(RECEIPT, OUTPUT, positive_child=True)
        assert binding is not None
        return Consent(binding, "f" * 32, expires)

    def permit(self, *, expires=20):
        assert self.owner.authorize(self.admit(expires=expires))


def test_new_decision_after_original_lease_would_have_expired():
    f = Fixture()
    f.tick = 7  # Past the independent dispatch fixture's deadline of 2.
    f.permit()
    f.tick = 9
    assert f.owner.release() == "confirmed"
    assert f.owner.release() == "confirmed"
    assert f.sink.effects == [(OUTPUT, DESTINATION)]
    assert [event for event, _ in f.events] == ["release_intent", "delivery_confirmed"]
    assert f.events[0][1] == f.events[1][1]
    assert f.events[0][1].binding.receipt == RECEIPT


@pytest.mark.parametrize("change", ["missing", "attempt", "actor", "digest", "delivery", "text", "child"])
def test_candidate_requires_matching_trusted_receipt_and_positive_child(change):
    f = Fixture()
    receipt = {
        "missing": None,
        "attempt": replace(RECEIPT, host=replace(HOST, attempt="0" * 32)),
        "actor": replace(RECEIPT, host=replace(HOST, operator_sid="S-1-5-21-501")),
        "digest": replace(RECEIPT, response_sha256="invalid"),
        "delivery": replace(RECEIPT, delivery_id="invalid"),
    }.get(change, RECEIPT)
    assert f.owner.admit(receipt, b"wrong" if change == "text" else OUTPUT,
                         positive_child=change != "child") is None
    assert f.owner.release() == "terminal_no_publication"
    assert not f.events and not f.sink.effects


@pytest.mark.parametrize("change", ["policy", "missing", "destination", "hash", "size", "expiry", "receipt"])
def test_no_permission_without_current_policy_and_exact_consent(change):
    f = Fixture()
    consent = f.admit()
    if change == "policy":
        f.owner.set_policy(False)
    elif change == "missing":
        consent = None
    elif change == "expiry":
        consent = replace(consent, expires=0)
    else:
        replacement = {"destination": {"destination": "other"}, "hash": {"sha256": "0" * 64},
                       "size": {"size": 1}, "receipt": {"receipt": replace(RECEIPT, delivery_id="0" * 32)}}[change]
        consent = replace(consent, binding=replace(consent.binding, **replacement))
    assert f.owner.authorize(consent) is False
    assert f.owner.release() == "terminal_no_publication"
    assert not f.events and not f.sink.effects


@pytest.mark.parametrize("now,success", [(9, True), (10, False), (11, False)])
def test_absolute_pending_deadline(now, success):
    f = Fixture()
    f.tick = now
    assert (f.owner.admit(RECEIPT, OUTPUT, positive_child=True) is not None) == success


@pytest.mark.parametrize("now,success", [(2, True), (3, False), (4, False)])
def test_release_deadline(now, success):
    f = Fixture()
    f.permit()
    f.tick = now
    assert (f.owner.release() == "confirmed") == success
    assert bool(f.sink.effects) == success


@pytest.mark.parametrize("change", ["revoke", "policy", "consent_expiry", "backwards", "invalid_clock", "audit_fault"])
def test_after_intent_checks_prevent_effect(change):
    f = Fixture()
    f.tick = 1
    f.permit(expires=3)

    def fault(event):
        assert event == "release_intent"
        if change == "revoke":
            f.owner.revoke()
        elif change == "policy":
            f.owner.set_policy(True)  # Even an allow-to-allow epoch change invalidates it.
        elif change == "consent_expiry":
            f.tick = 3
        elif change == "backwards":
            f.tick = 0
        elif change == "invalid_clock":
            f.tick = float("nan")
        else:
            raise OSError("flush failed")

    f.on_audit = fault
    assert f.owner.release() == "terminal_no_publication"
    assert not f.sink.effects
    assert f.owner.release() == "terminal_no_publication"


@pytest.mark.parametrize("lose_ack", [False, True])
def test_unknown_delivery_retains_intent_and_never_replays(lose_ack):
    f = Fixture(lose_ack=lose_ack)
    f.permit()

    def fail_confirmation(event):
        if event == "delivery_confirmed":
            raise OSError("confirmation write failed")

    f.on_audit = fail_confirmation
    assert f.owner.release() == "terminal_delivery_unknown"
    assert f.owner.release() == "terminal_delivery_unknown"
    assert [event for event, _ in f.events] == ["release_intent"]
    assert len(f.sink.effects) == 1


def test_duplicate_receipt_terminates_pending_attempt():
    f = Fixture()
    f.permit()
    assert f.owner.admit(RECEIPT, OUTPUT, positive_child=True) is None
    assert f.owner.release() == "terminal_no_publication"
    assert not f.sink.effects


def test_restart_has_no_permission_to_resume():
    f = Fixture()
    f.permit()
    restarted = Fixture()
    assert restarted.owner.release() == "awaiting_candidate"
    assert not restarted.sink.effects


def test_concurrent_release_consumes_once():
    f = Fixture()
    f.permit()
    start = Barrier(3, timeout=5)
    results = []

    def run():
        start.wait()
        results.append(f.owner.release())

    workers = [Thread(target=run) for _ in range(2)]
    for worker in workers:
        worker.start()
    start.wait()
    for worker in workers:
        worker.join(timeout=5)
        assert not worker.is_alive()
    assert results == ["confirmed", "confirmed"]
    assert len(f.sink.effects) == 1


@pytest.mark.parametrize("profile,sink", [("old", FakeSink()), (PROFILE, object())])
def test_only_new_profile_and_fake_sink_admitted(profile, sink):
    with pytest.raises(ValueError, match="output.invalid_fixture"):
        FinalOutput(HOST, OUTPUT, profile=profile, clock=lambda: 0, pending_ticks=1,
                    release_ticks=1, audit=lambda *_: None, sink=sink)

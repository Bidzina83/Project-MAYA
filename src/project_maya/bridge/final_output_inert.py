"""Unwired synthetic disclosure reference; no real publisher or worker route."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from threading import RLock

from .service import HostBinding

PROFILE = "maya.final-output.inert.v1"
DESTINATION = "synthetic:fake-operator"


@dataclass(frozen=True)
class Receipt:
    """Trusted adapter input after original dispatch and delivery verification."""
    host: HostBinding
    request_sha256: str
    response_sha256: str
    delivery_id: str


@dataclass(frozen=True)
class CandidateBinding:
    receipt: Receipt
    sha256: str
    size: int
    destination: str


@dataclass(frozen=True)
class Consent:
    binding: CandidateBinding
    consent_id: str
    expires: int


@dataclass(frozen=True)
class Intent:
    binding: CandidateBinding
    consent_id: str
    policy_epoch: int
    revocation_epoch: int
    release_id: str
    expires: int


class FakeSink:
    """In-memory effect only, with deterministic acknowledgement loss."""
    def __init__(self, *, lose_ack=False):
        self.effects = []
        self.lose_ack = lose_ack

    def accept(self, candidate: bytes, destination: str) -> bool:
        self.effects.append((candidate, destination))
        return not self.lose_ack


class FinalOutput:
    """Single-attempt owner (capacity one). Inputs are trusted except candidate bytes.

    The caller must verify receipt and positive child evidence before admission.
    The audit callback models a synchronous durable append. No production adapter
    or runtime command invokes this reference. Ticks are synthetic integers.
    """

    def __init__(self, host, expected, *, profile, clock, pending_ticks,
                 release_ticks, audit, sink):
        if (profile != PROFILE or type(host) is not HostBinding or type(sink) is not FakeSink
                or type(expected) is not bytes or not 0 < len(expected) <= 4096
                or any(type(n) is not int or n <= 0 for n in (pending_ticks, release_ticks))):
            raise ValueError("output.invalid_fixture")
        self._lock = RLock()
        self._clock, self._last = clock, -1
        self._deadline = self._now() + pending_ticks
        self._window = release_ticks
        self._host, self._expected = host, expected
        self._audit, self._sink = audit, sink
        self._policy_epoch = self._revocation_epoch = 0
        self._allowed = self._revoked = False
        self._state = "awaiting_candidate"
        self._binding = self._candidate = self._consent = self._intent = None

    @property
    def state(self):
        with self._lock:
            return self._state

    def _now(self):
        tick = self._clock()
        if type(tick) is not int or tick < 0 or tick < self._last:
            raise ValueError("output.invalid_time")
        self._last = tick
        return tick

    def set_policy(self, allowed):
        with self._lock:
            self._policy_epoch += 1
            self._allowed = allowed is True

    def revoke(self):
        with self._lock:
            self._revocation_epoch += 1
            self._revoked = True

    def _finish(self, state):
        self._state = state
        self._candidate = self._expected = self._consent = self._intent = None

    def _deny(self):
        self._finish("terminal_no_publication")

    def admit(self, receipt, candidate, *, positive_child):
        with self._lock:
            if self._state != "awaiting_candidate":
                if self._state in ("admitted", "permitted"):
                    self._deny()
                return None
            try:
                if (self._revoked or self._now() >= self._deadline or positive_child is not True
                        or type(receipt) is not Receipt or receipt.host != self._host
                        or not all(type(v) is str and re.fullmatch(p, v) for v, p in (
                            (receipt.request_sha256, r"[0-9a-f]{64}"),
                            (receipt.response_sha256, r"[0-9a-f]{64}"),
                            (receipt.delivery_id, r"[0-9a-f]{32}")))
                        or type(candidate) is not bytes or candidate != self._expected):
                    self._deny()
                    return None
                self._candidate = candidate
                self._binding = CandidateBinding(receipt, hashlib.sha256(candidate).hexdigest(),
                                                 len(candidate), DESTINATION)
                self._state = "admitted"
                return self._binding
            except Exception:
                self._deny()
                return None

    def authorize(self, consent):
        with self._lock:
            if self._state != "admitted":
                return False
            try:
                now = self._now()
                if (self._revoked or not self._allowed or now >= self._deadline
                        or type(consent) is not Consent or consent.binding != self._binding
                        or type(consent.expires) is not int or now >= consent.expires
                        or type(consent.consent_id) is not str
                        or not re.fullmatch(r"[0-9a-f]{32}", consent.consent_id)):
                    self._deny()
                    return False
                self._consent = consent
                self._intent = Intent(self._binding, consent.consent_id, self._policy_epoch,
                                      self._revocation_epoch, self._host.attempt,
                                      min(self._deadline, consent.expires, now + self._window))
                self._state = "permitted"
                return True
            except Exception:
                self._deny()
                return False

    def _live(self, intent):
        now = self._now()
        return (not self._revoked and self._allowed and now < intent.expires
                and self._policy_epoch == intent.policy_epoch
                and self._revocation_epoch == intent.revocation_epoch
                and self._consent.binding == intent.binding
                and self._consent.consent_id == intent.consent_id
                and self._binding == intent.binding
                and len(self._candidate) == intent.binding.size
                and hashlib.sha256(self._candidate).hexdigest() == intent.binding.sha256
                and intent.binding.destination == DESTINATION)

    def release(self):
        with self._lock:
            if self._state != "permitted":
                return self._state
            self._state = "consumed"
            intent = self._intent
            try:
                if not self._live(intent):
                    self._deny()
                    return self._state
                self._audit("release_intent", intent)
                if not self._live(intent):
                    self._deny()
                    return self._state
            except Exception:
                self._deny()
                return self._state

            # Once invoked, exceptions or lost confirmation cannot restore authority.
            try:
                if self._sink.accept(self._candidate, intent.binding.destination) is not True:
                    raise OSError("output.ack_unknown")
                self._audit("delivery_confirmed", intent)
            except Exception:
                self._finish("terminal_delivery_unknown")
            else:
                self._finish("confirmed")
            return self._state

"""Host-owned document authorization state machine; no generic proxy routes."""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from project_maya.audit import AuditRecord
from project_maya.governance import ActionRequest, ActionAuthorizationGateway, AuthorizationResult, GovernanceDecision

from .audit import RequiredAudit
from .protocol import encode

RESOURCE = "maya.synthetic.document.v1"
REQUEST_KEYS = frozenset({"v", "type", "attempt", "lease", "seq", "operation", "resource"})


class BridgeDenied(PermissionError):
    """Only fixed codes, never arbitrary worker/service exception messages."""
    def __init__(self, code: str = "bridge.denied") -> None:
        if code not in ("bridge.denied", "bridge.unavailable", "bridge.uncertain"):
            code = "bridge.unavailable"
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class HostBinding:
    """Created from verified host process/token handles, never child JSON."""
    operator_sid: str
    attempt: str
    channel_id: str

    def __post_init__(self) -> None:
        if (not re.fullmatch(r"S-1-5-(?:[0-9]+-)*[0-9]+", self.operator_sid)
                or not re.fullmatch(r"[0-9a-f]{32}", self.attempt)
                or not re.fullmatch(r"[0-9a-f]{64}", self.channel_id)):
            raise ValueError("bridge.invalid_host_binding")


@dataclass
class _Lease:
    token: str
    request_id: str
    expires: float
    phase: str = "issued"
    revoked: bool = False


class DocumentBridge:
    """Internal trusted orchestration, not a network or callable dispatch API.

    read_document must be the fixed verified host-resource reader; send is the
    coordinator's bound frame writer. Neither can originate in runtime input.
    Windows handle verification and lifecycle are prerequisites outside this core.
    """
    def __init__(self, binding: HostBinding, gateway: ActionAuthorizationGateway,
                 audit: RequiredAudit, read_document: Callable[[], bytes],
                 clock: Callable[[], float] = time.monotonic) -> None:
        if not isinstance(binding, HostBinding) or not isinstance(audit, RequiredAudit):
            raise ValueError("bridge.missing_host_services")
        self.binding = binding
        self._gateway, self._audit, self._read_document, self._clock = gateway, audit, read_document, clock
        self._lock = threading.RLock()
        self._lease: _Lease | None = None
        self._leases = self._requests = 0
        self._seq = 1
        self._closed = False
        self.read_attempts = self.reads = self.commits = self.sent = self.bytes_sent = 0

    def issue(self) -> dict:
        with self._lock:
            if (self._closed or self._audit.failed or self._leases >= 16 or
                    self._lease is not None and self._lease.phase not in ("consumed", "revoked")):
                raise BridgeDenied("bridge.unavailable")
            self._lease = _Lease(secrets.token_hex(32), secrets.token_hex(16), self._clock() + 2)
            self._leases += 1
            return dict(v=1, type="grant", attempt=self.binding.attempt, lease=self._lease.token,
                        ttl_ms=2000, next_seq=self._seq, operation="document.read", resource=RESOURCE)

    def revoke(self) -> None:
        with self._lock:
            if self._lease:
                self._lease.revoked = True
                if self._lease.phase not in ("release_committed", "response_sent", "consumed"):
                    self._lease.phase = "revoked"

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self.revoke()

    def delivery_observed(self, delivered: bool, coordinator_request_id: str) -> None:
        """Trusted coordinator confirmation; not callable through child requests."""
        with self._lock:
            lease = self._lease
            if (lease is None or type(delivered) is not bool or
                    not re.fullmatch(r"[0-9a-f]{32}", coordinator_request_id) or
                    delivered and lease.phase != "consumed"):
                self.close()
                raise BridgeDenied("bridge.unavailable")
            try:
                self._audit.write(AuditRecord(event_type="bridge.delivery_observed",
                    decision="allow" if delivered else "deny",
                    reason_code="bridge.sent" if delivered else "bridge.withheld",
                    actor_id="windows:"+self.binding.operator_sid, capability="file.disclose",
                    target="runtime:"+self.binding.attempt, operation="release",
                    data_classification="internal-synthetic", metadata={"attempt":self.binding.attempt,
                        "request_id":lease.request_id,"coordinator_request_id":coordinator_request_id}))
            except Exception:
                self.close()
                raise BridgeDenied("bridge.uncertain" if delivered else "bridge.unavailable") from None

    def _live(self, lease: _Lease) -> None:
        if self._closed or lease is not self._lease or lease.revoked or self._clock() >= lease.expires:
            raise BridgeDenied()

    def _authorize(self, lease: _Lease, capability: str, target: str, operation: str) -> None:
        decision = self._gateway.authorize(ActionRequest(
            actor_id="windows:" + self.binding.operator_sid, capability=capability,
            target=target, operation=operation, data_classification="internal-synthetic",
            metadata={"attempt": self.binding.attempt, "request_id": lease.request_id}))
        if (not isinstance(decision, AuthorizationResult) or decision.decision is not GovernanceDecision.ALLOW
                or decision.constraints or decision.redactions):
            raise BridgeDenied()

    def _event(self, lease: _Lease, stage: str, seq: int, digest: str = "") -> None:
        self._audit.write(AuditRecord(
            event_type="bridge." + stage, decision="allow", reason_code="bridge." + stage,
            actor_id="windows:" + self.binding.operator_sid, capability="file.read" if stage == "read_intent" else "file.disclose",
            target=RESOURCE if stage == "read_intent" else "runtime:"+self.binding.attempt,
            operation="read" if stage == "read_intent" else "release",
            data_classification="internal-synthetic", metadata={"attempt": self.binding.attempt,
                "request_id": lease.request_id, "seq": str(seq), "response_sha256": digest,
                "document_resource": RESOURCE}))

    def handle(self, request: dict, channel_id: str, send: Callable[[bytes], int]) -> None:
        lease = None
        committed = False
        stage = "read"
        try:
            with self._lock:
                lease = self._lease
                self._requests += 1
                if (lease is None or self._requests > 16 or type(request) is not dict or set(request) != REQUEST_KEYS
                        or type(channel_id) is not str or not hmac.compare_digest(channel_id, self.binding.channel_id)
                        or type(request["v"]) is not int or request["v"] != 1
                        or request["type"] != "request" or request["attempt"] != self.binding.attempt
                        or type(request["seq"]) is not int or request["seq"] != self._seq
                        or request["operation"] != "document.read" or request["resource"] != RESOURCE
                        or type(request["lease"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", request["lease"])
                        or not hmac.compare_digest(request["lease"], lease.token) or lease.phase != "issued"):
                    raise BridgeDenied()
                self._live(lease)
                self._seq += 1
                seq = request["seq"]
                lease.phase = "admitted"
            self._authorize(lease, "file.read", RESOURCE, "read")
            self._event(lease, "read_intent", seq)
            with self._lock:
                self._live(lease)
                lease.phase = "read_intent_durable"
            self.read_attempts += 1
            raw = self._read_document()
            self.reads += 1
            if type(raw) is not bytes or not 1 <= len(raw) <= 1024:
                raise BridgeDenied("bridge.unavailable")
            text = raw.decode("utf-8", errors="strict")
            stage = "release"
            self._authorize(lease, "file.disclose", "runtime:" + self.binding.attempt, "release")
            frame = encode(dict(v=1, type="response", attempt=self.binding.attempt, seq=seq,
                                status="ok", code="bridge.document_read", data={"text": text}))
            self._event(lease, "release_intent", seq, hashlib.sha256(raw).hexdigest())
            with self._lock:
                self._live(lease)
                lease.phase = "release_committed"
                self.commits += 1
                committed = True
                count = send(frame)
                if type(count) is not int or count != len(frame):
                    raise BridgeDenied("bridge.uncertain")
                self.sent += 1
                self.bytes_sent += len(raw)
                lease.phase = "consumed"
        except Exception as error:
            audit_failed = self._audit.failed
            if lease is not None and not committed and not audit_failed:
                try:
                    self._audit.write(AuditRecord(
                        event_type="bridge.denied", decision="deny", reason_code="bridge.denied",
                        actor_id="windows:" + self.binding.operator_sid, capability="file.read" if stage == "read" else "file.disclose",
                        target=RESOURCE if stage == "read" else "runtime:"+self.binding.attempt,
                        operation=stage, data_classification="internal-synthetic",
                        metadata={"attempt": self.binding.attempt, "request_id": lease.request_id}))
                except Exception:
                    audit_failed = True
            with self._lock:
                if lease is not None:
                    lease.revoked = True
                    lease.phase = "release_uncertain" if committed else "revoked"
                if committed or audit_failed:
                    self._closed = True
            if committed:
                raise BridgeDenied("bridge.uncertain") from None
            if audit_failed:
                raise BridgeDenied("bridge.unavailable") from None
            if isinstance(error, BridgeDenied):
                raise BridgeDenied(error.code) from None
            raise BridgeDenied("bridge.unavailable") from None

"""M04b unused, unexpired grant revocation; no alternate policy authority."""
from __future__ import annotations

from datetime import datetime
import hmac
import math
import re

from project_maya.audit import AuditRecord
from .model_service import MODEL, ORIGIN, PATH, ROUTE, ModelDenied, OfflineModelBridge, digest
from .model_route_validation import route_request, ENVELOPE_KEYS
from .protocol import ProtocolError, decode


def checked_age(value):
    if type(value) is not str or not re.fullmatch(r"0|[1-9][0-9]{0,3}", value) or int(value) >= 2000:
        raise ProtocolError()
    return int(value)


def revocation_metadata(binding, service_id, revoke_id, dispatch_id, lease, body,
                        output_hash, revoke_age, age):
    if checked_age(age) < checked_age(revoke_age):
        raise ProtocolError()
    rejection = dispatch_id != ""
    if not rejection and age != revoke_age:
        raise ProtocolError()
    route_request(binding, lease, body)
    ids = (service_id, revoke_id, dispatch_id) if rejection else (service_id, revoke_id)
    if (any(type(x) is not str or not re.fullmatch(r"[0-9a-f]{32}", x) for x in ids)
            or (rejection and revoke_id == dispatch_id)
            or type(output_hash) is not str or not re.fullmatch(r"[0-9a-f]{64}", output_hash)):
        raise ProtocolError()
    return dict(validation_schema="maya.model.lease_revocation.v1", case="M04b",
        stage="lease_revoked" if rejection else "revoke_applied", attempt=binding.attempt,
        request_id=service_id, coordinator_request_id=dispatch_id if rejection else revoke_id,
        revoke_command_id=revoke_id, dispatch_command_id=dispatch_id, route=ROUTE,
        endpoint=ORIGIN+PATH, model=MODEL, destination="provider", request_sha256=digest(body),
        request_bytes=str(len(body)), observed_request_sha256=digest(body) if rejection else "",
        observed_request_bytes=str(len(body)) if rejection else "0", lease_sha256=digest(lease.encode("ascii")),
        grant_ttl_ms="2000", worker_elapsed_ms=age, revoke_elapsed_ms=revoke_age,
        phase_before="issued", closed_before="false", revoked_before="true" if rejection else "false",
        revoked_after="true", grant_unexpired="true", original_guard_rejected="true" if rejection else "false",
        request_preflight_verified="true" if rejection else "false", request_validated="false",
        gateway_calls="0", dispatch_attempted="false", response_sha256="", response_bytes="0",
        output_sha256=output_hash, dispatches="0", runtime_prepared="0", runtime_released="0",
        operator_prepared="0", operator_released="0", real_inference="false")


class RevokedGrantBridge(OfflineModelBridge):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._issued_at = self._issued_expiry = self._issued_lease = self._last_time = None
        self._revoke_id = self._command_id = self._revoke_age = self._age = None
        self._ack_snapshot = self._rejection_snapshot = None
        self.preflight_verified = self.revocation_observed = self.validation_recorded = False

    def issue(self):
        with self._lock:
            if self._issued_lease is not None or self._revoked:
                raise ProtocolError()
            grant = super().issue()
            self._issued_expiry, self._issued_at, self._issued_lease = self._expires, self._expires - 2.0, self._token
            try:
                self._observe()
            except Exception:
                self.close()
                raise
            return grant

    def _context(self, revoked):
        return (self._issued_lease is not None and self._expires == self._issued_expiry
            and hmac.compare_digest(self._token or "", self._issued_lease)
            and self._phase == "issued" and self._closed is False and self._revoked is revoked
            and not self._audit.failed and self.request_validated is False
            and self.gateway_calls == 0 and self.egress_gateway_denied is False
            and self.dispatch_attempted is False and self.dispatches == 0
            and self.prepared_runtime_releases == self.confirmed_runtime_releases == 0
            and self.prepared_operator_releases == self.confirmed_operator_releases == 0)

    def _observe(self):
        now = self._clock()
        if (type(now) not in (int, float) or not math.isfinite(now)
                or self._issued_at is None or not math.isfinite(self._issued_expiry)
                or now < self._issued_at or now >= self._issued_expiry
                or (self._last_time is not None and now < self._last_time)):
            raise ProtocolError()
        age = str(math.floor((now - self._issued_at) * 1000))
        checked_age(age)
        self._last_time = now
        return age

    def _metadata(self, dispatch_id, age):
        return revocation_metadata(self.binding, self.request_id, self._revoke_id, dispatch_id,
            self._issued_lease, self._expected, digest(self._provider.text.encode("utf-8")), self._revoke_age, age)

    def _write_event(self, event, metadata):
        self._audit.write(AuditRecord(event_type="model_bridge."+event, decision="deny",
            reason_code="model_bridge."+event, actor_id="windows:"+self.binding.operator_sid,
            capability="model.egress", target="model:maya-offline-fixture", operation="infer",
            data_classification="internal-synthetic", metadata=metadata))

    def revoke_issued(self, lease, command_id):
        with self._lock:
            try:
                if (self._revoke_id is not None or not self._context(False)
                        or type(command_id) is not str or not re.fullmatch(r"[0-9a-f]{32}", command_id)
                        or type(lease) is not str or not hmac.compare_digest(lease, self._issued_lease)):
                    raise ProtocolError()
                self._observe()
                super().revoke()
                if not self._context(True):
                    raise ProtocolError()
                self._revoke_id, self._revoke_age = command_id, self._observe()
                metadata = self._metadata("", self._revoke_age)
                self._write_event("grant_revoked", metadata)
                self._observe()
                if not self._context(True):
                    raise ProtocolError()
                self._ack_snapshot = tuple(sorted(metadata.items()))
                return dict(self._ack_snapshot)
            except Exception:
                self.close()
                raise ProtocolError() from None

    def bind_command(self, command_id):
        if (self._command_id is not None or self._ack_snapshot is None
                or type(command_id) is not str or not re.fullmatch(r"[0-9a-f]{32}", command_id)
                or command_id == self._revoke_id):
            raise ProtocolError()
        self._command_id = command_id

    def prepare_runtime(self, message, channel_id):
        with self._lock:
            try:
                expected = route_request(self.binding, self._issued_lease, self._expected)
                if (self._ack_snapshot is None or self._command_id is None or not self._context(True)
                        or type(message) is not dict or set(message) != ENVELOPE_KEYS or message != expected
                        or type(message.get("v")) is not int or type(message.get("seq")) is not int
                        or type(channel_id) is not str or not hmac.compare_digest(channel_id, self.binding.channel_id)):
                    raise ProtocolError()
                self.preflight_verified = True
                return super().prepare_runtime(message, channel_id)
            except Exception as failure:
                if type(failure) is ModelDenied:
                    raise
                self.close()
                raise ProtocolError() from None

    def _live(self, phase):
        if phase != "issued" or not self._context(True) or not self.preflight_verified or self._ack_snapshot is None:
            raise ProtocolError()
        self._observe()
        try:
            super()._live(phase)
        except ModelDenied as failure:
            age = self._observe()
            if type(failure) is ModelDenied and failure.uncertain is False and self._context(True):
                self._age = age
                self.revocation_observed = True
                self.validation_stage = "lease_revoked"
            raise
        raise ProtocolError()

    def _event(self, stage, destination, allowed=True, coordinator_request_id=""):
        if (stage != "denied" or allowed or destination != "provider" or not self._context(True)
                or not self.revocation_observed or not self.preflight_verified or self.validation_recorded
                or self._ack_snapshot is None or self._command_id is None):
            raise ProtocolError()
        self._observe()
        metadata = self._metadata(self._command_id, self._age)
        self._write_event("lease_revoked", metadata)
        self._observe()
        if not self._context(True):
            raise ProtocolError()
        self._rejection_snapshot = tuple(sorted(metadata.items()))
        self.validation_recorded = True

    def evidence(self):
        if (not self.closed or self._audit.failed or not self.validation_recorded
                or self._ack_snapshot is None or self._rejection_snapshot is None
                or self._expires != self._issued_expiry or self._token != self._issued_lease
                or not self.revocation_observed or self.validation_stage != "lease_revoked"
                or self.request_validated or self.gateway_calls or self.dispatch_attempted or self.dispatches
                or any((self.prepared_runtime_releases, self.confirmed_runtime_releases,
                        self.prepared_operator_releases, self.confirmed_operator_releases))):
            raise ProtocolError()
        expected = self._metadata(self._command_id, self._age)
        if expected != dict(self._rejection_snapshot) or self._metadata("", self._revoke_age) != dict(self._ack_snapshot):
            raise ProtocolError()
        return expected


def verify_revocation_audit(raw, binding, service_id, revoke_id, dispatch_id, lease, body,
                            output_hash, revoke_age, age):
    if (type(dispatch_id) is not str or not re.fullmatch(r"[0-9a-f]{32}", dispatch_id) or dispatch_id == revoke_id
            or type(raw) is not bytes or not 1 <= len(raw) <= 131072 or raw.count(b"\n") != 2 or not raw.endswith(b"\n")):
        raise ProtocolError()
    for line, event, command, elapsed in zip(raw[:-1].split(b"\n"),
            ("grant_revoked", "lease_revoked"), ("", dispatch_id), (revoke_age, age)):
        record = decode(line)
        expected = dict(schema_version=1, event_type="model_bridge."+event, decision="deny",
            reason_code="model_bridge."+event, actor_id="windows:"+binding.operator_sid,
            capability="model.egress", target="model:maya-offline-fixture", operation="infer",
            data_classification="internal-synthetic", idempotency_key=None,
            metadata=revocation_metadata(binding, service_id, revoke_id, command, lease, body, output_hash, revoke_age, elapsed))
        if (set(record) != set(expected)|{"timestamp"} or type(record["schema_version"]) is not int
                or any(record[k] != value for k, value in expected.items())):
            raise ProtocolError()
        stamp = record["timestamp"]
        if type(stamp) is not str or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|\+00:00)", stamp):
            raise ProtocolError()
        try:
            datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except ValueError:
            raise ProtocolError() from None
    return 2

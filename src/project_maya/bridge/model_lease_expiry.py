"""M04a unused-grant expiry; no native clock injection or alternate authority."""
from __future__ import annotations

from datetime import datetime
import hmac
import math
import re

from project_maya.audit import AuditRecord
from .model_service import MODEL, ORIGIN, PATH, ROUTE, ModelDenied, OfflineModelBridge, digest
from .model_route_validation import route_request, ENVELOPE_KEYS
from .protocol import ProtocolError, decode


def checked_elapsed(value):
    if type(value) is not str or not re.fullmatch(r"[0-9]{4,5}", value):
        raise ProtocolError()
    elapsed = int(value)
    if str(elapsed) != value or not 2000 <= elapsed <= 30000:
        raise ProtocolError()
    return elapsed


def expiry_metadata(binding, service_id, command_id, lease, body, output_hash, elapsed):
    checked_elapsed(elapsed)
    route_request(binding, lease, body)
    if (any(type(x) is not str or not re.fullmatch(r"[0-9a-f]{32}", x) for x in (service_id, command_id))
            or type(output_hash) is not str or not re.fullmatch(r"[0-9a-f]{64}", output_hash)):
        raise ProtocolError()
    return dict(validation_schema="maya.model.lease_expiry.v1", case="M04a", stage="lease_expired",
        attempt=binding.attempt, request_id=service_id, coordinator_request_id=command_id,
        route=ROUTE, endpoint=ORIGIN+PATH, model=MODEL, destination="provider",
        request_sha256=digest(body), request_bytes=str(len(body)), observed_request_sha256=digest(body),
        observed_request_bytes=str(len(body)), lease_sha256=digest(lease.encode("ascii")),
        grant_ttl_ms="2000", worker_elapsed_ms=elapsed, phase_before="issued", closed_before="false",
        revoked_before="false", expiry_observed="true", request_preflight_verified="true",
        request_validated="false", gateway_calls="0", dispatch_attempted="false", response_sha256="",
        response_bytes="0", output_sha256=output_hash, dispatches="0", runtime_prepared="0",
        runtime_released="0", operator_prepared="0", operator_released="0", real_inference="false")


class ExpiredGrantBridge(OfflineModelBridge):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._command_id = None
        self._issued_at = self._issued_expiry = None
        self._issued_lease = None
        self._elapsed = None
        self._observed_at = None
        self.preflight_verified = self.expiry_observed = self.validation_recorded = False

    def issue(self):
        with self._lock:
            grant = super().issue()
            self._issued_expiry = self._expires
            self._issued_at = self._expires - 2.0
            self._issued_lease = self._token
            return grant

    def bind_command(self, command_id):
        if self._command_id is not None or type(command_id) is not str or not re.fullmatch(r"[0-9a-f]{32}", command_id):
            raise ProtocolError()
        self._command_id = command_id

    def _unused_context(self):
        return (self._issued_at is not None and self._expires == self._issued_expiry
            and self._issued_lease is not None and hmac.compare_digest(self._token or "", self._issued_lease)
            and self._phase == "issued" and not self._closed and not self._revoked and not self._audit.failed
            and self.preflight_verified is True and self.request_validated is False
            and self.gateway_calls == 0 and self.egress_gateway_denied is False
            and self.dispatch_attempted is False and self.dispatches == 0
            and self.prepared_runtime_releases == self.confirmed_runtime_releases == 0
            and self.prepared_operator_releases == self.confirmed_operator_releases == 0)

    def prepare_runtime(self, message, channel_id):
        with self._lock:
            try:
                expected = route_request(self.binding, self._token, self._expected)
                if (type(message) is not dict or set(message) != ENVELOPE_KEYS or message != expected
                        or type(message.get("v")) is not int or type(message.get("seq")) is not int
                        or type(channel_id) is not str or not hmac.compare_digest(channel_id, self.binding.channel_id)
                        or self._command_id is None):
                    raise ProtocolError()
                self.preflight_verified = True
            except Exception:
                self.close()
                raise ProtocolError() from None
            return super().prepare_runtime(message, channel_id)

    def _live(self, phase):
        # The original guard must reject. Preflight and a delay are not proof.
        try:
            super()._live(phase)
        except ModelDenied as failure:
            now = self._clock()
            if (type(failure) is ModelDenied and failure.uncertain is False
                    and phase == "issued" and self._unused_context() and type(now) in (int, float)
                    and math.isfinite(now) and now >= self._issued_expiry):
                elapsed = math.floor((now - self._issued_at) * 1000)
                checked_elapsed(str(elapsed))
                self._elapsed, self._observed_at = str(elapsed), now
                self.expiry_observed = True
                self.validation_stage = "lease_expired"
            raise
        # This fixed negative profile must not dispatch if the grant is still live.
        raise ProtocolError()

    def _zero_boundary(self):
        return (self.preflight_verified is True and self.expiry_observed is True
            and self.validation_stage == "lease_expired" and self.request_validated is False
            and self.gateway_calls == 0 and self.egress_gateway_denied is False
            and self.dispatch_attempted is False and self.dispatches == 0
            and self.prepared_runtime_releases == self.confirmed_runtime_releases == 0
            and self.prepared_operator_releases == self.confirmed_operator_releases == 0)

    def metadata(self):
        return expiry_metadata(self.binding, self.request_id, self._command_id, self._token,
            self._expected, digest(self._provider.text.encode("utf-8")), self._elapsed)

    def _event(self, stage, destination, allowed=True, coordinator_request_id=""):
        now = self._clock()
        if (stage != "denied" or allowed or destination != "provider" or not self._unused_context()
                or not self._zero_boundary() or type(now) not in (int, float) or not math.isfinite(now)
                or now < self._observed_at):
            raise ProtocolError()
        self._audit.write(AuditRecord(event_type="model_bridge.lease_expired", decision="deny",
            reason_code="model_bridge.lease_expired", actor_id="windows:"+self.binding.operator_sid,
            capability="model.egress", target="model:maya-offline-fixture", operation="infer",
            data_classification="internal-synthetic", metadata=self.metadata()))
        self.validation_recorded = True

    def evidence(self):
        if not self.closed or self._audit.failed or not self.validation_recorded or not self._zero_boundary():
            raise ProtocolError()
        return self.metadata()


def verify_expiry_audit(raw, binding, service_id, command_id, lease, body, output_hash, elapsed):
    if type(raw) is not bytes or not 1 <= len(raw) <= 131072 or raw.count(b"\n") != 1 or not raw.endswith(b"\n"):
        raise ProtocolError()
    record = decode(raw[:-1])
    expected = dict(schema_version=1, event_type="model_bridge.lease_expired", decision="deny",
        reason_code="model_bridge.lease_expired", actor_id="windows:"+binding.operator_sid,
        capability="model.egress", target="model:maya-offline-fixture", operation="infer",
        data_classification="internal-synthetic", idempotency_key=None,
        metadata=expiry_metadata(binding, service_id, command_id, lease, body, output_hash, elapsed))
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
    return 1

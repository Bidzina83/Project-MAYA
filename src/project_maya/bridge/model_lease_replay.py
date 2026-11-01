"""M04c consumed-grant observation with truthful first effects and audit prefix."""
from __future__ import annotations

from datetime import datetime
import hmac
import math
import re

from project_maya.audit import AuditRecord
from .model_lease_revocation import checked_age
from .model_route_validation import ENVELOPE_KEYS, route_request
from .model_service import MODEL, ORIGIN, PATH, ROUTE, TARGET, ModelDenied, OfflineModelBridge, digest
from .protocol import ProtocolError, decode


def replay_metadata(binding, service_id, first_id, delivery_id, replay_id, lease, body,
                    response, output_hash, delivery_age, age):
    ids = (service_id, first_id, delivery_id, replay_id)
    if (any(type(x) is not str or not re.fullmatch(r"[0-9a-f]{32}", x) for x in ids)
            or len({first_id, delivery_id, replay_id}) != 3
            or checked_age(age) < checked_age(delivery_age)
            or type(response) is not bytes or not 1 <= len(response) <= 4096
            or type(output_hash) is not str or not re.fullmatch(r"[0-9a-f]{64}", output_hash)):
        raise ProtocolError()
    route_request(binding, lease, body)
    decode(response)
    return dict(validation_schema="maya.model.lease_replay.v1", case="M04c", stage="lease_consumed",
        attempt=binding.attempt, request_id=service_id, coordinator_request_id=replay_id,
        first_dispatch_command_id=first_id, runtime_delivery_command_id=delivery_id, replay_command_id=replay_id,
        route=ROUTE, endpoint=ORIGIN+PATH, model=MODEL, destination="provider",
        request_sha256=digest(body), request_bytes=str(len(body)), observed_request_sha256=digest(body),
        observed_request_bytes=str(len(body)), lease_sha256=digest(lease.encode("ascii")),
        response_sha256=digest(response), response_bytes=str(len(response)), output_sha256=output_hash,
        grant_ttl_ms="2000", delivery_elapsed_ms=delivery_age, worker_elapsed_ms=age,
        phase_before="runtime_delivered", closed_before="false", revoked_before="false", grant_unexpired="true",
        original_guard_rejected="true", original_denial_uncertain="true", request_validated="true",
        replay_request_preflight_verified="true", replay_request_validated="false",
        gateway_calls="2", gateway_calls_before="2", gateway_calls_after="2", replay_gateway_delta="0",
        dispatch_attempted="true", replay_dispatch_attempted="false", dispatches="1", dispatches_before="1",
        dispatches_after="1", replay_dispatch_delta="0", runtime_prepared="1", runtime_released="1",
        replay_runtime_delta="0", operator_prepared="0", operator_released="0", replay_operator_delta="0",
        real_inference="false")


class ConsumedGrantBridge(OfflineModelBridge):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._issued_at = self._issued_expiry = self._issued_lease = self._last_time = None
        self._first_id = self._delivery_id = self._replay_id = None
        self._first_snapshot = self._response_snapshot = self._rejection_snapshot = None
        self._delivery_age = self._age = None
        self.preflight_verified = self.consumption_observed = self.validation_recorded = False

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

    def _observe(self):
        now = self._clock()
        if (type(now) not in (int, float) or not math.isfinite(now) or self._issued_at is None
                or not math.isfinite(self._issued_expiry) or now < self._issued_at or now >= self._issued_expiry
                or (self._last_time is not None and now < self._last_time)):
            raise ProtocolError()
        age = str(math.floor((now - self._issued_at) * 1000));checked_age(age)
        self._last_time = now
        return age

    def bind_first(self, command_id):
        if self._first_id is not None or type(command_id) is not str or not re.fullmatch(r"[0-9a-f]{32}", command_id):
            raise ProtocolError()
        self._first_id = command_id

    def _counts(self):
        return (self.request_validated is True and self.dispatch_attempted is True and self.gateway_calls == 2
            and self.egress_gateway_denied is False and self.dispatches == 1
            and self.prepared_runtime_releases == self.confirmed_runtime_releases == 1
            and self.prepared_operator_releases == self.confirmed_operator_releases == 0)

    def _binding(self):
        return (self._issued_lease is not None and self._token == self._issued_lease and self._expires == self._issued_expiry
            and self._response_snapshot is not None and self._response == self._response_snapshot
            and self._first_snapshot is not None and self._destination == "runtime:"+self.binding.attempt)

    def _state(self):
        return (self._binding() and self._counts() and self._phase == "runtime_delivered"
            and self._closed is False and self._revoked is False and not self._audit.failed)

    def prepare_runtime(self, message, channel_id):
        with self._lock:
            try:
                expected = route_request(self.binding, self._issued_lease, self._expected)
                if (type(message) is not dict or set(message) != ENVELOPE_KEYS or message != expected
                        or type(message.get("v")) is not int or type(message.get("seq")) is not int
                        or type(channel_id) is not str or not hmac.compare_digest(channel_id, self.binding.channel_id)):
                    raise ProtocolError()
                if self._replay_id is None:
                    if self._first_id is None or self._first_snapshot is not None:
                        raise ProtocolError()
                    self._first_snapshot = tuple(sorted(message.items()))
                    reply = super().prepare_runtime(message, channel_id)
                    self._response_snapshot = self._response
                    return reply
                if not self._state() or dict(self._first_snapshot) != message or self._delivery_age is None:
                    raise ProtocolError()
                self.preflight_verified = True
                return super().prepare_runtime(message, channel_id)
            except Exception as failure:
                if type(failure) is ModelDenied:
                    raise
                self.close()
                raise ProtocolError() from None

    def confirm_runtime_delivery(self, response_sha256, coordinator_request_id):
        with self._lock:
            try:
                if (self._delivery_id is not None or coordinator_request_id == self._first_id
                        or self._first_snapshot is None or self._response_snapshot is None):
                    raise ProtocolError()
                # Always record the committed first write before testing replay timing.
                super().confirm_runtime_delivery(response_sha256, coordinator_request_id)
                self._delivery_id = coordinator_request_id
                if not self._state():
                    raise ProtocolError()
                self._delivery_age = self._observe()
                return self._delivery_age
            except Exception:
                self.close()
                raise ProtocolError() from None

    def bind_replay(self, command_id):
        if (self._replay_id is not None or self._delivery_age is None or not self._state()
                or type(command_id) is not str or not re.fullmatch(r"[0-9a-f]{32}", command_id)
                or command_id in (self._first_id, self._delivery_id)):
            raise ProtocolError()
        self._replay_id = command_id

    def _live(self, phase):
        if self._replay_id is None:
            return super()._live(phase)
        if phase != "issued" or not self._state() or not self.preflight_verified:
            raise ProtocolError()
        self._observe()
        try:
            super()._live(phase)
        except ModelDenied as failure:
            age = self._observe()
            if type(failure) is ModelDenied and failure.uncertain is True and self._state():
                self._age = age;self.consumption_observed = True;self.validation_stage = "lease_consumed"
            raise
        raise ProtocolError()

    def metadata(self):
        return replay_metadata(self.binding, self.request_id, self._first_id, self._delivery_id, self._replay_id,
            self._issued_lease, self._expected, self._response_snapshot, digest(self._provider.text.encode("utf-8")),
            self._delivery_age, self._age)

    def _event(self, stage, destination, allowed=True, coordinator_request_id=""):
        if self._replay_id is None:
            return super()._event(stage, destination, allowed, coordinator_request_id)
        if (stage != "denied" or allowed or destination != "runtime:"+self.binding.attempt or not self._state()
                or not self.preflight_verified or not self.consumption_observed or self.validation_recorded):
            raise ProtocolError()
        self._observe();metadata = self.metadata()
        self._audit.write(AuditRecord(event_type="model_bridge.lease_consumed", decision="deny",
            reason_code="model_bridge.lease_consumed", actor_id="windows:"+self.binding.operator_sid,
            capability="model.egress", target=TARGET, operation="infer",
            data_classification="internal-synthetic", metadata=metadata))
        self._observe()
        if not self._state():raise ProtocolError()
        self._rejection_snapshot = tuple(sorted(metadata.items()));self.validation_recorded = True

    def evidence(self):
        if (not self.closed or self._audit.failed or not self.validation_recorded or not self._binding()
                or not self._counts() or not self.consumption_observed or self.validation_stage != "lease_consumed"
                or self._rejection_snapshot is None or self.metadata() != dict(self._rejection_snapshot)):
            raise ProtocolError()
        return dict(self._rejection_snapshot)


def verify_replay_audit(raw, binding, service_id, first_id, delivery_id, replay_id, lease, body,
                        response, output_hash, delivery_age, age):
    fifth = replay_metadata(binding, service_id, first_id, delivery_id, replay_id, lease, body,
                            response, output_hash, delivery_age, age)
    if type(raw) is not bytes or not 1 <= len(raw) <= 131072 or not raw.endswith(b"\n") or raw.count(b"\n") != 5:
        raise ProtocolError()
    previous = None
    stages = ("egress_intent", "dispatch_outcome", "runtime_release_intent", "runtime_delivery", "lease_consumed")
    for i, (line, stage) in enumerate(zip(raw[:-1].split(b"\n"), stages)):
        metadata = dict(attempt=binding.attempt, request_id=service_id, route=ROUTE, endpoint=ORIGIN+PATH,
            model=MODEL, destination="provider" if i < 2 else "runtime:"+binding.attempt,
            request_sha256=digest(body), response_sha256="" if i == 0 else digest(response), request_bytes=str(len(body)),
            response_bytes="0" if i == 0 else str(len(response)), output_sha256=output_hash,
            dispatches="0" if i == 0 else "1", real_inference="false")
        if i == 3:metadata["coordinator_request_id"] = delivery_id
        if i == 4:metadata = fifth
        expected = dict(schema_version=1, event_type="model_bridge."+stage, decision="deny" if i == 4 else "allow",
            reason_code="model_bridge."+stage, actor_id="windows:"+binding.operator_sid,
            capability="model.egress" if i < 2 or i == 4 else "model.output", target=TARGET,
            operation="infer" if i < 2 or i == 4 else "disclose", data_classification="internal-synthetic",
            idempotency_key=None, metadata=metadata)
        record = decode(line)
        if (set(record) != set(expected)|{"timestamp"} or type(record["schema_version"]) is not int
                or any(record[k] != value for k, value in expected.items())):raise ProtocolError()
        stamp = record["timestamp"]
        if type(stamp) is not str or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|\+00:00)", stamp):
            raise ProtocolError()
        try:
            now = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if previous is not None and now < previous:raise ValueError()
            previous = now
        except ValueError:raise ProtocolError() from None
    return 5

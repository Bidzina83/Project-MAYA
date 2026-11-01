"""Fixed M03b route diagnostic; the native body and actual host identity stay intact."""
from __future__ import annotations

from datetime import datetime
import re

from project_maya.audit import AuditRecord
from .model_service import MODEL, ORIGIN, PATH, ROUTE, OfflineModelBridge, checked_request, digest
from .protocol import ProtocolError, decode

WRONG_ROUTE = "maya.offline.model.v0"
ENVELOPE_KEYS = {"v", "type", "attempt", "route", "lease", "seq", "method", "path", "body"}


def route_request(binding, lease, body, *, mutant=False):
    checked_request(body)
    if type(mutant) is not bool or type(lease) is not str or not re.fullmatch(r"[0-9a-f]{64}", lease):
        raise ProtocolError()
    return dict(v=1, type="model_request", attempt=binding.attempt,
        route=WRONG_ROUTE if mutant else ROUTE, lease=lease, seq=1,
        method="POST", path=PATH, body=body.decode("utf-8"))


def route_projection(binding, lease, body, *, mutant=False):
    """Fixed ASCII field projection, not a hash of serializer-dependent pipe JSON."""
    request = route_request(binding, lease, body, mutant=mutant)
    return ("maya.model.route_projection.v1\n1\nmodel_request\n" + binding.attempt + "\n"
        + request["route"] + "\n" + digest(lease.encode("ascii")) + "\n1\nPOST\n" + PATH
        + "\n" + digest(body) + "\n" + str(len(body)) + "\n").encode("ascii")


def route_metadata(binding, service_id, command_id, lease, body, output_hash):
    if (any(type(x) is not str or not re.fullmatch(r"[0-9a-f]{32}", x) for x in (service_id, command_id))
            or type(output_hash) is not str or not re.fullmatch(r"[0-9a-f]{64}", output_hash)):
        raise ProtocolError()
    original = route_projection(binding, lease, body)
    mutant = route_projection(binding, lease, body, mutant=True)
    return dict(attempt=binding.attempt, request_id=service_id, route=ROUTE,
        endpoint=ORIGIN+PATH, model=MODEL, destination="provider", request_sha256=digest(body),
        request_bytes=str(len(body)), response_sha256="", response_bytes="0", output_sha256=output_hash,
        dispatches="0", real_inference="false", validation_schema="maya.model.route_validation.v1",
        case="M03b", stage="request_route", coordinator_request_id=command_id,
        projection_schema="maya.model.route_projection.v1", original_projection_sha256=digest(original),
        original_projection_bytes=str(len(original)), mutated_projection_sha256=digest(mutant),
        mutated_projection_bytes=str(len(mutant)), observed_route=WRONG_ROUTE,
        mutated_request_sha256=digest(body), mutated_request_bytes=str(len(body)),
        gateway_calls="0", dispatch_attempted="false", runtime_prepared="0", runtime_released="0",
        operator_prepared="0", operator_released="0")


class WrongRouteBridge(OfflineModelBridge):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._command_id = None
        self.validation_recorded = False

    def bind_command(self, command_id):
        if self._command_id is not None or type(command_id) is not str or not re.fullmatch(r"[0-9a-f]{32}", command_id):
            raise ProtocolError()
        self._command_id = command_id

    def prepare_runtime(self, message, channel_id):
        # Independently reconstruct every field from trusted state, not testimony.
        expected = route_request(self.binding, self._token, self._expected, mutant=True)
        if (type(message) is not dict or set(message) != ENVELOPE_KEYS or message != expected
                or type(message.get("v")) is not int or type(message.get("seq")) is not int):
            self.close()
            raise ProtocolError()
        return super().prepare_runtime(message, channel_id)

    def _zero_boundary(self):
        return (self.envelope_identity_validated is True and self.envelope_validated is False
            and self.validation_stage == "request_route" and self.gateway_calls == 0
            and self.dispatch_attempted is False and self.dispatches == 0
            and self.request_validated is False and self.egress_gateway_denied is False
            and self.prepared_runtime_releases == self.confirmed_runtime_releases == 0
            and self.prepared_operator_releases == self.confirmed_operator_releases == 0)

    def metadata(self):
        return route_metadata(self.binding, self.request_id, self._command_id, self._token,
            self._expected, digest(self._provider.text.encode("utf-8")))

    def _event(self, stage, destination, allowed=True, coordinator_request_id=""):
        if (stage != "denied" or allowed or destination != "provider" or not self._zero_boundary()
                or self._clock() >= self._expires or self._revoked):
            raise ProtocolError()
        self._audit.write(AuditRecord(event_type="model_bridge.route_rejected", decision="deny",
            reason_code="model_bridge.wrong_route", actor_id="windows:"+self.binding.operator_sid,
            capability="model.egress", target="model:maya-offline-fixture", operation="infer",
            data_classification="internal-synthetic", metadata=self.metadata()))
        self.validation_recorded = True

    def evidence(self):
        if not self.closed or self._audit.failed or not self.validation_recorded or not self._zero_boundary():
            raise ProtocolError()
        return self.metadata()


def verify_route_audit(raw, binding, service_id, command_id, lease, body, output_hash):
    if type(raw) is not bytes or not 1 <= len(raw) <= 131072 or raw.count(b"\n") != 1 or not raw.endswith(b"\n"):
        raise ProtocolError()
    record = decode(raw[:-1])
    expected = dict(schema_version=1, event_type="model_bridge.route_rejected", decision="deny",
        reason_code="model_bridge.wrong_route", actor_id="windows:"+binding.operator_sid,
        capability="model.egress", target="model:maya-offline-fixture", operation="infer",
        data_classification="internal-synthetic", idempotency_key=None,
        metadata=route_metadata(binding, service_id, command_id, lease, body, output_hash))
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

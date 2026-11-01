"""Fixed M03d worker diagnostic. No generic mutation or provider dispatch API."""
from __future__ import annotations

from datetime import datetime
import json
import re

from project_maya.audit import AuditRecord
from .model_service import MODEL, OfflineModelBridge, checked_request, digest
from .protocol import ProtocolError, decode



def wrong_body_request(original: bytes) -> bytes:
    body = checked_request(original)
    def serialize(value):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if (serialize(body) != original or list(body) != ["messages", "model", "max_tokens", "stream"]
            or body["max_tokens"] != 32 or len(body["messages"]) != 2
            or body["messages"][0]["role"] != "system" or body["messages"][1]["role"] != "user"):
        raise ProtocolError()
    user = body["messages"][1]["content"]
    if not re.fullmatch(r"MAYA_OFFLINE_MODEL_REQUEST:[0-9a-f]{64}", user):
        raise ProtocolError()
    body["messages"][1]["content"] = user[:-1] + ("1" if user[-1] == "0" else "0")
    mutant = serialize(body)
    checked_request(mutant)
    if len(mutant) != len(original) or not 1 <= len(mutant) <= 4096 or mutant == original:
        raise ProtocolError()
    return mutant


def body_metadata(binding, service_id, command_id, original, mutant, output_hash):
    if (any(type(x) is not str or not re.fullmatch(r"[0-9a-f]{32}", x) for x in (service_id, command_id))
            or type(output_hash) is not str or not re.fullmatch(r"[0-9a-f]{64}", output_hash)
            or mutant != wrong_body_request(original)):
        raise ProtocolError()
    return dict(attempt=binding.attempt, request_id=service_id, route="maya.offline.model.v1",
        endpoint="https://maya-offline-model.invalid/v1/chat/completions", model=MODEL,
        destination="provider", request_sha256=digest(original), request_bytes=str(len(original)),
        response_sha256="", response_bytes="0", output_sha256=output_hash, dispatches="0", real_inference="false",
        validation_schema="maya.model.body_validation.v1", case="M03d", stage="request_body",
        coordinator_request_id=command_id, mutated_sha256=digest(mutant), mutated_bytes=str(len(mutant)),
        observed_model=MODEL, mutation_field="messages[1].content.canary.last_hex",
        mutation_rule="last_digit_0_to_1_otherwise_to_0", gateway_calls="0", dispatch_attempted="false",
        runtime_prepared="0", runtime_released="0", operator_prepared="0", operator_released="0")


class WrongBodyBridge(OfflineModelBridge):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutant = wrong_body_request(self._expected)
        self._command_id = None
        self.validation_recorded = False

    def bind_command(self, command_id):
        if self._command_id is not None or type(command_id) is not str or not re.fullmatch(r"[0-9a-f]{32}", command_id):
            raise ProtocolError()
        self._command_id = command_id

    def prepare_runtime(self, message, channel_id):
        if type(message) is not dict or message.get("body") != self._mutant.decode("utf-8"):
            self.close()
            raise ProtocolError()
        return super().prepare_runtime(message, channel_id)

    def _zero_boundary(self):
        return (self.envelope_validated is True and self.envelope_identity_validated is True
            and self.request_shape_validated is True and self.validation_stage == "request_body"
            and self.gateway_calls == 0 and self.dispatch_attempted is False and self.dispatches == 0
            and self.request_validated is False and self.egress_gateway_denied is False
            and self.prepared_runtime_releases == self.confirmed_runtime_releases == 0
            and self.prepared_operator_releases == self.confirmed_operator_releases == 0)

    def metadata(self):
        return body_metadata(self.binding, self.request_id, self._command_id,
            self._expected, self._mutant, digest(self._provider.text.encode("utf-8")))

    def _event(self, stage, destination, allowed=True, coordinator_request_id=""):
        if (stage != "denied" or allowed or destination != "provider" or not self._zero_boundary()
                or self._clock() >= self._expires or self._revoked):
            raise ProtocolError()
        self._audit.write(AuditRecord(event_type="model_bridge.body_rejected", decision="deny",
            reason_code="model_bridge.wrong_body", actor_id="windows:"+self.binding.operator_sid,
            capability="model.egress", target="model:maya-offline-fixture", operation="infer",
            data_classification="internal-synthetic", metadata=self.metadata()))
        self.validation_recorded = True

    def evidence(self):
        if not self.closed or self._audit.failed or not self.validation_recorded or not self._zero_boundary():
            raise ProtocolError()
        return self.metadata()


def verify_body_audit(raw, binding, service_id, command_id, original, mutant, output_hash):
    if type(raw) is not bytes or not 1 <= len(raw) <= 131072 or raw.count(b"\n") != 1 or not raw.endswith(b"\n"):
        raise ProtocolError()
    record = decode(raw[:-1])
    expected = dict(schema_version=1, event_type="model_bridge.body_rejected", decision="deny",
        reason_code="model_bridge.wrong_body", actor_id="windows:"+binding.operator_sid,
        capability="model.egress", target="model:maya-offline-fixture", operation="infer",
        data_classification="internal-synthetic", idempotency_key=None,
        metadata=body_metadata(binding, service_id, command_id, original, mutant, output_hash))
    if (set(record) != set(expected)|{"timestamp"} or type(record["schema_version"]) is not int
            or any(record[k] != v for k,v in expected.items())):
        raise ProtocolError()
    stamp = record["timestamp"]
    if type(stamp) is not str or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|\+00:00)", stamp):
        raise ProtocolError()
    try:
        datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        raise ProtocolError() from None
    return 1

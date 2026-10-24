"""Exact offline positive-path audit readback, separate from writer state."""
from __future__ import annotations

from datetime import datetime, timezone
import re

from .model_service import MODEL, ORIGIN, PATH, ROUTE, TARGET, digest
from .protocol import ProtocolError, decode
from .service import HostBinding

STAGES = ("egress_intent", "dispatch_outcome", "runtime_release_intent", "runtime_delivery",
          "operator_release_intent", "operator_delivery")


def verify_model_audit(raw: bytes, binding: HostBinding, request_id: str,
                       expected_request: bytes, expected_response: bytes, expected_output: str,
                       coordinator_requests: tuple[str, str]) -> int:
    if (type(raw) is not bytes or not 1 <= len(raw) <= 131072 or not raw.endswith(b"\n")
            or not isinstance(binding, HostBinding) or type(request_id) is not str
            or not re.fullmatch(r"[0-9a-f]{32}", request_id)
            or type(expected_request) is not bytes or not 1 <= len(expected_request) <= 4096
            or type(expected_response) is not bytes or not 1 <= len(expected_response) <= 4096
            or type(expected_output) is not str or not 1 <= len(expected_output.encode("utf-8")) <= 1024
            or type(coordinator_requests) is not tuple or len(coordinator_requests) != 2
            or any(type(x) is not str or not re.fullmatch(r"[0-9a-f]{32}", x) for x in coordinator_requests)
            or coordinator_requests[0] == coordinator_requests[1]):
        raise ProtocolError()
    lines = raw[:-1].split(b"\n")
    if len(lines) != len(STAGES):
        raise ProtocolError()
    previous = None
    for index, (line, stage) in enumerate(zip(lines, STAGES)):
        record = decode(line)
        destination = "provider" if index < 2 else "runtime:"+binding.attempt if index < 4 else "operator"
        expected = dict(schema_version=1, event_type="model_bridge."+stage, decision="allow",
            reason_code="model_bridge."+stage, actor_id="windows:"+binding.operator_sid,
            capability="model.egress" if index < 2 else "model.output", target=TARGET,
            operation="infer" if index < 2 else "disclose", data_classification="internal-synthetic",
            idempotency_key=None, metadata=dict(attempt=binding.attempt, request_id=request_id,
                route=ROUTE, endpoint=ORIGIN+PATH, model=MODEL, destination=destination,
                request_sha256=digest(expected_request), response_sha256="" if index == 0 else digest(expected_response),
                request_bytes=str(len(expected_request)), response_bytes="0" if index == 0 else str(len(expected_response)),
                output_sha256=digest(expected_output.encode("utf-8")), dispatches="0" if index == 0 else "1",
                real_inference="false"))
        if index in (3, 5):
            expected["metadata"]["coordinator_request_id"] = coordinator_requests[0 if index == 3 else 1]
        if set(record) != set(expected) | {"timestamp"} or type(record["schema_version"]) is not int:
            raise ProtocolError()
        for key, value in expected.items():
            if record[key] != value:
                raise ProtocolError()
        try:
            if (type(record["timestamp"]) is not str or not re.fullmatch(
                    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\+00:00|Z)", record["timestamp"])):
                raise ValueError()
            stamp = datetime.fromisoformat(record["timestamp"])
            if stamp.utcoffset() != timezone.utc.utcoffset(stamp) or previous is not None and stamp < previous:
                raise ValueError()
            previous = stamp
        except (TypeError, ValueError):
            raise ProtocolError() from None
    return len(STAGES)

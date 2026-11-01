"""M02-only negative admission and audit predicates. No runtime/provider imports."""
from __future__ import annotations

from datetime import datetime
import re

from .model_service import MODEL, ORIGIN, PATH, ROUTE, TARGET, digest
from .protocol import ProtocolError, decode
from .service import HostBinding


def denial_evidence(service, audit) -> dict:
    if (not service.closed or audit.failed or service.request_validated is not True
            or service.egress_gateway_denied is not True or service.dispatch_attempted is not False
            or service.dispatches != 0 or service.prepared_runtime_releases != 0
            or service.confirmed_runtime_releases != 0 or service.prepared_operator_releases != 0
            or service.confirmed_operator_releases != 0):
        raise ProtocolError()
    return dict(case="M02", boundary="gateway_egress", request_validated=True,
                gateway_denied=True, dispatches=0, confirmed_runtime_releases=0,
                confirmed_operator_releases=0, real_inference=False)


def verify_denial_audit(raw: bytes, binding: HostBinding, request_id: str,
                       expected_request: bytes, output_hash: str) -> int:
    if (type(raw) is not bytes or not 1 <= len(raw) <= 131072 or not raw.endswith(b"\n")
            or raw.count(b"\n") != 1 or not isinstance(binding, HostBinding)
            or type(request_id) is not str or not re.fullmatch(r"[0-9a-f]{32}", request_id)
            or type(expected_request) is not bytes or not 1 <= len(expected_request) <= 4096
            or type(output_hash) is not str or not re.fullmatch(r"[0-9a-f]{64}", output_hash)):
        raise ProtocolError()
    record = decode(raw[:-1])
    expected = dict(schema_version=1, event_type="model_bridge.denied", decision="deny",
        reason_code="model_bridge.denied", actor_id="windows:"+binding.operator_sid,
        capability="model.egress", target=TARGET, operation="infer",
        data_classification="internal-synthetic", idempotency_key=None,
        metadata=dict(attempt=binding.attempt, request_id=request_id, route=ROUTE,
            endpoint=ORIGIN+PATH, model=MODEL, destination="provider",
            request_sha256=digest(expected_request), response_sha256="",
            request_bytes=str(len(expected_request)), response_bytes="0",
            output_sha256=output_hash, dispatches="0", real_inference="false"))
    if (set(record) != set(expected) | {"timestamp"} or type(record["schema_version"]) is not int
            or any(record[k] != v for k,v in expected.items())):
        raise ProtocolError()
    stamp = record["timestamp"]
    if type(stamp) is not str or not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\+00:00|Z)", stamp):
        raise ProtocolError()
    try:
        datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        raise ProtocolError() from None
    return 1

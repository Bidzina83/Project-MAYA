"""M05a terminal snapshot and independent exact four-record positive-prefix admission."""
from datetime import datetime
import re

from .model_service import MODEL, ORIGIN, PATH, ROUTE, TARGET, digest
from .protocol import ProtocolError, decode


def finish_adapter_budget(service, delivery_id):
    with service._lock:
        if (service.closed or service._audit.failed or service._revoked
                or service._phase != "runtime_delivered" or not service.request_validated
                or service.gateway_calls != 2 or service.dispatches != 1
                or service.prepared_runtime_releases != 1 or service.confirmed_runtime_releases != 1
                or service.prepared_operator_releases or service.confirmed_operator_releases
                or type(delivery_id) is not str or not re.fullmatch(r"[0-9a-f]{32}", delivery_id)):
            raise ProtocolError()
        # Snapshot prior effects only. No new authorization or expiry/liveness claim.
        result = dict(case="M05a", gateway_calls=2, dispatches=1, confirmed_runtime_releases=1,
                      confirmed_operator_releases=0, real_inference=False,
                      request_sha256=digest(service._expected), response_sha256=digest(service._response),
                      delivery_command_id=delivery_id)
        service.close()
        return result


def verify_budget_audit(raw, binding, service_id, body, response, output, delivery_id):
    for value in (service_id, delivery_id):
        if type(value) is not str or not re.fullmatch(r"[0-9a-f]{32}", value):
            raise ProtocolError()
    if (type(raw) is not bytes or not 1 <= len(raw) <= 131072 or not raw.endswith(b"\n")
            or raw.count(b"\n") != 4 or type(body) is not bytes or not 1 <= len(body) <= 4096
            or type(response) is not bytes or not 1 <= len(response) <= 4096
            or type(output) is not str or not 1 <= len(output.encode()) <= 1024):
        raise ProtocolError()
    previous = None
    for index, stage in enumerate(("egress_intent", "dispatch_outcome", "runtime_release_intent", "runtime_delivery")):
        metadata = dict(attempt=binding.attempt, request_id=service_id, route=ROUTE, endpoint=ORIGIN+PATH,
            model=MODEL, destination="provider" if index < 2 else "runtime:"+binding.attempt,
            request_sha256=digest(body), request_bytes=str(len(body)),
            response_sha256="" if index == 0 else digest(response),
            response_bytes="0" if index == 0 else str(len(response)), output_sha256=digest(output.encode()),
            dispatches="0" if index == 0 else "1", real_inference="false")
        if index == 3:
            metadata["coordinator_request_id"] = delivery_id
        expected = dict(schema_version=1, event_type="model_bridge."+stage, decision="allow",
            reason_code="model_bridge."+stage, actor_id="windows:"+binding.operator_sid,
            capability="model.egress" if index < 2 else "model.output", target=TARGET,
            operation="infer" if index < 2 else "disclose", data_classification="internal-synthetic",
            idempotency_key=None, metadata=metadata)
        record = decode(raw[:-1].split(b"\n")[index])
        if (set(record) != set(expected)|{"timestamp"} or type(record["schema_version"]) is not int
                or any(record[key] != value for key, value in expected.items())):
            raise ProtocolError()
        stamp = record["timestamp"]
        if type(stamp) is not str or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|\+00:00)", stamp):
            raise ProtocolError()
        try:
            now = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if previous is not None and now < previous:
                raise ValueError()
            previous = now
        except ValueError:
            raise ProtocolError() from None
    return 4

"""M06 host-only evidence and exact three-record admission; no response release."""
from datetime import datetime
import json
import re

from .model_service import MODEL, ORIGIN, PATH, ROUTE, TARGET, digest
from .protocol import ProtocolError, decode
from .service import HostBinding


def expected_runtime_response(text):
    if type(text) is not str or not re.fullmatch(r"MAYA_OFFLINE_MODEL_OK:[0-9a-f]{32}", text):
        raise ProtocolError()
    return json.dumps(dict(id="maya-offline-synthetic", object="chat.completion", created=0,
        model=MODEL, choices=[dict(index=0, message=dict(role="assistant", content=text),
            finish_reason="stop")], usage=dict(prompt_tokens=0, completion_tokens=0, total_tokens=0)),
        ensure_ascii=True, separators=(",", ":")).encode("ascii")


def output_denial_evidence(service, audit, denial):
    response = expected_runtime_response(service._provider.text)
    if (not service.closed or audit.failed or denial.uncertain is not True
            or service.runtime_output_gateway_denied is not True or service.egress_gateway_denied
            or service.request_validated is not True or service.dispatch_attempted is not True
            or service._phase != "dispatched" or service._response != response
            or service._expected_response != response or service.gateway_calls != 2 or service.dispatches != 1
            or any((service.prepared_runtime_releases, service.confirmed_runtime_releases,
                    service.prepared_operator_releases, service.confirmed_operator_releases))):
        raise ProtocolError()
    return dict(case="M06", boundary="gateway_runtime_output", request_validated=True,
        response_validated=True, gateway_denied=True, gateway_calls=2, dispatch_attempted=True,
        dispatches=1, prepared_runtime_releases=0, confirmed_runtime_releases=0,
        prepared_operator_releases=0, confirmed_operator_releases=0, real_inference=False,
        uncertain=True, request_sha256=digest(service._expected), request_bytes=len(service._expected),
        response_sha256=digest(response), response_bytes=len(response))


def verify_output_denial_audit(raw, binding, request_id, body, output):
    if (type(raw) is not bytes or not 1 <= len(raw) <= 131072 or not raw.endswith(b"\n")
            or raw.count(b"\n") != 3 or not isinstance(binding, HostBinding)
            or type(request_id) is not str or not re.fullmatch(r"[0-9a-f]{32}", request_id)
            or type(body) is not bytes or not 1 <= len(body) <= 4096):
        raise ProtocolError()
    response = expected_runtime_response(output)
    previous = None
    for index, stage in enumerate(("egress_intent", "dispatch_outcome", "denied")):
        provider = index < 2
        metadata = dict(attempt=binding.attempt, request_id=request_id, route=ROUTE,
            endpoint=ORIGIN+PATH, model=MODEL, destination="provider" if provider else "runtime:"+binding.attempt,
            request_sha256=digest(body), request_bytes=str(len(body)),
            response_sha256="" if index == 0 else digest(response),
            response_bytes="0" if index == 0 else str(len(response)), output_sha256=digest(output.encode()),
            dispatches="0" if index == 0 else "1", real_inference="false")
        expected = dict(schema_version=1, event_type="model_bridge."+stage,
            decision="allow" if provider else "deny", reason_code="model_bridge."+stage,
            actor_id="windows:"+binding.operator_sid, capability="model.egress" if provider else "model.output",
            target=TARGET, operation="infer" if provider else "disclose", data_classification="internal-synthetic",
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
    return 3

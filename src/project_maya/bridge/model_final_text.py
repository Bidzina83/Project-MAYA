"""M08 fixed final-text rejection evidence; no change to admission predicates."""
import re
from datetime import datetime

from .model_output_denial import expected_runtime_response
from .model_service import MODEL, ORIGIN, PATH, ROUTE, TARGET, OfflineModelBridge, SyntheticModel, digest
from .protocol import ProtocolError, decode
from .service import HostBinding

GUARD_KEYS = frozenset(("schema", "attempt", "runtime_delivery_command_id", "final_command_id",
    "expected_phase", "phase", "closed", "audit_failed", "revoked", "clock_called",
    "clock_returned", "comparison_evaluated", "at_or_after_deadline", "decision", "cause",
    "timing_valid", "issue_sampled", "elapsed_ms", "remaining_ms", "ttl_ms"))


def validate_final_guard(value, attempt, delivery_id, command_id):
    if type(value) is not dict or set(value) != GUARD_KEYS:
        raise ProtocolError()
    for ident in (attempt, delivery_id, command_id):
        if type(ident) is not str or not re.fullmatch(r"[0-9a-f]{32}", ident):
            raise ProtocolError()
    if (delivery_id == command_id or value["schema"] != "maya.model.final_guard.v1"
            or value["attempt"] != attempt or value["runtime_delivery_command_id"] != delivery_id
            or value["final_command_id"] != command_id or value["expected_phase"] != "runtime_delivered"
            or type(value["ttl_ms"]) is not int or value["ttl_ms"] != 2000):
        raise ProtocolError()
    for key in ("clock_called","clock_returned","comparison_evaluated","timing_valid","issue_sampled"):
        if type(value[key]) is not bool:
            raise ProtocolError()
    for key in ("closed","audit_failed","revoked","at_or_after_deadline"):
        if value[key] is not None and type(value[key]) is not bool:
            raise ProtocolError()
    phases = (None,"new","issued","admitted","dispatched","runtime_prepared","runtime_delivered",
              "operator_admitted","operator_prepared","complete","other")
    if value["phase"] not in phases or value["decision"] not in ("allowed","rejected","raised"):
        raise ProtocolError()
    if value["closed"] is True:
        cause = "closed"
        tail = ("audit_failed","revoked","phase")
    elif value["closed"] is False and value["audit_failed"] is True:
        cause = "audit_failed"
        tail = ("revoked","phase")
    elif value["closed"] is False and value["audit_failed"] is False and value["revoked"] is True:
        cause = "revoked"
        tail = ("phase",)
    elif all(value[k] is False for k in ("closed","audit_failed","revoked")) and value["phase"] is not None:
        cause = "phase_mismatch" if value["phase"] != "runtime_delivered" else None
        tail = ()
    else:
        cause = "state_exception"
        tail = ()
        values = (value["closed"],value["audit_failed"],value["revoked"],value["phase"])
        # A failed operand leaves that operand and every subsequent one unobserved.
        if None not in values or any(v is not None for v in values[values.index(None):]):
            raise ProtocolError()
    if any(value[k] is not None for k in tail):
        raise ProtocolError()
    if cause is not None:
        if (value["clock_called"] or value["clock_returned"] or value["comparison_evaluated"]
                or value["at_or_after_deadline"] is not None
                or value["decision"] != ("raised" if cause == "state_exception" else "rejected")):
            raise ProtocolError()
    else:
        if not value["clock_called"]:
            raise ProtocolError()
        if not value["clock_returned"]:
            cause = "clock_exception"
            if value["comparison_evaluated"] or value["at_or_after_deadline"] is not None or value["decision"] != "raised":
                raise ProtocolError()
        elif not value["comparison_evaluated"]:
            cause = "clock_value_exception"
            if value["at_or_after_deadline"] is not None or value["decision"] != "raised":
                raise ProtocolError()
        else:
            if type(value["at_or_after_deadline"]) is not bool:
                raise ProtocolError()
            cause = "expired" if value["at_or_after_deadline"] else "allowed"
            if value["decision"] != ("rejected" if value["at_or_after_deadline"] else "allowed"):
                raise ProtocolError()
    if value["cause"] != cause:
        raise ProtocolError()
    if value["timing_valid"]:
        if (not value["comparison_evaluated"] or not value["clock_returned"] or not value["issue_sampled"]
                or type(value["elapsed_ms"]) is not int or not 0 <= value["elapsed_ms"] <= 2147483647
                or type(value["remaining_ms"]) is not int or not -2147483647 <= value["remaining_ms"] <= 2147483647
                or (value["at_or_after_deadline"] and value["remaining_ms"] > 0)
                or (not value["at_or_after_deadline"] and value["remaining_ms"] < 0)):
            raise ProtocolError()
    elif value["elapsed_ms"] is not None or value["remaining_ms"] is not None:
        raise ProtocolError()
    return value["decision"] == "allowed" and value["timing_valid"]


def final_guard_evidence(service, denial, delivery_id, command_id):
    if (type(service) is not OfflineModelBridge or service.final_diagnostics_enabled is not True
            or not service.closed or denial.uncertain is not True or type(service._final_guard) is not dict):
        raise ProtocolError()
    result = dict(service._final_guard, schema="maya.model.final_guard.v1", attempt=service.binding.attempt,
        runtime_delivery_command_id=delivery_id, final_command_id=command_id)
    validate_final_guard(result, service.binding.attempt, delivery_id, command_id)
    return result


def fixed_final_text(text):
    expected_runtime_response(text)
    return text[:-1] + ("1" if text[-1] == "0" else "0")


def final_text_evidence(service, audit, denial, delivery_id, command_id):
    for value in (delivery_id, command_id):
        if type(value) is not str or not re.fullmatch(r"[0-9a-f]{32}", value):
            raise ProtocolError()
    if delivery_id == command_id:
        raise ProtocolError()
    expected = expected_runtime_response(service._provider.text)
    original = service._provider.text.encode("utf-8")
    fault = fixed_final_text(service._provider.text).encode("utf-8")
    if (type(service) is not OfflineModelBridge or type(service._provider) is not SyntheticModel
            or not service.closed or audit.failed or denial.uncertain is not True
            or service.request_validated is not True or service.dispatch_attempted is not True
            or service.final_failure_stage != "operator_text"
            or service.final_failure_sha256 != digest(fault) or service.final_failure_bytes != len(fault)
            or service._response != expected or service._expected_response != expected
            or service._phase != "runtime_delivered" or service._destination != "operator"
            or service.gateway_calls != 2 or service.dispatches != 1
            or service.egress_gateway_denied or service.runtime_output_gateway_denied
            or service.prepared_runtime_releases != 1 or service.confirmed_runtime_releases != 1
            or service.prepared_operator_releases != 0 or service.confirmed_operator_releases != 0):
        raise ProtocolError()
    return dict(case="M08", boundary="operator_text", request_validated=True,
        response_validated=True, gateway_calls=2, dispatch_attempted=True, dispatches=1,
        uncertain=True, validation_stage="operator_text", runtime_delivery_command_id=delivery_id,
        final_command_id=command_id, request_sha256=digest(service._expected), request_bytes=len(service._expected),
        response_sha256=digest(expected), response_bytes=len(expected),
        original_text_sha256=digest(original), original_text_bytes=len(original),
        observed_text_sha256=digest(fault), observed_text_bytes=len(fault),
        prepared_runtime_releases=1, confirmed_runtime_releases=1,
        prepared_operator_releases=0, confirmed_operator_releases=0,
        egress_gateway_denied=False, runtime_output_gateway_denied=False, real_inference=False)


def verify_final_audit(raw, binding, service_id, body, output, delivery_id):
    response = expected_runtime_response(output)
    if (type(raw) is not bytes or not 1 <= len(raw) <= 131072 or not raw.endswith(b"\n")
            or raw.count(b"\n") != 5 or not isinstance(binding, HostBinding)
            or type(body) is not bytes or not 1 <= len(body) <= 4096
            or any(type(v) is not str or not re.fullmatch(r"[0-9a-f]{32}", v)
                   for v in (service_id, delivery_id))):
        raise ProtocolError()
    previous = None
    for i, (line, stage) in enumerate(zip(raw[:-1].split(b"\n"),
            ("egress_intent", "dispatch_outcome", "runtime_release_intent", "runtime_delivery", "denied"))):
        destination = "provider" if i < 2 else "runtime:" + binding.attempt if i < 4 else "operator"
        metadata = dict(attempt=binding.attempt, request_id=service_id, route=ROUTE, endpoint=ORIGIN+PATH,
            model=MODEL, destination=destination, request_sha256=digest(body), request_bytes=str(len(body)),
            response_sha256="" if i == 0 else digest(response), response_bytes="0" if i == 0 else str(len(response)),
            output_sha256=digest(output.encode("utf-8")), dispatches="0" if i == 0 else "1", real_inference="false")
        if i == 3:
            metadata["coordinator_request_id"] = delivery_id
        expected = dict(schema_version=1, event_type="model_bridge."+stage, decision="deny" if i == 4 else "allow",
            reason_code="model_bridge."+stage, actor_id="windows:"+binding.operator_sid,
            capability="model.egress" if i < 2 else "model.output", target=TARGET,
            operation="infer" if i < 2 else "disclose", data_classification="internal-synthetic",
            idempotency_key=None, metadata=metadata)
        record = decode(line)
        if (set(record) != set(expected)|{"timestamp"} or type(record["schema_version"]) is not int
                or any(record[k] != v for k, v in expected.items())):
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
    return 5

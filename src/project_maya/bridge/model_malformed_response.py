"""M07a construction-time fixed fault and exact two-record rejection admission."""
from datetime import datetime
import re

from .model_service import MODEL, ORIGIN, PATH, ROUTE, TARGET, SyntheticModel, OfflineModelBridge, digest
from .model_output_denial import expected_runtime_response
from .protocol import ProtocolError, decode
from .service import HostBinding

FAULT_BYTES = b"{"


class MalformedJSONProvider(SyntheticModel):
    def dispatch(self):
        super().dispatch()
        return FAULT_BYTES


class MalformedJSONBridge(OfflineModelBridge):
    def _new_provider(self, fixture_text):
        return MalformedJSONProvider(fixture_text)


def malformed_response_evidence(service, audit, denial):
    expected = expected_runtime_response(service._provider.text)
    if (type(service) is not MalformedJSONBridge or type(service._provider) is not MalformedJSONProvider
            or not service.closed or audit.failed or denial.uncertain is not True
            or service.request_validated is not True or service.dispatch_attempted is not True
            or service.response_failure_stage != "response_json"
            or service.response_failure_sha256 != digest(FAULT_BYTES) or service.response_failure_bytes != 1
            or service._response is not None or service._expected_response != expected
            or service._phase != "admitted" or service._destination != "provider"
            or service.gateway_calls != 1 or service.dispatches != 1
            or service.egress_gateway_denied or service.runtime_output_gateway_denied
            or any((service.prepared_runtime_releases,service.confirmed_runtime_releases,
                    service.prepared_operator_releases,service.confirmed_operator_releases))):
        raise ProtocolError()
    return dict(case="M07a",boundary="response_json",request_validated=True,egress_allowed=True,
        gateway_calls=1,dispatch_attempted=True,dispatches=1,response_validated=False,validation_stage="response_json",
        observed_response_sha256=digest(FAULT_BYTES),observed_response_bytes=1,response_sha256="",response_bytes=0,
        expected_response_sha256=digest(expected),expected_response_bytes=len(expected),
        prepared_runtime_releases=0,confirmed_runtime_releases=0,prepared_operator_releases=0,
        confirmed_operator_releases=0,real_inference=False,uncertain=True,
        request_sha256=digest(service._expected),request_bytes=len(service._expected),
        egress_gateway_denied=False,runtime_output_gateway_denied=False)


def verify_malformed_audit(raw,binding,request_id,body,output):
    expected_runtime_response(output)
    if (type(raw) is not bytes or not 1 <= len(raw) <= 131072 or not raw.endswith(b"\n")
            or raw.count(b"\n") != 2 or not isinstance(binding,HostBinding)
            or type(request_id) is not str or not re.fullmatch(r"[0-9a-f]{32}",request_id)
            or type(body) is not bytes or not 1 <= len(body) <= 4096):
        raise ProtocolError()
    previous=None
    for i,stage in enumerate(("egress_intent","denied")):
        metadata=dict(attempt=binding.attempt,request_id=request_id,route=ROUTE,endpoint=ORIGIN+PATH,
            model=MODEL,destination="provider",request_sha256=digest(body),request_bytes=str(len(body)),
            response_sha256="",response_bytes="0",output_sha256=digest(output.encode()),
            dispatches=str(i),real_inference="false")
        expected=dict(schema_version=1,event_type="model_bridge."+stage,decision="allow" if i==0 else "deny",
            reason_code="model_bridge."+stage,actor_id="windows:"+binding.operator_sid,capability="model.egress",
            target=TARGET,operation="infer",data_classification="internal-synthetic",idempotency_key=None,metadata=metadata)
        record=decode(raw[:-1].split(b"\n")[i])
        if (set(record)!=set(expected)|{"timestamp"} or type(record["schema_version"]) is not int
                or any(record[k]!=v for k,v in expected.items())):
            raise ProtocolError()
        stamp=record["timestamp"]
        if type(stamp) is not str or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|\+00:00)",stamp):
            raise ProtocolError()
        try:
            now=datetime.fromisoformat(stamp.replace("Z","+00:00"))
            if previous is not None and now<previous:raise ValueError()
            previous=now
        except ValueError:raise ProtocolError() from None
    return 2

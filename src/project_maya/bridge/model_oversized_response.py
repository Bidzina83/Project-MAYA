"""M07b construction-time fixed fault and exact two-record rejection admission."""
from datetime import datetime
import re

from .model_service import MODEL, ORIGIN, PATH, ROUTE, TARGET, SyntheticModel, OfflineModelBridge, digest
from .model_output_denial import expected_runtime_response
from .protocol import ProtocolError, decode
from .service import HostBinding

FAULT_BYTES = b'{"x":"' + b"a" * 4089 + b'"}'


class OversizedJSONProvider(SyntheticModel):
    def dispatch(self):
        super().dispatch()
        return FAULT_BYTES


class OversizedJSONBridge(OfflineModelBridge):
    def _new_provider(self, fixture_text):
        return OversizedJSONProvider(fixture_text)


def oversized_response_evidence(service, audit, denial):
    expected = expected_runtime_response(service._provider.text)
    if (type(service) is not OversizedJSONBridge or type(service._provider) is not OversizedJSONProvider
            or not service.closed or audit.failed or denial.uncertain is not True
            or service.request_validated is not True or service.dispatch_attempted is not True
            or service.response_failure_stage != "response_size"
            or service.response_failure_sha256 != digest(FAULT_BYTES) or service.response_failure_bytes != 4097
            or service._response is not None or service._expected_response != expected
            or service._phase != "admitted" or service._destination != "provider"
            or service.gateway_calls != 1 or service.dispatches != 1
            or service.egress_gateway_denied or service.runtime_output_gateway_denied
            or any((service.prepared_runtime_releases,service.confirmed_runtime_releases,
                    service.prepared_operator_releases,service.confirmed_operator_releases))):
        raise ProtocolError()
    return dict(case="M07b",boundary="response_size",request_validated=True,egress_allowed=True,
        gateway_calls=1,dispatch_attempted=True,dispatches=1,response_validated=False,validation_stage="response_size",
        observed_response_sha256=digest(FAULT_BYTES),observed_response_bytes=4097,response_sha256="",response_bytes=0,
        expected_response_sha256=digest(expected),expected_response_bytes=len(expected),
        prepared_runtime_releases=0,confirmed_runtime_releases=0,prepared_operator_releases=0,
        confirmed_operator_releases=0,real_inference=False,uncertain=True,
        request_sha256=digest(service._expected),request_bytes=len(service._expected),
        egress_gateway_denied=False,runtime_output_gateway_denied=False)



def verify_oversized_audit(raw, binding, request_id, body, output):
    from .model_malformed_response import verify_malformed_audit
    return verify_malformed_audit(raw, binding, request_id, body, output)

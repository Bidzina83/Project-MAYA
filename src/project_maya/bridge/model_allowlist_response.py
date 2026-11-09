"""Fixed M07c provider and independent expected fault oracle."""
import json

from .model_output_denial import expected_runtime_response
from .model_service import OfflineModelBridge, SyntheticModel, digest
from .protocol import ProtocolError, decode


def expected_allowlist_fault(text):
    expected_runtime_response(text)
    return expected_runtime_response(text[:-1] + ("1" if text[-1] == "0" else "0"))


class AllowlistMismatchProvider(SyntheticModel):
    def dispatch(self):
        original = super().dispatch()
        expected_runtime_response(self.text)
        response = decode(original)
        message = response["choices"][0]["message"]
        content = message["content"]
        message["content"] = content[:-1] + ("1" if content[-1] == "0" else "0")
        return json.dumps(response, ensure_ascii=True, separators=(",", ":")).encode("ascii")


class AllowlistMismatchBridge(OfflineModelBridge):
    def _new_provider(self, fixture_text):
        return AllowlistMismatchProvider(fixture_text)

def allowlist_response_evidence(service, audit, denial):
    fault = expected_allowlist_fault(service._provider.text)
    expected = expected_runtime_response(service._provider.text)
    if (type(service) is not AllowlistMismatchBridge or type(service._provider) is not AllowlistMismatchProvider
            or not service.closed or audit.failed or denial.uncertain is not True
            or service.request_validated is not True or service.dispatch_attempted is not True
            or service.response_failure_stage != "response_allowlist"
            or service.response_failure_sha256 != digest(fault) or service.response_failure_bytes != len(fault)
            or service._response is not None or service._expected_response != expected
            or service._phase != "admitted" or service._destination != "provider"
            or service.gateway_calls != 1 or service.dispatches != 1
            or service.egress_gateway_denied or service.runtime_output_gateway_denied
            or any((service.prepared_runtime_releases,service.confirmed_runtime_releases,
                    service.prepared_operator_releases,service.confirmed_operator_releases))):
        raise ProtocolError()
    return dict(case="M07c",boundary="response_allowlist",request_validated=True,egress_allowed=True,
        gateway_calls=1,dispatch_attempted=True,dispatches=1,response_validated=False,validation_stage="response_allowlist",
        observed_response_sha256=digest(fault),observed_response_bytes=len(fault),response_sha256="",response_bytes=0,
        expected_response_sha256=digest(expected),expected_response_bytes=len(expected),
        prepared_runtime_releases=0,confirmed_runtime_releases=0,prepared_operator_releases=0,
        confirmed_operator_releases=0,real_inference=False,uncertain=True,
        request_sha256=digest(service._expected),request_bytes=len(service._expected),
        egress_gateway_denied=False,runtime_output_gateway_denied=False)



def verify_allowlist_audit(raw, binding, request_id, body, output):
    from .model_malformed_response import verify_malformed_audit
    return verify_malformed_audit(raw, binding, request_id, body, output)

import pytest

from project_maya.bridge.model_allowlist_response import (
    AllowlistMismatchBridge,
    AllowlistMismatchProvider,
    expected_allowlist_fault,
)
from project_maya.bridge.model_service import ModelDenied, digest
from project_maya.bridge.protocol import decode
from test_model_oversized_response_inert import CHANNEL, OversizedTests as _OversizedFixture


@pytest.mark.parametrize("last", ["0", "f"])
def test_fixed_mutation_preserves_envelope(last):
    text = "MAYA_OFFLINE_MODEL_OK:" + "a" * 31 + last
    provider = AllowlistMismatchProvider(text)
    original = provider.wire_reply()
    fault = provider.dispatch()
    assert fault == expected_allowlist_fault(text)
    assert len(fault) == len(original) == 313
    assert sum(a != b for a, b in zip(original, fault)) == 1
    expected = decode(original)
    expected["choices"][0]["message"]["content"] = text[:-1] + ("1" if last == "0" else "0")
    assert decode(fault) == expected
    assert provider.wire_reply() == original
    with pytest.raises(ModelDenied):
        provider.dispatch()


def test_original_service_rejects_at_allowlist(monkeypatch):
    monkeypatch.setattr("project_maya.bridge.audit.os.fsync", lambda _: None)
    service, _, request = _OversizedFixture().service(AllowlistMismatchBridge)
    original = service._expected_response
    with pytest.raises(ModelDenied) as caught:
        service.prepare_runtime(request, CHANNEL)
    assert caught.value.uncertain is True
    assert service.response_failure_stage == "response_allowlist"
    assert service.response_failure_sha256 == digest(expected_allowlist_fault(service._provider.text))
    assert service._expected_response == original
    assert service._response is None
    assert service.gateway_calls == service.dispatches == 1

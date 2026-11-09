"""M08 in-memory worker/service fixtures; no native or bundled-runtime execution."""
import copy
import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from project_maya.bridge.audit import RequiredAudit
from project_maya.bridge.model_final_text import fixed_final_text, final_text_evidence, verify_final_audit, validate_final_guard
from project_maya.bridge.model_service import OfflineModelBridge, ModelDenied, digest
from project_maya.bridge.model_worker import serve_model
from project_maya.bridge.protocol import ProtocolError
from project_maya.bridge.service import HostBinding
import test_model_bridge_worker_inert as fixture
import test_model_oversized_response_inert as service_fixture


class Stream(io.BytesIO):
    def fileno(self):
        return 123


def worker_fixture(change=lambda m:m, mode=True, rules=None, fault=None, retained=None, peer=None):
    class AuditStream(Stream):
        def write(self, raw):
            if fault == ("write", self.getvalue().count(b"\n")):
                raise OSError()
            return super().write(raw)
        def flush(self):
            if fault == ("flush", self.getvalue().count(b"\n")-1):
                raise OSError()
            return super().flush()
    channel = peer or fixture.CoordinatorFixture()
    def modify(message):
        if message["type"] == "model_prepare_final":
            message = dict(message, text=fixed_final_text(fixture.OUTPUT))
        return change(message)
    channel.modify = modify
    raw = AuditStream()
    if retained is not None:
        retained.extend((raw, channel))
    config = dict(operator_sid=fixture.SID, attempt=fixture.ATTEMPT, channel_id=fixture.CHANNEL,
        utc_day="2026-10-24", canary=fixture.CANARY, fixture_text=fixture.OUTPUT)
    with patch("project_maya.bridge.audit.os.fsync"):
        result = serve_model(channel, config, fixture.policy() if rules is None else rules,
            fixture.LITERALS.read_bytes(), RequiredAudit(raw), channel.write_expected, final_text=mode)
    return result, raw.getvalue(), channel


def verify(raw, channel, delivery_id="0"*31+"3"):
    return verify_final_audit(raw, HostBinding(fixture.SID, fixture.ATTEMPT, fixture.CHANNEL),
        channel.sent[0]["service_request_id"], channel.expected, fixture.OUTPUT, delivery_id)


@pytest.mark.parametrize("last", list("0123456789abcdef"))
def test_fixed_rule_changes_one_byte(last):
    text = "MAYA_OFFLINE_MODEL_OK:" + "a"*31 + last
    fault = fixed_final_text(text)
    assert len(fault) == len(text)
    assert sum(a != b for a,b in zip(text, fault)) == 1
    assert fault[-1] == ("1" if last == "0" else "0")


def test_worker_requires_truthful_positive_prefix():
    effects, raw, channel = worker_fixture()
    assert len(effects) == 26
    assert (effects["dispatches"], effects["confirmed_runtime_releases"], effects["confirmed_operator_releases"]) == (1,1,0)
    assert effects["gateway_calls"] == 2 and effects["uncertain"] is True
    assert verify(raw, channel) == 5
    assert channel.index == 4
    assert [m["type"] for m in channel.sent] == [
        "model_worker_ready", "model_grant_reply", "model_dispatch_reply",
        "model_runtime_ack", "model_final_observed"]
    assert validate_final_guard(channel.sent[-1]["guard"],fixture.ATTEMPT,
        effects["runtime_delivery_command_id"],effects["final_command_id"])
    records = [json.loads(line) for line in raw.splitlines()]
    assert [r["metadata"]["destination"] for r in records] == [
        "provider", "provider", "runtime:"+fixture.ATTEMPT, "runtime:"+fixture.ATTEMPT, "operator"]
    assert all(r["metadata"]["response_sha256"] == effects["response_sha256"] for r in records[1:])
    assert records[-1]["metadata"]["output_sha256"] == digest(fixture.OUTPUT.encode())
    assert "text" not in channel.sent[-1] and "lease" not in channel.sent[-1]
    assert fixed_final_text(fixture.OUTPUT) not in json.dumps(channel.sent)


@pytest.mark.parametrize("kind", ["wrong_text", "unchanged", "type", "duplicate_id", "wrong_attempt", "extra", "runtime_hash"])
def test_invalid_controls_do_not_pass(kind):
    def change(m):
        if m["type"] == "model_prepare_final":
            if kind == "wrong_text": return dict(m,text="other")
            if kind == "unchanged": return dict(m,text=fixture.OUTPUT)
            if kind == "type": return dict(m,text=1)
            if kind == "duplicate_id": return dict(m,request_id="0"*31+"3")
            if kind == "wrong_attempt": return dict(m,attempt="f"*32)
            if kind == "extra": return dict(m,extra=True)
        if kind == "runtime_hash" and m["type"] == "model_runtime_delivered":
            return dict(m,response_sha256="f"*64)
        return m
    if kind in ("wrong_text","type"):
        effects, _, peer = worker_fixture(change)
        assert effects == dict(diagnostic_only=True)
        assert peer.sent[-1]["effects"] is None
    else:
        with pytest.raises((ProtocolError, ModelDenied)):
            worker_fixture(change)


def test_audit_fields_schedule_and_actual_delivery_binding():
    _, raw, channel = worker_fixture()
    records = [json.loads(line) for line in raw.splitlines()]
    for i, record in enumerate(records):
        for key in record:
            changed = copy.deepcopy(records)
            changed[i][key] = "wrong"
            with pytest.raises(ProtocolError):
                verify(("\n".join(json.dumps(x) for x in changed)+"\n").encode(),channel)
        for key in record["metadata"]:
            changed = copy.deepcopy(records)
            changed[i]["metadata"][key] = "wrong"
            with pytest.raises(ProtocolError):
                verify(("\n".join(json.dumps(x) for x in changed)+"\n").encode(),channel)
    lines = raw.splitlines(keepends=True)
    for mutant in (b"".join(lines[:4]),raw+lines[-1],b"".join(reversed(lines)),raw[:-1]):
        with pytest.raises(ProtocolError): verify(mutant,channel)
    with pytest.raises(ProtocolError): verify(raw,channel,"f"*32)


@pytest.mark.parametrize("index", range(5))
@pytest.mark.parametrize("kind", ["write","flush"])
def test_all_audit_failures_block(index, kind):
    retained = []
    if index == 4:
        effects, _, peer = worker_fixture(fault=(kind,index),retained=retained)
        assert effects == dict(diagnostic_only=True) and peer.sent[-1]["effects"] is None
    else:
        with pytest.raises((ProtocolError, ModelDenied)):
            worker_fixture(fault=(kind,index),retained=retained)
    if index == 4:
        assert [m["type"] for m in retained[1].sent][-1] == "model_final_observed"


def test_control_send_failure_preserves_actual_prior_effects():
    class Peer(fixture.CoordinatorFixture):
        def send(self,m):
            if m["type"] == "model_final_observed": raise OSError()
            super().send(m)
    retained=[]
    with pytest.raises(OSError):worker_fixture(peer=Peer(),retained=retained)
    assert verify(retained[0].getvalue(),retained[1]) == 5


@pytest.mark.parametrize("kind", ["expired","revoked","wrong_phase","wrong_hash","extra_gateway","response","operator_prepared","operator_released"])
def test_original_worker_guard_and_evidence_fail_closed(kind, monkeypatch):
    monkeypatch.setattr("project_maya.bridge.audit.os.fsync",lambda _:None)
    now=[0.0]
    service, _, request = service_fixture.OversizedTests().service(OfflineModelBridge,clock=lambda:now[0])
    response=service.prepare_runtime(request,fixture.CHANNEL)
    service.confirm_runtime_delivery(response["response_sha256"],"3"*32)
    if kind == "expired": now[0]=3.0
    if kind == "revoked": service.revoke()
    if kind == "wrong_phase": service._phase="issued"
    with pytest.raises(ModelDenied) as caught: service.prepare_operator(fixed_final_text(fixture.OUTPUT))
    if kind == "wrong_hash": service.final_failure_sha256="f"*64
    if kind == "extra_gateway": service.gateway_calls=3
    if kind == "response": service._response=b"{}"
    if kind == "operator_prepared": service.prepared_operator_releases=1
    if kind == "operator_released": service.confirmed_operator_releases=1
    with pytest.raises(ProtocolError):final_text_evidence(service,service._audit,caught.value,"3"*32,"4"*32)


def test_source_order_keeps_both_original_guards_and_positive_child():
    root=Path(__file__).resolve().parents[1]/"src/project_maya/windows_runtime"
    source=(root/"ModelBridgeRuntime.cs").read_text()
    assert source.index('if(!output.Equals(final["text"]))') < source.index('if(ModelFinalAdmission.Enabled)return RunFinalText')
    assert source.index('record["model_child_report_untrusted"]=report;') < source.index('if(ModelFinalAdmission.Enabled)return RunFinalText')
    branch=source[source.index("uint RunFinalText("):source.index("internal void Stop()")]
    assert "publish(" not in branch and '"model_operator_delivered"' not in branch
    child=(root/"model_child_entry.py").read_text()
    negative=next(line for line in child.splitlines() if "negative =" in line)
    assert "final_text" not in negative

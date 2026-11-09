"""Original-guard differential tests; frozen AST only, no product entry point."""
import ast
import copy
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from project_maya.bridge import model_service
from project_maya.bridge.model_service import ModelDenied, OfflineModelBridge
from project_maya.bridge.model_final_text import (
    final_guard_evidence, final_text_evidence, fixed_final_text, validate_final_guard,
)
from project_maya.bridge.protocol import ProtocolError
import test_model_final_text_inert as fixture
import test_model_bridge_worker_inert as constants
import test_model_oversized_response_inert as service_fixture

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/".codex-build/maya-offline-model-final-20261104-1"
SOURCE="src/project_maya/bridge/model_service.py"
manifest=json.loads((BASE/"Maya-Offline-Model-Final-1/package-manifest.json").read_bytes())
frozen=(BASE/"source-freeze"/SOURCE).read_bytes()
assert hashlib.sha256(frozen).hexdigest()==next(i["sha256"] for i in manifest["source_files"] if i["path"]==SOURCE)
tree=ast.parse(frozen)
klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="OfflineModelBridge")
reference={}
for name in ("_live","issue"):
    node=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name==name)
    env=dict(ModelDenied=ModelDenied,secrets=model_service.secrets,ROUTE=model_service.ROUTE,digest=model_service.digest)
    exec(compile(ast.Module(body=[node],type_ignores=[]),"<frozen-inert-guard>","exec"),env)
    reference[name]=env[name]


class State:
    def __init__(self,kind="normal",sample=1.0):
        import threading
        self.trace=[]
        self.kind=kind
        self.sample=sample
        self._closed=kind=="closed"
        self._revoked=kind=="revoked"
        self._phase="issued" if kind=="phase" else "runtime_delivered"
        self._expires=2.0
        self.dispatch_attempted=True
        self.final_diagnostics_enabled=True
        self._final_issue_sample=0.0
        self._final_guard=None
        self._lock=threading.Lock()
        self._expected=b"{}"
        self.binding=model_service.HostBinding(constants.SID,constants.ATTEMPT,constants.CHANNEL)
        state=self
        class Audit:
            @property
            def failed(self):
                state.trace.append("audit.failed")
                if state.kind=="audit_error":
                    raise OSError("private diagnostic fixture")
                return state.kind=="audit"
        self._audit=Audit()
    def _clock(self):
        self.trace.append("clock.call")
        if self.kind=="clock_error":
            raise OSError("private clock fixture")
        return self.sample
    def __getattribute__(self,key):
        if key in ("_closed","_audit","_revoked","_phase","_clock","_expires","dispatch_attempted"):
            object.__getattribute__(self,"trace").append(key)
            if (object.__getattribute__(self,"kind"),key) in (
                    ("closed_error","_closed"),("revoked_error","_revoked"),("phase_error","_phase")):
                raise OSError("private state fixture")
        return object.__getattribute__(self,key)


def outcome(fn,state):
    try:
        fn(state,"runtime_delivered")
        return ("allowed",None)
    except Exception as error:
        return (type(error),getattr(error,"uncertain",None))


@pytest.mark.parametrize("kind,sample",[
    ("normal",0.0),("normal",1.999),("normal",2.0),("normal",2.001),("normal",50.0),
    ("normal",float("nan")),("normal",float("inf")),("normal",None),
    ("closed",1.0),("audit",1.0),("revoked",1.0),("phase",1.0),
    ("audit_error",1.0),("clock_error",1.0),("closed_error",1.0),("revoked_error",1.0),("phase_error",1.0),("normal",True)])
def test_original_decision_short_circuit_and_clock_count(kind,sample):
    before=State(kind,sample)
    after=State(kind,sample)
    assert outcome(reference["_live"],before)==outcome(OfflineModelBridge._live,after)
    assert after.trace==before.trace
    guard=dict(after._final_guard,schema="maya.model.final_guard.v1",attempt="a"*32,
        runtime_delivery_command_id="3"*32,final_command_id="4"*32)
    allowed=validate_final_guard(guard,"a"*32,"3"*32,"4"*32)
    assert allowed==(kind=="normal" and type(sample) in (float,int) and 0 <= sample < 2)
    if kind in ("closed","audit","revoked","phase","audit_error","closed_error","revoked_error","phase_error"):
        assert guard["clock_called"] is False
        assert guard["clock_returned"] is False
        assert guard["elapsed_ms"] is guard["remaining_ms"] is None
    if kind=="clock_error":
        assert guard["cause"]=="clock_exception" and guard["decision"]=="raised"


def test_issue_uses_original_single_clock_sample():
    before=State(sample=12.0)
    after=State(sample=12.0)
    before._phase=after._phase="new"
    with patch.object(model_service.secrets,"token_hex",return_value="f"*64):
        original=reference["issue"](before)
        observed=OfflineModelBridge.issue(after)
    assert original==observed and before._expires==after._expires==14.0
    assert before.trace==after.trace
    assert after._final_issue_sample==12.0


@pytest.mark.parametrize("expired",[False,True])
def test_actual_delivery_then_text_or_expiry_cannot_be_confused(expired,monkeypatch):
    monkeypatch.setattr("project_maya.bridge.audit.os.fsync",lambda _:None)
    now=[0.0]
    from project_maya.bridge.audit import RequiredAudit
    from project_maya.bridge.service import HostBinding
    from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
    gateway=PolicyAuthorizationGateway(tuple(PolicyRule(**r) for r in constants.policy()["allow"]))
    service=OfflineModelBridge(HostBinding(constants.SID,constants.ATTEMPT,constants.CHANNEL),
        gateway,RequiredAudit(fixture.Stream()),constants.expected_request(),constants.OUTPUT,lambda:now[0])
    service.final_diagnostics_enabled=True
    grant=service.issue()
    request=dict(v=1,type="model_request",attempt=constants.ATTEMPT,route=model_service.ROUTE,
        lease=grant["lease"],seq=1,method="POST",path=model_service.PATH,body=constants.expected_request().decode())
    reply=service.prepare_runtime(request,constants.CHANNEL)
    now[0]=3.0 if expired else 1.0
    service.confirm_runtime_delivery(reply["response_sha256"],"3"*32)
    with pytest.raises(ModelDenied) as caught:
        service.prepare_operator(fixed_final_text(constants.OUTPUT))
    guard=final_guard_evidence(service,caught.value,"3"*32,"4"*32)
    assert guard["cause"]==("expired" if expired else "allowed")
    assert service.confirmed_runtime_releases==service.dispatches==1
    assert service.confirmed_operator_releases==service.prepared_operator_releases==0
    assert caught.value.uncertain is True
    if expired:
        assert guard["at_or_after_deadline"] is True
        with pytest.raises(ProtocolError):final_text_evidence(service,service._audit,caught.value,"3"*32,"4"*32)
    else:
        assert final_text_evidence(service,service._audit,caught.value,"3"*32,"4"*32)["case"]=="M08"


def test_guard_observer_failure_cannot_change_original_outcome(monkeypatch):
    def fail(*args):
        raise OSError("private observer fixture")
    monkeypatch.setattr(model_service,"observe_guard",fail)
    for sample in (1.0,3.0):
        before,after=State(sample=sample),State(sample=sample)
        assert outcome(reference["_live"],before)==outcome(OfflineModelBridge._live,after)
        assert after.trace==before.trace
        assert after._final_guard is None


def test_worker_exports_expiry_diagnostic_without_m08_success(monkeypatch):
    now=[0.0]
    original=OfflineModelBridge
    def construct(*args,**kwargs):
        return original(*args,**kwargs,clock=lambda:now[0])
    monkeypatch.setattr("project_maya.bridge.model_worker.OfflineModelBridge",construct)
    def change(message):
        if message["type"]=="model_prepare_final":
            now[0]=3.0
        return message
    effects,raw,peer=fixture.worker_fixture(change)
    assert effects==dict(diagnostic_only=True)
    reply=peer.sent[-1]
    assert reply["type"]=="model_final_observed" and reply["effects"] is None
    guard=reply["guard"]
    assert guard["cause"]=="expired" and guard["at_or_after_deadline"] is True
    assert guard["elapsed_ms"]==3000 and guard["remaining_ms"]==-1000
    assert validate_final_guard(guard,constants.ATTEMPT,guard["runtime_delivery_command_id"],guard["final_command_id"]) is False
    records=[json.loads(line) for line in raw.splitlines()]
    assert records[3]["event_type"]=="model_bridge.runtime_delivery"
    assert records[4]["metadata"]["destination"]=="runtime:"+constants.ATTEMPT
    with pytest.raises(ProtocolError):fixture.verify(raw,peer)


def test_guard_fields_types_binding_and_bounds():
    _,_,peer=fixture.worker_fixture()
    guard=peer.sent[-1]["guard"]
    ids=(constants.ATTEMPT,guard["runtime_delivery_command_id"],guard["final_command_id"])
    assert validate_final_guard(guard,*ids)
    for key in guard:
        for mode in ("missing","type"):
            changed=copy.deepcopy(guard)
            if mode=="missing":del changed[key]
            else:changed[key]=["untrusted"]
            with pytest.raises(ProtocolError):validate_final_guard(changed,*ids)
    for key,value in (("ttl_ms",3000),("elapsed_ms",-1),("elapsed_ms",2147483648),
            ("remaining_ms",-2147483648),("cause","expired"),("decision","rejected"),
            ("attempt","f"*32),("phase","operator_admitted"),("clock_called",False)):
        changed=dict(guard,**{key:value})
        with pytest.raises(ProtocolError):validate_final_guard(changed,*ids)
    with pytest.raises(ProtocolError):validate_final_guard(dict(guard,extra=True),*ids)


def test_original_m08_success_and_audit_helpers_are_unchanged():
    path="src/project_maya/bridge/model_final_text.py"
    old=ast.parse((BASE/"source-freeze"/path).read_bytes())
    new=ast.parse((ROOT/path).read_bytes())
    for name in ("fixed_final_text","final_text_evidence","verify_final_audit"):
        get=lambda tree:next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        assert ast.dump(get(old),include_attributes=False)==ast.dump(get(new),include_attributes=False)

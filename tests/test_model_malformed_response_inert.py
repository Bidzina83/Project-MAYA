"""M07a in-memory fixtures; never execute Hermes, bundled runtime or native product."""
import ast
import copy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import httpx

from project_maya.bridge.audit import RequiredAudit
from project_maya.bridge.model_service import OfflineModelBridge,SyntheticModel,ModelDenied,TARGET,ORIGIN,PATH,PUBLIC_KEY,digest
from project_maya.bridge.model_malformed_response import MalformedJSONBridge,MalformedJSONProvider,FAULT_BYTES,malformed_response_evidence,verify_malformed_audit
from project_maya.bridge.model_output_denial import expected_runtime_response
from project_maya.bridge.model_worker import serve_model
from project_maya.bridge.protocol import ProtocolError,encode
from project_maya.bridge.service import HostBinding
from project_maya.bridge.transport import PrivateChannel
from project_maya.governance import PolicyAuthorizationGateway,PolicyRule
from project_maya.hermes_plugins.model_bridge import MalformedResponseChannelClient,PipeModelTransport
from test_model_bridge_worker_inert import ATTEMPT,CHANNEL,CANARY,SID,OUTPUT,LITERALS,policy,CoordinatorFixture,expected_request


class Stream(io.BytesIO):
    def fileno(self):return 123


def worker_fixture(modify=lambda m:m,rules=None,modes=None,fault=None,reached=None,peer=None,retained=None):
    peer=peer or CoordinatorFixture();peer.modify=modify
    class AuditStream(Stream):
        def write(self,data):
            if fault==("write",self.getvalue().count(b"\n")):
                if reached is not None:reached.append(fault)
                raise OSError()
            return super().write(data)
        def flush(self):
            if fault==("flush",self.getvalue().count(b"\n")-1):
                if reached is not None:reached.append(fault)
                raise OSError()
    raw=AuditStream()
    if retained is not None:retained.extend((raw,peer))
    config=dict(operator_sid=SID,attempt=ATTEMPT,channel_id=CHANNEL,utc_day="2026-10-24",canary=CANARY,fixture_text=OUTPUT)
    with patch("project_maya.bridge.audit.os.fsync"):
        result=serve_model(peer,config,policy() if rules is None else rules,LITERALS.read_bytes(),RequiredAudit(raw),peer.write_expected,
                           **(dict(malformed_response=True) if modes is None else modes))
    return result,raw.getvalue(),peer


class MalformedTests(unittest.TestCase):
    def setUp(self):
        sync=patch("project_maya.bridge.audit.os.fsync");sync.start();self.addCleanup(sync.stop)

    def service(self,kind=MalformedJSONBridge,rules=None,clock=lambda:0.0,stream=None):
        raw=stream if stream is not None else Stream()
        gateway=PolicyAuthorizationGateway(tuple(PolicyRule(**r) for r in (policy()["allow"] if rules is None else rules)))
        s=kind(HostBinding(SID,ATTEMPT,CHANNEL),gateway,RequiredAudit(raw),expected_request(),OUTPUT,clock)
        grant=s.issue()
        request=dict(v=1,type="model_request",attempt=ATTEMPT,route="maya.offline.model.v1",lease=grant["lease"],seq=1,method="POST",path=PATH,body=expected_request().decode())
        return s,raw,request

    def verify(self,raw,peer):
        return verify_malformed_audit(raw,HostBinding(SID,ATTEMPT,CHANNEL),peer.sent[0]["service_request_id"],peer.expected,OUTPUT)

    def test_fixed_factory_original_guard_and_canonical_expected_bytes(self):
        s,raw,request=self.service()
        self.assertIs(type(s._provider),MalformedJSONProvider)
        self.assertIs(MalformedJSONProvider.wire_reply,SyntheticModel.wire_reply)
        self.assertEqual(s._expected_response,expected_runtime_response(OUTPUT))
        with self.assertRaises(ModelDenied) as caught:s.prepare_runtime(request,CHANNEL)
        e=malformed_response_evidence(s,s._audit,caught.exception)
        self.assertEqual(len(e),25);self.assertEqual(e["observed_response_sha256"],digest(b"{"))
        self.assertEqual(e["observed_response_bytes"],1);self.assertEqual(e["gateway_calls"],1)
        self.assertEqual(e["dispatches"],1);self.assertTrue(e["uncertain"])
        self.assertIsNone(s._response);self.assertEqual(s._expected_response,expected_runtime_response(OUTPUT))
        self.assertEqual(s._phase,"admitted");self.assertFalse(s.runtime_output_gateway_denied)
        self.assertEqual([json.loads(l)["event_type"] for l in raw.getvalue().splitlines()],["model_bridge.egress_intent","model_bridge.denied"])
        with self.assertRaises(ModelDenied):s._provider.dispatch()
        self.assertEqual(s.dispatches,1)

    def test_default_factory_and_both_policy_positive_reference_unchanged(self):
        s,raw,request=self.service(OfflineModelBridge)
        self.assertIs(type(s._provider),SyntheticModel)
        reply=s.prepare_runtime(request,CHANNEL)
        self.assertEqual(reply["body"].encode(),expected_runtime_response(OUTPUT))
        self.assertEqual((s.gateway_calls,s.dispatches,s.prepared_runtime_releases),(2,1,1))
        self.assertEqual((s.response_failure_stage,s.response_failure_sha256,s.response_failure_bytes),("","",0))
        with self.assertRaises(ProtocolError):malformed_response_evidence(s,s._audit,ModelDenied(True))

    def test_worker_exact_two_records_no_fault_or_normal_response_release(self):
        e,raw,peer=worker_fixture()
        self.assertEqual(self.verify(raw,peer),2);self.assertEqual(e["case"],"M07a")
        self.assertEqual(peer.index,2)
        self.assertEqual([m["type"] for m in peer.sent],["model_worker_ready","model_grant_reply","model_response_json_rejected"])
        self.assertNotIn('"body"',json.dumps(peer.sent[-1]));self.assertNotIn('"lease"',json.dumps(peer.sent[-1]))
        self.assertNotIn(OUTPUT,json.dumps(peer.sent));self.assertNotIn(OUTPUT,raw.decode())
        records=[json.loads(l) for l in raw.splitlines()]
        self.assertEqual([r["metadata"]["dispatches"] for r in records],["0","1"])
        self.assertTrue(all(r["metadata"]["response_sha256"]=="" and r["metadata"]["response_bytes"]=="0" for r in records))
        self.assertTrue(all(r["metadata"]["destination"]=="provider" for r in records))

    def test_bad_policies_and_conflicting_modes_block(self):
        for rules in ({"allow":[]},{"allow":policy()["allow"][:1]},{"allow":policy()["allow"][1:]}):
            with self.subTest(rules=rules),self.assertRaises(ProtocolError):worker_fixture(rules=rules)
        for mode in (dict(malformed_response=1),dict(malformed_response=True,deny_runtime_output=True),
                     dict(malformed_response=True,deny_egress=True),dict(malformed_response=True,recreated_client_budget=True)):
            with self.subTest(mode=mode),self.assertRaises(ProtocolError):worker_fixture(modes=mode)

    def test_wrong_fault_bytes_types_and_provider_throw_cannot_pass(self):
        for value in (b"]",b"{}",b" "*4097,"{",None,OSError()):
            def dispatch(provider):
                SyntheticModel.dispatch(provider)
                if isinstance(value,Exception):raise value
                return value
            with self.subTest(value=type(value).__name__):
                s,raw,request=self.service()
                # Inert fault control only, never installed into bundled/runtime product execution.
                with patch.object(MalformedJSONProvider,"dispatch",dispatch):
                    with self.assertRaises(ModelDenied) as caught:s.prepare_runtime(request,CHANNEL)
                self.assertTrue(caught.exception.uncertain);self.assertEqual(s.dispatches,1)
                with self.assertRaises(ProtocolError):malformed_response_evidence(s,s._audit,caught.exception)

    def test_failed_request_egress_and_expiry_cannot_claim_response_rejection(self):
        for kind in ("request","egress","expiry"):
            now=[0.0];s,raw,request=self.service(rules=[] if kind=="egress" else None,clock=lambda:now[0])
            if kind=="request":request["body"]="{}"
            if kind=="expiry":now[0]=3.0
            with self.subTest(kind=kind):
                with self.assertRaises(ModelDenied) as caught:s.prepare_runtime(request,CHANNEL)
                self.assertEqual(s.dispatches,0);self.assertEqual(s.response_failure_stage,"")
                with self.assertRaises(ProtocolError):malformed_response_evidence(s,s._audit,caught.exception)

    def test_forged_snapshot_fields_and_uncertainty_reject(self):
        s,raw,request=self.service()
        with self.assertRaises(ModelDenied) as caught:s.prepare_runtime(request,CHANNEL)
        for key,value in (("response_failure_stage","other"),("response_failure_sha256","0"*64),("response_failure_bytes",2),
                          ("_response",b"{}"),("gateway_calls",2),("_phase","dispatched"),("_destination","operator"),
                          ("prepared_runtime_releases",1),("confirmed_runtime_releases",1),("prepared_operator_releases",1),
                          ("confirmed_operator_releases",1),("egress_gateway_denied",True),("runtime_output_gateway_denied",True)):
            old=getattr(s,key);setattr(s,key,value)
            with self.subTest(key=key),self.assertRaises(ProtocolError):malformed_response_evidence(s,s._audit,caught.exception)
            setattr(s,key,old)
        with self.assertRaises(ProtocolError):malformed_response_evidence(s,s._audit,ModelDenied(False))

    def test_denial_control_exact_case_and_reason_no_receipt(self):
        control=dict(v=1,type="model_denied",attempt=ATTEMPT,seq=1,case="M07a",reason="response_json_rejected")
        for change in ({},{"case":"M06"},{"reason":"gateway_runtime_output_denied"},{"attempt":"f"*32},{"seq":True},{"extra":0}):
            with self.subTest(change=change):
                out=io.BytesIO();c=MalformedResponseChannelClient(PrivateChannel(io.BytesIO(encode(dict(control,**change))),out),ATTEMPT)
                c.bind_grant(dict(v=1,type="model_grant",attempt=ATTEMPT,route="maya.offline.model.v1",lease="e"*64,seq=1,ttl_ms=2000,request_sha256=digest(expected_request())))
                with httpx.Client(transport=PipeModelTransport(c),trust_env=False) as http:
                    with self.assertRaises(httpx.TransportError):http.post(ORIGIN+PATH,content=expected_request(),headers={"authorization":"Bearer "+PUBLIC_KEY,"content-type":"application/json"})
                self.assertEqual(c.denial_observed,not bool(change));self.assertEqual(c.requests,1)
                self.assertNotIn(b'model_runtime_receipt',out.getvalue())

    def test_audit_all_fields_count_and_schedule(self):
        _,raw,peer=worker_fixture();records=[json.loads(l) for l in raw.splitlines()]
        for i,r in enumerate(records):
            for key in r:
                changed=copy.deepcopy(records);changed[i][key]="wrong"
                with self.subTest(index=i,key=key),self.assertRaises(ProtocolError):self.verify(("\n".join(json.dumps(x) for x in changed)+"\n").encode(),peer)
            for key in r["metadata"]:
                changed=copy.deepcopy(records);changed[i]["metadata"][key]="wrong"
                with self.subTest(index=i,meta=key),self.assertRaises(ProtocolError):self.verify(("\n".join(json.dumps(x) for x in changed)+"\n").encode(),peer)
        lines=raw.splitlines(keepends=True)
        for changed in (lines[0],raw+lines[-1],b"".join(reversed(lines)),raw[:-1]):
            with self.assertRaises(ProtocolError):self.verify(changed,peer)

    def test_audit_faults_never_pass_and_preserve_dispatch_counts(self):
        for i in range(2):
            for kind in ("write","flush"):
                reached=[];retained=[]
                with self.subTest(index=i,kind=kind),self.assertRaises(ProtocolError):worker_fixture(fault=(kind,i),reached=reached,retained=retained)
                self.assertEqual(reached,[(kind,i)])
                if i==1:
                    first=json.loads(retained[0].getvalue().splitlines()[0]);self.assertEqual(first["metadata"]["dispatches"],"0")

    def test_control_send_fault_preserves_original_two_records(self):
        class Peer(CoordinatorFixture):
            def send(self,m):
                if m["type"]=="model_response_json_rejected":raise OSError()
                super().send(m)
        retained=[]
        with self.assertRaises(OSError):worker_fixture(peer=Peer(),retained=retained)
        self.assertEqual(self.verify(retained[0].getvalue(),retained[1]),2)

    def test_fixed_source_order_and_no_live_provider_assignment_in_worker(self):
        root=Path(__file__).resolve().parents[1]/"src/project_maya"
        worker=(root/"bridge/model_worker.py").read_text()
        self.assertNotIn("service._provider =",worker)
        source=(root/"windows_runtime/ModelBridgeRuntime.cs").read_text()
        branch=source[source.index("uint RunMalformed("):source.index("uint RunOutputDenial(")]
        for forbidden in ('"model_response"','"model_runtime_delivered"','"model_prepare_final"',"publish("):
            self.assertNotIn(forbidden,branch)
        for name in ("model_malformed_child_entry.py","model_malformed_worker_entry.py"):
            text=(root/"windows_runtime"/name).read_text();tree=ast.parse(text)
            self.assertIsInstance(tree.body[2],ast.If);self.assertIsInstance(tree.body[2].body[0],ast.Raise)
            self.assertIn("malformed_response=True",text)


if __name__=="__main__":unittest.main()

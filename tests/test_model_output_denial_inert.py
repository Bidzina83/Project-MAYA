"""M06 in-memory worker/service/transport fixtures. Never run Hermes or native product."""
import ast
import copy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import httpx

from project_maya.bridge.audit import RequiredAudit
from project_maya.bridge.model_service import OfflineModelBridge, SyntheticModel, ModelDenied, TARGET, digest, ORIGIN, PATH, PUBLIC_KEY
from project_maya.bridge.model_output_denial import expected_runtime_response, output_denial_evidence, verify_output_denial_audit
from project_maya.bridge.model_worker import serve_model
from project_maya.bridge.protocol import ProtocolError, encode
from project_maya.bridge.service import HostBinding
from project_maya.bridge.transport import PrivateChannel
from project_maya.governance import AuthorizationResult, GovernanceDecision, PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.model_bridge import RuntimeOutputDenialChannelClient, PipeModelTransport
from test_model_bridge_worker_inert import ATTEMPT, CHANNEL, SID, CANARY, OUTPUT, LITERALS, expected_request, policy, CoordinatorFixture


def worker_fixture(modify=lambda m:m, rules=None, fault=None, reached=None, modes=None):
    peer=CoordinatorFixture();peer.modify=modify;raw=io.BytesIO()
    class Stream:
        def write(self,data):
            if fault==("write",raw.getvalue().count(b"\n")):
                if reached is not None:reached.append(fault)
                raise OSError()
            return raw.write(data)
        def flush(self):
            if fault==("flush",raw.getvalue().count(b"\n")-1):
                if reached is not None:reached.append(fault)
                raise OSError()
        def fileno(self):return 123
    config=dict(operator_sid=SID,attempt=ATTEMPT,channel_id=CHANNEL,utc_day="2026-10-24",canary=CANARY,fixture_text=OUTPUT)
    if rules is None:rules={"allow":policy()["allow"][:1]}
    with patch("project_maya.bridge.audit.os.fsync"):
        result=serve_model(peer,config,rules,LITERALS.read_bytes(),RequiredAudit(Stream()),peer.write_expected,
                           **(dict(deny_runtime_output=True) if modes is None else modes))
    return result,raw.getvalue(),peer


class OutputDenialTests(unittest.TestCase):
    def setUp(self):
        sync=patch("project_maya.bridge.audit.os.fsync");sync.start();self.addCleanup(sync.stop)

    def service(self,gateway=None,clock=lambda:0.0):
        class Stream(io.BytesIO):
            def fileno(self):return 123
        raw=Stream()
        gateway=gateway or PolicyAuthorizationGateway((PolicyRule("model.egress",TARGET,"infer","windows:"+SID),))
        service=OfflineModelBridge(HostBinding(SID,ATTEMPT,CHANNEL),gateway,RequiredAudit(raw),expected_request(),OUTPUT,clock)
        grant=service.issue()
        request=dict(v=1,type="model_request",attempt=ATTEMPT,route="maya.offline.model.v1",lease=grant["lease"],
                     seq=1,method="POST",path=PATH,body=expected_request().decode())
        return service,raw,request

    def verify(self,raw,peer):
        return verify_output_denial_audit(raw,HostBinding(SID,ATTEMPT,CHANNEL),peer.sent[0]["service_request_id"],peer.expected,OUTPUT)

    def test_original_service_named_output_denial_preserves_dispatch_and_uncertainty(self):
        s,raw,request=self.service()
        with self.assertRaises(ModelDenied) as caught:s.prepare_runtime(request,CHANNEL)
        e=output_denial_evidence(s,s._audit,caught.exception)
        self.assertTrue(caught.exception.uncertain)
        self.assertEqual((e["dispatches"],e["confirmed_runtime_releases"],e["confirmed_operator_releases"]),(1,0,0))
        self.assertEqual(e["gateway_calls"],2)
        self.assertEqual(s._response,expected_runtime_response(OUTPUT))
        self.assertEqual([json.loads(l)["event_type"] for l in raw.getvalue().splitlines()],
                         ["model_bridge.egress_intent","model_bridge.dispatch_outcome","model_bridge.denied"])
        self.assertTrue(s.closed)

    def test_fixed_worker_three_records_no_response_body_release(self):
        result,raw,peer=worker_fixture()
        self.assertEqual(result["case"],"M06");self.assertTrue(result["uncertain"])
        self.assertEqual(self.verify(raw,peer),3)
        self.assertEqual([m["type"] for m in peer.sent],["model_worker_ready","model_grant_reply","model_runtime_output_denied"])
        self.assertEqual(peer.index,2)
        self.assertNotIn(OUTPUT,json.dumps(peer.sent));self.assertNotIn('"body"',json.dumps(peer.sent[-1]))
        self.assertNotIn('"lease"',json.dumps(peer.sent[-1]))
        self.assertNotIn(OUTPUT,raw.decode())
        response=expected_runtime_response(OUTPUT)
        self.assertEqual(result["response_sha256"],digest(response));self.assertEqual(result["response_bytes"],len(response))

    def test_response_oracle_matches_fixture_and_rejects_arbitrary_text(self):
        for digit in "0123456789abcdef":
            with self.subTest(digit=digit):
                text="MAYA_OFFLINE_MODEL_OK:"+digit*32
                self.assertEqual(expected_runtime_response(text),SyntheticModel(text).wire_reply())
        for text in (None,"",OUTPUT+"\n",OUTPUT.upper(),"customer text",'"'+OUTPUT,OUTPUT[:-1]):
            with self.subTest(text=text),self.assertRaises(ProtocolError):expected_runtime_response(text)

    def test_both_rules_positive_reference_still_releases_normally(self):
        result,raw,peer=worker_fixture(rules=policy(),modes={})
        self.assertEqual(result["dispatches"],1);self.assertEqual(result["confirmed_runtime_releases"],1)
        self.assertEqual(result["confirmed_operator_releases"],1)
        self.assertEqual(len(raw.splitlines()),6)
        with self.assertRaises(ProtocolError):self.verify(raw,peer)

    def test_exact_policy_rejects_egress_absent_extra_output_and_wrong_binding(self):
        for rules in ({"allow":[]},policy(),{"allow":policy()["allow"][1:]}):
            with self.subTest(rules=rules),self.assertRaises(ProtocolError):worker_fixture(rules=rules)
        for key in ("actor_id","target","operation","capability"):
            rules={"allow":copy.deepcopy(policy()["allow"][:1])};rules["allow"][0][key]="wrong"
            with self.subTest(key=key),self.assertRaises(ProtocolError):worker_fixture(rules=rules)

    def test_conflicting_and_nonbool_modes_reject_before_readiness(self):
        for mode in (dict(deny_runtime_output=1),dict(deny_runtime_output=True,deny_egress=True),
                     dict(deny_runtime_output=True,wrong_model=True),dict(deny_runtime_output=True,recreated_client_budget=True)):
            with self.subTest(mode=mode),self.assertRaises(ProtocolError):worker_fixture(modes=mode)

    def test_bad_native_request_cannot_pass_as_output_denial(self):
        for change in ({"body":"{}"},{"attempt":"f"*32},{"route":"wrong"},{"seq":True}):
            def mutate(m):
                if m["type"]=="model_dispatch":m=dict(m,request=dict(m["request"],**change))
                return m
            with self.subTest(change=change),self.assertRaises(ProtocolError):worker_fixture(modify=mutate)

    def test_generic_gateway_failure_and_nonexact_denials_cannot_pass(self):
        bad=[None,AuthorizationResult(GovernanceDecision.DENY,"other"),
             AuthorizationResult(GovernanceDecision.DENY,"governance.no_matching_rule",constraints=("x",)),
             AuthorizationResult(GovernanceDecision.DENY,"governance.no_matching_rule",redactions={"x":"y"}),
             AuthorizationResult(GovernanceDecision.REDACT,"governance.no_matching_rule"),OSError()]
        for result in bad:
            class Gateway:
                def authorize(self,request):
                    if request.capability=="model.egress":return AuthorizationResult(GovernanceDecision.ALLOW,"inert")
                    if isinstance(result,Exception):raise result
                    return result
            with self.subTest(result=type(result).__name__):
                s,raw,request=self.service(Gateway())
                with self.assertRaises(ModelDenied) as caught:s.prepare_runtime(request,CHANNEL)
                self.assertFalse(s.runtime_output_gateway_denied)
                self.assertTrue(caught.exception.uncertain);self.assertEqual(s.dispatches,1)
                with self.assertRaises(ProtocolError):output_denial_evidence(s,s._audit,caught.exception)

    def test_wrong_destination_or_phase_cannot_set_named_observation(self):
        for destination,phase in (("operator","dispatched"),("runtime:"+"f"*32,"dispatched"),("runtime:"+ATTEMPT,"issued")):
            s,raw,request=self.service();s._phase=phase
            with self.assertRaises(ModelDenied):s._authorize("model.output",destination)
            self.assertFalse(s.runtime_output_gateway_denied)

    def test_expiry_and_egress_deny_are_not_output_denial(self):
        clock=[0.0];s,raw,request=self.service(clock=lambda:clock[0]);clock[0]=3.0
        with self.assertRaises(ModelDenied) as caught:s.prepare_runtime(request,CHANNEL)
        self.assertFalse(s.runtime_output_gateway_denied);self.assertEqual(s.dispatches,0)
        with self.assertRaises(ProtocolError):output_denial_evidence(s,s._audit,caught.exception)
        s,raw,request=self.service(PolicyAuthorizationGateway(()))
        with self.assertRaises(ModelDenied) as caught:s.prepare_runtime(request,CHANNEL)
        self.assertTrue(s.egress_gateway_denied);self.assertFalse(s.runtime_output_gateway_denied)
        with self.assertRaises(ProtocolError):output_denial_evidence(s,s._audit,caught.exception)

    def test_response_validation_fault_cannot_claim_named_output_boundary(self):
        # Explicit inert fixture peer fault, not native provider substitution.
        class InvalidProvider:
            text=OUTPUT
            dispatches=0
            def dispatch(self):self.dispatches+=1;return b'{}'
        s,raw,request=self.service();s._provider=InvalidProvider()
        with self.assertRaises(ModelDenied) as caught:s.prepare_runtime(request,CHANNEL)
        self.assertTrue(caught.exception.uncertain);self.assertFalse(s.runtime_output_gateway_denied)
        with self.assertRaises(ProtocolError):output_denial_evidence(s,s._audit,caught.exception)

    def test_exact_control_observation_never_yields_model_response_or_receipt(self):
        control=dict(v=1,type="model_denied",attempt=ATTEMPT,seq=1,case="M06",reason="gateway_runtime_output_denied")
        for change in ({},{"case":"M02"},{"reason":"other"},{"attempt":"f"*32},{"seq":True},{"extra":True}):
            with self.subTest(change=change):
                out=io.BytesIO();c=RuntimeOutputDenialChannelClient(PrivateChannel(io.BytesIO(encode(dict(control,**change))),out),ATTEMPT)
                c.bind_grant(dict(v=1,type="model_grant",attempt=ATTEMPT,route="maya.offline.model.v1",lease="e"*64,
                    seq=1,ttl_ms=2000,request_sha256=digest(expected_request())))
                client=httpx.Client(transport=PipeModelTransport(c),trust_env=False,follow_redirects=False)
                try:
                    with self.assertRaises(httpx.TransportError):client.post(ORIGIN+PATH,content=expected_request(),headers={"authorization":"Bearer "+PUBLIC_KEY,"content-type":"application/json"})
                    self.assertEqual(c.denial_observed,not bool(change));self.assertEqual(c.requests,1)
                    self.assertEqual(out.getvalue().count(b'"type":"model_request"'),1)
                    self.assertNotIn(b'model_runtime_receipt',out.getvalue())
                finally:client.close()

    def test_audit_every_record_and_metadata_field_mutation_rejects(self):
        _,raw,peer=worker_fixture();records=[json.loads(l) for l in raw.splitlines()]
        for i,record in enumerate(records):
            for key in record:
                changed=copy.deepcopy(records);changed[i][key]="wrong"
                with self.subTest(index=i,key=key),self.assertRaises(ProtocolError):
                    self.verify(("\n".join(json.dumps(r) for r in changed)+"\n").encode(),peer)
            for key in record["metadata"]:
                changed=copy.deepcopy(records);changed[i]["metadata"][key]="wrong"
                with self.subTest(index=i,meta=key),self.assertRaises(ProtocolError):
                    self.verify(("\n".join(json.dumps(r) for r in changed)+"\n").encode(),peer)

    def test_audit_count_order_and_every_write_flush_fault_rejects(self):
        _,raw,peer=worker_fixture();lines=raw.splitlines(keepends=True)
        for changed in (b"".join(lines[:-1]),raw+lines[-1],b"".join(reversed(lines)),raw[:-1]):
            with self.assertRaises(ProtocolError):self.verify(changed,peer)
        for i in range(3):
            for kind in ("write","flush"):
                reached=[]
                with self.subTest(index=i,kind=kind),self.assertRaises(ProtocolError):
                    worker_fixture(fault=(kind,i),reached=reached)
                self.assertEqual(reached,[(kind,i)])

    def test_denial_control_write_failure_keeps_dispatch_and_ledger_truth(self):
        class Peer(CoordinatorFixture):
            def send(self,message):
                if message["type"]=="model_runtime_output_denied":raise OSError("inert broken pipe")
                super().send(message)
        class Stream(io.BytesIO):
            def fileno(self):return 123
        peer=Peer();raw=Stream()
        config=dict(operator_sid=SID,attempt=ATTEMPT,channel_id=CHANNEL,utc_day="2026-10-24",canary=CANARY,fixture_text=OUTPUT)
        with self.assertRaises(OSError):
            serve_model(peer,config,{"allow":policy()["allow"][:1]},LITERALS.read_bytes(),RequiredAudit(raw),peer.write_expected,deny_runtime_output=True)
        self.assertEqual(self.verify(raw.getvalue(),peer),3)
        self.assertEqual(peer.index,2)
        self.assertEqual(json.loads(raw.getvalue().splitlines()[-1])["metadata"]["dispatches"],"1")
        self.assertEqual([m["type"] for m in peer.sent],["model_worker_ready","model_grant_reply"])

    def test_required_audit_faults_preserve_actual_prior_dispatch_counts(self):
        for index in range(3):
            for kind in ("write","flush"):
                class Stream(io.BytesIO):
                    def write(self,data):
                        if kind=="write" and self.getvalue().count(b"\n")==index:raise OSError()
                        return super().write(data)
                    def flush(self):
                        if kind=="flush" and self.getvalue().count(b"\n")-1==index:raise OSError()
                    def fileno(self):return 123
                s,_,request=self.service();raw=Stream();s._audit=RequiredAudit(raw)
                with self.subTest(index=index,kind=kind):
                    with self.assertRaises(ModelDenied) as caught:s.prepare_runtime(request,CHANNEL)
                    self.assertEqual(s.dispatches,0 if index==0 else 1)
                    self.assertEqual(caught.exception.uncertain,index!=0)
                    self.assertTrue(s._audit.failed)
                    self.assertEqual(s.confirmed_runtime_releases,0)
                    with self.assertRaises(ProtocolError):output_denial_evidence(s,s._audit,caught.exception)

    def test_fixed_entry_guard_and_no_positive_release_branch(self):
        root=Path(__file__).resolve().parents[1]/"src/project_maya/windows_runtime"
        for name in ("model_output_deny_child_entry.py","model_output_deny_worker_entry.py"):
            source=(root/name).read_text();tree=ast.parse(source)
            self.assertIsInstance(tree.body[2],ast.If);self.assertIsInstance(tree.body[2].body[0],ast.Raise)
            self.assertIn("deny_runtime_output=True",source)
        source=(root/"ModelBridgeRuntime.cs").read_text();branch=source[source.index("uint RunOutputDenial("):source.index("uint RunDenial(")]
        for forbidden in ('"model_dispatch_reply"','"model_response"','"model_runtime_delivered"','"model_prepare_final"',"publish("):
            self.assertNotIn(forbidden,branch)
        self.assertLess(branch.index('record["model_synthetic_dispatches"]=1'),branch.index('childChannel.Write'))
        self.assertLess(branch.index('worker.WaitBridge'),branch.index('ModelOutputDenialAdmission.Audit'))


if __name__=="__main__":unittest.main()

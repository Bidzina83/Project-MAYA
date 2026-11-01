"""M05b inert factory/lifecycle controls. No Hermes/SDK or native product execution."""
import io
import ast
import copy
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

import httpx

from project_maya.bridge.model_service import ORIGIN, PATH, PUBLIC_KEY, MODEL, SyntheticModel, digest
from project_maya.bridge.protocol import ProtocolError, encode
from project_maya.bridge.transport import PrivateChannel
from project_maya.hermes_plugins.model_budget import BudgetChannelClient
from project_maya.hermes_plugins.model_recreate import RecreatedClientBudgetMixin, RecreatePipeTransport, successful_lifecycle
from test_model_bridge_worker_inert import ATTEMPT, OUTPUT, expected_request
from test_model_budget_lifecycle_inert import NativeShape
from test_model_adapter_budget_inert import BudgetCoordinator
from project_maya.bridge.audit import RequiredAudit
from project_maya.bridge.model_worker import serve_model
from project_maya.bridge.model_adapter_budget import verify_budget_audit
from project_maya.bridge.service import HostBinding
from test_model_bridge_worker_inert import SID, CHANNEL, CANARY, LITERALS, policy


class Agent(RecreatedClientBudgetMixin, NativeShape):
    def _stage(self, stage):
        super()._stage(stage)
        if hasattr(self, "events"):
            self.events.append(stage)


def fixture(control=None, cls=Agent):
    body = expected_request()
    response = SyntheticModel(OUTPUT).wire_reply()
    reply = dict(v=1, type="model_response", attempt=ATTEMPT, seq=1, status="ok",
        body=response.decode(), response_sha256=digest(response))
    probe = dict(v=1, type="model_adapter_probe", attempt=ATTEMPT, request_id="f"*32)
    output = io.BytesIO()
    channel = BudgetChannelClient(PrivateChannel(io.BytesIO(encode(reply)+encode(probe if control is None else control)), output), ATTEMPT)
    channel.bind_grant(dict(v=1, type="model_grant", attempt=ATTEMPT, route="maya.offline.model.v1",
        lease="e"*64, seq=1, ttl_ms=2000, request_sha256=digest(body)))
    agent = cls(maya_model_channel=channel, provider="custom", api_mode="chat_completions", model=MODEL,
        base_url=ORIGIN+"/v1", api_key=PUBLIC_KEY, fallback_model=None, credential_pool=None, max_tokens=32)
    return agent, channel, output


class RecreateTests(unittest.TestCase):
    def setup_agent(self, **kwargs):
        agent, channel, output = fixture(**kwargs)
        self.addCleanup(agent.close_model_clients)
        return agent, channel, output

    def failed(self, agent):
        with self.assertRaises(ProtocolError):
            agent.finish_budget_probe()
        self.assertNotEqual(agent.budget_lifecycle_snapshot()["failure_stage"], "")

    def test_positive_closes_old_then_recreates_same_consumed_adapter(self):
        a,c,out = self.setup_agent(); a.arm_budget_probe()
        self.assertEqual(a.run_native_shape(), dict(final_response=OUTPUT))
        self.assertEqual(a.budget_lifecycle_snapshot(), successful_lifecycle())
        p = a.finish_budget_probe()
        self.assertEqual(p, dict(case="M05b",boundary="adapter_consumed_budget",transport_attempts=2,
            model_requests=1,completed_exchanges=1,budget_rejections=1,distinct_new_clients=True,
            same_consumed_adapter=True,request_sha256=digest(expected_request()),request_bytes=len(expected_request())))
        self.assertEqual(a.budget_probe_command_id,"f"*32)
        self.assertEqual(len(a._maya_model_clients),3)
        old,new = a._maya_model_clients[1:]
        self.assertTrue(all(old[i] is not new[i] for i in range(3)))
        self.assertIs(old[2].channel, new[2].channel)
        self.assertIs(c, new[2].channel)
        self.assertTrue(old[1].is_closed and new[1].is_closed)
        self.assertEqual(len(a.close_calls),1)
        self.assertLess(a.events.index("native_close"),a.events.index("factory_recreation"))
        self.assertLess(a.events.index("second_request"),a.events.index("conversation_return"))
        self.assertEqual(out.getvalue().count(b'"type":"model_request"'),1)
        self.assertEqual(out.getvalue().count(b'"type":"model_runtime_receipt"'),1)
        self.assertEqual((c.requests,c.budget_rejections),(1,1))
        self.assertIsNone(c._grant)
        self.assertTrue(c._bound)

    def test_can_run_on_owner_thread_distinct_from_constructor(self):
        a,c,out=self.setup_agent();a.arm_budget_probe(); errors=[]
        def run():
            try:a.run_native_shape()
            except Exception as e:errors.append(type(e).__name__)
        t=threading.Thread(target=run);t.start();t.join(2)
        self.assertFalse(t.is_alive());self.assertEqual(errors,[])
        self.assertEqual(a.finish_budget_probe()["case"],"M05b")

    def test_bad_controls_fail_after_old_close_without_new_factory(self):
        control=dict(v=1,type="model_adapter_probe",attempt=ATTEMPT,request_id="f"*32)
        for mutation in ({"v":True},{"type":"model_begin"},{"attempt":"b"*32},{"request_id":"bad"},{"extra":0}):
            with self.subTest(mutation=mutation):
                a,c,out=self.setup_agent(control=dict(control,**mutation));a.arm_budget_probe()
                self.assertEqual(a.run_native_shape()["final_response"],OUTPUT)
                self.failed(a);self.assertEqual(len(a._maya_model_clients),2)
                self.assertTrue(a._maya_model_clients[1][1].is_closed)
                self.assertEqual((c.requests,c.budget_rejections),(1,0))

    def test_unarmed_wrong_reason_abort_and_duplicate_close(self):
        for mode in ("unarmed","reason","abort","duplicate"):
            with self.subTest(mode=mode):
                a,c,out=self.setup_agent()
                if mode!="unarmed":a.arm_budget_probe()
                during=(lambda a,c:a._abort_request_openai_client(c,reason="stale")) if mode=="abort" else None
                a.run_native_shape(reason="interrupted" if mode=="reason" else "request_complete",during=during)
                if mode=="duplicate":
                    before=out.getvalue()
                    a._close_request_openai_client(a._maya_model_clients[1][0],reason="request_complete")
                    self.assertEqual(before,out.getvalue())
                self.failed(a)

    def test_old_close_failure_never_recreates_or_claims_budget_rejection(self):
        for fault in ("raise","swallow"):
            with self.subTest(fault=fault):
                a,c,out=self.setup_agent();a.arm_budget_probe();a.close_fault=fault
                a.run_native_shape();self.failed(a)
                self.assertEqual(len(a.close_calls),1)
                self.assertEqual(len(a._maya_model_clients),2)
                self.assertEqual(c.budget_rejections,0)

    def test_shared_shutdown_and_premature_old_close_do_not_pass(self):
        for action in (lambda a,c:a.close_model_clients(),lambda a,c:c.close()):
            a,c,out=self.setup_agent();a.arm_budget_probe()
            a.run_native_shape(during=action);self.failed(a)
            self.assertEqual(len(a._maya_model_clients),2)
            self.assertEqual(c.budget_rejections,0)

    def test_wrong_owner_and_wrong_used_sdk_do_not_pass(self):
        for mode in ("owner","sdk"):
            a,c,out=self.setup_agent();a.arm_budget_probe()
            def during(a,sdk):
                target=a.client if mode=="sdk" else sdk
                if mode=="owner":
                    t=threading.Thread(target=lambda:a._close_request_openai_client(target,reason="request_complete"))
                    t.start();t.join(2);self.assertFalse(t.is_alive())
                else:a._close_request_openai_client(target,reason="request_complete")
            a.run_native_shape(during=during);self.failed(a)
            self.assertEqual(c.budget_rejections,0)

    def test_factory_failure_and_client_cap_preserve_first_exchange(self):
        for mode in ("fault","cap"):
            class BadFactory(Agent):
                def _create_openai_client(self,kwargs,*,reason,shared):
                    if self._recreate_expected is not None and mode=="fault":raise OSError()
                    return super()._create_openai_client(kwargs,reason=reason,shared=shared)
            a,c,out=self.setup_agent(cls=BadFactory);a.arm_budget_probe()
            def during(a,sdk):
                if mode=="cap":
                    for _ in range(6):a._create_openai_client(a.kwargs,reason="inert_cap",shared=False)
            a.run_native_shape(during=during);self.failed(a)
            self.assertEqual((c.requests,c.budget_rejections),(1,0))
            self.assertEqual(out.getvalue().count(b'"type":"model_request"'),1)

    def test_new_closed_client_changed_snapshot_and_alternate_adapter_reject(self):
        for mode in ("closed","snapshot","adapter","reuse"):
            class BadFactory(Agent):
                def _create_openai_client(self,kwargs,*,reason,shared):
                    result=super()._create_openai_client(kwargs,reason=reason,shared=shared)
                    if self._recreate_expected is not None:
                        sdk,http,t=self._maya_model_clients[-1]
                        if mode=="closed":result.close()
                        if mode=="snapshot":t.expected=("GET",)+t.expected[1:]
                        if mode=="adapter":t.channel=BudgetChannelClient(PrivateChannel(io.BytesIO(),io.BytesIO()),ATTEMPT)
                        if mode=="reuse":self._maya_model_clients[-1]=self._maya_model_clients[1]
                    return result
            a,c,out=self.setup_agent(cls=BadFactory);a.arm_budget_probe();a.run_native_shape();self.failed(a)
            self.assertEqual(c.budget_rejections,0)
            self.assertEqual(out.getvalue().count(b'"type":"model_request"'),1)

    def test_new_close_failure_blocks_even_after_local_rejection(self):
        class CloseFault(Agent):
            def _create_openai_client(self,kwargs,*,reason,shared):
                sdk=super()._create_openai_client(kwargs,reason=reason,shared=shared)
                if self._recreate_expected is not None:
                    def fail():raise OSError()
                    sdk.close=fail
                return sdk
        a,c,out=fixture(cls=CloseFault);a.arm_budget_probe();a.run_native_shape();self.failed(a)
        self.assertEqual(c.budget_rejections,1)
        # Deliberately broken SDK close is a failing control, not silently ignored cleanup.
        with self.assertRaises(ProtocolError):a.close_model_clients()
        self.assertTrue(all(http.is_closed for _,http,_ in a._maya_model_clients))

    def test_snapshots_do_not_rearm_and_bind_cannot_reset(self):
        a,c,out=self.setup_agent();a.arm_budget_probe();a.run_native_shape()
        snapshot=a.budget_lifecycle_snapshot();snapshot["hook_calls"]=0
        self.assertEqual(a.budget_lifecycle_snapshot()["hook_calls"],1)
        with self.assertRaises(ProtocolError):a.arm_budget_probe()
        before=out.getvalue()
        with self.assertRaises(ProtocolError):c.bind_grant({})
        self.assertEqual(out.getvalue(),before)

    def test_abort_at_control_read_does_not_hold_lock_or_recreate(self):
        a,c,out=self.setup_agent();a.arm_budget_probe()
        data=c.channel._source.getvalue()
        boundary=data.index(encode(dict(v=1,type="model_adapter_probe",attempt=ATTEMPT,request_id="f"*32)))
        class Source(io.BytesIO):
            fired=False
            def read(self,size=-1):
                if self.tell()==boundary and not self.fired:
                    self.fired=True
                    t=threading.Thread(target=lambda:a._abort_request_openai_client(a._maya_model_clients[1][0],reason="stale"))
                    t.start();t.join(2)
                    if t.is_alive():raise RuntimeError("inert lock deadlock")
                return super().read(size)
        c.channel._source=Source(data)
        a.run_native_shape();self.failed(a)
        self.assertEqual(a.budget_lifecycle_snapshot()["failure_stage"],"abort")
        self.assertEqual(len(a._maya_model_clients),2)
        self.assertEqual(c.budget_rejections,0)

    def test_probe_EOF_does_not_claim_budget_failure(self):
        a,c,out=self.setup_agent();a.arm_budget_probe()
        data=c.channel._source.getvalue()
        c.channel._source=io.BytesIO(data[:data.index(encode(dict(v=1,type="model_adapter_probe",attempt=ATTEMPT,request_id="f"*32)))])
        a.run_native_shape();self.failed(a)
        self.assertEqual(a.budget_lifecycle_snapshot()["failure_stage"],"probe_control")
        self.assertEqual(c.budget_rejections,0)
        self.assertTrue(a._maya_model_clients[1][1].is_closed)

    def test_original_transport_validation_before_budget_observation(self):
        for change in ("url","header","body","method"):
            a,c,out=self.setup_agent();a.arm_budget_probe()
            # Isolated invalid request control retains original request guards.
            transport=RecreatePipeTransport(c)
            headers={"authorization":"Bearer "+PUBLIC_KEY,"content-type":"application/json"}
            raw=expected_request()
            if change=="header":headers["authorization"]="wrong"
            if change=="body":raw=b'{}'
            request=httpx.Request("GET" if change=="method" else "POST",
                ORIGIN+PATH+("?x=1" if change=="url" else ""),headers=headers,content=raw)
            with self.assertRaises(httpx.TransportError):transport.handle_request(request)
            self.assertEqual(c.budget_rejections,0)
            self.assertEqual(out.getvalue(),b"")


def worker_fixture(modify=lambda m:m, fault=None, reached=None):
    peer=BudgetCoordinator();peer.modify=modify;raw=io.BytesIO()
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
    with patch("project_maya.bridge.audit.os.fsync"):
        result=serve_model(peer,config,policy(),LITERALS.read_bytes(),RequiredAudit(Stream()),peer.write_expected,
                           recreated_client_budget=True)
    return result,raw.getvalue(),peer


class RecreateWorkerTests(unittest.TestCase):
    def verify(self,raw,peer):
        return verify_budget_audit(raw,HostBinding(SID,ATTEMPT,CHANNEL),peer.sent[0]["service_request_id"],
            peer.expected,peer.sent[2]["response"]["body"].encode(),OUTPUT,format(3,"032x"))

    def test_exact_four_record_m05b_finish_preserves_prior_effects(self):
        result,raw,peer=worker_fixture()
        self.assertEqual(result["case"],"M05b")
        self.assertEqual([result[k] for k in ("gateway_calls","dispatches","confirmed_runtime_releases","confirmed_operator_releases")],[2,1,1,0])
        self.assertEqual(self.verify(raw,peer),4)
        self.assertEqual([m["type"] for m in peer.sent],["model_worker_ready","model_grant_reply",
            "model_dispatch_reply","model_runtime_ack","model_adapter_complete"])

    def test_terminal_binding_wrong_phase_and_extra_frame_reject(self):
        for change in ({"attempt":"f"*32},{"request_id":format(2,"032x")},{"delivery_command_id":"f"*32},
                       {"extra":True},{"type":"model_dispatch"},{"type":"model_prepare_final"}):
            with self.subTest(change=change),self.assertRaises(ProtocolError):
                worker_fixture(lambda m:dict(m,**change) if m["type"]=="model_adapter_finish" else m)

    def test_modes_are_boolean_and_exclusive_before_any_readiness(self):
        config=dict(operator_sid=SID,attempt=ATTEMPT,channel_id=CHANNEL,utc_day="2026-10-24",canary=CANARY,fixture_text=OUTPUT)
        for mode in (dict(recreated_client_budget=1),dict(recreated_client_budget=True,same_client_budget=True),
                     dict(recreated_client_budget=True,wrong_model=True),dict(recreated_client_budget=True,replay_grant=True)):
            peer=BudgetCoordinator()
            with self.subTest(mode=mode),self.assertRaises(ProtocolError):
                serve_model(peer,config,policy(),LITERALS.read_bytes(),RequiredAudit(io.BytesIO()),peer.write_expected,**mode)
            self.assertEqual(peer.sent,[])

    def test_audit_all_record_and_metadata_mutations_reject(self):
        _,raw,peer=worker_fixture();records=[json.loads(line) for line in raw.splitlines()]
        for index,record in enumerate(records):
            for key in record:
                changed=copy.deepcopy(records);changed[index][key]="wrong"
                with self.subTest(index=index,key=key),self.assertRaises(ProtocolError):
                    self.verify(("\n".join(json.dumps(r) for r in changed)+"\n").encode(),peer)
            for key in record["metadata"]:
                changed=copy.deepcopy(records);changed[index]["metadata"][key]="wrong"
                with self.subTest(index=index,metadata=key),self.assertRaises(ProtocolError):
                    self.verify(("\n".join(json.dumps(r) for r in changed)+"\n").encode(),peer)

    def test_audit_schedule_truncation_and_all_write_flush_faults(self):
        _,raw,peer=worker_fixture();lines=raw.splitlines(keepends=True)
        for changed in (b"".join(lines[:-1]),raw+lines[-1],b"".join(reversed(lines)),raw[:-1]):
            with self.assertRaises(ProtocolError):self.verify(changed,peer)
        for i in range(4):
            for kind in ("write","flush"):
                reached=[]
                with self.subTest(index=i,kind=kind),self.assertRaises(PermissionError):
                    worker_fixture(fault=(kind,i),reached=reached)
                self.assertEqual(reached,[(kind,i)])

    def test_fixed_bootstraps_guard_before_import_and_case_selector(self):
        root=Path(__file__).resolve().parents[1]/"src/project_maya/windows_runtime"
        for name in ("model_recreate_child_entry.py","model_recreate_worker_entry.py"):
            source=(root/name).read_text();tree=ast.parse(source)
            self.assertIsInstance(tree.body[2],ast.If)
            self.assertIsInstance(tree.body[2].body[0],ast.Raise)
            self.assertIn("recreated_client_budget=True",source)
        source=(root/"model_child_entry.py").read_text()
        self.assertIn('["M05b"] if recreated_client_budget',source)
        self.assertLess(source.index("agent.arm_budget_probe()"),source.index("result = agent.run_conversation"))
        self.assertLess(source.index('report["probe"] = agent.finish_budget_probe()'),source.index("agent.shutdown_memory_provider"))


if __name__=="__main__":unittest.main()

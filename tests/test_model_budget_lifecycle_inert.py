"""Native-shaped lifecycle fixtures and pinned AST checks; never execute Hermes or SDK."""
import ast
import hashlib
import io
import json
from pathlib import Path
import threading
import unittest
import zipfile

from httpx import TransportError

from project_maya.bridge.model_service import ORIGIN, PATH, PUBLIC_KEY, SyntheticModel, digest, MODEL
from project_maya.bridge.protocol import ProtocolError, encode
from project_maya.bridge.transport import PrivateChannel
from project_maya.hermes_plugins.model_budget import BudgetChannelClient, SameClientBudgetMixin, successful_lifecycle, verify_lifecycle_source, LIFECYCLE_PIN
from test_model_bridge_inert import FactoryBase
from test_model_bridge_worker_inert import ATTEMPT, OUTPUT, expected_request


class NativeShape(FactoryBase):
    """Inert factory/call/finally shape, not an imported or executed Hermes method."""
    def __init__(self, **kwargs):
        self.events = []
        self.close_calls = []
        self.abort_calls = []
        self.close_fault = None
        super().__init__(**kwargs)

    def _close_request_openai_client(self, client, *, reason):
        self.events.append("native_close")
        self.close_calls.append((client, reason))
        if self.close_fault == "raise":
            raise OSError("private detail")
        if self.close_fault != "swallow":
            client.close()

    def _abort_request_openai_client(self, client, *, reason):
        self.abort_calls.append((client, reason))

    def run_native_shape(self, *, reason="request_complete", during=None):
        sdk = self._create_openai_client(self.kwargs, reason="chat_completion_request", shared=False)
        http = self._maya_model_clients[-1][1]
        try:
            response = http.post(ORIGIN+PATH, content=expected_request(),
                headers={"authorization":"Bearer "+PUBLIC_KEY,"content-type":"application/json"})
            response.close()
            self.events.append("sdk_return")
            if during is not None: during(self,sdk)
        finally:
            self._close_request_openai_client(sdk, reason=reason)
        self.events.append("conversation_return")
        return dict(final_response=OUTPUT)


class LifecycleAgent(SameClientBudgetMixin, NativeShape):
    def _budget_stage(self, stage):
        super()._budget_stage(stage)
        if hasattr(self, "events"):
            self.events.append(stage)


def fixture(probe=None):
    body = expected_request()
    response = SyntheticModel(OUTPUT).wire_reply()
    reply = dict(v=1,type="model_response",attempt=ATTEMPT,seq=1,status="ok",body=response.decode(),response_sha256=digest(response))
    control = dict(v=1,type="model_adapter_probe",attempt=ATTEMPT,request_id="f"*32) if probe is None else probe
    output = io.BytesIO()
    channel = BudgetChannelClient(PrivateChannel(io.BytesIO(encode(reply)+encode(control)),output),ATTEMPT)
    grant = dict(v=1,type="model_grant",attempt=ATTEMPT,route="maya.offline.model.v1",lease="e"*64,
        seq=1,ttl_ms=2000,request_sha256=digest(body))
    channel.bind_grant(grant)
    agent = LifecycleAgent(maya_model_channel=channel,provider="custom",api_mode="chat_completions",model=MODEL,
        base_url=ORIGIN+"/v1",api_key=PUBLIC_KEY,fallback_model=None,credential_pool=None,max_tokens=32)
    return agent,channel,output


class LifecycleTests(unittest.TestCase):
    def agent(self,probe=None):
        agent,channel,output=fixture(probe)
        self.addCleanup(agent.close_model_clients)
        return agent,channel,output

    def test_native_style_factory_call_probe_close_conversation_order(self):
        agent,channel,output=self.agent();agent.arm_budget_probe()
        self.assertEqual(agent.run_native_shape()["final_response"],OUTPUT)
        evidence=agent.finish_budget_probe()
        self.assertEqual(agent.budget_lifecycle_snapshot(),successful_lifecycle())
        self.assertEqual(agent.budget_probe_command_id,"f"*32)
        self.assertEqual(len(agent._maya_model_clients),2)
        self.assertEqual(len(agent.close_calls),1)
        self.assertIs(agent.close_calls[0][0],agent._maya_model_clients[1][0])
        self.assertLess(agent.events.index("sdk_return"),agent.events.index("second_request"))
        self.assertLess(agent.events.index("second_request"),agent.events.index("native_close"))
        self.assertLess(agent.events.index("native_close"),agent.events.index("conversation_return"))
        self.assertEqual(evidence["budget_rejections"],1)
        self.assertEqual(output.getvalue().count(b'"type":"model_request"'),1)
        self.assertEqual(output.getvalue().count(b'"type":"model_runtime_receipt"'),1)
        self.assertTrue(agent._maya_model_clients[1][1].is_closed)
        self.assertFalse(agent._maya_model_clients[0][1].is_closed)

    def test_owner_thread_may_differ_from_constructor_and_report_thread(self):
        agent,channel,output=self.agent();agent.arm_budget_probe();errors=[]
        def worker():
            try:agent.run_native_shape()
            except Exception as error:errors.append(type(error).__name__)
        thread=threading.Thread(target=worker);thread.start();thread.join(2)
        self.assertFalse(thread.is_alive());self.assertEqual(errors,[])
        self.assertEqual(agent.finish_budget_probe()["transport_attempts"],2)
        self.assertEqual(agent.budget_lifecycle_snapshot(),successful_lifecycle())

    def test_unarmed_or_wrong_reason_still_delegates_original_close(self):
        for armed,reason in ((False,"request_complete"),(True,"interrupted"),(True,"request_failed")):
            with self.subTest(armed=armed,reason=reason):
                agent,channel,output=self.agent()
                if armed:agent.arm_budget_probe()
                agent.run_native_shape(reason=reason)
                with self.assertRaises(ProtocolError):agent.finish_budget_probe()
                self.assertEqual(len(agent.close_calls),1)
                self.assertTrue(agent._maya_model_clients[1][1].is_closed)
                self.assertEqual(channel.budget_rejections,0)
                self.assertEqual(agent.budget_lifecycle_snapshot()["failure_stage"],"close_entry")

    def test_bad_probe_controls_do_not_throw_into_native_retry_path(self):
        original=dict(v=1,type="model_adapter_probe",attempt=ATTEMPT,request_id="f"*32)
        for change in ({"v":True},{"attempt":"b"*32},{"type":"model_begin"},{"request_id":"bad"},{"extra":0}):
            with self.subTest(change=change):
                agent,channel,output=self.agent(dict(original,**change));agent.arm_budget_probe()
                self.assertEqual(agent.run_native_shape()["final_response"],OUTPUT)
                with self.assertRaises(ProtocolError):agent.finish_budget_probe()
                self.assertEqual(agent.budget_lifecycle_snapshot()["failure_stage"],"probe_control")
                self.assertEqual(len(agent.close_calls),1);self.assertTrue(agent._maya_model_clients[1][1].is_closed)
                self.assertEqual(channel.budget_rejections,0)

    def test_abort_before_cleanup_poisoned_but_native_abort_and_close_delegated(self):
        agent,channel,output=self.agent();agent.arm_budget_probe()
        agent.run_native_shape(during=lambda a,c:a._abort_request_openai_client(c,reason="stale"))
        self.assertEqual(len(agent.abort_calls),1);self.assertEqual(len(agent.close_calls),1)
        self.assertEqual(agent.budget_lifecycle_snapshot()["failure_stage"],"abort")
        with self.assertRaises(ProtocolError):agent.finish_budget_probe()
        self.assertEqual(channel.budget_rejections,0)

    def test_duplicate_cleanup_never_second_probe_or_reset(self):
        agent,channel,output=self.agent();agent.arm_budget_probe();agent.run_native_shape()
        before=output.getvalue()
        agent._close_request_openai_client(agent._maya_model_clients[-1][0],reason="request_complete")
        self.assertEqual(len(agent.close_calls),2);self.assertEqual(channel.budget_rejections,1)
        self.assertEqual(before,output.getvalue())
        with self.assertRaises(ProtocolError):agent.finish_budget_probe()

    def test_native_close_raise_or_swallowed_failure_cannot_pass(self):
        for fault in ("raise","swallow"):
            with self.subTest(fault=fault):
                agent,channel,output=self.agent();agent.arm_budget_probe();agent.close_fault=fault
                agent.run_native_shape()
                self.assertEqual(len(agent.close_calls),1)
                self.assertEqual(agent.budget_lifecycle_snapshot()["failure_stage"],"native_close")
                self.assertEqual(channel.budget_rejections,1)
                with self.assertRaises(ProtocolError):agent.finish_budget_probe()

    def test_already_closed_client_not_reopened(self):
        agent,channel,output=self.agent();agent.arm_budget_probe()
        agent.run_native_shape(during=lambda a,c:c.close())
        self.assertEqual(agent.budget_lifecycle_snapshot()["failure_stage"],"client_preflight")
        self.assertEqual(channel.budget_rejections,0)
        self.assertEqual(len(agent.close_calls),1)
        with self.assertRaises(ProtocolError):agent.finish_budget_probe()

    def test_wrong_cleanup_owner_still_closes_but_cannot_probe(self):
        agent,channel,output=self.agent();agent.arm_budget_probe()
        def wrong_owner(a,sdk):
            thread=threading.Thread(target=lambda:a._close_request_openai_client(sdk,reason="request_complete"))
            thread.start();thread.join(2);self.assertFalse(thread.is_alive())
        agent.run_native_shape(during=wrong_owner)
        self.assertEqual(agent.budget_lifecycle_snapshot()["failure_stage"],"owner_binding")
        self.assertEqual(channel.budget_rejections,0)
        with self.assertRaises(ProtocolError):agent.finish_budget_probe()

    def test_snapshot_cannot_reset_diagnostic_or_rearm(self):
        agent,channel,output=self.agent();agent.arm_budget_probe();agent.run_native_shape()
        snapshot=agent.budget_lifecycle_snapshot();snapshot["hook_calls"]=0
        self.assertEqual(agent.budget_lifecycle_snapshot()["hook_calls"],1)
        with self.assertRaises(ProtocolError):agent.arm_budget_probe()

    def test_wrong_used_sdk_identity_blocks_and_both_native_closes_are_retained(self):
        agent,channel,output=self.agent();agent.arm_budget_probe()
        agent.run_native_shape(during=lambda a,c:a._close_request_openai_client(a.client,reason="request_complete"))
        self.assertEqual(agent.budget_lifecycle_snapshot()["failure_stage"],"owner_binding")
        self.assertEqual(len(agent.close_calls),2)
        self.assertEqual(channel.budget_rejections,0)
        self.assertTrue(all(http.is_closed for _,http,_ in agent._maya_model_clients))
        with self.assertRaises(ProtocolError):agent.finish_budget_probe()

    def test_first_transport_failure_still_closes_without_consuming_probe(self):
        agent,channel,output=self.agent();agent.arm_budget_probe()
        # Exhaust the fixture response stream before the first request.
        channel.channel._source=io.BytesIO()
        with self.assertRaises(TransportError):agent.run_native_shape()
        self.assertEqual(len(agent.close_calls),1)
        self.assertTrue(agent._maya_model_clients[-1][1].is_closed)
        self.assertEqual(agent.budget_lifecycle_snapshot()["failure_stage"],"client_preflight")
        self.assertEqual(channel.budget_rejections,0)
        with self.assertRaises(ProtocolError):agent.finish_budget_probe()

    def test_abort_at_control_read_does_not_hold_diagnostic_lock_or_issue_second_request(self):
        agent,channel,output=self.agent();agent.arm_budget_probe()
        raw=channel.channel._source.getvalue()
        boundary=raw.index(encode(dict(v=1,type="model_adapter_probe",attempt=ATTEMPT,request_id="f"*32)))
        class CallbackSource(io.BytesIO):
            fired=False
            def read(self,size=-1):
                if self.tell()==boundary and not self.fired:
                    self.fired=True
                    thread=threading.Thread(target=lambda:agent._abort_request_openai_client(agent._maya_model_clients[-1][0],reason="stale"))
                    thread.start();thread.join(2)
                    if thread.is_alive():raise RuntimeError("fixture abort lock blocked")
                return super().read(size)
        channel.channel._source=CallbackSource(raw)
        agent.run_native_shape()
        self.assertEqual(len(agent.abort_calls),1);self.assertEqual(len(agent.close_calls),1)
        self.assertEqual(agent.budget_lifecycle_snapshot()["failure_stage"],"abort")
        self.assertEqual(channel.budget_rejections,0)
        self.assertEqual(agent._maya_model_clients[-1][2].validated_attempts,1)
        with self.assertRaises(ProtocolError):agent.finish_budget_probe()

    def test_lifecycle_source_pin_rejects_tampered_helper(self):
        path=Path(__file__).resolve().parents[1]/".codex-build/maya-offline-model-budget-20261101-1/model-payload.zip"
        with zipfile.ZipFile(path) as archive:raw=archive.read("hermes/agent/chat_completion_helpers.py")
        class BytesPath:
            def __init__(self,data):self.data=data
            def __truediv__(self,name):
                if name!="agent/chat_completion_helpers.py":raise AssertionError(name)
                return self
            def read_bytes(self):return self.data
        verify_lifecycle_source(BytesPath(raw))
        with self.assertRaises(ProtocolError):verify_lifecycle_source(BytesPath(raw+b"\n"))

    def test_pinned_native_source_uses_request_factory_and_finally_close(self):
        path=Path(__file__).resolve().parents[1]/".codex-build/maya-offline-model-budget-20261101-1/model-payload.zip"
        with zipfile.ZipFile(path) as archive:
            raw=archive.read("hermes/agent/chat_completion_helpers.py")
            native=archive.read("hermes/run_agent.py")
        self.assertEqual(hashlib.sha256(raw).hexdigest(),LIFECYCLE_PIN)
        self.assertEqual(hashlib.sha256(native).hexdigest(),"7a36be48ffdc0fe62b855263683d55c1c7138cc65acf597175920fcf86b45bd5")
        tree=ast.parse(raw)
        calls=[node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=="_call"]
        chosen=[node for node in calls if any(isinstance(n,ast.Call) and ast.unparse(n.func)=="request_client.chat.completions.create" for n in ast.walk(node))]
        self.assertEqual(len(chosen),1)
        block=chosen[0].body[0];self.assertIsInstance(block,ast.Try)
        self.assertEqual(ast.unparse(block.finalbody[0]),"_close_request_client_once('request_complete')")
        waits=[node for node in ast.walk(tree) if isinstance(node,ast.While) and ast.unparse(node.test)=="t.is_alive()"]
        self.assertTrue(any("t.join(timeout=0.3)" in ast.unparse(node) for node in waits))
        close=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="_close_request_client_once"][0]
        self.assertIn("agent._close_request_openai_client(request_client, reason=reason)",ast.unparse(close))
        native_tree=ast.parse(native)
        method=[n for n in ast.walk(native_tree) if isinstance(n,ast.FunctionDef) and n.name=="_close_request_openai_client"][0]
        self.assertIn("self._close_openai_client(client, reason=reason, shared=False)",ast.unparse(method))


if __name__ == "__main__":
    unittest.main()

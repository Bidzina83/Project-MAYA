"""Host request oracle, worker protocol and ledger fixtures; no native execution."""
import copy
import ast
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from project_maya.bridge.audit import RequiredAudit
from project_maya.bridge.model_audit import verify_model_audit
from project_maya.bridge.model_native import native_request
from project_maya.bridge.model_service import MODEL, PATH as MODEL_PATH, ROUTE, TARGET, OfflineModelBridge, digest
from project_maya.bridge.model_worker import serve_model
from project_maya.bridge.protocol import ProtocolError, decode
from project_maya.bridge.service import HostBinding
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule

ATTEMPT, CHANNEL, CANARY = "a"*32, "b"*64, "c"*64
SID = "S-1-5-21-1-2-3-500"
OUTPUT = "MAYA_OFFLINE_MODEL_OK:"+"d"*32
LITERALS = Path(__file__).resolve().parents[1]/"src/project_maya/windows_runtime/model-native-literals.json"


def expected_request():
    return native_request(LITERALS.read_bytes(), ATTEMPT, "2026-10-24", CANARY)


def policy():
    return {"allow":[dict(capability=cap,target=TARGET,operation=op,actor_id="windows:"+SID)
                     for cap,op in (("model.egress","infer"),("model.output","disclose"))]}


class OracleTests(unittest.TestCase):
    def test_host_owned_native_prompt_is_bounded_and_deterministic(self):
        raw=expected_request(); body=decode(raw)
        self.assertEqual(raw, expected_request())
        self.assertLessEqual(len(raw),4096)
        self.assertGreater(len(body["messages"][0]["content"].encode()),1024)
        self.assertIn("Conversation started: Saturday, October 24, 2026",body["messages"][0]["content"])
        self.assertIn("C:\\ProgramData\\MayaProtectedPython-Startup1\\"+ATTEMPT+"\\state",body["messages"][0]["content"])
        self.assertEqual(body["messages"][1]["content"],"MAYA_OFFLINE_MODEL_REQUEST:"+CANARY)
        self.assertEqual(list(body),["messages","model","max_tokens","stream"])

    def test_changed_literal_is_not_authorized(self):
        raw=LITERALS.read_bytes().replace(b"Nous Research",b"Somebody Else")
        with self.assertRaises(ProtocolError): native_request(raw,ATTEMPT,"2026-10-24",CANARY)

    def test_invalid_trusted_inputs_rejected(self):
        for a,day,c in (("wrong","2026-10-24",CANARY),(ATTEMPT,"2026-02-30",CANARY),
                        (ATTEMPT,"tomorrow",CANARY),(ATTEMPT,"2026-10-24","prompt")):
            with self.subTest(day=day),self.assertRaises(ProtocolError): native_request(LITERALS.read_bytes(),a,day,c)

    def test_host_day_or_canary_change_produces_different_exact_bytes(self):
        self.assertNotEqual(expected_request(),native_request(LITERALS.read_bytes(),ATTEMPT,"2026-10-25",CANARY))
        self.assertNotEqual(expected_request(),native_request(LITERALS.read_bytes(),ATTEMPT,"2026-10-24","e"*64))


class CoordinatorFixture:
    """In-memory protocol peer, explicitly not a native Windows coordinator."""
    def __init__(self):
        self.sent=[]; self.expected=None; self.index=0; self.modify=lambda m:m

    def send(self,message): self.sent.append(message)

    def write_expected(self,raw): self.expected=raw; return len(raw)

    def receive(self):
        sequence=("model_issue","model_dispatch","model_runtime_delivered","model_prepare_final",
                  "model_operator_delivered","model_shutdown")
        kind=sequence[self.index]; self.index+=1
        message=dict(v=1,type=kind,attempt=ATTEMPT,request_id=format(self.index,"032x"))
        if kind=="model_dispatch":
            grant=self.sent[-1]["grant"]
            message["request"]=dict(v=1,type="model_request",attempt=ATTEMPT,route=ROUTE,
                lease=grant["lease"],seq=1,method="POST",path=MODEL_PATH,body=self.expected.decode())
        elif kind=="model_runtime_delivered":
            message["response_sha256"]=self.sent[-1]["response"]["response_sha256"]
        elif kind=="model_prepare_final": message["text"]=OUTPUT
        elif kind=="model_operator_delivered": message["text_sha256"]=digest(OUTPUT.encode())
        return self.modify(message)


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.sync=patch("project_maya.bridge.audit.os.fsync"); self.sync.start(); self.addCleanup(self.sync.stop)
        self.records=[]; self.stream=Mock()
        self.stream.write.side_effect=lambda raw:self.records.append(json.loads(raw)) or len(raw)
        self.audit=RequiredAudit(self.stream)
        self.channel=CoordinatorFixture()
        self.config=dict(operator_sid=SID,attempt=ATTEMPT,channel_id=CHANNEL,utc_day="2026-10-24",
                         canary=CANARY,fixture_text=OUTPUT)

    def run_worker(self,rule=None,write=None):
        return serve_model(self.channel,self.config,policy() if rule is None else rule,LITERALS.read_bytes(),
                           self.audit,write or self.channel.write_expected)

    def test_complete_protocol_and_independent_ledger_readback(self):
        result=self.run_worker()
        self.assertEqual(result,dict(dispatches=1,confirmed_runtime_releases=1,
                                     confirmed_operator_releases=1,real_inference=False))
        self.assertEqual([m["type"] for m in self.channel.sent],["model_worker_ready","model_grant_reply",
            "model_dispatch_reply","model_runtime_ack","model_final_prepared","model_operator_ack","model_worker_complete"])
        self.assertEqual(self.channel.sent[2]["confirmed_runtime_releases"],0)
        raw=("\n".join(json.dumps(r) for r in self.records)+"\n").encode()
        response=self.channel.sent[2]["response"]["body"].encode()
        self.assertEqual(verify_model_audit(raw,HostBinding(SID,ATTEMPT,CHANNEL),
            self.channel.sent[0]["service_request_id"],self.channel.expected,response,OUTPUT,
            (format(3,"032x"),format(5,"032x"))),6)

    def test_policy_cannot_use_wildcard_actor(self):
        rules=policy(); rules["allow"][0]["actor_id"]="*"
        with self.assertRaises(ProtocolError): self.run_worker(rules)
        self.assertEqual(self.channel.sent,[])

    def test_short_expected_write_never_issues_admission(self):
        with self.assertRaises(ProtocolError): self.run_worker(write=lambda raw:1)
        self.assertEqual(self.channel.sent,[])

    def test_replayed_coordinator_request_id_stops_before_dispatch(self):
        self.channel.modify=lambda m:dict(m,request_id="0"*32)
        with self.assertRaises(ProtocolError): self.run_worker()
        self.assertNotIn("model_dispatch_reply",[m["type"] for m in self.channel.sent])

    def test_runtime_confirmation_cannot_claim_different_response(self):
        self.channel.modify=lambda m:dict(m,response_sha256="0"*64) if m["type"]=="model_runtime_delivered" else m
        with self.assertRaises(PermissionError): self.run_worker()
        self.assertNotIn("model_runtime_ack",[m["type"] for m in self.channel.sent])

    def test_unknown_field_and_wrong_attempt_block_protocol(self):
        self.channel.modify=lambda m:dict(m,attempt="0"*32)
        with self.assertRaises(ProtocolError): self.run_worker()
        self.assertEqual(len(self.channel.sent),1)

    def test_raw_exception_does_not_become_protocol_reply(self):
        self.stream.flush.side_effect=OSError("private detail")
        with self.assertRaises(PermissionError): self.run_worker()
        self.assertNotIn("private detail",json.dumps(self.channel.sent))
        self.assertTrue(self.audit.failed)


class LedgerTests(unittest.TestCase):
    def setUp(self):
        sync=patch("project_maya.bridge.audit.os.fsync"); sync.start(); self.addCleanup(sync.stop)
        self.binding=HostBinding(SID,ATTEMPT,CHANNEL)
        self.records=[]; stream=Mock(); stream.write.side_effect=lambda raw:self.records.append(json.loads(raw)) or len(raw)
        gateway=PolicyAuthorizationGateway(tuple(PolicyRule(**x) for x in policy()["allow"]))
        service=OfflineModelBridge(self.binding,gateway,RequiredAudit(stream),expected_request(),OUTPUT)
        grant=service.issue(); request=dict(v=1,type="model_request",attempt=ATTEMPT,route=ROUTE,
            lease=grant["lease"],seq=1,method="POST",path=MODEL_PATH,body=expected_request().decode())
        self.reply=service.prepare_runtime(request,CHANNEL)
        service.confirm_runtime_delivery(self.reply["response_sha256"],"1"*32)
        service.prepare_operator(OUTPUT); service.confirm_operator_delivery(digest(OUTPUT.encode()),"2"*32)
        self.request_id=service.request_id

    def verify(self,records=None,**kwargs):
        args=dict(raw=("\n".join(json.dumps(r) for r in (self.records if records is None else records))+"\n").encode(),
            binding=self.binding,request_id=self.request_id,expected_request=expected_request(),
            expected_response=self.reply["body"].encode(),expected_output=OUTPUT,coordinator_requests=("1"*32,"2"*32))
        args.update(kwargs);return verify_model_audit(**args)

    def test_complete_six_record_admission(self): self.assertEqual(self.verify(),6)

    def test_missing_extra_or_reordered_record_rejected(self):
        for records in (self.records[:-1],self.records+[self.records[-1]],list(reversed(self.records))):
            with self.assertRaises(ProtocolError):self.verify(records)

    def test_every_record_field_is_required(self):
        for index,record in enumerate(self.records):
            for key in record:
                records=copy.deepcopy(self.records);del records[index][key]
                with self.subTest(index=index,key=key),self.assertRaises(ProtocolError):self.verify(records)

    def test_every_binding_field_is_checked(self):
        for index,record in enumerate(self.records):
            for key in record["metadata"]:
                records=copy.deepcopy(self.records);records[index]["metadata"][key]="wrong"
                with self.subTest(index=index,key=key),self.assertRaises(ProtocolError):self.verify(records)

    def test_partial_duplicate_key_and_oversized_input(self):
        for raw in (b"{}",b'{"x":1,"x":2}\n',b"x"*131073):
            with self.assertRaises(ProtocolError):self.verify(raw=raw)

    def test_boolean_schema_and_non_UTC_timestamp_rejected(self):
        records=copy.deepcopy(self.records);records[0]["schema_version"]=True
        with self.assertRaises(ProtocolError):self.verify(records)
        records=copy.deepcopy(self.records);records[0]["timestamp"]="2026-10-24T12:00:00+04:00"
        with self.assertRaises(ProtocolError):self.verify(records)

    def test_confirmations_must_be_distinct_and_match_actual_host_values(self):
        for ids in (("1"*32,"1"*32),("0"*32,"2"*32)):
            with self.assertRaises(ProtocolError):self.verify(coordinator_requests=ids)


class NativeSourceGuardTests(unittest.TestCase):
    def entry(self,name):
        path=LITERALS.parent/name
        spec=importlib.util.spec_from_file_location("maya_inert_"+path.stem,path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_child_guard_returns_without_importing_hermes_or_writing(self):
        module=self.entry("model_child_entry.py")
        with patch.object(module.sys,"platform","linux"),patch.object(Path,"write_bytes",side_effect=AssertionError("no writes")):
            self.assertEqual(module.main(),2)

    def test_worker_guard_returns_without_native_handle_access(self):
        from project_maya.bridge import model_worker
        with patch.object(model_worker.os,"name","posix"),patch.object(model_worker,"open_private",side_effect=AssertionError("no native calls")):
            self.assertEqual(model_worker.main(),2)

    def test_worker_bootstrap_guard_never_dispatches(self):
        import runpy
        import sys
        with patch.object(sys,"platform","linux"),patch.object(runpy,"run_module") as run:
            with self.assertRaises(SystemExit) as error:self.entry("model_worker_entry.py")
            self.assertEqual(error.exception.code,2);run.assert_not_called()

    def test_native_entry_calls_real_conversation_and_tracks_close(self):
        source=(LITERALS.parent/"model_child_entry.py").read_text()
        tree=ast.parse(source)
        calls=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
        self.assertIn("run_conversation",calls);self.assertIn("close_model_clients",calls)
        self.assertNotIn("create",calls)
        self.assertIn("agent.session_api_calls == 1",source)
        self.assertIn("native_module.__file__",source)

    def test_private_model_config_pins_UTC_and_one_attempt(self):
        config=json.loads((LITERALS.parent/"model-config.json").read_text())
        self.assertEqual(config["timezone"],"UTC")
        self.assertIs(type(config["agent"]["api_max_retries"]),int)
        self.assertEqual(config["agent"]["api_max_retries"],1)
        self.assertIs(config["compression"]["enabled"],False)
        self.assertIs(config["agent"]["environment_probe"],False)
        self.assertEqual(config["tools"]["tool_search"]["enabled"],"off")


if __name__=="__main__":unittest.main()

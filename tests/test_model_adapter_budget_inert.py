"""M05a in-memory transport/worker fixtures. No Hermes, product main or native setup."""
import copy
import ast
import io
import json
from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from project_maya.bridge.audit import RequiredAudit
from project_maya.bridge.model_adapter_budget import finish_adapter_budget, verify_budget_audit
from project_maya.bridge.model_service import ORIGIN, PATH, PUBLIC_KEY, SyntheticModel, digest
from project_maya.bridge.model_worker import serve_model
from project_maya.bridge.protocol import ProtocolError, encode
from project_maya.bridge.service import HostBinding
from project_maya.bridge.transport import PrivateChannel
from project_maya.hermes_plugins.model_budget import BudgetChannelClient, BudgetPipeTransport, SameClientBudgetMixin, probe_same_client
from test_model_bridge_inert import FactoryBase
from test_model_bridge_worker_inert import ATTEMPT, CHANNEL, CANARY, SID, OUTPUT, LITERALS, expected_request, policy, CoordinatorFixture


def transport_fixture():
    raw = expected_request()
    response = SyntheticModel(OUTPUT).wire_reply()
    reply = dict(v=1, type="model_response", attempt=ATTEMPT, seq=1, status="ok",
                 body=response.decode(), response_sha256=digest(response))
    incoming, outgoing = io.BytesIO(encode(reply)), io.BytesIO()
    channel = BudgetChannelClient(PrivateChannel(incoming, outgoing), ATTEMPT)
    grant = dict(v=1, type="model_grant", attempt=ATTEMPT, route="maya.offline.model.v1",
                 lease="e"*64, seq=1, ttl_ms=2000, request_sha256=digest(raw))
    channel.bind_grant(grant)
    transport = BudgetPipeTransport(channel)
    client = httpx.Client(transport=transport, trust_env=False, follow_redirects=False)
    sdk = SimpleNamespace(is_closed=lambda: client.is_closed)
    agent = SimpleNamespace(_maya_model_channel=channel, _maya_model_clients=[(sdk, client, transport)])
    headers = {"authorization":"Bearer "+PUBLIC_KEY, "content-type":"application/json"}
    return agent, client, transport, outgoing, raw, headers, grant


class BudgetTransportTests(unittest.TestCase):
    def test_case_factory_delegates_and_shares_one_adapter_then_closes_all_clients(self):
        class Agent(SameClientBudgetMixin, FactoryBase):
            pass
        from project_maya.bridge.model_service import MODEL
        channel=BudgetChannelClient(PrivateChannel(io.BytesIO(),io.BytesIO()),ATTEMPT)
        agent=Agent(maya_model_channel=channel,provider="custom",api_mode="chat_completions",model=MODEL,
            base_url=ORIGIN+"/v1",api_key=PUBLIC_KEY,fallback_model=None,credential_pool=None,max_tokens=32)
        agent._create_openai_client(agent.kwargs,reason="request",shared=False)
        self.assertEqual(len(agent._maya_model_clients),2)
        self.assertIsNot(agent._maya_model_clients[0][1],agent._maya_model_clients[1][1])
        for sdk,client,transport in agent._maya_model_clients:
            self.assertIs(type(transport),BudgetPipeTransport)
            self.assertIs(transport.channel,channel)
            self.assertEqual(sdk.max_retries,0)
        agent.close_model_clients()
        self.assertTrue(channel.closed)
        for sdk,client,transport in agent._maya_model_clients:
            self.assertTrue(sdk.is_closed() and client.is_closed and transport.closed)

    def first(self):
        fixture = transport_fixture()
        agent, client, transport, outgoing, raw, headers, grant = fixture
        self.addCleanup(client.close)
        reply = client.post(ORIGIN+PATH, content=raw, headers=headers)
        self.assertEqual(reply.status_code, 200)
        reply.close()
        return fixture

    def test_exact_used_client_second_request_local_guard_no_pipe_delta(self):
        agent, client, transport, outgoing, raw, headers, grant = self.first()
        before = outgoing.getvalue()
        evidence = probe_same_client(agent)
        self.assertEqual(evidence, dict(case="M05a", boundary="adapter_consumed_budget", transport_attempts=2,
            model_requests=1, completed_exchanges=1, budget_rejections=1, same_used_client=True,
            request_sha256=digest(raw), request_bytes=len(raw)))
        self.assertEqual(outgoing.getvalue(), before)
        self.assertEqual(before.count(b'"type":"model_request"'), 1)
        self.assertEqual(before.count(b'"type":"model_runtime_receipt"'), 1)

    def test_unused_client_is_not_selected(self):
        agent, client, transport, outgoing, raw, headers, grant = self.first()
        unused = BudgetPipeTransport(agent._maya_model_channel)
        unused_client = httpx.Client(transport=unused, trust_env=False)
        self.addCleanup(unused_client.close)
        agent._maya_model_clients.insert(0, (SimpleNamespace(is_closed=lambda:False), unused_client, unused))
        probe_same_client(agent)
        self.assertEqual(unused.validated_attempts, 0)
        self.assertFalse(unused_client.is_closed)

    def test_premature_client_transport_or_shared_close_cannot_pass(self):
        for kind in ("http", "transport", "shared"):
            with self.subTest(kind=kind):
                agent, client, transport, outgoing, raw, headers, grant = self.first()
                if kind == "http": client.close()
                if kind == "transport": transport.close()
                if kind == "shared": agent._maya_model_channel.closed = True
                with self.assertRaises(ProtocolError): probe_same_client(agent)
                self.assertEqual(agent._maya_model_channel.budget_rejections, 0)

    def test_wrong_or_duplicate_used_transport_rejected(self):
        for kind in ("wrong_adapter", "duplicate"):
            with self.subTest(kind=kind):
                agent, client, transport, outgoing, raw, headers, grant = self.first()
                if kind == "duplicate": agent._maya_model_clients.append(agent._maya_model_clients[0])
                else: transport.channel = BudgetChannelClient(PrivateChannel(io.BytesIO(), io.BytesIO()), ATTEMPT)
                with self.assertRaises(ProtocolError): probe_same_client(agent)

    def test_invalid_second_headers_or_body_never_claim_budget_boundary(self):
        for kind in ("header", "body"):
            with self.subTest(kind=kind):
                agent, client, transport, outgoing, raw, headers, grant = self.first()
                before = outgoing.getvalue()
                if kind == "header": headers["authorization"] = "Bearer wrong"
                else: raw = b"{}"
                with self.assertRaises(httpx.TransportError): client.post(ORIGIN+PATH, content=raw, headers=headers)
                self.assertEqual(agent._maya_model_channel.budget_rejections, 0)
                self.assertEqual(outgoing.getvalue(), before)

    def test_rebind_cannot_reset_budget(self):
        agent, client, transport, outgoing, raw, headers, grant = self.first()
        with self.assertRaises(ProtocolError): agent._maya_model_channel.bind_grant(grant)
        with self.assertRaises(ProtocolError): probe_same_client(agent)
        self.assertEqual(agent._maya_model_channel.requests, 1)

    def test_missing_success_or_repeated_probe_never_passes(self):
        agent, client, transport, outgoing, raw, headers, grant = transport_fixture()
        self.addCleanup(client.close)
        with self.assertRaises(ProtocolError): probe_same_client(agent)
        agent, client, transport, outgoing, raw, headers, grant = self.first()
        probe_same_client(agent)
        with self.assertRaises(ProtocolError): probe_same_client(agent)

    def test_generic_transport_failure_without_guard_observation_is_not_pass(self):
        agent, client, transport, outgoing, raw, headers, grant = self.first()
        with patch.object(client, "send", side_effect=httpx.TransportError("model_bridge.unavailable")):
            with self.assertRaises(ProtocolError): probe_same_client(agent)


class BudgetCoordinator(CoordinatorFixture):
    def receive(self):
        if self.index < 3:
            return super().receive()
        self.index += 1
        return self.modify(dict(v=1, type="model_adapter_finish", attempt=ATTEMPT,
            request_id=format(self.index,"032x"), delivery_command_id=format(3,"032x")))


def worker_fixture(modify=lambda message:message, audit_fault=None, reached=None):
    peer = BudgetCoordinator();peer.modify = modify
    raw = io.BytesIO()
    class Stream:
        def write(self, data):
            if audit_fault == ("write", raw.getvalue().count(b"\n")):
                if reached is not None: reached.append(audit_fault)
                raise OSError()
            return raw.write(data)
        def flush(self):
            if audit_fault == ("flush", raw.getvalue().count(b"\n")-1):
                if reached is not None: reached.append(audit_fault)
                raise OSError()
        def fileno(self): return 123
    audit = RequiredAudit(Stream())
    config = dict(operator_sid=SID,attempt=ATTEMPT,channel_id=CHANNEL,utc_day="2026-10-24",canary=CANARY,fixture_text=OUTPUT)
    with patch("project_maya.bridge.audit.os.fsync"):
        result = serve_model(peer, config, policy(), LITERALS.read_bytes(), audit, peer.write_expected, same_client_budget=True)
    return result, raw.getvalue(), peer


class BudgetWorkerTests(unittest.TestCase):
    def test_conflicting_or_non_boolean_modes_block_before_worker_readiness(self):
        config=dict(operator_sid=SID,attempt=ATTEMPT,channel_id=CHANNEL,utc_day="2026-10-24",canary=CANARY,fixture_text=OUTPUT)
        for mode in (dict(same_client_budget=1),dict(same_client_budget=True,replay_grant=True),
                     dict(same_client_budget=True,wrong_model=True),dict(same_client_budget=True,deny_egress=True)):
            peer=BudgetCoordinator()
            with self.subTest(mode=mode),self.assertRaises(ProtocolError):
                serve_model(peer,config,policy(),LITERALS.read_bytes(),RequiredAudit(io.BytesIO()),peer.write_expected,**mode)
            self.assertEqual(peer.sent,[])

    def verify(self, raw, peer):
        return verify_budget_audit(raw, HostBinding(SID,ATTEMPT,CHANNEL), peer.sent[0]["service_request_id"],
            peer.expected, peer.sent[2]["response"]["body"].encode(), OUTPUT, format(3,"032x"))

    def test_exact_four_record_completion_preserves_first_effects(self):
        result, raw, peer = worker_fixture()
        self.assertEqual(result["gateway_calls"], 2)
        self.assertEqual(result["dispatches"], 1)
        self.assertEqual(result["confirmed_runtime_releases"], 1)
        self.assertEqual(result["confirmed_operator_releases"], 0)
        self.assertEqual(self.verify(raw, peer), 4)
        self.assertEqual([m["type"] for m in peer.sent], ["model_worker_ready","model_grant_reply",
            "model_dispatch_reply","model_runtime_ack","model_adapter_complete"])

    def test_terminal_wrong_binding_replay_or_extra_request_rejected(self):
        for mutation in ({"delivery_command_id":"f"*32}, {"request_id":format(2,"032x")},
                         {"type":"model_dispatch"}, {"attempt":"f"*32}, {"extra":True}):
            with self.subTest(mutation=mutation), self.assertRaises(ProtocolError):
                worker_fixture(lambda m:dict(m,**mutation) if m["type"]=="model_adapter_finish" else m)

    def test_each_record_field_and_metadata_field_cannot_be_mutated(self):
        result, raw, peer = worker_fixture()
        records = [json.loads(line) for line in raw.splitlines()]
        for index, record in enumerate(records):
            for key in record:
                changed = copy.deepcopy(records);changed[index][key] = "wrong"
                with self.subTest(index=index,key=key), self.assertRaises(ProtocolError):
                    self.verify(("\n".join(json.dumps(r) for r in changed)+"\n").encode(),peer)
            for key in record["metadata"]:
                changed = copy.deepcopy(records);changed[index]["metadata"][key] = "wrong"
                with self.subTest(index=index,metadata=key), self.assertRaises(ProtocolError):
                    self.verify(("\n".join(json.dumps(r) for r in changed)+"\n").encode(),peer)

    def test_missing_extra_reordered_or_unterminated_ledger_fails(self):
        result, raw, peer = worker_fixture();lines=raw.splitlines(keepends=True)
        for changed in (b"".join(lines[:-1]),raw+lines[-1],b"".join(reversed(lines)),raw[:-1]):
            with self.assertRaises(ProtocolError): self.verify(changed,peer)

    def test_all_four_write_and_flush_failure_locations_are_reached(self):
        for index in range(4):
            for kind in ("write","flush"):
                reached = []
                with self.subTest(index=index,kind=kind):
                    with self.assertRaises(PermissionError): worker_fixture(audit_fault=(kind,index), reached=reached)
                    self.assertEqual(reached, [(kind,index)])

    def test_terminal_failed_audit_or_wrong_phase_does_not_pass(self):
        for key,value in (("_closed",True),("_revoked",True),("_phase","issued"),("gateway_calls",3),
                          ("confirmed_runtime_releases",0),("prepared_operator_releases",1)):
            service=SimpleNamespace(_lock=__import__('threading').RLock(),closed=False,_revoked=False,
                _audit=SimpleNamespace(failed=False),_phase="runtime_delivered",request_validated=True,
                gateway_calls=2,dispatches=1,prepared_runtime_releases=1,confirmed_runtime_releases=1,
                prepared_operator_releases=0,confirmed_operator_releases=0)
            setattr(service,"closed" if key=="_closed" else key,value)
            with self.subTest(key=key), self.assertRaises(ProtocolError): finish_adapter_budget(service,"1"*32)

    def test_native_source_order_and_fixed_entry_guards_without_execution(self):
        root=Path(__file__).resolve().parents[1]/"src/project_maya/windows_runtime"
        child=(root/"model_child_entry.py").read_text()
        self.assertLess(child.index('agent.arm_budget_probe()'), child.index('result = agent.run_conversation'))
        self.assertLess(child.index('result = agent.run_conversation'), child.index('report["probe"] = agent.finish_budget_probe()'))
        self.assertLess(child.index('report["probe"] = agent.finish_budget_probe()'), child.index('agent.shutdown_memory_provider'))
        self.assertNotIn('probe_same_client(agent)', child)
        source=(root/"ModelBridgeRuntime.cs").read_text()
        branch=source[source.index('uint RunBudget('):source.index('public void Dispose()')]
        self.assertNotIn('publish(',branch)
        self.assertNotIn('model_prepare_final',branch)
        self.assertLess(branch.index('childChannel.Eof'),branch.index('model_adapter_finish'))
        self.assertLess(branch.index('worker.WaitBridge'),branch.index('ModelBudgetAdmission.Audit'))
        for name in ('model_budget_child_entry.py','model_budget_worker_entry.py'):
            tree=ast.parse((root/name).read_text())
            self.assertIsInstance(tree.body[2],ast.If)
            self.assertIsInstance(tree.body[2].body[0],ast.Raise)
            self.assertIn('same_client_budget=True',(root/name).read_text())


if __name__ == "__main__":
    unittest.main()

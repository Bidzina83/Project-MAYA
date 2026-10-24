"""M1 unit fixtures. No Hermes/SDK import, product process, native API or network."""
import io
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import httpx

from project_maya.bridge.audit import RequiredAudit
from project_maya.bridge.model_service import (
    MODEL, ORIGIN, PATH, PUBLIC_KEY, ROUTE, TARGET, ModelDenied, OfflineModelBridge,
    SyntheticModel, checked_request, digest,
)
from project_maya.bridge.protocol import Decoder, ProtocolError, encode
from project_maya.bridge.service import HostBinding
from project_maya.bridge.transport import PrivateChannel
from project_maya.governance import AuthorizationResult, GovernanceDecision, PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.model_bridge import ModelChannelClient, OfflineModelClientMixin, PipeModelTransport

ATTEMPT, CHANNEL, COORDINATOR = "a" * 32, "b" * 64, "c" * 32
SID = "S-1-5-21-1-2-3-500"
TEXT = "explicit synthetic reply"


def payload():
    return json.dumps(dict(model=MODEL, messages=[dict(role="user", content="synthetic host canary")],
                           max_tokens=32, stream=False), separators=(",", ":")).encode()


class ModelCoreTests(unittest.TestCase):
    def setUp(self):
        sync = patch("project_maya.bridge.audit.os.fsync")
        self.sync = sync.start()
        self.addCleanup(sync.stop)
        self.fresh()

    def fresh(self):
        self.clock = Mock(return_value=0)
        self.events = []
        self.stream = Mock()
        self.stream.write.side_effect = lambda raw: self.events.append(json.loads(raw)) or len(raw)
        self.audit = RequiredAudit(self.stream)
        self.gateway = PolicyAuthorizationGateway(tuple(PolicyRule(capability=cap, target=TARGET,
            operation=operation, actor_id="windows:" + SID) for cap, operation in
            (("model.egress", "infer"), ("model.output", "disclose"))))
        self.bridge = OfflineModelBridge(HostBinding(SID, ATTEMPT, CHANNEL), self.gateway,
            self.audit, payload(), TEXT, self.clock)
        self.grant = self.bridge.issue()

    def request(self):
        return dict(v=1, type="model_request", attempt=ATTEMPT, route=ROUTE,
            lease=self.grant["lease"], seq=1, method="POST", path=PATH, body=payload().decode())

    def prepare(self):
        return self.bridge.prepare_runtime(self.request(), CHANNEL)

    def delivered(self):
        reply = self.prepare()
        self.bridge.confirm_runtime_delivery(reply["response_sha256"], COORDINATOR)
        return reply

    def test_success_six_events_and_separate_preparation_delivery(self):
        reply = self.prepare()
        self.assertEqual((self.bridge.dispatches, self.bridge.prepared_runtime_releases,
                          self.bridge.confirmed_runtime_releases), (1, 1, 0))
        self.assertEqual(reply["body"], self.bridge._response.decode())
        self.bridge.confirm_runtime_delivery(reply["response_sha256"], COORDINATOR)
        self.assertEqual(self.bridge.prepare_operator(TEXT), TEXT)
        self.assertEqual(self.bridge.confirmed_operator_releases, 0)
        self.bridge.confirm_operator_delivery(digest(TEXT.encode()), COORDINATOR)
        self.assertEqual(self.bridge.confirmed_operator_releases, 1)
        self.assertTrue(self.bridge.closed)
        self.assertEqual([e["event_type"] for e in self.events], ["model_bridge." + stage for stage in
            ("egress_intent", "dispatch_outcome", "runtime_release_intent", "runtime_delivery",
             "operator_release_intent", "operator_delivery")])
        for e in self.events:
            self.assertEqual(e["actor_id"], "windows:" + SID)
            self.assertEqual(e["metadata"]["attempt"], ATTEMPT)
            self.assertEqual(e["metadata"]["real_inference"], "false")
            self.assertNotIn(TEXT, json.dumps(e))
            self.assertNotIn("synthetic host canary", json.dumps(e))

    def test_egress_deny_has_zero_dispatch(self):
        self.bridge._gateway = PolicyAuthorizationGateway(())
        with self.assertRaises(ModelDenied): self.prepare()
        self.assertEqual(self.bridge.dispatches, 0)
        self.assertEqual(self.events[-1]["decision"], "deny")

    def test_output_deny_occurs_after_dispatch_before_release(self):
        self.bridge._gateway = PolicyAuthorizationGateway((PolicyRule("model.egress"),))
        with self.assertRaises(ModelDenied): self.prepare()
        self.assertEqual(self.bridge.dispatches, 1)
        self.assertEqual(self.bridge.prepared_runtime_releases, 0)

    def test_operator_has_separate_policy_gate(self):
        self.delivered()
        self.bridge._gateway = PolicyAuthorizationGateway(())
        with self.assertRaises(ModelDenied): self.bridge.prepare_operator(TEXT)
        self.assertEqual(self.bridge.confirmed_runtime_releases, 1)
        self.assertEqual(self.bridge.prepared_operator_releases, 0)

    def test_bad_actor_resource_route_and_replay(self):
        for field, value in (("actor", "admin"), ("route", "other"), ("path", "/v1/responses"),
                             ("seq", True), ("lease", "0" * 64), ("method", "GET"),
                             ("attempt", "0" * 32), ("body", payload().decode()+" ")):
            with self.subTest(field=field):
                request = self.request(); request[field] = value
                with self.assertRaises(ModelDenied): self.bridge.prepare_runtime(request, CHANNEL)
                self.assertEqual(self.bridge.dispatches, 0)
                # Fresh service/audit per rejected terminal attempt.
                self.fresh()

    def test_wrong_channel(self):
        with self.assertRaises(ModelDenied): self.bridge.prepare_runtime(self.request(), "f" * 64)
        self.assertEqual(self.bridge.dispatches, 0)

    def test_expired_and_cancelled_admission(self):
        self.clock.return_value = 2
        with self.assertRaises(ModelDenied): self.prepare()
        self.assertEqual(self.bridge.dispatches, 0)

    def test_cancel_after_authorization_before_dispatch(self):
        self.stream.flush.side_effect = self.bridge.revoke
        with self.assertRaises(ModelDenied): self.prepare()
        self.assertEqual(self.bridge.dispatches, 0)

    def test_cancel_after_dispatch_blocks_release(self):
        dispatch = self.bridge._provider.dispatch
        def cancel():
            result = dispatch(); self.bridge.revoke(); return result
        self.bridge._provider.dispatch = cancel
        with self.assertRaises(ModelDenied): self.prepare()
        self.assertEqual(self.bridge.dispatches, 1)
        self.assertEqual(self.bridge.prepared_runtime_releases, 0)

    def test_pre_send_required_audit_failure(self):
        self.stream.write.side_effect = OSError("private secret")
        with self.assertRaisesRegex(ModelDenied, "model_bridge.denied"): self.prepare()
        self.assertTrue(self.audit.failed)
        self.assertEqual(self.bridge.dispatches, 0)
        with self.assertRaises(ModelDenied): self.bridge.issue()

    def test_audit_failure_after_send_retains_effect(self):
        count = 0
        def write(raw):
            nonlocal count
            count += 1
            if count == 2: raise OSError("not public")
            return len(raw)
        self.stream.write.side_effect = write
        with self.assertRaisesRegex(ModelDenied, "model_bridge.uncertain"): self.prepare()
        self.assertTrue(self.audit.failed)
        self.assertEqual(self.bridge.dispatches, 1)
        self.assertEqual(self.bridge.prepared_runtime_releases, 0)

    def test_runtime_intent_audit_failure_prevents_release(self):
        self.stream.flush.side_effect = [None, None, OSError()]
        with self.assertRaises(ModelDenied): self.prepare()
        self.assertEqual(self.bridge.prepared_runtime_releases, 0)

    def test_confirmation_audit_failure_records_already_delivered_count(self):
        reply = self.prepare()
        self.stream.flush.side_effect = OSError()
        with self.assertRaises(ModelDenied):
            self.bridge.confirm_runtime_delivery(reply["response_sha256"], COORDINATOR)
        self.assertEqual(self.bridge.confirmed_runtime_releases, 1)
        self.assertTrue(self.audit.failed)

    def test_replayed_request_never_dispatches_twice(self):
        self.prepare()
        with self.assertRaises(ModelDenied): self.prepare()
        self.assertEqual(self.bridge.dispatches, 1)

    def test_wrong_runtime_confirmation_blocks_final_output(self):
        self.prepare()
        with self.assertRaises(ModelDenied): self.bridge.confirm_runtime_delivery("0" * 64, COORDINATOR)
        self.assertEqual(self.bridge.confirmed_runtime_releases, 0)
        with self.assertRaises(ModelDenied): self.bridge.prepare_operator(TEXT)

    def test_final_output_mismatch_is_not_disclosed(self):
        self.delivered()
        with self.assertRaises(ModelDenied): self.bridge.prepare_operator("unvalidated output")
        self.assertEqual(self.bridge.prepared_operator_releases, 0)

    def test_record_delivery_after_expiry_but_block_new_operation(self):
        reply = self.prepare(); self.clock.return_value = 3
        self.bridge.confirm_runtime_delivery(reply["response_sha256"], COORDINATOR)
        self.assertEqual(self.bridge.confirmed_runtime_releases, 1)
        with self.assertRaises(ModelDenied): self.bridge.prepare_operator(TEXT)

    def test_constrained_allow_is_not_executed(self):
        for result in (AuthorizationResult(GovernanceDecision.ALLOW, "x", constraints=("x",)),
                       AuthorizationResult(GovernanceDecision.ALLOW, "x", redactions={"x": "y"}),
                       AuthorizationResult(GovernanceDecision.REDACT, "x"), None):
            self.bridge._gateway = Mock(); self.bridge._gateway.authorize.return_value = result
            with self.assertRaises(ModelDenied): self.prepare()
            self.assertEqual(self.bridge.dispatches, 0)
            self.fresh()

    def test_invalid_or_oversized_response(self):
        self.bridge._provider.dispatch = Mock(return_value=b"x" * 4097)
        with self.assertRaises(ModelDenied): self.prepare()
        self.assertTrue(self.bridge.dispatch_attempted)
        self.assertEqual(self.bridge.prepared_runtime_releases, 0)

    def test_request_wire_shape_limits(self):
        for raw in (b"{}", payload().replace(b"false", b"true"), payload()+b"x"*4096,
                    b'{"model":"x","model":"y"}', b'\xef\xbb\xbf{}', b'{"x":NaN}'):
            with self.subTest(raw=raw[:20]), self.assertRaises((ModelDenied, ProtocolError)):
                checked_request(raw)

    def test_second_grant_is_not_another_budget(self):
        with self.assertRaises(ModelDenied): self.bridge.issue()

    def test_revoked_before_request(self):
        self.bridge.revoke()
        with self.assertRaises(ModelDenied): self.prepare()
        self.assertEqual(self.bridge.dispatches, 0)

    def test_extra_provider_response_data_is_never_released(self):
        raw = json.loads(self.bridge._provider.wire_reply())
        raw["debug"] = "private"
        self.bridge._provider.dispatch = Mock(return_value=json.dumps(raw).encode())
        with self.assertRaises(ModelDenied): self.prepare()
        self.assertEqual(self.bridge.prepared_runtime_releases, 0)

    def test_operator_audit_failure_blocks_operator_release(self):
        self.delivered()
        self.stream.flush.side_effect = OSError()
        with self.assertRaises(ModelDenied): self.bridge.prepare_operator(TEXT)
        self.assertEqual(self.bridge.prepared_operator_releases, 0)
        self.assertEqual(self.bridge.confirmed_runtime_releases, 1)

    def test_operator_confirmation_failure_retains_delivery_count(self):
        self.delivered(); self.bridge.prepare_operator(TEXT)
        self.stream.flush.side_effect = OSError()
        with self.assertRaises(ModelDenied): self.bridge.confirm_operator_delivery(digest(TEXT.encode()), COORDINATOR)
        self.assertEqual(self.bridge.confirmed_operator_releases, 1)

    def test_operator_delivery_confirmation_is_not_repeatable(self):
        self.delivered(); self.bridge.prepare_operator(TEXT)
        self.bridge.confirm_operator_delivery(digest(TEXT.encode()), COORDINATOR)
        with self.assertRaises(ModelDenied): self.bridge.confirm_operator_delivery(digest(TEXT.encode()), COORDINATOR)
        self.assertEqual(self.bridge.confirmed_operator_releases, 1)

    def test_final_text_without_runtime_delivery_is_rejected(self):
        self.prepare()
        with self.assertRaises(ModelDenied): self.bridge.prepare_operator(TEXT)
        self.assertEqual(self.bridge.prepared_operator_releases, 0)

    def test_synthetic_provider_has_no_second_dispatch(self):
        provider = SyntheticModel(TEXT); provider.dispatch()
        with self.assertRaises(ModelDenied): provider.dispatch()


class ModelTransportTests(unittest.TestCase):
    def channel(self, response=None):
        raw = SyntheticModel(TEXT).dispatch()
        reply = dict(v=1, type="model_response", attempt=ATTEMPT, seq=1, status="ok",
                     body=raw.decode(), response_sha256=digest(raw))
        if response: reply.update(response)
        self.output = io.BytesIO()
        pipe = PrivateChannel(io.BytesIO(encode(reply)), self.output)
        client = ModelChannelClient(pipe, ATTEMPT)
        client.bind_grant(dict(v=1, type="model_grant", attempt=ATTEMPT, route=ROUTE,
                              lease="d"*64, seq=1, ttl_ms=2000, request_sha256=digest(payload())))
        return client

    def request(self, **kwargs):
        args = dict(method="POST", url=ORIGIN+PATH, content=payload(),
                    headers={"authorization": "Bearer "+PUBLIC_KEY, "content-type": "application/json"})
        args.update(kwargs)
        return httpx.Request(**args)

    def test_real_httpx_serialization_no_network(self):
        channel = self.channel()
        with httpx.Client(transport=PipeModelTransport(channel), trust_env=False, follow_redirects=False) as client:
            result = client.post(ORIGIN+PATH, content=payload(),
                headers={"authorization": "Bearer "+PUBLIC_KEY, "content-type": "application/json"})
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()["choices"][0]["message"]["content"], TEXT)
        request = Decoder().feed(self.output.getvalue())[0]
        self.assertEqual(request["body"].encode(), payload())
        self.assertNotIn("authorization", request)

    def test_changed_route_method_or_headers_denied_without_pipe_send(self):
        for change in (dict(url="https://other.invalid"+PATH), dict(url=ORIGIN+PATH+"?x=1"),
                       dict(method="GET"), dict(headers={"authorization":"Bearer private"}),
                       dict(headers={"cookie":"x"})):
            channel = self.channel(); transport = PipeModelTransport(channel)
            with self.subTest(change=change), self.assertRaisesRegex(httpx.TransportError, "model_bridge.unavailable"):
                transport.handle_request(self.request(**change))
            self.assertEqual(self.output.getvalue(), b"")

    def test_response_digest_mismatch_is_terminal(self):
        channel = self.channel({"response_sha256":"0"*64})
        with self.assertRaises(httpx.TransportError): PipeModelTransport(channel).handle_request(self.request())
        self.assertTrue(channel.closed)

    def test_close_one_transport_does_not_close_shared_channel(self):
        channel = self.channel(); first = PipeModelTransport(channel); first.close()
        self.assertFalse(channel.closed)
        self.assertEqual(PipeModelTransport(channel).handle_request(self.request()).status_code, 200)
        with self.assertRaises(httpx.TransportError): PipeModelTransport(channel).handle_request(self.request())
        self.assertEqual(channel.requests, 1)

    def test_fresh_grant_cannot_reset_channel_budget(self):
        channel = self.channel()
        with self.assertRaises(ProtocolError): channel.bind_grant({})
        self.assertTrue(channel.closed)

    def test_short_write_is_terminal_and_not_retried(self):
        channel = self.channel()
        writer = Mock(); writer.write.return_value = 1
        channel.channel._destination = writer
        with self.assertRaises(httpx.TransportError): PipeModelTransport(channel).handle_request(self.request())
        self.assertEqual(writer.write.call_count, 1)
        self.assertTrue(channel.closed)

    def test_parallel_exchange_is_rejected(self):
        channel = self.channel()
        channel._lock.acquire()
        try:
            with self.assertRaises(ProtocolError): channel.exchange(payload())
        finally:
            channel._lock.release()
        self.assertTrue(channel.closed)
        self.assertEqual(self.output.getvalue(), b"")

    def test_lazy_stream_body_is_rejected(self):
        channel = self.channel()
        request = self.request(content=iter([payload()]))
        with self.assertRaises(httpx.TransportError): PipeModelTransport(channel).handle_request(request)
        self.assertEqual(self.output.getvalue(), b"")


class FactoryBase:
    """Inert native-factory interface fixture, never used in product construction."""
    def __init__(self, **kwargs):
        self.provider, self.api_mode = kwargs["provider"], kwargs["api_mode"]
        self._api_max_retries, self.valid_tool_names = 1, set()
        self._fallback_model, self._fallback_chain = None, []
        self.kwargs = dict(api_key=kwargs["api_key"], base_url=kwargs["base_url"])
        self.client = self._create_openai_client(self.kwargs, reason="init", shared=True)

    def _create_openai_client(self, kwargs, *, reason, shared):
        self.received = kwargs
        closed = [False]
        def close():
            closed[0] = True; kwargs["http_client"].close()
        return SimpleNamespace(max_retries=kwargs["max_retries"], close=close, is_closed=lambda: closed[0])


class FactoryFixture(OfflineModelClientMixin, FactoryBase):
    pass


class ModelFactoryTests(unittest.TestCase):
    def agent(self, cls=FactoryFixture, **changes):
        pipe = PrivateChannel(io.BytesIO(), io.BytesIO())
        channel = ModelChannelClient(pipe, ATTEMPT)
        kwargs = dict(maya_model_channel=channel, provider="custom", api_mode="chat_completions",
                      model=MODEL, base_url=ORIGIN+"/v1", api_key=PUBLIC_KEY,
                      fallback_model=None, credential_pool=None, max_tokens=32)
        kwargs.update(changes)
        return cls(**kwargs)

    def test_parent_delegation_preserves_kwargs_and_fresh_client_ownership(self):
        agent = self.agent()
        self.assertNotIn("http_client", agent.kwargs)
        self.assertNotIn("max_retries", agent.kwargs)
        self.assertTrue(agent._disable_streaming)
        first = agent._maya_model_clients[0]
        agent._create_openai_client(agent.kwargs, reason="request", shared=False)
        second = agent._maya_model_clients[1]
        self.assertIsNot(first[1], second[1])
        first[0].close()
        self.assertFalse(second[1].is_closed)
        self.assertFalse(agent._maya_model_channel.closed)
        self.assertEqual(second[0].max_retries, 0)
        agent.close_model_clients()
        self.assertTrue(second[1].is_closed)

    def test_unsupported_route_or_provider_rejected(self):
        for change in (dict(provider="other"), dict(api_mode="responses"), dict(api_key="private"),
                       dict(base_url="https://other.invalid/v1"), dict(model="other"),
                       dict(fallback_model={"model":"other"}), dict(credential_pool=object()),
                       dict(max_tokens=33), dict(max_tokens=True)):
            with self.subTest(change=change), self.assertRaises(ProtocolError): self.agent(**change)

    def test_caller_cannot_supply_http_client_or_headers(self):
        for key in ("http_client", "default_headers", "default_query"):
            agent = self.agent(); kwargs=agent.kwargs.copy(); kwargs[key]=object()
            with self.assertRaises(ProtocolError): agent._create_openai_client(kwargs, reason="x", shared=False)
            agent.close_model_clients()

    def test_parent_factory_failure_closes_new_http_client(self):
        agent = self.agent()
        with patch.object(FactoryBase, "_create_openai_client", side_effect=RuntimeError("not public")), \
             patch("project_maya.hermes_plugins.model_bridge.httpx.Client", wraps=httpx.Client) as constructor:
            with self.assertRaisesRegex(ProtocolError, "bridge.invalid_protocol"):
                agent._create_openai_client(agent.kwargs, reason="x", shared=False)
            # Actual original constructor creates an owned client; no socket is opened.
            self.assertEqual(constructor.call_count, 1)
        agent.close_model_clients()

    def test_close_failure_is_not_reported_healthy(self):
        agent = self.agent(); agent.client.close = Mock(side_effect=OSError())
        with self.assertRaises(ProtocolError): agent.close_model_clients()
        self.assertTrue(agent._maya_model_clients[0][1].is_closed)

    def test_bounded_client_recreation(self):
        agent = self.agent()
        for _ in range(7): agent._create_openai_client(agent.kwargs, reason="request", shared=False)
        with self.assertRaises(ProtocolError): agent._create_openai_client(agent.kwargs, reason="request", shared=False)
        agent.close_model_clients()


if __name__ == "__main__":
    unittest.main()

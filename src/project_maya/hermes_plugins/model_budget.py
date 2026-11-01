"""Fixed M05a observation; original transport validation and budget guard remain authority."""
import re
import threading

import httpx

from project_maya.bridge.model_service import ORIGIN, PATH, digest
from project_maya.bridge.protocol import ProtocolError
from .model_bridge import ModelChannelClient, OfflineModelClientMixin, PipeModelTransport

LIFECYCLE_PIN = "ff17762913d3e38aefa57fa22b56048f99d09fc18d189ab6441bf9c69433a76c"
PROBE_STAGES = frozenset(("unarmed", "armed", "close_entry", "owner_binding", "probe_control",
    "adapter_preflight", "used_client_select", "client_preflight", "request_snapshot",
    "second_request", "probe_postconditions", "native_close", "complete", "failed", "abort"))


def verify_lifecycle_source(root):
    if digest((root/"agent/chat_completion_helpers.py").read_bytes()) != LIFECYCLE_PIN:
        raise ProtocolError()


def successful_lifecycle():
    return dict(schema="maya.model.adapter_budget.lifecycle.v1", stage="complete", failure_stage="",
        armed=True, hook_calls=1, close_delegations=1, owner_thread_verified=True,
        used_client_verified=True, native_close_verified=True, probe_before_native_close=True)


class BudgetChannelClient(ModelChannelClient):
    def __init__(self, channel, attempt):
        super().__init__(channel, attempt)
        self.budget_rejections = 0

    def _budget_rejected(self):
        if (not self.closed and self._bound is True and self._grant is None
                and type(self.requests) is int and self.requests == 1):
            self.budget_rejections += 1


class BudgetPipeTransport(PipeModelTransport):
    def __init__(self, channel):
        if type(channel) is not BudgetChannelClient:
            raise ProtocolError()
        super().__init__(channel)
        self.validated_attempts = self.completed_exchanges = 0
        self.first = None
        self.owner_thread = None

    def _validated_request(self, request):
        snapshot = (request.method, str(request.url), tuple(request.headers.raw), bytes(request.content))
        if self.first is None:
            if self.validated_attempts or self.channel.requests:
                raise ProtocolError()
            self.first = snapshot
            self.owner_thread = threading.get_ident()
        elif snapshot != self.first:
            raise ProtocolError()
        self.validated_attempts += 1
        if self.validated_attempts > 2:
            raise ProtocolError()

    def _response_received(self):
        if self.owner_thread != threading.get_ident():
            raise ProtocolError()
        self.completed_exchanges += 1


class SameClientBudgetMixin(OfflineModelClientMixin):
    def __init__(self, **kwargs):
        self._budget_lock = threading.Lock()
        self._budget_state = dict(successful_lifecycle(), stage="unarmed", armed=False, hook_calls=0,
            close_delegations=0, owner_thread_verified=False, used_client_verified=False,
            native_close_verified=False, probe_before_native_close=False)
        self._budget_probe = None
        self._budget_command = ""
        super().__init__(**kwargs)

    def _maya_new_transport(self):
        return BudgetPipeTransport(self._maya_model_channel)

    def _budget_stage(self, stage):
        if stage not in PROBE_STAGES:
            raise ProtocolError()
        with self._budget_lock:
            if not self._budget_state["failure_stage"]:
                self._budget_state["stage"] = stage

    def _budget_fail(self, stage):
        with self._budget_lock:
            if not self._budget_state["failure_stage"]:
                self._budget_state["failure_stage"] = stage if stage in PROBE_STAGES else "close_entry"
            self._budget_state["stage"] = "failed"

    def arm_budget_probe(self):
        adapter = self._maya_model_channel
        with self._budget_lock:
            if (self._budget_state["armed"] or self._budget_state["hook_calls"] or self._budget_state["failure_stage"]
                    or type(adapter) is not BudgetChannelClient or adapter.closed or adapter.requests
                    or adapter._bound is not True or adapter._grant is None):
                raise ProtocolError()
            self._budget_state.update(armed=True, stage="armed")

    def budget_lifecycle_snapshot(self):
        with self._budget_lock:
            return self._budget_state.copy()

    @property
    def budget_probe_command_id(self):
        with self._budget_lock:
            return self._budget_command

    def finish_budget_probe(self):
        with self._budget_lock:
            if self._budget_state != successful_lifecycle() or self._budget_probe is None:
                raise ProtocolError()
            return self._budget_probe.copy()

    def _abort_request_openai_client(self, client, *, reason):
        self._budget_fail("abort")
        return super()._abort_request_openai_client(client, reason=reason)

    def _close_request_openai_client(self, client, *, reason):
        owned = None
        try:
            self._budget_stage("close_entry")
            with self._budget_lock:
                self._budget_state["hook_calls"] += 1
                if (not self._budget_state["armed"] or self._budget_state["hook_calls"] != 1
                        or self._budget_state["failure_stage"] or reason != "request_complete"):
                    raise ProtocolError()
            self._budget_stage("owner_binding")
            used = [(sdk, http, transport) for sdk, http, transport in self._maya_model_clients
                    if type(transport) is BudgetPipeTransport and transport.validated_attempts]
            if len(used) != 1 or used[0][0] is not client:
                raise ProtocolError()
            owned = used[0]
            if owned[2].owner_thread != threading.get_ident():
                raise ProtocolError()
            with self._budget_lock:
                self._budget_state.update(owner_thread_verified=True, used_client_verified=True)
            self._budget_stage("client_preflight")
            adapter = self._maya_model_channel
            if (owned[0].is_closed() or owned[1].is_closed or owned[2].closed or owned[2].channel is not adapter
                    or owned[2].validated_attempts != 1 or owned[2].completed_exchanges != 1
                    or type(adapter) is not BudgetChannelClient or adapter.closed or adapter.requests != 1
                    or adapter._bound is not True or adapter._grant is not None or adapter.budget_rejections):
                raise ProtocolError()
            # No lock is held across pipe I/O. An abort poisons final admission.
            self._budget_stage("probe_control")
            probe = self._maya_model_channel.channel.receive()
            if (type(probe) is not dict or set(probe) != {"v", "type", "attempt", "request_id"}
                    or type(probe["v"]) is not int or probe["v"] != 1 or probe["type"] != "model_adapter_probe"
                    or probe["attempt"] != self._maya_model_channel.attempt
                    or type(probe["request_id"]) is not str or not re.fullmatch(r"[0-9a-f]{32}", probe["request_id"])):
                raise ProtocolError()
            with self._budget_lock:
                self._budget_command = probe["request_id"]
                if self._budget_state["failure_stage"]:
                    raise ProtocolError()
            result = probe_same_client(self, observe=self._budget_stage)
            with self._budget_lock:
                if self._budget_state["failure_stage"]:
                    raise ProtocolError()
                self._budget_probe = result
                self._budget_state["probe_before_native_close"] = True
        except Exception:
            self._budget_fail(self.budget_lifecycle_snapshot()["stage"])
        finally:
            self._budget_stage("native_close")
            with self._budget_lock:
                self._budget_state["close_delegations"] += 1
            try:
                # Never suppress/defer/reopen native close, even when diagnosis fails.
                super()._close_request_openai_client(client, reason=reason)
                if owned is None or not (owned[0].is_closed() and owned[1].is_closed and owned[2].closed):
                    raise ProtocolError()
                with self._budget_lock:
                    self._budget_state["native_close_verified"] = True
            except Exception:
                self._budget_fail("native_close")
            if self.budget_lifecycle_snapshot()["failure_stage"] == "":
                self._budget_stage("complete")
        # A diagnostic failure is admitted only as failure AFTER conversation returns,
        # not raised here into Hermes's SDK retry/error machinery.


def probe_same_client(agent, *, observe=None):
    """Explicit second HTTP request, never an SDK retry or a second conversation."""
    def stage(name):
        if observe is not None:
            observe(name)

    stage("adapter_preflight")
    adapter = agent._maya_model_channel
    if (type(adapter) is not BudgetChannelClient or adapter.closed or not adapter._bound
            or adapter._grant is not None or adapter.requests != 1 or adapter.budget_rejections):
        raise ProtocolError()
    stage("used_client_select")
    used = [(sdk, client, transport) for sdk, client, transport in agent._maya_model_clients
            if type(transport) is BudgetPipeTransport and transport.validated_attempts]
    if len(used) != 1:
        raise ProtocolError()
    sdk, client, transport = used[0]
    stage("client_preflight")
    if (sdk.is_closed() or client.is_closed or transport.closed or transport.channel is not adapter
            or transport.validated_attempts != 1 or transport.completed_exchanges != 1 or transport.first is None):
        raise ProtocolError()
    stage("request_snapshot")
    method, url, headers, raw = transport.first
    if method != "POST" or url != ORIGIN+PATH:
        raise ProtocolError()
    # Request preserves the exact validated bytes and headers; no caller-selected payload.
    request = httpx.Request(method, url, headers=headers, content=raw)
    stage("second_request")
    try:
        response = client.send(request, follow_redirects=False)
    except httpx.TransportError as error:
        stage("probe_postconditions")
        if (type(error) is not httpx.TransportError or str(error) != "model_bridge.unavailable"
                or not adapter.closed or not transport.closed or adapter.budget_rejections != 1
                or adapter.requests != 1 or transport.validated_attempts != 2
                or transport.completed_exchanges != 1):
            raise ProtocolError() from None
    else:
        response.close()
        raise ProtocolError()
    return dict(case="M05a", boundary="adapter_consumed_budget", transport_attempts=2,
                model_requests=1, completed_exchanges=1, budget_rejections=1,
                same_used_client=True, request_sha256=digest(raw), request_bytes=len(raw))

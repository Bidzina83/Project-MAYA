"""Fixed M05b lifecycle observation; original factory, validation and guard are authority."""
import re
import threading

import httpx

from project_maya.bridge.model_service import digest
from project_maya.bridge.protocol import ProtocolError
from .model_bridge import OfflineModelClientMixin, PipeModelTransport
from .model_budget import BudgetChannelClient


def successful_lifecycle():
    return dict(schema="maya.model.recreate.lifecycle.v1", stage="complete", failure_stage="",
        armed=True, hook_calls=1, close_delegations=1, owner_thread_verified=True,
        used_client_verified=True, native_close_verified=True, probe_after_native_close=True,
        new_clients_distinct=True, same_adapter_verified=True, new_client_close_verified=True)


class RecreatePipeTransport(PipeModelTransport):
    def __init__(self, channel, expected=None):
        if type(channel) is not BudgetChannelClient:
            raise ProtocolError()
        super().__init__(channel)
        self.expected = expected
        self.first = self.owner_thread = None
        self.validated_attempts = self.completed_exchanges = 0

    def _validated_request(self, request):
        snapshot = (request.method, str(request.url), tuple(request.headers.raw), bytes(request.content))
        if self.validated_attempts or self.first is not None:
            raise ProtocolError()
        if self.expected is None:
            if self.channel.requests:
                raise ProtocolError()
        elif snapshot != self.expected or self.channel.requests != 1:
            raise ProtocolError()
        self.first, self.owner_thread = snapshot, threading.get_ident()
        self.validated_attempts = 1

    def _response_received(self):
        if self.owner_thread != threading.get_ident():
            raise ProtocolError()
        self.completed_exchanges += 1


class RecreatedClientBudgetMixin(OfflineModelClientMixin):
    def __init__(self, **kwargs):
        self._recreate_lock = threading.Lock()
        self._recreate_state = dict(successful_lifecycle(), stage="unarmed", armed=False,
            hook_calls=0, close_delegations=0, owner_thread_verified=False,
            used_client_verified=False, native_close_verified=False, probe_after_native_close=False,
            new_clients_distinct=False, same_adapter_verified=False, new_client_close_verified=False)
        self._recreate_expected = None
        self._recreate_factories = []
        self._recreate_probe = None
        self._recreate_command = ""
        super().__init__(**kwargs)

    def _maya_new_transport(self):
        return RecreatePipeTransport(self._maya_model_channel, self._recreate_expected)

    def _create_openai_client(self, client_kwargs, *, reason, shared):
        # Capture only the fixed factory input, never modify native client kwargs.
        copied = client_kwargs.copy() if type(client_kwargs) is dict else None
        client = super()._create_openai_client(client_kwargs, reason=reason, shared=shared)
        self._recreate_factories.append((client, copied, reason, shared))
        return client

    def _stage(self, stage):
        with self._recreate_lock:
            if not self._recreate_state["failure_stage"]:
                self._recreate_state["stage"] = stage

    def _fail(self, stage):
        with self._recreate_lock:
            if not self._recreate_state["failure_stage"]:
                self._recreate_state["failure_stage"] = stage
            self._recreate_state["stage"] = "failed"
        self._maya_model_channel.closed = True

    def _flag(self, **values):
        with self._recreate_lock:
            if self._recreate_state["failure_stage"]:
                raise ProtocolError()
            self._recreate_state.update(values)

    def budget_lifecycle_snapshot(self):
        with self._recreate_lock:
            return self._recreate_state.copy()

    @property
    def budget_probe_command_id(self):
        with self._recreate_lock:
            return self._recreate_command

    def arm_budget_probe(self):
        adapter = self._maya_model_channel
        with self._recreate_lock:
            if (self._recreate_state["armed"] or self._recreate_state["hook_calls"]
                    or self._recreate_state["failure_stage"] or type(adapter) is not BudgetChannelClient
                    or adapter.closed or adapter.requests or adapter._bound is not True or adapter._grant is None):
                raise ProtocolError()
            self._recreate_state.update(armed=True, stage="armed")

    def finish_budget_probe(self):
        with self._recreate_lock:
            if self._recreate_state != successful_lifecycle() or self._recreate_probe is None:
                raise ProtocolError()
            return self._recreate_probe.copy()

    def _abort_request_openai_client(self, client, *, reason):
        self._fail("abort")
        return super()._abort_request_openai_client(client, reason=reason)

    def _close_request_openai_client(self, client, *, reason):
        owned = factory = None
        adapter = self._maya_model_channel
        try:
            self._stage("close_entry")
            with self._recreate_lock:
                self._recreate_state["hook_calls"] += 1
                if (not self._recreate_state["armed"] or self._recreate_state["hook_calls"] != 1
                        or self._recreate_state["failure_stage"] or reason != "request_complete"):
                    raise ProtocolError()
            self._stage("owner_binding")
            used = [triple for triple in self._maya_model_clients
                    if type(triple[2]) is RecreatePipeTransport and triple[2].completed_exchanges]
            if len(used) != 1 or used[0][0] is not client:
                raise ProtocolError()
            owned = used[0]
            if owned[2].owner_thread != threading.get_ident():
                raise ProtocolError()
            self._flag(owner_thread_verified=True, used_client_verified=True)
            self._stage("old_client_preflight")
            self._adapter_preflight(adapter)
            if (owned[0].is_closed() or owned[1].is_closed or owned[2].closed
                    or owned[2].channel is not adapter or owned[2].validated_attempts != 1
                    or owned[2].completed_exchanges != 1 or owned[2].first is None):
                raise ProtocolError()
            factories = [item for item in self._recreate_factories if item[0] is client]
            if (len(factories) != 1 or factories[0][2] != "chat_completion_request"
                    or factories[0][3] is not False):
                raise ProtocolError()
            factory = factories[0]
        except Exception:
            self._fail(self.budget_lifecycle_snapshot()["stage"])
        finally:
            self._stage("native_close")
            with self._recreate_lock:
                self._recreate_state["close_delegations"] += 1
            try:
                super()._close_request_openai_client(client, reason=reason)
                if owned is None or not (owned[0].is_closed() and owned[1].is_closed and owned[2].closed):
                    raise ProtocolError()
                self._flag(native_close_verified=True)
            except Exception:
                self._fail("native_close")
        if self.budget_lifecycle_snapshot()["failure_stage"]:
            return
        new = None
        try:
            self._stage("probe_control")
            control = adapter.channel.receive()
            if (type(control) is not dict or set(control) != {"v", "type", "attempt", "request_id"}
                    or type(control["v"]) is not int or control["v"] != 1
                    or control["type"] != "model_adapter_probe" or control["attempt"] != adapter.attempt
                    or type(control["request_id"]) is not str or not re.fullmatch(r"[0-9a-f]{32}", control["request_id"])):
                raise ProtocolError()
            with self._recreate_lock:
                self._recreate_command = control["request_id"]
            self._stage("factory_recreation")
            self._adapter_preflight(adapter)
            before = tuple(self._maya_model_clients)
            self._recreate_expected = owned[2].first
            sdk = self._create_openai_client(factory[1].copy(), reason=factory[2], shared=False)
            if len(self._maya_model_clients) != len(before)+1:
                raise ProtocolError()
            new = self._maya_model_clients[-1]
            if (new[0] is not sdk or any(new[i] is old[i] for old in before for i in range(3))
                    or any(self._maya_model_clients[i] is not before[i] for i in range(len(before)))
                    or type(new[0]) is not type(owned[0]) or type(new[1]) is not httpx.Client
                    or type(new[2]) is not RecreatePipeTransport or new[2].channel is not adapter
                    or self._maya_model_channel is not adapter or new[0].is_closed()
                    or new[1].is_closed or new[2].closed or new[0].max_retries != 0):
                raise ProtocolError()
            self._adapter_preflight(adapter)
            self._flag(new_clients_distinct=True, same_adapter_verified=True, probe_after_native_close=True)
            self._stage("second_request")
            method, url, headers, raw = owned[2].first
            try:
                response = new[1].send(httpx.Request(method, url, headers=headers, content=raw), follow_redirects=False)
            except httpx.TransportError as error:
                if (type(error) is not httpx.TransportError or str(error) != "model_bridge.unavailable"
                        or not adapter.closed or not new[2].closed or adapter.budget_rejections != 1
                        or adapter.requests != 1 or new[2].validated_attempts != 1
                        or new[2].completed_exchanges != 0 or new[2].first != owned[2].first
                        or new[2].owner_thread != owned[2].owner_thread):
                    raise ProtocolError() from None
            else:
                response.close()
                raise ProtocolError()
            self._recreate_probe = dict(case="M05b", boundary="adapter_consumed_budget", transport_attempts=2,
                model_requests=1, completed_exchanges=1, budget_rejections=1,
                distinct_new_clients=True, same_consumed_adapter=True, request_sha256=digest(raw), request_bytes=len(raw))
        except Exception:
            self._fail(self.budget_lifecycle_snapshot()["stage"])
        finally:
            self._recreate_expected = None
            if new is not None:
                self._stage("new_client_close")
                try:
                    new[0].close()
                    new[1].close()
                    if not (new[0].is_closed() and new[1].is_closed and new[2].closed):
                        raise ProtocolError()
                    self._flag(new_client_close_verified=True)
                except Exception:
                    self._fail("new_client_close")
            if not self.budget_lifecycle_snapshot()["failure_stage"]:
                self._stage("complete")
        # Never feed diagnostic errors into native SDK retry/fallback logic.

    @staticmethod
    def _adapter_preflight(adapter):
        if (type(adapter) is not BudgetChannelClient or adapter.closed or adapter.requests != 1
                or adapter._bound is not True or adapter._grant is not None or adapter.budget_rejections):
            raise ProtocolError()

"""Pinned Hermes factory integration and non-network OpenAI-wire transport.

No native Hermes or OpenAI import occurs until explicit product construction.
Transport settings are compatibility plumbing, not the authorization authority.
"""
from __future__ import annotations

import hashlib
import inspect
from pathlib import Path
import re
import threading

import httpx

from project_maya.bridge.model_service import MODEL, ORIGIN, PATH, PUBLIC_KEY, ROUTE, checked_request, digest
from project_maya.bridge.protocol import ProtocolError, decode
from project_maya.bridge.transport import PrivateChannel

PINNED_SOURCES = {
    "run_agent.py": "7a36be48ffdc0fe62b855263683d55c1c7138cc65acf597175920fcf86b45bd5",
    "agent/agent_runtime_helpers.py": "1a0fb199102e02261d22bfaa7b64e5d3bb8e9fd6642696551e6b0ff7f278dac9",
    "agent/conversation_loop.py": "b32a7c2ef5f0f607488a92e6e513d267bd6f49f9a2564c1301c2e5dfea7ba4e8",
}


class ModelChannelClient:
    """Single-inflight child-side pipe endpoint shared by separately owned SDKs."""
    def __init__(self, channel: PrivateChannel, attempt: str) -> None:
        if (not isinstance(channel, PrivateChannel) or type(attempt) is not str
                or not re.fullmatch(r"[0-9a-f]{32}", attempt)):
            raise ProtocolError()
        self.channel, self.attempt = channel, attempt
        self._grant = None
        self._bound = False
        self._lock = threading.Lock()
        self.closed = False
        self.requests = 0

    def bind_grant(self, grant: dict) -> None:
        with self._lock:
            if (self.closed or self._bound or type(grant) is not dict or set(grant) !=
                    {"v", "type", "attempt", "route", "lease", "seq", "ttl_ms", "request_sha256"}
                    or type(grant["v"]) is not int or grant["v"] != 1 or grant["type"] != "model_grant"
                    or grant["attempt"] != self.attempt or grant["route"] != ROUTE
                    or type(grant["seq"]) is not int or grant["seq"] != 1
                    or type(grant["ttl_ms"]) is not int or grant["ttl_ms"] != 2000
                    or any(type(grant[k]) is not str or not re.fullmatch(r"[0-9a-f]{64}", grant[k])
                           for k in ("lease", "request_sha256"))):
                self.closed = True
                raise ProtocolError()
            self._grant, self._bound = grant.copy(), True

    def exchange(self, raw: bytes) -> bytes:
        if not self._lock.acquire(blocking=False):
            self.closed = True
            raise ProtocolError()
        try:
            if self.closed or self._grant is None or self.requests:
                raise ProtocolError()
            checked_request(raw)
            grant, self._grant = self._grant, None
            if digest(raw) != grant["request_sha256"]:
                raise ProtocolError()
            self.requests += 1
            self.channel.send(dict(v=1, type="model_request", attempt=self.attempt, route=ROUTE,
                lease=grant["lease"], seq=1, method="POST", path=PATH, body=raw.decode("utf-8")))
            reply = self.channel.receive()
            if (type(reply) is not dict or set(reply) !=
                    {"v", "type", "attempt", "seq", "status", "body", "response_sha256"}
                    or type(reply["v"]) is not int or reply["v"] != 1
                    or reply["type"] != "model_response" or reply["attempt"] != self.attempt
                    or type(reply["seq"]) is not int or reply["seq"] != 1
                    or reply["status"] != "ok" or type(reply["body"]) is not str):
                raise ProtocolError()
            response = reply["body"].encode("utf-8", errors="strict")
            if not 1 <= len(response) <= 4096 or digest(response) != reply["response_sha256"]:
                raise ProtocolError()
            decode(response)
            if self.closed:
                raise ProtocolError()
            self.channel.send(dict(v=1, type="model_runtime_receipt", attempt=self.attempt,
                                   response_sha256=digest(response), bytes=len(response)))
            return response
        except Exception:
            self.closed = True
            raise ProtocolError() from None
        finally:
            self._lock.release()


class PipeModelTransport(httpx.BaseTransport):
    """Actual httpx transport that cannot create an HTTP/network connection."""
    _headers = frozenset({"host", "content-type", "content-length", "authorization", "accept",
        "accept-encoding", "connection", "user-agent", "x-stainless-lang", "x-stainless-package-version",
        "x-stainless-os", "x-stainless-arch", "x-stainless-runtime", "x-stainless-runtime-version",
        "x-stainless-async", "x-stainless-retry-count", "x-stainless-read-timeout"})

    def __init__(self, channel: ModelChannelClient) -> None:
        if not isinstance(channel, ModelChannelClient):
            raise ProtocolError()
        self.channel = channel
        self.closed = False

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        try:
            if self.closed or request.method != "POST" or str(request.url) != ORIGIN + PATH:
                raise ProtocolError()
            names = [key.decode("ascii").lower() for key, _ in request.headers.raw]
            if len(set(names)) != len(names) or not set(names) <= self._headers:
                raise ProtocolError()
            if (request.headers.get("host") != "maya-offline-model.invalid"
                    or request.headers.get("authorization") != "Bearer " + PUBLIC_KEY
                    or request.headers.get("content-type") != "application/json"
                    or request.headers.get("x-stainless-retry-count", "0") != "0"):
                raise ProtocolError()
            # SDK sends a materialized JSON body; reject lazy/streaming bodies.
            raw = request.content
            checked_request(raw)
            if request.headers.get("content-length") != str(len(raw)):
                raise ProtocolError()
            response = self.channel.exchange(raw)
            return httpx.Response(200, headers={"content-type": "application/json"},
                                  content=response, request=request)
        except Exception:
            self.closed = True
            self.channel.closed = True
            raise httpx.TransportError("model_bridge.unavailable") from None

    def close(self) -> None:
        # Each SDK owns this transport, but not the shared coordinator pipe handles.
        self.closed = True


class OfflineModelClientMixin:
    """Version-bound real-AIAgent mixin; does not replace native conversation code."""
    _disable_streaming = True

    def __init__(self, *, maya_model_channel: ModelChannelClient, **kwargs) -> None:
        if (not isinstance(maya_model_channel, ModelChannelClient)
                or kwargs.get("provider") != "custom" or kwargs.get("api_mode") != "chat_completions"
                or kwargs.get("base_url") != ORIGIN + "/v1" or kwargs.get("model") != MODEL
                or kwargs.get("api_key") != PUBLIC_KEY or kwargs.get("fallback_model") is not None
                or kwargs.get("credential_pool") is not None
                or type(kwargs.get("max_tokens")) is not int or kwargs["max_tokens"] != 32):
            raise ProtocolError()
        self._maya_model_channel = maya_model_channel
        self._maya_factory_lock = threading.RLock()
        self._maya_model_clients: list[tuple[object, httpx.Client, PipeModelTransport]] = []
        try:
            super().__init__(**kwargs)
            if (self._disable_streaming is not True or type(self._api_max_retries) is not int
                    or self._api_max_retries != 1
                    or self.valid_tool_names != set() or self._fallback_model is not None
                    or self._fallback_chain != []
                    or not self._maya_model_clients):
                raise ProtocolError()
        except Exception:
            self._maya_model_channel.closed = True
            self.close_model_clients()
            raise ProtocolError() from None

    def _create_openai_client(self, client_kwargs: dict, *, reason: str, shared: bool):
        with self._maya_factory_lock:
            return self._maya_create_client(client_kwargs, reason=reason, shared=shared)

    def _maya_create_client(self, client_kwargs: dict, *, reason: str, shared: bool):
        if (type(client_kwargs) is not dict or not set(client_kwargs) <=
                {"api_key", "base_url", "timeout", "max_retries"}
                or client_kwargs.get("api_key") != PUBLIC_KEY
                or str(client_kwargs.get("base_url")) != ORIGIN + "/v1"
                or self.provider != "custom" or self.api_mode != "chat_completions"
                or len(self._maya_model_clients) >= 8 or self._maya_model_channel.closed):
            raise ProtocolError()
        kwargs = client_kwargs.copy()
        transport = PipeModelTransport(self._maya_model_channel)
        http_client = httpx.Client(transport=transport, trust_env=False, follow_redirects=False, timeout=2.0)
        kwargs["http_client"], kwargs["max_retries"] = http_client, 0
        kwargs["timeout"] = 2.0
        client = None
        try:
            client = super()._create_openai_client(kwargs, reason=reason, shared=shared)
            if client.max_retries != 0:
                raise ProtocolError()
        except Exception:
            try:
                if client is not None:
                    client.close()
            except Exception:
                pass
            try:
                http_client.close()
            except Exception:
                pass
            raise ProtocolError() from None
        self._maya_model_clients.append((client, http_client, transport))
        return client

    def close_model_clients(self) -> None:
        failures = False
        with self._maya_factory_lock:
            self._maya_model_channel.closed = True
            clients = tuple(self._maya_model_clients)
        for client, http_client, transport in clients:
            try:
                client.close()
                http_client.close()
                if not client.is_closed() or not http_client.is_closed or not transport.closed:
                    failures = True
            except Exception:
                failures = True
                try:
                    http_client.close()
                except Exception:
                    pass
        if failures:
            raise ProtocolError()


def offline_agent_class():
    """Import real pinned Hermes only during separately approved product execution."""
    from run_agent import AIAgent

    filename = inspect.getsourcefile(AIAgent)
    if AIAgent.__module__ != "run_agent" or filename is None:
        raise ProtocolError()
    root = Path(filename).resolve().parent
    if any(digest((root / name).read_bytes()) != expected for name, expected in PINNED_SOURCES.items()):
        raise ProtocolError()

    class OfflineModelAgent(OfflineModelClientMixin, AIAgent):
        pass

    return OfflineModelAgent

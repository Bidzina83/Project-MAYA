"""Offline model-wire admission. No network, credentials or generic URL dispatch."""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import threading
import time
from collections.abc import Callable

from project_maya.audit import AuditRecord
from project_maya.governance import ActionRequest, AuthorizationResult, GovernanceDecision

from .audit import RequiredAudit
from .protocol import decode, encode
from .service import HostBinding

ORIGIN = "https://maya-offline-model.invalid"
PATH = "/v1/chat/completions"
MODEL = "maya-offline-wire-v1"
ROUTE = "maya.offline.model.v1"
PUBLIC_KEY = "maya-public-nonsecret-offline-wire-only"
TARGET = "model:maya-offline-fixture"


class ModelDenied(PermissionError):
    def __init__(self, uncertain: bool = False) -> None:
        self.uncertain = uncertain
        super().__init__("model_bridge.uncertain" if uncertain else "model_bridge.denied")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def checked_request(raw: bytes) -> dict:
    if type(raw) is not bytes or not 1 <= len(raw) <= 4096:
        raise ModelDenied()
    body = decode(raw)
    if (set(body) != {"model", "messages", "max_tokens", "stream"}
            or body["model"] != MODEL or body["stream"] is not False
            or type(body["max_tokens"]) is not int or not 1 <= body["max_tokens"] <= 32
            or type(body["messages"]) is not list or not 1 <= len(body["messages"]) <= 4):
        raise ModelDenied()
    for item in body["messages"]:
        if (type(item) is not dict or set(item) != {"role", "content"}
                or item["role"] not in ("system", "user") or type(item["content"]) is not str
                or not item["content"] or len(item["content"].encode("utf-8")) > 4096):
            raise ModelDenied()
    return body


class SyntheticModel:
    """Explicit wire-format fixture, never a model or a provider substitute claim."""
    def __init__(self, text: str) -> None:
        if type(text) is not str or not 1 <= len(text.encode("utf-8")) <= 1024:
            raise ValueError("model_bridge.invalid_fixture")
        self.text = text
        self.dispatches = 0

    def dispatch(self) -> bytes:
        if self.dispatches:
            raise ModelDenied()
        self.dispatches += 1
        return self.wire_reply()

    def wire_reply(self) -> bytes:
        return json.dumps(dict(id="maya-offline-synthetic", object="chat.completion", created=0,
            model=MODEL, choices=[dict(index=0, message=dict(role="assistant", content=self.text),
                                      finish_reason="stop")],
            usage=dict(prompt_tokens=0, completion_tokens=0, total_tokens=0)),
            ensure_ascii=True, separators=(",", ":")).encode("ascii")


class OfflineModelBridge:
    """Trusted host-only service; raw child messages carry no authority.

    expected_request and fixture text must originate in verified host setup.
    Preparation counters do not assert delivery. Only separately bound coordinator
    confirmations can record delivery; they are not child protocol operations.
    This class has no production provider mode and never opens a path or socket.
    """
    def __init__(self, binding: HostBinding, gateway, audit: RequiredAudit,
                 expected_request: bytes, fixture_text: str,
                 clock: Callable[[], float] = time.monotonic) -> None:
        if not isinstance(binding, HostBinding) or not isinstance(audit, RequiredAudit):
            raise ValueError("model_bridge.missing_host_services")
        checked_request(expected_request)
        self.binding, self._gateway, self._audit, self._clock = binding, gateway, audit, clock
        self._expected = expected_request
        self._provider = SyntheticModel(fixture_text)
        self._expected_response = self._provider.wire_reply()
        if len(self._expected_response) > 4096:
            raise ValueError("model_bridge.invalid_fixture")
        self._lock = threading.RLock()
        self._token: str | None = None
        self._expires = 0.0
        self._phase = "new"
        self._revoked = False
        self._closed = False
        self._request_id = secrets.token_hex(16)
        self._response: bytes | None = None
        self._destination = "provider"
        self.dispatch_attempted = False
        self.prepared_runtime_releases = self.confirmed_runtime_releases = 0
        self.prepared_operator_releases = self.confirmed_operator_releases = 0

    @property
    def dispatches(self) -> int:
        return self._provider.dispatches

    @property
    def request_id(self) -> str:
        return self._request_id

    @property
    def closed(self) -> bool:
        return self._closed

    def _live(self, phase: str) -> None:
        if (self._closed or self._audit.failed or self._revoked or self._phase != phase
                or self._clock() >= self._expires):
            raise ModelDenied(self.dispatch_attempted)

    def issue(self) -> dict:
        with self._lock:
            if self._closed or self._audit.failed or self._phase != "new":
                raise ModelDenied(self.dispatch_attempted)
            self._token, self._expires, self._phase = secrets.token_hex(32), self._clock() + 2, "issued"
            return dict(v=1, type="model_grant", attempt=self.binding.attempt, route=ROUTE,
                lease=self._token, seq=1, ttl_ms=2000, request_sha256=digest(self._expected))

    def revoke(self) -> None:
        with self._lock:
            self._revoked = True

    def close(self) -> None:
        with self._lock:
            self._revoked = self._closed = True

    def _authorize(self, capability: str, destination: str) -> None:
        result = self._gateway.authorize(ActionRequest(
            actor_id="windows:" + self.binding.operator_sid, capability=capability,
            target=TARGET, operation="infer" if capability == "model.egress" else "disclose",
            data_classification="internal-synthetic", metadata=self._metadata(destination)))
        if (not isinstance(result, AuthorizationResult) or result.decision is not GovernanceDecision.ALLOW
                or result.constraints or result.redactions):
            raise ModelDenied(self.dispatch_attempted)

    def _metadata(self, destination: str) -> dict[str, str]:
        return dict(attempt=self.binding.attempt, request_id=self._request_id, route=ROUTE,
                    endpoint=ORIGIN + PATH, model=MODEL, destination=destination,
                    request_sha256=digest(self._expected),
                    response_sha256=digest(self._response) if self._response is not None else "",
                    request_bytes=str(len(self._expected)),
                    response_bytes=str(len(self._response)) if self._response is not None else "0",
                    output_sha256=digest(self._provider.text.encode("utf-8")),
                    dispatches=str(self.dispatches), real_inference="false")

    def _event(self, stage: str, destination: str, allowed: bool = True,
               coordinator_request_id: str = "") -> None:
        metadata = self._metadata(destination)
        if stage in ("runtime_delivery", "operator_delivery"):
            metadata["coordinator_request_id"] = coordinator_request_id
        self._audit.write(AuditRecord(event_type="model_bridge." + stage,
            decision="allow" if allowed else "deny", reason_code="model_bridge." + stage,
            actor_id="windows:" + self.binding.operator_sid,
            capability="model.egress" if destination == "provider" else "model.output",
            target=TARGET, operation="infer" if destination == "provider" else "disclose",
            data_classification="internal-synthetic", metadata=metadata))

    def _fail(self) -> None:
        if not self._closed and not self._audit.failed:
            try:
                self._event("denied", self._destination, False)
            except Exception:
                pass
        self.close()
        raise ModelDenied(self.dispatch_attempted) from None

    def prepare_runtime(self, message: dict, channel_id: str) -> dict:
        """Return an audited prepared reply, NOT a claim of child-pipe delivery."""
        try:
            with self._lock:
                self._live("issued")
                if (type(message) is not dict or set(message) !=
                        {"v", "type", "attempt", "route", "lease", "seq", "method", "path", "body"}
                        or type(message["v"]) is not int or message["v"] != 1
                        or message["type"] != "model_request" or message["attempt"] != self.binding.attempt
                        or message["route"] != ROUTE or type(message["seq"]) is not int or message["seq"] != 1
                        or message["method"] != "POST" or message["path"] != PATH
                        or type(channel_id) is not str or not hmac.compare_digest(channel_id, self.binding.channel_id)
                        or type(message["lease"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", message["lease"])
                        or not hmac.compare_digest(message["lease"], self._token or "")
                        or type(message["body"]) is not str):
                    raise ModelDenied()
                raw = message["body"].encode("utf-8", errors="strict")
                checked_request(raw)
                if not hmac.compare_digest(raw, self._expected):
                    raise ModelDenied()
                self._phase = "admitted"
            self._authorize("model.egress", "provider")
            self._event("egress_intent", "provider")
            with self._lock:
                self._live("admitted")
                self.dispatch_attempted = True
                raw = self._provider.dispatch()
                if type(raw) is not bytes or not 1 <= len(raw) <= 4096:
                    raise ModelDenied(True)
                # The provider is an explicit fixed fixture, not extensible transport.
                decode(raw)
                if not hmac.compare_digest(raw, self._expected_response):
                    raise ModelDenied(True)
                self._response = raw
                self._phase = "dispatched"
            self._event("dispatch_outcome", "provider")
            self._destination = "runtime:" + self.binding.attempt
            self._authorize("model.output", "runtime:" + self.binding.attempt)
            self._event("runtime_release_intent", "runtime:" + self.binding.attempt)
            with self._lock:
                self._live("dispatched")
                reply = dict(v=1, type="model_response", attempt=self.binding.attempt, seq=1,
                    status="ok", body=raw.decode("utf-8"), response_sha256=digest(raw))
                encode(reply)
                self._phase = "runtime_prepared"
                self.prepared_runtime_releases = 1
                return reply
        except Exception:
            self._fail()

    def confirm_runtime_delivery(self, response_sha256: str, coordinator_request_id: str) -> None:
        try:
            with self._lock:
                # Observe a prior write even if expiry/revocation has since occurred.
                # This records an effect; it never grants a new protected operation.
                if self._closed or self._audit.failed or self._phase != "runtime_prepared":
                    raise ModelDenied(True)
                if (type(response_sha256) is not str or self._response is None
                        or not hmac.compare_digest(response_sha256, digest(self._response))
                        or type(coordinator_request_id) is not str
                        or not re.fullmatch(r"[0-9a-f]{32}", coordinator_request_id)):
                    raise ModelDenied(True)
                # Confirmation is from the trusted coordinator, never child testimony.
                self.confirmed_runtime_releases = 1
                self._event("runtime_delivery", "runtime:" + self.binding.attempt,
                            coordinator_request_id=coordinator_request_id)
                self._phase = "runtime_delivered"
        except Exception:
            self._fail()

    def prepare_operator(self, final_text: str) -> str:
        try:
            with self._lock:
                self._live("runtime_delivered")
                self._destination = "operator"
                if type(final_text) is not str or final_text != self._provider.text:
                    raise ModelDenied(True)
                self._phase = "operator_admitted"
            self._authorize("model.output", "operator")
            self._event("operator_release_intent", "operator")
            with self._lock:
                self._live("operator_admitted")
                self.prepared_operator_releases = 1
                self._phase = "operator_prepared"
                return final_text
        except Exception:
            self._fail()

    def confirm_operator_delivery(self, text_sha256: str, coordinator_request_id: str) -> None:
        try:
            with self._lock:
                if self._closed or self._audit.failed or self._phase != "operator_prepared":
                    raise ModelDenied(True)
                if (type(text_sha256) is not str
                        or not hmac.compare_digest(text_sha256, digest(self._provider.text.encode("utf-8")))
                        or type(coordinator_request_id) is not str
                        or not re.fullmatch(r"[0-9a-f]{32}", coordinator_request_id)):
                    raise ModelDenied(True)
                self.confirmed_operator_releases = 1
                self._event("operator_delivery", "operator", coordinator_request_id=coordinator_request_id)
                self._phase = "complete"
                self._closed = True
        except Exception:
            self._fail()

"""Authenticated local API boundary for Project MAYA."""

from __future__ import annotations

import hmac
import json
from dataclasses import dataclass, field
from typing import Mapping, Protocol, runtime_checkable

from .agent import Agent, AgentError
from .agent.contracts import AgentRuntime
from .governance import ActionDeniedError
from .secrets import SecretRef, SecretStore, SecretStoreError


class LocalAPIError(RuntimeError):
    """Raised when the local API cannot handle a request."""


@dataclass(frozen=True)
class LocalAPIRequest:
    method: str
    path: str
    headers: Mapping[str, str] = field(default_factory=dict)
    body: bytes = b""


@dataclass(frozen=True)
class LocalAPIResponse:
    status_code: int
    body: Mapping[str, object]
    headers: Mapping[str, str] = field(
        default_factory=lambda: {"content-type": "application/json"}
    )

    def json_bytes(self) -> bytes:
        return json.dumps(self.body, sort_keys=True).encode("utf-8")


@runtime_checkable
class LocalAPIAuthenticator(Protocol):
    def authenticate(self, headers: Mapping[str, str]) -> bool:
        """Return whether request headers identify an authorized local client."""


class BearerTokenAuthenticator:
    """Bearer-token authenticator backed by the configured secret store."""

    def __init__(
        self,
        secret_store: SecretStore,
        token_ref: SecretRef | None = None,
    ) -> None:
        self._secret_store = secret_store
        self._token_ref = token_ref or SecretRef.parse("secret://local-api/token")

    def authenticate(self, headers: Mapping[str, str]) -> bool:
        authorization = _header(headers, "authorization")
        if not authorization.startswith("Bearer "):
            return False
        supplied = authorization.removeprefix("Bearer ").strip()
        if not supplied:
            return False
        try:
            expected = self._secret_store.read(self._token_ref)
        except SecretStoreError:
            return False
        return hmac.compare_digest(supplied, expected)


class LocalAPI:
    """Minimal authenticated local request handler.

    This is the product API boundary. A future HTTP server should delegate to
    this handler rather than calling the agent directly.
    """

    def __init__(
        self,
        *,
        agent: Agent,
        runtime: AgentRuntime,
        authenticator: LocalAPIAuthenticator,
        max_body_bytes: int = 65536,
    ) -> None:
        if max_body_bytes < 1:
            raise ValueError("max_body_bytes must be positive")
        self._agent = agent
        self._runtime = runtime
        self._authenticator = authenticator
        self._max_body_bytes = max_body_bytes

    def handle(self, request: LocalAPIRequest) -> LocalAPIResponse:
        if not request.path.startswith("/v1/"):
            return _json_response(404, "not_found", "route not found")
        if not self._authenticator.authenticate(request.headers):
            return _json_response(401, "unauthorized", "authentication required")
        if len(request.body) > self._max_body_bytes:
            return _json_response(413, "request_too_large", "request body too large")
        if request.path == "/v1/health":
            return self._health(request)
        if request.path == "/v1/run":
            return self._run(request)
        return _json_response(404, "not_found", "route not found")

    def _health(self, request: LocalAPIRequest) -> LocalAPIResponse:
        if request.method.upper() != "GET":
            return _json_response(405, "method_not_allowed", "method not allowed")
        health = self._runtime.health()
        return LocalAPIResponse(
            status_code=200,
            body={
                "status": "ok",
                "runtime": health.state.value,
            },
        )

    def _run(self, request: LocalAPIRequest) -> LocalAPIResponse:
        if request.method.upper() != "POST":
            return _json_response(405, "method_not_allowed", "method not allowed")
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return _json_response(400, "invalid_json", "request body must be JSON")
        if not isinstance(payload, Mapping):
            return _json_response(400, "invalid_request", "request body must be an object")
        message = payload.get("input")
        if not isinstance(message, str) or not message.strip():
            return _json_response(400, "invalid_request", "input is required")
        idempotency_key = payload.get("idempotency_key")
        if idempotency_key is not None and not isinstance(idempotency_key, str):
            return _json_response(400, "invalid_request", "idempotency_key must be a string")
        try:
            result = self._agent.run(message, idempotency_key=idempotency_key)
        except ActionDeniedError:
            return _json_response(403, "action_denied", "action denied")
        except AgentError:
            return _json_response(409, "agent_unavailable", "agent unavailable")
        except Exception:
            return _json_response(500, "request_failed", "request failed")
        return LocalAPIResponse(status_code=200, body={"result": result})


def _json_response(status_code: int, code: str, message: str) -> LocalAPIResponse:
    return LocalAPIResponse(
        status_code=status_code,
        body={"error": {"code": code, "message": message}},
    )


def _header(headers: Mapping[str, str], name: str) -> str:
    lowered = name.lower()
    for key, value in headers.items():
        if key.lower() == lowered:
            return value
    return ""

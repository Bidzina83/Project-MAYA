"""Authenticated local API boundary for Project MAYA."""

from __future__ import annotations

import hmac
import hashlib
import json
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Mapping, Protocol, runtime_checkable

from .agent import Agent, AgentError
from .agent.contracts import AgentRuntime
from .governance import ActionDeniedError
from .hermes_plugins.governance import RequestIdentity, bind_request_identity
from .hermes_plugins.session_requests import CandidateSessionRequestBinding, REQUEST_BINDING_CONTRACT
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
        *,
        actor_id: str = "local-user",
        data_classification: str = "confidential",
    ) -> None:
        with bind_request_identity(actor_id, data_classification):
            pass
        self._identity = RequestIdentity(actor_id, data_classification)
        self._secret_store = secret_store
        self._token_ref = token_ref or SecretRef.parse("secret://local-api/token")

    def authenticate(self, headers: Mapping[str, str]) -> bool:
        return self.authenticate_identity(headers) is not None

    def authenticate_identity(self, headers: Mapping[str, str]) -> RequestIdentity | None:
        """Map this token to its host-configured identity, never a request field."""
        authorization = _header(headers, "authorization")
        if not authorization.startswith("Bearer "):
            return None
        supplied = authorization.removeprefix("Bearer ").strip()
        if not supplied:
            return None
        try:
            expected = self._secret_store.read(self._token_ref)
        except SecretStoreError:
            return None
        return self._identity if hmac.compare_digest(supplied, expected) else None


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
        candidate_session_binding: CandidateSessionRequestBinding | None = None,
    ) -> None:
        if max_body_bytes < 1:
            raise ValueError("max_body_bytes must be positive")
        self._agent = agent
        self._runtime = runtime
        self._authenticator = authenticator
        self._max_body_bytes = max_body_bytes
        if candidate_session_binding is not None and not isinstance(candidate_session_binding, CandidateSessionRequestBinding):
            raise TypeError("candidate_session_binding must be a candidate session binding")
        self._candidate_session_binding = candidate_session_binding

    def handle(self, request: LocalAPIRequest) -> LocalAPIResponse:
        if not request.path.startswith("/v1/"):
            return _json_response(404, "not_found", "route not found")
        identity = None
        if self._candidate_session_binding is not None:
            authenticate_identity = getattr(self._authenticator, "authenticate_identity", None)
            if callable(authenticate_identity):
                try:
                    identity = authenticate_identity(request.headers)
                except Exception:
                    identity = None
            authenticated = isinstance(identity, RequestIdentity)
        else:
            authenticated = self._authenticator.authenticate(request.headers)
        if not authenticated:
            return _json_response(401, "unauthorized", "authentication required")
        required_binding = _header(request.headers, "x-maya-session-binding")
        if required_binding and (self._candidate_session_binding is None or required_binding != REQUEST_BINDING_CONTRACT):
            return _json_response(403, "action_denied", "action denied")
        if len(request.body) > self._max_body_bytes:
            return _json_response(413, "request_too_large", "request body too large")
        if request.path == "/v1/health":
            return self._health(request)
        if request.path == "/v1/run":
            return self._run(request, identity)
        if request.path == "/v1/session-binding":
            if request.method.upper() != "GET":
                return _json_response(405, "method_not_allowed", "method not allowed")
            if self._candidate_session_binding is None or identity is None:
                return _json_response(403, "action_denied", "action denied")
            try:
                with self._candidate_session_binding.authenticated_request(identity):
                    return LocalAPIResponse(200, {"session_binding_contract": REQUEST_BINDING_CONTRACT,
                                                  "qualification": "source_candidate_only"})
            except ActionDeniedError:
                return _json_response(403, "action_denied", "action denied")
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

    def _run(self, request: LocalAPIRequest, identity: RequestIdentity | None = None) -> LocalAPIResponse:
        if request.method.upper() != "POST":
            return _json_response(405, "method_not_allowed", "method not allowed")
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return _json_response(400, "invalid_json", "request body must be JSON")
        if not isinstance(payload, Mapping):
            return _json_response(400, "invalid_request", "request body must be an object")
        if self._candidate_session_binding is not None and set(payload) - {"input", "idempotency_key", "data_classification"}:
            return _json_response(400, "invalid_request", "unsupported request fields")
        message = payload.get("input")
        if not isinstance(message, str) or not message.strip():
            return _json_response(400, "invalid_request", "input is required")
        idempotency_key = payload.get("idempotency_key")
        if idempotency_key is not None and not isinstance(idempotency_key, str):
            return _json_response(400, "invalid_request", "idempotency_key must be a string")
        data_classification = payload.get("data_classification", "internal")
        if (
            not isinstance(data_classification, str)
            or not data_classification.strip()
        ):
            return _json_response(
                400,
                "invalid_request",
                "data_classification must be a string",
            )
        try:
            if self._candidate_session_binding is not None:
                if identity is None or ("data_classification" in payload and data_classification != identity.data_classification):
                    return _json_response(403, "action_denied", "action denied")
                with self._candidate_session_binding.authenticated_request(identity):
                    safe_idempotency_key = ("sha256:" + hashlib.sha256(idempotency_key.encode()).hexdigest()
                                            if idempotency_key is not None else None)
                    result = self._agent.run(message, idempotency_key=safe_idempotency_key,
                                             data_classification=identity.data_classification)
            else:
                result = self._agent.run(
                    message,
                    idempotency_key=idempotency_key,
                    data_classification=data_classification,
                )
        except ActionDeniedError:
            return _json_response(403, "action_denied", "action denied")
        except AgentError:
            return _json_response(409, "agent_unavailable", "agent unavailable")
        except Exception:
            return _json_response(500, "request_failed", "request failed")
        body = {"result": result}
        if self._candidate_session_binding is not None:
            body.update(session_binding_contract=REQUEST_BINDING_CONTRACT, qualification="source_candidate_only")
        return LocalAPIResponse(status_code=200, body=body)


def build_local_api_http_server(
    api: LocalAPI,
    *,
    bind: str = "127.0.0.1",
    port: int = 0,
    remote_access: bool = False,
) -> ThreadingHTTPServer:
    """Create a loopback HTTP server that delegates to LocalAPI."""

    if remote_access or not _is_loopback(bind):
        raise LocalAPIError("Phase 1 local API HTTP server only supports loopback")

    class MayaLocalAPIRequestHandler(BaseHTTPRequestHandler):
        server_version = "ProjectMayaLocalAPI/1"

        def do_GET(self) -> None:
            self._handle()

        def do_POST(self) -> None:
            self._handle()

        def do_OPTIONS(self) -> None:
            self._handle()

        def log_message(self, format: str, *args: object) -> None:
            return

        def _handle(self) -> None:
            length = self.headers.get("content-length", "0")
            try:
                body_length = int(length)
            except ValueError:
                body_length = 0
            body = self.rfile.read(max(body_length, 0)) if body_length else b""
            response = api.handle(
                LocalAPIRequest(
                    method=self.command,
                    path=self.path,
                    headers=dict(self.headers.items()),
                    body=body,
                )
            )
            payload = response.json_bytes()
            self.send_response(response.status_code)
            for name, value in response.headers.items():
                self.send_header(name, value)
            self.send_header("content-length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return ThreadingHTTPServer((bind, port), MayaLocalAPIRequestHandler)


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


def _is_loopback(bind: str) -> bool:
    return bind == "localhost" or bind.startswith("127.") or bind == "::1"

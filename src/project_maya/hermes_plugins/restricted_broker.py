"""Test-only host broker for Gate A; this module does not provide containment."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable

from project_maya.audit import AuditRecord, AuditSink, NullAuditSink
from project_maya.governance import ActionRequest, ActionAuthorizationGateway


class BrokerDenied(PermissionError):
    """A fixed public error; never expose underlying service exceptions."""


@dataclass(frozen=True)
class BrokerIdentity:
    actor_id: str
    request_id: str
    classification: str

    def __post_init__(self) -> None:
        if not all(isinstance(x, str) and x.strip() for x in (
            self.actor_id, self.request_id, self.classification
        )):
            raise ValueError("broker.invalid_identity")


class RestrictedBroker:
    """One host-bound request lease; never a generic URL or file proxy.

    Construct only in the trusted test host. Supplied handlers are real host
    services/fixture transport; runtime-provided callables are never accepted.
    """

    def __init__(self, *, identity: BrokerIdentity, gateway: ActionAuthorizationGateway,
                 audit: AuditSink, document_id: str, memory_id: str,
                 read_document: Callable[[], Any], search_memory: Callable[[str], Any],
                 model_transport: Callable[[dict[str, Any]], Any],
                 validate_result: Callable[[Any], Any], ttl: float = 30,
                 max_effects: int = 8, clock: Callable[[], float] = time.monotonic) -> None:
        if isinstance(audit, NullAuditSink) or audit is None:
            raise ValueError("broker.required_audit_missing")
        if not 0 < ttl <= 300 or type(max_effects) is not int or not 1 <= max_effects <= 32:
            raise ValueError("broker.invalid_budget")
        if not all(isinstance(x, str) and x.strip() for x in (document_id, memory_id)):
            raise ValueError("broker.invalid_resource")
        self._identity, self._gateway, self._audit = identity, gateway, audit
        self._document_id, self._memory_id = document_id, memory_id
        self._read, self._search = read_document, search_memory
        self._model, self._validate = model_transport, validate_result
        self._clock, self._expires = clock, clock() + ttl
        self._remaining = max_effects
        self._revoked = threading.Event()
        self._token = secrets.token_urlsafe(32)
        self._lock = threading.RLock()

    @property
    def admission_token(self) -> str:
        # Supply only through private process admission, never logs/manifests.
        return self._token

    def revoke(self) -> None:
        # Revocation must not wait behind a blocking provider/service call.
        self._revoked.set()

    def _live(self, token: str) -> None:
        if (not isinstance(token, str) or not token.isascii()
                or not hmac.compare_digest(token, self._token)
                or self._revoked.is_set() or self._clock() >= self._expires):
            raise BrokerDenied("broker.admission_denied")

    def _authorize(self, capability: str, target: str, operation: str,
                   payload: bytes) -> None:
        identity = self._identity
        action = ActionRequest(identity.actor_id, capability, target, operation,
                               identity.classification, metadata={
                                   "request_id": identity.request_id,
                                   "payload_sha256": hashlib.sha256(payload).hexdigest(),
                               })
        result = self._gateway.authorize(action)
        # Constraints/redactions require actual handling, not an ALLOW shortcut.
        permitted = result.allowed and not result.constraints and not result.redactions
        self._audit.write(AuditRecord(
            event_type="gate_a.broker_decision", decision="allow" if permitted else "deny",
            reason_code="broker.policy_allow" if permitted else "broker.policy_deny",
            actor_id=identity.actor_id, capability=capability, target=target,
            operation=operation, data_classification=identity.classification,
            metadata=action.metadata,
        ))
        if not permitted:
            raise BrokerDenied("broker.policy_denied")

    def handle(self, token: str, route: str, raw: bytes) -> Any:
        """Authorize exact parsed requests before invoking host-owned effects."""
        try:
            with self._lock:
                self._live(token)
                if not isinstance(raw, bytes) or len(raw) > 256 * 1024:
                    raise BrokerDenied("broker.invalid_request")
                body = json.loads(raw, object_pairs_hook=_unique_object,
                                  parse_constant=_invalid_constant)
                json.dumps(body, allow_nan=False)
                if not isinstance(body, dict):
                    raise BrokerDenied("broker.invalid_request")
                if self._remaining <= 0:
                    raise BrokerDenied("broker.budget_exhausted")
                if route == "/maya/document/read":
                    if body != {"document_id": self._document_id}:
                        raise BrokerDenied("broker.invalid_request")
                    capability, target, operation = "file.read", self._document_id, "read"
                    effect = self._read
                elif route == "/maya/memory/search":
                    if (set(body) != {"memory_id", "query"}
                            or body["memory_id"] != self._memory_id
                            or not isinstance(body["query"], str)
                            or not 0 < len(body["query"]) <= 4096):
                        raise BrokerDenied("broker.invalid_request")
                    capability, target, operation = "memory.search", self._memory_id, "search"
                    effect = lambda: self._search(body["query"])
                elif route == "/v1/responses":
                    if (set(body) - {"model", "input", "instructions", "tools", "tool_choice",
                                     "reasoning", "max_output_tokens", "stream", "store",
                                     "parallel_tool_calls", "prompt_cache_key", "include",
                                     "temperature", "service_tier", "text", "truncation"}
                            or body.get("model") != "gpt-6-luna" or "input" not in body
                            or body.get("store", False) is not False):
                        raise BrokerDenied("broker.invalid_request")
                    capability, target, operation = "model.egress", "openai/gpt-6-luna", "infer"
                    effect = lambda: self._model(body)
                else:
                    raise BrokerDenied("broker.unsupported_route")
                self._authorize(capability, target, operation, raw)
                self._live(token)
                self._remaining -= 1
                result = effect()
                self._live(token)
                # Validation precedes returning data to the restricted runtime.
                checked = self._validate(result)
                self._live(token)
                return checked
        except BrokerDenied:
            self.revoke()
            raise
        except Exception:
            self.revoke()
            raise BrokerDenied("broker.request_failed") from None

    def deliver(self, token: str, result: Any) -> Any:
        """Separate host-side final disclosure gate; no raw console delivery."""
        try:
            with self._lock:
                self._live(token)
                data = json.dumps(result, allow_nan=False).encode("utf-8")
                if len(data) > 256 * 1024:
                    raise BrokerDenied("broker.invalid_result")
                if self._remaining <= 0:
                    raise BrokerDenied("broker.budget_exhausted")
                self._authorize("model.output", "operator", "deliver", data)
                self._live(token)
                self._remaining -= 1
                checked = self._validate(result)
                self._live(token)
                self._revoked.set()
                return checked
        except BrokerDenied:
            self.revoke()
            raise
        except Exception:
            self.revoke()
            raise BrokerDenied("broker.delivery_failed") from None


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("broker.duplicate_json_key")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError("broker.invalid_json_constant")

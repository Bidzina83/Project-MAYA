"""Local governance and action-authorization contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Mapping, Protocol, runtime_checkable


class GovernanceDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REDACT = "redact"
    CONSTRAIN = "constrain"
    REQUEST_CONFIRMATION = "request_confirmation"
    REQUIRE_APPROVER = "require_approver"
    DEFER = "defer"


@dataclass(frozen=True)
class ActionRequest:
    actor_id: str
    capability: str
    target: str
    operation: str
    data_classification: str = "internal"
    idempotency_key: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AuthorizationResult:
    decision: GovernanceDecision
    reason_code: str
    audit_required: bool = True
    constraints: tuple[str, ...] = ()
    redactions: Mapping[str, str] = field(default_factory=dict)

    @property
    def allowed(self) -> bool:
        return self.decision is GovernanceDecision.ALLOW


class ActionDeniedError(PermissionError):
    """Raised when a consequential action is not authorized."""


@runtime_checkable
class ActionAuthorizationGateway(Protocol):
    def authorize(self, request: ActionRequest) -> AuthorizationResult:
        """Authorize, deny, constrain, or defer a proposed action."""


class DenyByDefaultGateway:
    """Conservative default gateway used before policy engines are installed."""

    def authorize(self, request: ActionRequest) -> AuthorizationResult:
        return AuthorizationResult(
            decision=GovernanceDecision.DENY,
            reason_code="governance.default_deny",
        )


@dataclass(frozen=True)
class PolicyRule:
    capability: str
    target: str = "*"
    operation: str = "*"
    actor_id: str = "*"
    decision: GovernanceDecision = GovernanceDecision.ALLOW
    reason_code: str = "governance.policy_rule"

    def matches(self, request: ActionRequest) -> bool:
        return (
            _matches(self.capability, request.capability)
            and _matches(self.target, request.target)
            and _matches(self.operation, request.operation)
            and _matches(self.actor_id, request.actor_id)
        )


class PolicyAuthorizationGateway:
    """File-backed allowlist policy with deny-by-default fallback."""

    def __init__(self, rules: tuple[PolicyRule, ...]) -> None:
        self._rules = rules

    def authorize(self, request: ActionRequest) -> AuthorizationResult:
        for rule in self._rules:
            if rule.matches(request):
                return AuthorizationResult(
                    decision=rule.decision,
                    reason_code=rule.reason_code,
                )
        return AuthorizationResult(
            decision=GovernanceDecision.DENY,
            reason_code="governance.no_matching_rule",
        )


def load_policy_gateway(path: Path | str) -> PolicyAuthorizationGateway:
    """Load a minimal local authorization policy from JSON."""

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError("policy must be an object")
    rules_raw = raw.get("allow", [])
    if not isinstance(rules_raw, list):
        raise ValueError("policy allow must be a list")
    rules = tuple(_rule_from_mapping(item) for item in rules_raw)
    return PolicyAuthorizationGateway(rules)


def require_authorized(
    gateway: ActionAuthorizationGateway,
    request: ActionRequest,
) -> AuthorizationResult:
    result = gateway.authorize(request)
    if not result.allowed:
        raise ActionDeniedError(result.reason_code)
    return result


def _rule_from_mapping(data: Mapping[str, object]) -> PolicyRule:
    if not isinstance(data, Mapping):
        raise ValueError("policy rule must be an object")
    capability = data.get("capability")
    if not isinstance(capability, str) or not capability.strip():
        raise ValueError("policy rule capability is required")
    decision = GovernanceDecision(str(data.get("decision", "allow")))
    return PolicyRule(
        capability=capability,
        target=str(data.get("target", "*")),
        operation=str(data.get("operation", "*")),
        actor_id=str(data.get("actor_id", "*")),
        decision=decision,
        reason_code=str(data.get("reason_code", "governance.policy_rule")),
    )


def _matches(pattern: str, value: str) -> bool:
    return pattern == "*" or pattern == value

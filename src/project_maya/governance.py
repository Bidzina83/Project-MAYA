"""Local governance and action-authorization contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
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


def require_authorized(
    gateway: ActionAuthorizationGateway,
    request: ActionRequest,
) -> AuthorizationResult:
    result = gateway.authorize(request)
    if not result.allowed:
        raise ActionDeniedError(result.reason_code)
    return result

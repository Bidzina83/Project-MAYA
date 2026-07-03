"""Metabase integration and provisioning contracts for Project MAYA."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping
from urllib.parse import urlparse

from .audit import AuditRecord, AuditSink, NullAuditSink
from .config import ComponentProfile, MayaConfig
from .governance import ActionAuthorizationGateway, ActionDeniedError, ActionRequest


class MetabaseCapabilityError(RuntimeError):
    """Raised when a Metabase capability operation cannot be completed."""


@dataclass(frozen=True)
class MetabaseHealth:
    status: str
    deployment: str
    endpoint_state: str
    application_database: str
    analytics_sources: int
    network_used: bool = False
    live_check: str = "not_requested"
    metadata: Mapping[str, str] = field(default_factory=dict)

    def redacted_summary(self) -> dict[str, object]:
        return {
            "status": self.status,
            "deployment": self.deployment,
            "endpoint_state": self.endpoint_state,
            "application_database": self.application_database,
            "analytics_sources": self.analytics_sources,
            "network_used": self.network_used,
            "live_check": self.live_check,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class MetabaseProvisioningStep:
    action: str
    target: str
    status: str
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class MetabaseProvisioningPlan:
    status: str
    deployment: str
    apply: bool
    steps: tuple[MetabaseProvisioningStep, ...]
    network_used: bool = False

    def redacted_summary(self) -> dict[str, object]:
        return {
            "status": self.status,
            "deployment": self.deployment,
            "apply": self.apply,
            "network_used": self.network_used,
            "steps": [
                {
                    "action": step.action,
                    "target": step.target,
                    "status": step.status,
                    "metadata": dict(step.metadata),
                }
                for step in self.steps
            ],
        }


def validate_metabase_health(
    config: MayaConfig,
    *,
    live: bool = False,
) -> MetabaseHealth:
    _require_metabase_profile(config)
    metabase = config.metabase
    endpoint_state = _endpoint_state(metabase.endpoint)
    app_db_state = (
        "configured"
        if metabase.application_database is not None
        and metabase.application_database.credential_ref.startswith("secret://")
        else "missing"
    )
    if not metabase.enabled:
        status = "disabled"
    elif metabase.deployment not in {"managed_local", "customer_managed"}:
        status = "unsupported_deployment"
    elif endpoint_state == "missing" or app_db_state == "missing":
        status = "not_ready"
    else:
        status = "ready"
    live_check = "disabled"
    if live:
        live_check = "deferred"
        status = "live_check_deferred" if status == "ready" else status
    return MetabaseHealth(
        status=status,
        deployment=metabase.deployment,
        endpoint_state=endpoint_state,
        application_database=app_db_state,
        analytics_sources=len(metabase.analytics_sources),
        network_used=False,
        live_check=live_check,
        metadata={
            "memory_exposed": "false",
            "credential_ref": (
                "configured"
                if metabase.application_database is not None
                and metabase.application_database.credential_ref
                else "missing"
            ),
        },
    )


def plan_metabase_provisioning(config: MayaConfig) -> MetabaseProvisioningPlan:
    health = validate_metabase_health(config)
    steps: list[MetabaseProvisioningStep] = []
    steps.append(
        MetabaseProvisioningStep(
            action="validate-application-database",
            target="metabase.application_database",
            status=health.application_database,
            metadata={"memory_source": "excluded"},
        )
    )
    if config.metabase.analytics_sources:
        for source in config.metabase.analytics_sources:
            steps.append(
                MetabaseProvisioningStep(
                    action="validate-analytics-source",
                    target=f"analytics_source:{source.name}",
                    status="configured",
                    metadata={
                        "engine": source.engine,
                        "credential_ref": "configured",
                    },
                )
            )
    else:
        steps.append(
            MetabaseProvisioningStep(
                action="validate-analytics-source",
                target="analytics_source:none",
                status="missing_optional",
                metadata={"hint": "configure approved analytics sources"},
            )
        )
    steps.append(
        MetabaseProvisioningStep(
            action="plan-governed-dashboard",
            target="collection:maya-operational",
            status="planned" if health.status in {"ready", "live_check_deferred"} else "blocked",
            metadata={
                "raw_memory": "excluded",
                "prompts": "excluded",
                "secrets": "excluded",
                "files": "excluded",
            },
        )
    )
    overall = "planned"
    if any(step.status == "blocked" for step in steps):
        overall = "blocked"
    return MetabaseProvisioningPlan(
        status=overall,
        deployment=config.metabase.deployment,
        apply=False,
        steps=tuple(steps),
        network_used=False,
    )


def apply_metabase_provisioning(
    config: MayaConfig,
    *,
    gateway: ActionAuthorizationGateway,
    actor_id: str = "local-user",
    audit_sink: AuditSink | None = None,
    data_classification: str = "internal",
    idempotency_key: str | None = None,
) -> MetabaseProvisioningPlan:
    plan = plan_metabase_provisioning(config)
    _authorize_metabase_action(
        gateway,
        audit_sink or NullAuditSink(),
        actor_id=actor_id,
        operation="apply-provision",
        data_classification=data_classification,
        idempotency_key=idempotency_key,
        metadata={
            "deployment": config.metabase.deployment,
            "steps": str(len(plan.steps)),
            "network_used": "false",
        },
    )
    if plan.status == "blocked":
        raise MetabaseCapabilityError("Metabase provisioning plan is blocked")
    return MetabaseProvisioningPlan(
        status="applied",
        deployment=plan.deployment,
        apply=True,
        steps=tuple(
            MetabaseProvisioningStep(
                action=step.action,
                target=step.target,
                status="applied" if step.status in {"planned", "configured"} else step.status,
                metadata=step.metadata,
            )
            for step in plan.steps
        ),
        network_used=False,
    )


def metabase_capability_checks(config: MayaConfig) -> tuple[MetabaseHealth, MetabaseProvisioningPlan]:
    if ComponentProfile.METABASE not in config.runtime.enabled_profiles:
        return ()
    return (validate_metabase_health(config), plan_metabase_provisioning(config))


def _require_metabase_profile(config: MayaConfig) -> None:
    if ComponentProfile.METABASE not in config.runtime.enabled_profiles:
        raise MetabaseCapabilityError("maya-metabase profile is not enabled")


def _endpoint_state(endpoint: str | None) -> str:
    if not endpoint:
        return "missing"
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return "invalid"
    host = parsed.hostname.lower()
    if host in {"127.0.0.1", "localhost", "::1"}:
        return "loopback_configured"
    return "remote_configured"


def _authorize_metabase_action(
    gateway: ActionAuthorizationGateway,
    audit_sink: AuditSink,
    *,
    actor_id: str,
    operation: str,
    data_classification: str,
    idempotency_key: str | None,
    metadata: Mapping[str, str],
) -> None:
    action = ActionRequest(
        actor_id=actor_id,
        capability=f"metabase.{operation}",
        target="metabase:provisioning",
        operation=operation,
        data_classification=data_classification,
        idempotency_key=idempotency_key,
        metadata=metadata,
    )
    result = gateway.authorize(action)
    if result.audit_required:
        audit_sink.write(
            AuditRecord(
                event_type="authorization.metabase",
                decision=result.decision.value,
                reason_code=result.reason_code,
                actor_id=action.actor_id,
                capability=action.capability,
                target=action.target,
                operation=action.operation,
                data_classification=action.data_classification,
                idempotency_key=action.idempotency_key,
                metadata=action.metadata,
            )
        )
    if not result.allowed:
        raise ActionDeniedError(result.reason_code)

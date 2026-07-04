"""Metabase integration and provisioning contracts for Project MAYA."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse

from .audit import AuditRecord, AuditSink, NullAuditSink
from .config import ComponentProfile, MayaConfig
from .governance import ActionAuthorizationGateway, ActionDeniedError, ActionRequest


class MetabaseCapabilityError(RuntimeError):
    """Raised when a Metabase capability operation cannot be completed."""


@dataclass(frozen=True)
class GovernedMetabaseViewSpec:
    name: str
    source_name: str
    engine: str
    status: str = "planned"

    def redacted_summary(self) -> dict[str, str]:
        return {
            "name": self.name,
            "source_name": self.source_name,
            "engine": self.engine,
            "status": self.status,
            "least_privilege": "true",
            "raw_memory": "excluded",
            "prompts": "excluded",
            "secrets": "excluded",
            "files": "excluded",
        }


@dataclass(frozen=True)
class MetabaseDashboardCardSpec:
    name: str
    view_name: str
    visualization: str
    status: str = "planned"

    def redacted_summary(self) -> dict[str, str]:
        return {
            "name": self.name,
            "view_name": self.view_name,
            "visualization": self.visualization,
            "status": self.status,
        }


@dataclass(frozen=True)
class MetabaseDashboardSpec:
    name: str
    collection: str
    cards: tuple[MetabaseDashboardCardSpec, ...]
    status: str = "planned"

    def redacted_summary(self) -> dict[str, object]:
        return {
            "name": self.name,
            "collection": self.collection,
            "status": self.status,
            "cards": [card.redacted_summary() for card in self.cards],
        }


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
    views: tuple[GovernedMetabaseViewSpec, ...] = ()
    dashboards: tuple[MetabaseDashboardSpec, ...] = ()
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
            "views": [view.redacted_summary() for view in self.views],
            "dashboards": [
                dashboard.redacted_summary() for dashboard in self.dashboards
            ],
        }


@dataclass(frozen=True)
class MetabaseLifecycleState:
    status: str
    deployment: str
    application_dir: str
    provisioning_dir: str
    service_artifact: str
    customer_managed: bool

    def redacted_summary(self) -> dict[str, object]:
        return {
            "status": self.status,
            "deployment": self.deployment,
            "application_dir": self.application_dir,
            "provisioning_dir": self.provisioning_dir,
            "service_artifact": self.service_artifact,
            "customer_managed": self.customer_managed,
        }


def validate_metabase_health(
    config: MayaConfig,
    *,
    live: bool = False,
    timeout_seconds: float = 2.0,
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
    live_check = "not_requested"
    network_used = False
    live_metadata: dict[str, str] = {}
    if live:
        network_used = True
        if status == "ready":
            live_status, live_metadata = _bounded_live_health(
                metabase.endpoint,
                timeout_seconds=timeout_seconds,
            )
            live_check = live_status
            status = "ready" if live_status == "reachable" else "live_unavailable"
        else:
            live_check = "skipped_not_ready"
    return MetabaseHealth(
        status=status,
        deployment=metabase.deployment,
        endpoint_state=endpoint_state,
        application_database=app_db_state,
        analytics_sources=len(metabase.analytics_sources),
        network_used=network_used,
        live_check=live_check,
        metadata={
            "memory_exposed": "false",
            "credential_ref": (
                "configured"
                if metabase.application_database is not None
                and metabase.application_database.credential_ref
                else "missing"
            ),
            **live_metadata,
        },
    )


def inspect_metabase_lifecycle(config: MayaConfig) -> MetabaseLifecycleState:
    _require_metabase_profile(config)
    application_dir = config.deployment.data_dir / "metabase" / "application"
    provisioning_dir = config.deployment.data_dir / "metabase" / "provisioning"
    service_artifact = application_dir / "metabase.jar"
    if not config.metabase.enabled:
        status = "disabled"
    elif config.metabase.deployment == "customer_managed":
        status = "customer_managed"
    elif config.metabase.deployment == "managed_local":
        status = "managed_local_ready" if service_artifact.is_file() else "managed_local_artifact_missing"
    else:
        status = "unsupported_deployment"
    return MetabaseLifecycleState(
        status=status,
        deployment=config.metabase.deployment,
        application_dir=_path_state(application_dir),
        provisioning_dir=_path_state(provisioning_dir),
        service_artifact="configured" if service_artifact.is_file() else "missing",
        customer_managed=config.metabase.deployment == "customer_managed",
    )


def plan_metabase_provisioning(config: MayaConfig) -> MetabaseProvisioningPlan:
    health = validate_metabase_health(config)
    steps: list[MetabaseProvisioningStep] = []
    views = _governed_views(config)
    dashboards = _dashboard_specs(views)
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
            action="plan-governed-views",
            target="views:approved-analytics-sources",
            status="planned" if views else "blocked",
            metadata={
                "view_count": str(len(views)),
                "least_privilege": "true",
                "raw_memory": "excluded",
                "prompts": "excluded",
                "secrets": "excluded",
                "files": "excluded",
            },
        )
    )
    steps.append(
        MetabaseProvisioningStep(
            action="plan-governed-dashboard",
            target="collection:maya-operational",
            status="planned" if health.status == "ready" and dashboards else "blocked",
            metadata={
                "dashboard_count": str(len(dashboards)),
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
        views=views,
        dashboards=dashboards,
        network_used=False,
    )


def write_metabase_provisioning_plan(
    config: MayaConfig,
    plan: MetabaseProvisioningPlan,
    *,
    filename: str = "latest-plan.json",
) -> Path:
    target = _provisioning_file(config, filename)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(plan.redacted_summary(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    return target


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
    applied = MetabaseProvisioningPlan(
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
        views=tuple(
            GovernedMetabaseViewSpec(
                name=view.name,
                source_name=view.source_name,
                engine=view.engine,
                status="applied",
            )
            for view in plan.views
        ),
        dashboards=tuple(
            MetabaseDashboardSpec(
                name=dashboard.name,
                collection=dashboard.collection,
                cards=tuple(
                    MetabaseDashboardCardSpec(
                        name=card.name,
                        view_name=card.view_name,
                        visualization=card.visualization,
                        status="applied",
                    )
                    for card in dashboard.cards
                ),
                status="applied",
            )
            for dashboard in plan.dashboards
        ),
        network_used=False,
    )
    write_metabase_provisioning_plan(config, applied, filename="last-applied-plan.json")
    write_metabase_provisioning_plan(config, applied, filename="dashboards.json")
    return applied


def metabase_capability_checks(
    config: MayaConfig,
) -> tuple[MetabaseHealth, MetabaseLifecycleState, MetabaseProvisioningPlan]:
    if ComponentProfile.METABASE not in config.runtime.enabled_profiles:
        return ()
    return (
        validate_metabase_health(config),
        inspect_metabase_lifecycle(config),
        plan_metabase_provisioning(config),
    )


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


def _bounded_live_health(
    endpoint: str | None,
    *,
    timeout_seconds: float,
) -> tuple[str, dict[str, str]]:
    if not endpoint:
        return "skipped_not_ready", {"live_error": "endpoint_missing"}
    url = endpoint.rstrip("/") + "/api/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
            status = getattr(response, "status", 0)
            if 200 <= int(status) < 500:
                return "reachable", {"live_endpoint": "configured"}
    except (OSError, urllib.error.URLError, ValueError):
        return "unreachable", {"live_endpoint": "configured"}
    return "unreachable", {"live_endpoint": "configured"}


def _governed_views(config: MayaConfig) -> tuple[GovernedMetabaseViewSpec, ...]:
    return tuple(
        GovernedMetabaseViewSpec(
            name=f"maya_{_safe_identifier(source.name)}_governed",
            source_name=source.name,
            engine=source.engine,
        )
        for source in config.metabase.analytics_sources
    )


def _dashboard_specs(
    views: tuple[GovernedMetabaseViewSpec, ...],
) -> tuple[MetabaseDashboardSpec, ...]:
    if not views:
        return ()
    cards = tuple(
        MetabaseDashboardCardSpec(
            name=f"{view.source_name} overview",
            view_name=view.name,
            visualization="table",
        )
        for view in views
    )
    return (
        MetabaseDashboardSpec(
            name="Maya Operational Overview",
            collection="maya-operational",
            cards=cards,
        ),
    )


def _safe_identifier(value: str) -> str:
    normalized = "".join(
        char.lower() if char.isalnum() else "_"
        for char in value.strip()
    ).strip("_")
    if not normalized:
        raise MetabaseCapabilityError("analytics source name is required")
    return normalized


def _path_state(path: Path) -> str:
    if path.is_dir():
        return "exists"
    if path.exists():
        return "invalid"
    return "will_create"


def _provisioning_file(config: MayaConfig, filename: str) -> Path:
    if Path(filename).name != filename or filename in {"", ".", ".."}:
        raise MetabaseCapabilityError("provisioning filename is unsafe")
    target = (
        config.deployment.data_dir
        / "metabase"
        / "provisioning"
        / filename
    ).resolve()
    root = (config.deployment.data_dir / "metabase" / "provisioning").resolve()
    if target != root and root not in target.parents:
        raise MetabaseCapabilityError("provisioning path escapes metabase directory")
    return target


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

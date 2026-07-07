"""Operator health summary helpers for Project MAYA."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .agent.contracts import AgentRuntime
from .config import MayaConfig
from .doctor import DoctorReport, DoctorStatus, run_doctor
from .repair import repair_local_state
from .secrets import SecretStore
from .setup import plan_setup
from .skills import packaged_document_skill_status
from .update import check_updates, rollback_update


class HealthStatus(str, Enum):
    READY = "ready"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    NOT_CONFIGURED = "not_configured"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class HealthCategory:
    name: str
    status: HealthStatus
    checks: int
    message: str

    def redacted_summary(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status.value,
            "checks": self.checks,
            "message": self.message,
        }


@dataclass(frozen=True)
class HealthSummary:
    status: HealthStatus
    categories: tuple[HealthCategory, ...]
    update_status: str
    rollback_status: str
    network_used: bool

    def redacted_summary(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "network_used": self.network_used,
            "update": self.update_status,
            "rollback": self.rollback_status,
            "categories": [
                category.redacted_summary() for category in self.categories
            ],
        }


CHECK_CATEGORIES = (
    ("configuration", ("config", "profiles.")),
    ("platform", ("release.platform",)),
    ("filesystem", ("filesystem.",)),
    ("governance", ("governance.",)),
    ("memory", ("memory.",)),
    ("secrets", ("secrets.",)),
    ("runtime", ("lifecycle.", "hermes.")),
    ("connectors", ("connectors.", "dependencies.service.google", "dependencies.service.slack", "dependencies.service.telegram")),
    ("models", ("model.", "dependencies.model.")),
    ("documents", ("documents.", "dependencies.python.", "dependencies.command.pdftoppm", "dependencies.command.soffice", "dependencies.application.ms-office")),
    ("metabase", ("metabase.", "dependencies.service.metabase", "dependencies.database.")),
    ("backup", ("backup.",)),
)


def summarize_health(
    config: MayaConfig,
    runtime: AgentRuntime,
    *,
    lifecycle_state=None,
    secret_store: SecretStore | None = None,
) -> HealthSummary:
    """Build a redacted operator health summary from existing diagnostics."""

    report = run_doctor(
        config,
        runtime,
        lifecycle_state=lifecycle_state,
        secret_store=secret_store,
    )
    categories = tuple(
        _category_from_report(name, prefixes, report)
        for name, prefixes in CHECK_CATEGORIES
    )
    update = check_updates(config)
    rollback = rollback_update(config)
    update_category = HealthCategory(
        name="update",
        status=_metadata_status(update.status),
        checks=2,
        message=f"update={update.status}; rollback={rollback.status}",
    )
    setup_category = _setup_category(config)
    recovery_category = _recovery_category(config)
    restore_category = HealthCategory(
        name="restore",
        status=HealthStatus.UNKNOWN,
        checks=1,
        message="restore readiness depends on a selected backup archive",
    )
    migration_category = HealthCategory(
        name="migration",
        status=HealthStatus.READY,
        checks=1,
        message="migration UX is available and dry-run by default",
    )
    skills_category = _skills_category()
    categories = (
        setup_category,
        recovery_category,
        *categories,
        restore_category,
        migration_category,
        update_category,
        skills_category,
    )
    status = _overall_status(categories)
    return HealthSummary(
        status=status,
        categories=categories,
        update_status=update.status,
        rollback_status=rollback.status,
        network_used=update.network_used or rollback.network_used,
    )


def _setup_category(config: MayaConfig) -> HealthCategory:
    try:
        setup = plan_setup(config)
    except Exception:
        return HealthCategory(
            name="setup",
            status=HealthStatus.BLOCKED,
            checks=1,
            message="setup plan failed",
        )
    if setup.blocked:
        status = HealthStatus.BLOCKED
    elif any(action.severity.value == "warn" for action in setup.actions):
        status = HealthStatus.DEGRADED
    else:
        status = HealthStatus.READY
    return HealthCategory(
        name="setup",
        status=status,
        checks=len(setup.actions),
        message=f"actions={len(setup.actions)}; dry_run={setup.dry_run}",
    )


def _recovery_category(config: MayaConfig) -> HealthCategory:
    try:
        repair = repair_local_state(config)
    except Exception:
        return HealthCategory(
            name="recovery",
            status=HealthStatus.BLOCKED,
            checks=1,
            message="repair plan failed",
        )
    planned = sum(1 for action in repair.actions if action.status == "planned")
    return HealthCategory(
        name="recovery",
        status=HealthStatus.DEGRADED if planned else HealthStatus.READY,
        checks=len(repair.actions),
        message=f"planned_repairs={planned}; dry_run={repair.dry_run}",
    )


def _skills_category() -> HealthCategory:
    statuses = packaged_document_skill_status()
    blocked = [status for status in statuses if not status.discoverable]
    return HealthCategory(
        name="skills",
        status=HealthStatus.BLOCKED if blocked else HealthStatus.READY,
        checks=len(statuses),
        message=(
            "packaged="
            f"{sum(1 for status in statuses if status.packaged)}; "
            "discoverable="
            f"{sum(1 for status in statuses if status.discoverable)}"
        ),
    )


def _category_from_report(
    name: str,
    prefixes: tuple[str, ...],
    report: DoctorReport,
) -> HealthCategory:
    checks = [
        check for check in report.checks if any(check.name.startswith(prefix) for prefix in prefixes)
    ]
    if not checks:
        return HealthCategory(name, HealthStatus.NOT_CONFIGURED, 0, "no checks")
    if any(check.status is DoctorStatus.FAIL for check in checks):
        status = HealthStatus.BLOCKED
    elif any(check.status is DoctorStatus.WARN for check in checks):
        status = HealthStatus.DEGRADED
    else:
        status = HealthStatus.READY
    return HealthCategory(
        name=name,
        status=status,
        checks=len(checks),
        message=f"pass={sum(1 for check in checks if check.status is DoctorStatus.PASS)}; "
        f"warn={sum(1 for check in checks if check.status is DoctorStatus.WARN)}; "
        f"fail={sum(1 for check in checks if check.status is DoctorStatus.FAIL)}",
    )


def _metadata_status(status: str) -> HealthStatus:
    if status in {"available", "ready"}:
        return HealthStatus.READY
    if status == "unavailable":
        return HealthStatus.NOT_CONFIGURED
    if status.endswith("_rejected"):
        return HealthStatus.BLOCKED
    return HealthStatus.UNKNOWN


def _overall_status(categories: tuple[HealthCategory, ...]) -> HealthStatus:
    if any(category.status is HealthStatus.BLOCKED for category in categories):
        return HealthStatus.BLOCKED
    if any(category.status is HealthStatus.DEGRADED for category in categories):
        return HealthStatus.DEGRADED
    if all(category.status is HealthStatus.NOT_CONFIGURED for category in categories):
        return HealthStatus.NOT_CONFIGURED
    return HealthStatus.READY

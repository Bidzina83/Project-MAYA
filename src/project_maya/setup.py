"""Setup planning helpers for Project MAYA."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .config import MayaConfig
from .dependencies import evaluate_enabled_profile_readiness
from .repair import RepairAction, repair_local_state


class SetupSeverity(str, Enum):
    INFO = "info"
    WARN = "warn"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class SetupAction:
    category: str
    action: str
    status: str
    severity: SetupSeverity
    mutation: bool
    target_ref: str
    hint: str

    def redacted_summary(self) -> dict[str, object]:
        return {
            "category": self.category,
            "action": self.action,
            "status": self.status,
            "severity": self.severity.value,
            "mutation": self.mutation,
            "target": self.target_ref,
            "hint": self.hint,
        }


@dataclass(frozen=True)
class SetupPlan:
    dry_run: bool
    actions: tuple[SetupAction, ...]

    @property
    def blocked(self) -> bool:
        return any(action.severity is SetupSeverity.BLOCKED for action in self.actions)

    def redacted_summary(self) -> dict[str, object]:
        return {
            "status": "blocked" if self.blocked else "ready",
            "dry_run": self.dry_run,
            "actions": [action.redacted_summary() for action in self.actions],
        }


def plan_setup(config: MayaConfig, *, apply: bool = False) -> SetupPlan:
    """Plan or apply safe local setup initialization."""

    config.validate()
    repair = repair_local_state(config, apply=apply)
    actions = [_from_repair_action(config, action) for action in repair.actions]
    actions.extend(_profile_readiness_actions(config))
    actions.append(
        SetupAction(
            category="credentials",
            action="validate_secret_references",
            status="manual",
            severity=SetupSeverity.INFO,
            mutation=False,
            target_ref="configuration",
            hint="store real secret values with maya rotate-secret or an approved vault",
        )
    )
    return SetupPlan(dry_run=not apply, actions=tuple(actions))


def _from_repair_action(config: MayaConfig, action: RepairAction) -> SetupAction:
    mutation = action.action != "none"
    severity = SetupSeverity.INFO
    if action.status == "planned":
        severity = SetupSeverity.WARN
    return SetupAction(
        category=action.category,
        action=action.action,
        status=action.status,
        severity=severity,
        mutation=mutation,
        target_ref=_target_ref(config, action.path),
        hint=action.hint,
    )


def _profile_readiness_actions(config: MayaConfig) -> tuple[SetupAction, ...]:
    actions: list[SetupAction] = []
    for profile in evaluate_enabled_profile_readiness(config):
        if profile.status.value in {"available", "customer_managed", "disabled"}:
            severity = SetupSeverity.INFO
        elif profile.status.value == "missing_required":
            severity = SetupSeverity.BLOCKED
        else:
            severity = SetupSeverity.WARN
        actions.append(
            SetupAction(
                category="dependencies",
                action="validate_profile_readiness",
                status=profile.status.value,
                severity=severity,
                mutation=False,
                target_ref=profile.profile.value,
                hint=profile.redacted_summary(),
            )
        )
    return tuple(actions)


def _target_ref(config: MayaConfig, path: Path) -> str:
    root = config.deployment.data_dir.resolve()
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError:
        return "maya-data" if resolved == root else "external"
    return f"maya-data/{relative}" if relative else "maya-data"

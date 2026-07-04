"""Setup planning helpers for Project MAYA."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .config import (
    BrokerMode,
    ComponentProfile,
    CredentialMode,
    Edition,
    MayaConfig,
)
from .dependencies import evaluate_enabled_profile_readiness
from .repair import RepairAction, repair_local_state


class SetupSeverity(str, Enum):
    INFO = "info"
    WARN = "warn"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class SetupAction:
    component: str
    category: str
    action: str
    status: str
    severity: SetupSeverity
    mutation: bool
    target_ref: str
    hint: str
    next_command: str | None = None
    manual_action: bool = False

    def redacted_summary(self) -> dict[str, object]:
        return {
            "component": self.component,
            "category": self.category,
            "action": self.action,
            "status": self.status,
            "severity": self.severity.value,
            "mutation": self.mutation,
            "target": self.target_ref,
            "hint": self.hint,
            "next_command": self.next_command,
            "manual_action": self.manual_action,
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
    actions.extend(_edition_setup_actions(config))
    actions.extend(_profile_readiness_actions(config))
    actions.append(
        SetupAction(
            component="secrets",
            category="credentials",
            action="validate_secret_references",
            status="manual",
            severity=SetupSeverity.INFO,
            mutation=False,
            target_ref="configuration",
            hint="store real secret values with maya rotate-secret or an approved vault",
            next_command="maya rotate-secret <name> --config <path> --value-stdin",
            manual_action=True,
        )
    )
    return SetupPlan(dry_run=not apply, actions=tuple(actions))


def _from_repair_action(config: MayaConfig, action: RepairAction) -> SetupAction:
    mutation = action.action != "none"
    severity = SetupSeverity.INFO
    if action.status == "planned":
        severity = SetupSeverity.WARN
    return SetupAction(
        component=action.category,
        category=action.category,
        action=action.action,
        status=action.status,
        severity=severity,
        mutation=mutation,
        target_ref=_target_ref(config, action.path),
        hint=action.hint,
        next_command=(
            "maya setup init --config <path> --apply"
            if action.action != "none"
            else None
        ),
    )


def _edition_setup_actions(config: MayaConfig) -> tuple[SetupAction, ...]:
    actions: list[SetupAction] = [
        SetupAction(
            component="edition",
            category="setup",
            action="validate_edition",
            status=config.product.edition.value,
            severity=SetupSeverity.INFO,
            mutation=False,
            target_ref="configuration",
            hint=_edition_hint(config),
            next_command="maya health summary --config <path>",
        ),
        SetupAction(
            component="broker",
            category="setup",
            action="validate_broker_mode",
            status=config.broker.mode.value,
            severity=_broker_severity(config),
            mutation=False,
            target_ref="configuration",
            hint=_broker_hint(config),
            manual_action=config.broker.mode is not BrokerMode.DISABLED,
        ),
        SetupAction(
            component="model",
            category="setup",
            action="validate_model_mode",
            status=config.llm.mode,
            severity=SetupSeverity.INFO,
            mutation=False,
            target_ref="configuration",
            hint=_model_hint(config),
            next_command="maya doctor --config <path>",
            manual_action=bool(config.llm.credential_ref),
        ),
        SetupAction(
            component="network",
            category="setup",
            action="validate_network_policy",
            status=config.deployment.network_policy,
            severity=SetupSeverity.INFO,
            mutation=False,
            target_ref="configuration",
            hint="network policy is recorded for local setup and health guidance",
        ),
    ]
    actions.extend(_integration_setup_actions(config))
    actions.extend(_profile_setup_actions(config))
    return tuple(actions)


def _integration_setup_actions(config: MayaConfig) -> tuple[SetupAction, ...]:
    actions: list[SetupAction] = []
    for name, integration in sorted(config.integrations.items()):
        if not integration.enabled:
            status = "disabled"
            severity = SetupSeverity.INFO
            hint = f"{name} integration is disabled"
            manual = False
        elif integration.credential_mode is CredentialMode.BROKER:
            status = "broker_pending"
            severity = SetupSeverity.WARN
            hint = (
                f"{name} is configured for broker credentials; Phase 4 reports "
                "readiness only and does not create OAuth grants"
            )
            manual = True
        elif integration.credential_mode is CredentialMode.CUSTOMER_OWNED:
            status = "customer_owned"
            severity = SetupSeverity.INFO
            hint = f"{name} uses a customer-owned credential reference"
            manual = True
        elif integration.credential_mode is CredentialMode.LOCAL_ONLY:
            status = "local_only"
            severity = SetupSeverity.INFO
            hint = f"{name} uses local-only credential handling"
            manual = True
        else:
            status = "disabled"
            severity = SetupSeverity.INFO
            hint = f"{name} credential mode is disabled"
            manual = False
        actions.append(
            SetupAction(
                component=f"connector.{name}",
                category="connectors",
                action="validate_connector_setup",
                status=status,
                severity=severity,
                mutation=False,
                target_ref=f"integrations.{name}",
                hint=hint,
                next_command="maya doctor --config <path>",
                manual_action=manual,
            )
        )
    return tuple(actions)


def _profile_setup_actions(config: MayaConfig) -> tuple[SetupAction, ...]:
    actions: list[SetupAction] = []
    enabled = set(config.runtime.enabled_profiles)
    for profile, component, hint in (
        (
            ComponentProfile.METABASE,
            "metabase",
            "Metabase setup is guided through health and provisioning checks",
        ),
        (
            ComponentProfile.DOCUMENTS,
            "documents",
            "Document setup validates local document roots and LibreOffice readiness",
        ),
        (
            ComponentProfile.MESSAGING,
            "messaging",
            "Messaging setup validates connector references without OAuth",
        ),
        (
            ComponentProfile.LOCAL_MODELS,
            "local-models",
            "Local model setup validates configured endpoints without live inference",
        ),
    ):
        actions.append(
            SetupAction(
                component=component,
                category="profiles",
                action="validate_profile_enabled",
                status="enabled" if profile in enabled else "not_configured",
                severity=SetupSeverity.INFO,
                mutation=False,
                target_ref=profile.value,
                hint=hint,
                next_command="maya health summary --config <path>",
            )
        )
    return tuple(actions)


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
                component=profile.profile.value,
                category="dependencies",
                action="validate_profile_readiness",
                status=profile.status.value,
                severity=severity,
                mutation=False,
                target_ref=profile.profile.value,
                hint=profile.redacted_summary(),
                next_command="maya doctor --config <path>",
                manual_action=profile.status.value
                not in {"available", "customer_managed", "disabled"},
            )
        )
    return tuple(actions)


def _edition_hint(config: MayaConfig) -> str:
    if config.product.edition is Edition.ENTERPRISE:
        return (
            "Enterprise setup keeps credentials customer-owned and broker "
            "participation optional or disabled"
        )
    return (
        "Standard setup keeps local state customer-controlled and reports "
        "broker-assisted capabilities as pending until Phase 5"
    )


def _broker_severity(config: MayaConfig) -> SetupSeverity:
    if config.broker.mode is BrokerMode.RUNTIME:
        return SetupSeverity.WARN
    if config.broker.mode is BrokerMode.SETUP_ONLY:
        return SetupSeverity.WARN
    return SetupSeverity.INFO


def _broker_hint(config: MayaConfig) -> str:
    if config.broker.mode is BrokerMode.DISABLED:
        return "broker is disabled; setup remains fully local"
    if config.broker.mode is BrokerMode.SETUP_ONLY:
        return "setup-only broker mode is recorded; Phase 4 does not open broker sessions"
    return "runtime broker mode is recorded; Phase 4 does not implement broker/OAuth flows"


def _model_hint(config: MayaConfig) -> str:
    if config.llm.mode == "local":
        return "local model setup validates configuration without probing live inference"
    if config.llm.credential_ref:
        return "model credential reference is configured; secret value stays in local storage"
    return "model mode is configured without a raw secret in configuration"


def _target_ref(config: MayaConfig, path: Path) -> str:
    root = config.deployment.data_dir.resolve()
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError:
        return "maya-data" if resolved == root else "external"
    return f"maya-data/{relative}" if relative else "maya-data"

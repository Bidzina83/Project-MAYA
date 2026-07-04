"""Diagnostic checks for the minimal local Maya runtime."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from enum import Enum

from .agent import AgentState
from .agent.contracts import AgentRuntime
from .config import ConfigError, MayaConfig
from .connectors import validate_configured_connectors
from .dependencies import (
    DependencyReadinessStatus,
    evaluate_enabled_profile_readiness,
)
from .documents import document_capability_checks
from .governance import load_policy_gateway
from .metabase import metabase_capability_checks
from .model_config import validate_model_config
from .secrets import SecretStore, SecretStoreStatus
from .skills import packaged_document_skill_status


class DoctorStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: DoctorStatus
    message: str


@dataclass(frozen=True)
class DoctorReport:
    checks: tuple[DoctorCheck, ...]

    @property
    def healthy(self) -> bool:
        return all(check.status is not DoctorStatus.FAIL for check in self.checks)


def run_doctor(
    config: MayaConfig,
    runtime: AgentRuntime,
    *,
    lifecycle_state: AgentState | str | None = None,
    secret_store: SecretStore | None = None,
) -> DoctorReport:
    checks: list[DoctorCheck] = []
    try:
        config.validate()
    except ConfigError as exc:
        checks.append(
            DoctorCheck("config", DoctorStatus.FAIL, f"configuration invalid: {exc}")
        )
    else:
        checks.append(DoctorCheck("config", DoctorStatus.PASS, "configuration valid"))

    checks.append(_data_dir_check(config))
    checks.append(_disk_space_check(config))
    checks.append(_memory_store_check(config))
    checks.append(_governance_policy_check(config))
    checks.append(_audit_log_check(config))
    checks.append(_managed_directory_check(config, "backup.state", "backups"))
    checks.append(_managed_directory_check(config, "migration.state", "migrations"))
    checks.append(_lifecycle_state_check(lifecycle_state))
    checks.append(_enabled_profiles_check(config))
    checks.extend(_dependency_readiness_checks(config))
    checks.extend(_document_capability_checks(config))
    checks.extend(_metabase_capability_checks(config))
    checks.extend(_skill_package_checks())
    checks.append(_model_config_check(config))
    checks.append(_connector_config_check(config))

    checks.append(
        DoctorCheck(
            "local_api.binding",
            DoctorStatus.PASS,
            (
                f"bind={config.local_api.bind}; "
                f"remote_access={config.local_api.remote_access}; "
                "authentication=required"
            ),
        )
    )

    if secret_store is None:
        checks.append(
            DoctorCheck(
                "secrets.backend",
                DoctorStatus.WARN,
                "secret store was not assembled",
            )
        )
    else:
        secret_health = secret_store.health()
        checks.append(
            DoctorCheck(
                "secrets.backend",
                (
                    DoctorStatus.PASS
                    if secret_health.status is SecretStoreStatus.HEALTHY
                    else DoctorStatus.WARN
                ),
                f"{secret_health.backend}: {secret_health.status.value}",
            )
        )

    compatibility = runtime.compatibility()
    if compatibility.compatible:
        checks.append(
            DoctorCheck(
                "hermes.compatibility",
                DoctorStatus.PASS,
                f"{compatibility.runtime_name} {compatibility.runtime_version}",
            )
        )
    else:
        checks.append(
            DoctorCheck(
                "hermes.compatibility",
                DoctorStatus.FAIL,
                compatibility.reason or "runtime incompatible",
            )
        )

    health = runtime.health()
    checks.append(
        DoctorCheck(
            "hermes.health",
            DoctorStatus.PASS if health.state.value == "healthy" else DoctorStatus.FAIL,
            health.state.value,
        )
    )
    return DoctorReport(tuple(checks))


def _data_dir_check(config: MayaConfig) -> DoctorCheck:
    data_dir = config.deployment.data_dir
    if data_dir.exists() and not data_dir.is_dir():
        return DoctorCheck(
            "filesystem.data_dir",
            DoctorStatus.FAIL,
            "deployment.data_dir exists but is not a directory",
        )
    if data_dir.exists():
        return DoctorCheck(
            "filesystem.data_dir",
            DoctorStatus.PASS,
            "deployment.data_dir exists",
        )
    parent = data_dir.parent
    if parent.exists() and parent.is_dir():
        return DoctorCheck(
            "filesystem.data_dir",
            DoctorStatus.WARN,
            "deployment.data_dir will be created on first write",
        )
    return DoctorCheck(
        "filesystem.data_dir",
        DoctorStatus.FAIL,
        "deployment.data_dir parent does not exist",
    )


def _disk_space_check(config: MayaConfig) -> DoctorCheck:
    data_dir = config.deployment.data_dir
    target = data_dir if data_dir.exists() else data_dir.parent
    if not target.exists():
        return DoctorCheck(
            "filesystem.disk_space",
            DoctorStatus.FAIL,
            "cannot inspect disk space because deployment.data_dir parent is missing",
        )
    try:
        usage = shutil.disk_usage(target)
    except OSError as exc:
        return DoctorCheck(
            "filesystem.disk_space",
            DoctorStatus.WARN,
            f"disk space unavailable: {exc}",
        )
    free_mib = usage.free // (1024 * 1024)
    total_mib = usage.total // (1024 * 1024)
    return DoctorCheck(
        "filesystem.disk_space",
        DoctorStatus.PASS if usage.free > 0 else DoctorStatus.FAIL,
        f"free={free_mib} MiB; total={total_mib} MiB",
    )


def _memory_store_check(config: MayaConfig) -> DoctorCheck:
    if config.memory.retriever != "local_json":
        return DoctorCheck(
            "memory.store",
            DoctorStatus.WARN,
            f"doctor has no local check for memory.retriever={config.memory.retriever}",
        )
    store_path = config.deployment.data_dir / "memory" / "records.json"
    if not store_path.exists():
        return DoctorCheck(
            "memory.store",
            DoctorStatus.WARN,
            "local_json memory store will be created on first write",
        )
    try:
        raw = json.loads(store_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return DoctorCheck(
            "memory.store",
            DoctorStatus.FAIL,
            f"local_json memory store is unreadable: {exc}",
        )
    if not isinstance(raw, list):
        return DoctorCheck(
            "memory.store",
            DoctorStatus.FAIL,
            "local_json memory store must contain a JSON list",
        )
    return DoctorCheck(
        "memory.store",
        DoctorStatus.PASS,
        f"local_json memory store valid; records={len(raw)}",
    )


def _governance_policy_check(config: MayaConfig) -> DoctorCheck:
    policy_file = config.governance.policy_file
    if not policy_file.exists():
        return DoctorCheck(
            "governance.policy",
            DoctorStatus.WARN,
            "policy file missing; default deny gateway will be used",
        )
    try:
        load_policy_gateway(policy_file)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return DoctorCheck(
            "governance.policy",
            DoctorStatus.FAIL,
            f"policy file invalid: {exc}",
        )
    return DoctorCheck(
        "governance.policy",
        DoctorStatus.PASS,
        "policy file valid",
    )


def _audit_log_check(config: MayaConfig) -> DoctorCheck:
    audit_path = config.deployment.data_dir / "governance" / "audit" / "runtime.jsonl"
    if audit_path.exists() and not audit_path.is_file():
        return DoctorCheck(
            "audit.runtime",
            DoctorStatus.FAIL,
            "runtime audit path exists but is not a file",
        )
    if audit_path.exists():
        try:
            with audit_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        json.loads(line)
        except (OSError, json.JSONDecodeError) as exc:
            return DoctorCheck(
                "audit.runtime",
                DoctorStatus.FAIL,
                f"runtime audit log is unreadable: {exc}",
            )
        return DoctorCheck(
            "audit.runtime",
            DoctorStatus.PASS,
            "runtime audit log valid",
        )
    parent = audit_path.parent
    if parent.exists() and not parent.is_dir():
        return DoctorCheck(
            "audit.runtime",
            DoctorStatus.FAIL,
            "runtime audit directory path is not a directory",
        )
    return DoctorCheck(
        "audit.runtime",
        DoctorStatus.WARN,
        "runtime audit log will be created on first audited action",
    )


def _managed_directory_check(
    config: MayaConfig,
    check_name: str,
    relative_name: str,
) -> DoctorCheck:
    path = config.deployment.data_dir / relative_name
    if path.exists() and not path.is_dir():
        return DoctorCheck(
            check_name,
            DoctorStatus.FAIL,
            f"{relative_name} path exists but is not a directory",
        )
    if path.exists():
        return DoctorCheck(
            check_name,
            DoctorStatus.PASS,
            f"{relative_name} directory exists",
        )
    data_dir = config.deployment.data_dir
    if (
        (data_dir.exists() and data_dir.is_dir())
        or (not data_dir.exists() and data_dir.parent.exists())
    ):
        return DoctorCheck(
            check_name,
            DoctorStatus.WARN,
            f"{relative_name} directory will be created when needed",
        )
    return DoctorCheck(
        check_name,
        DoctorStatus.FAIL,
        f"{relative_name} directory parent does not exist",
    )


def _lifecycle_state_check(lifecycle_state: AgentState | str | None) -> DoctorCheck:
    if lifecycle_state is None:
        return DoctorCheck(
            "lifecycle.agent",
            DoctorStatus.WARN,
            "agent lifecycle state was not supplied",
        )
    try:
        state = AgentState(lifecycle_state)
    except ValueError:
        return DoctorCheck(
            "lifecycle.agent",
            DoctorStatus.FAIL,
            f"unknown agent lifecycle state: {lifecycle_state}",
        )
    if state is AgentState.FAILED:
        return DoctorCheck(
            "lifecycle.agent",
            DoctorStatus.FAIL,
            "agent lifecycle state is failed",
        )
    if state in {AgentState.STARTING, AgentState.STOPPING}:
        return DoctorCheck(
            "lifecycle.agent",
            DoctorStatus.WARN,
            f"agent lifecycle state is transient: {state.value}",
        )
    return DoctorCheck(
        "lifecycle.agent",
        DoctorStatus.PASS,
        f"agent lifecycle state is {state.value}",
    )


def _enabled_profiles_check(config: MayaConfig) -> DoctorCheck:
    profiles = tuple(profile.value for profile in config.runtime.enabled_profiles)
    if not profiles:
        return DoctorCheck(
            "profiles.enabled",
            DoctorStatus.FAIL,
            "no component profiles are enabled",
        )
    return DoctorCheck(
        "profiles.enabled",
        DoctorStatus.PASS,
        "enabled profiles: " + ", ".join(profiles),
    )


def _dependency_readiness_checks(config: MayaConfig) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    for profile in evaluate_enabled_profile_readiness(config):
        checks.append(
            DoctorCheck(
                f"dependencies.profile.{profile.profile.value}",
                _dependency_status_to_doctor_status(profile.status),
                profile.redacted_summary(),
            )
        )
        for dependency in profile.dependencies:
            checks.append(
                DoctorCheck(
                    dependency.check_name,
                    _dependency_status_to_doctor_status(dependency.status),
                    dependency.redacted_summary(),
                )
            )
    return checks


def _dependency_status_to_doctor_status(
    status: DependencyReadinessStatus,
) -> DoctorStatus:
    if status in {
        DependencyReadinessStatus.AVAILABLE,
        DependencyReadinessStatus.CUSTOMER_MANAGED,
        DependencyReadinessStatus.DISABLED,
    }:
        return DoctorStatus.PASS
    if status in {
        DependencyReadinessStatus.MISSING_OPTIONAL,
        DependencyReadinessStatus.UNSUPPORTED_OS,
        DependencyReadinessStatus.UNKNOWN,
    }:
        return DoctorStatus.WARN
    return DoctorStatus.FAIL


def _document_capability_checks(config: MayaConfig) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    for result in document_capability_checks(config):
        status = DoctorStatus.PASS
        if result.status == "will_create":
            status = DoctorStatus.WARN
        if result.status in {"invalid", "missing_required"}:
            status = DoctorStatus.FAIL
        checks.append(
            DoctorCheck(
                f"documents.{result.operation}",
                status,
                _summary_message(result.redacted_summary()),
            )
        )
    return checks


def _metabase_capability_checks(config: MayaConfig) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    for result in metabase_capability_checks(config):
        summary = result.redacted_summary()
        if "endpoint_state" in summary:
            name = "metabase.health"
        elif "service_artifact" in summary:
            name = "metabase.lifecycle"
        else:
            name = "metabase.provisioning"
        status_value = str(summary.get("status", "unknown"))
        status = DoctorStatus.PASS
        if status_value in {"not_ready", "blocked", "unsupported_deployment"}:
            status = DoctorStatus.FAIL
        elif status_value in {
            "live_check_deferred",
            "managed_local_artifact_missing",
        }:
            status = DoctorStatus.WARN
        checks.append(
            DoctorCheck(
                name,
                status,
                _summary_message(summary),
            )
        )
    return checks


def _skill_package_checks() -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    for result in packaged_document_skill_status():
        status = DoctorStatus.PASS if result.discoverable else DoctorStatus.FAIL
        checks.append(
            DoctorCheck(
                f"skills.{result.skill_id.replace('/', '.')}",
                status,
                _summary_message(result.redacted_summary()),
            )
        )
    return checks


def _summary_message(summary: dict[str, object]) -> str:
    return "; ".join(
        f"{key}={_summary_value(value)}"
        for key, value in sorted(summary.items())
    )


def _summary_value(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, list):
        return f"items={len(value)}"
    if isinstance(value, dict):
        return ",".join(f"{key}:{item}" for key, item in sorted(value.items()))
    return str(value)


def _model_config_check(config: MayaConfig) -> DoctorCheck:
    validation = validate_model_config(config)
    return DoctorCheck(
        "model.config",
        DoctorStatus.PASS if validation.valid else DoctorStatus.FAIL,
        f"{validation.redacted_summary()}; "
        f"timeout_seconds={config.llm.timeout_seconds}",
    )


def _connector_config_check(config: MayaConfig) -> DoctorCheck:
    if not config.integrations:
        return DoctorCheck(
            "connectors.config",
            DoctorStatus.WARN,
            "no connectors configured",
        )
    validations = validate_configured_connectors(
        config.integrations,
        broker_mode=config.broker.mode,
    )
    return DoctorCheck(
        "connectors.config",
        (
            DoctorStatus.PASS
            if all(validation.valid for validation in validations)
            else DoctorStatus.FAIL
        ),
        "; ".join(validation.redacted_summary() for validation in validations),
    )

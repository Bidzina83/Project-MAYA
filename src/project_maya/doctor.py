"""Diagnostic checks for the minimal local Maya runtime."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from .agent import AgentState
from .agent.contracts import AgentRuntime
from .config import ConfigError, MayaConfig
from .governance import load_policy_gateway
from .secrets import SecretStore, SecretStoreStatus


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
    checks.append(_memory_store_check(config))
    checks.append(_governance_policy_check(config))
    checks.append(_audit_log_check(config))
    checks.append(_lifecycle_state_check(lifecycle_state))

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

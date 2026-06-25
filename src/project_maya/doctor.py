"""Diagnostic checks for the minimal local Maya runtime."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .agent.contracts import AgentRuntime
from .config import ConfigError, MayaConfig
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

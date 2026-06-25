"""Runtime boundary used by the public Project MAYA API."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Protocol, runtime_checkable


class RuntimeHealthState(str, Enum):
    """Lifecycle-independent health states reported by a runtime adapter."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True)
class RuntimeCompatibility:
    """Compatibility report for the concrete execution runtime."""

    runtime_name: str
    runtime_version: str
    supported_contract: str
    compatible: bool
    reason: str | None = None


@dataclass(frozen=True)
class RuntimeHealth:
    """Redacted health report from a concrete execution runtime."""

    state: RuntimeHealthState
    components: Mapping[str, RuntimeHealthState]
    details: Mapping[str, str] | None = None


@runtime_checkable
class AgentRuntime(Protocol):
    """Adapter contract for an execution runtime such as Hermes Agent."""

    def compatibility(self) -> RuntimeCompatibility:
        """Report whether the runtime satisfies Maya's expected contract."""

    def attach_memory(self, memory_provider: Any) -> None:
        """Attach a runtime-native memory provider before startup."""

    def load_plugin(self, name: str, plugin: Any | None = None) -> None:
        """Load one plugin, raising when discovery or initialization fails."""

    def start(self, *, agent_name: str) -> None:
        """Start the runtime and acquire its resources."""

    def run(self, request: str, **kwargs: Any) -> Any:
        """Execute a request using the active runtime."""

    def health(self) -> RuntimeHealth:
        """Return a redacted health report for diagnostics and maya doctor."""

    def stop(self) -> None:
        """Release runtime resources. Implementations should be idempotent."""

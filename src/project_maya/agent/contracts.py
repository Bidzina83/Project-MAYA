"""Runtime boundary used by the public Project MAYA API."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AgentRuntime(Protocol):
    """Adapter contract for an execution runtime such as Hermes Agent."""

    def attach_memory(self, memory_provider: Any) -> None:
        """Attach a runtime-native memory provider before startup."""

    def load_plugin(self, name: str, plugin: Any | None = None) -> None:
        """Load one plugin, raising when discovery or initialization fails."""

    def start(self, *, agent_name: str) -> None:
        """Start the runtime and acquire its resources."""

    def run(self, request: str, **kwargs: Any) -> Any:
        """Execute a request using the active runtime."""

    def stop(self) -> None:
        """Release runtime resources. Implementations should be idempotent."""

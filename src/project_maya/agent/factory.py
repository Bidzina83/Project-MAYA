"""Public Agent facade and factory."""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from threading import RLock
from types import MappingProxyType
from typing import Any, Optional

from .contracts import AgentRuntime


class AgentError(RuntimeError):
    """Base exception for the public Agent API."""


class RuntimeNotConfiguredError(AgentError):
    """Raised when execution is requested without a runtime adapter."""


class AgentLifecycleError(AgentError):
    """Raised when an operation is invalid for the current lifecycle state."""


class AgentStartError(AgentError):
    """Raised when runtime startup fails and rollback has been attempted."""


class AgentNotRunningError(AgentLifecycleError):
    """Raised when run() is called before a successful start()."""


class AgentState(str, Enum):
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class Agent:
    """Lifecycle facade over a concrete execution runtime.

    The facade deliberately contains no fallback agent implementation. A
    Hermes adapter (or another AgentRuntime) must be supplied before startup.
    """

    def __init__(
        self,
        name: str = "project_maya.agent",
        *,
        runtime: AgentRuntime | None = None,
    ) -> None:
        self.name = name
        self._runtime = runtime
        self._memory_provider: Any | None = None
        self._pending_plugins: dict[str, Any | None] = {}
        self._loaded_plugins: dict[str, Any | None] = {}
        self._state = AgentState.CREATED
        self._lock = RLock()

    @property
    def state(self) -> AgentState:
        return self._state

    @property
    def plugins(self) -> Mapping[str, Any | None]:
        return MappingProxyType(self._loaded_plugins)

    def attach_memory(self, memory_provider: Any) -> None:
        """Configure one runtime-native memory provider before startup."""
        if memory_provider is None:
            raise TypeError("memory_provider cannot be None")
        with self._lock:
            self._require_configurable("attach memory")
            self._memory_provider = memory_provider

    def load_plugin(self, name: str, plugin: Any | None = None) -> None:
        """Queue a plugin before startup or load it into a running runtime."""
        if not name or not name.strip():
            raise ValueError("plugin name cannot be empty")
        with self._lock:
            if self._state in {
                AgentState.STARTING,
                AgentState.STOPPING,
                AgentState.STOPPED,
                AgentState.FAILED,
            }:
                raise AgentLifecycleError(
                    f"cannot load plugin while agent is {self._state.value}"
                )
            if name in self._pending_plugins or name in self._loaded_plugins:
                raise ValueError(f"plugin already configured: {name}")
            if self._state is AgentState.CREATED:
                self._pending_plugins[name] = plugin
                return

            runtime = self._require_runtime()
            runtime.load_plugin(name, plugin)
            self._loaded_plugins[name] = plugin

    def start(self) -> None:
        """Configure and start the runtime, rolling back partial startup."""
        with self._lock:
            if self._state is not AgentState.CREATED:
                raise AgentLifecycleError(
                    f"cannot start agent while it is {self._state.value}"
                )
            runtime = self._require_runtime()
            self._state = AgentState.STARTING
            loaded_during_start: list[str] = []
            try:
                if self._memory_provider is not None:
                    runtime.attach_memory(self._memory_provider)
                for name, plugin in self._pending_plugins.items():
                    runtime.load_plugin(name, plugin)
                    loaded_during_start.append(name)
                runtime.start(agent_name=self.name)
            except Exception as exc:
                try:
                    runtime.stop()
                except Exception:
                    pass
                self._state = AgentState.FAILED
                raise AgentStartError(f"failed to start agent {self.name!r}") from exc

            for name in loaded_during_start:
                self._loaded_plugins[name] = self._pending_plugins[name]
            self._pending_plugins.clear()
            self._state = AgentState.RUNNING

    def run(self, request: str, **kwargs: Any) -> Any:
        with self._lock:
            if self._state is not AgentState.RUNNING:
                raise AgentNotRunningError(
                    f"cannot run request while agent is {self._state.value}"
                )
            runtime = self._require_runtime()
        return runtime.run(request, **kwargs)

    def stop(self) -> None:
        with self._lock:
            if self._state is AgentState.STOPPED:
                return
            if self._state is AgentState.CREATED:
                self._state = AgentState.STOPPED
                return
            if self._state is not AgentState.RUNNING:
                raise AgentLifecycleError(
                    f"cannot stop agent while it is {self._state.value}"
                )
            runtime = self._require_runtime()
            self._state = AgentState.STOPPING
            try:
                runtime.stop()
            except Exception:
                self._state = AgentState.FAILED
                raise
            self._state = AgentState.STOPPED

    def __enter__(self) -> "Agent":
        self.start()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.stop()

    def _require_runtime(self) -> AgentRuntime:
        if self._runtime is None:
            raise RuntimeNotConfiguredError(
                "no execution runtime configured; supply a Hermes AgentRuntime adapter"
            )
        if not isinstance(self._runtime, AgentRuntime):
            raise TypeError("runtime does not implement the AgentRuntime contract")
        return self._runtime

    def _require_configurable(self, operation: str) -> None:
        if self._state is not AgentState.CREATED:
            raise AgentLifecycleError(
                f"cannot {operation} while agent is {self._state.value}"
            )


def create_agent(
    name: Optional[str] = None,
    *,
    runtime: AgentRuntime | None = None,
) -> Agent:
    """Create an Agent facade; execution requires a concrete runtime adapter."""
    return Agent(name=name or "project_maya.agent", runtime=runtime)

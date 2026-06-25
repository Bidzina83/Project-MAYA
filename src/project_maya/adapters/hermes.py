"""Concrete adapter boundary for Hermes Agent runtime integration."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Callable

from project_maya.agent.contracts import (
    RuntimeCompatibility,
    RuntimeHealth,
    RuntimeHealthState,
)


class HermesRuntimeUnavailableError(RuntimeError):
    """Raised when no compatible Hermes runtime factory can be loaded."""


class HermesRuntimeAdapter:
    """Adapter from Project MAYA's AgentRuntime contract to Hermes.

    The adapter is concrete about the boundary it owns, but it does not provide
    a fallback runtime. If Hermes is not installed or an explicit factory is
    not supplied, compatibility and health report that honestly.
    """

    contract_version = "project-maya.agent-runtime.v1"

    def __init__(
        self,
        *,
        factory: Callable[..., Any] | None = None,
        factory_path: str = "run_agent:AIAgent",
        runtime_version: str | None = None,
        supported_contract: str | None = None,
        factory_kwargs: dict[str, Any] | None = None,
    ) -> None:
        self._factory = factory
        self._factory_path = factory_path
        self._runtime_version = runtime_version or "unknown"
        self._supported_contract = supported_contract or self.contract_version
        self._factory_kwargs = dict(factory_kwargs or {})
        self._runtime: Any | None = None
        self._pending_memory: list[Any] = []
        self._pending_plugins: list[tuple[str, Any | None]] = []
        self._startup_error: str | None = None
        self._started = False

    def compatibility(self) -> RuntimeCompatibility:
        try:
            factory = self._resolve_factory()
        except Exception as exc:
            return RuntimeCompatibility(
                runtime_name="hermes-agent",
                runtime_version=self._runtime_version,
                supported_contract=self._supported_contract,
                compatible=False,
                reason=f"Hermes runtime factory unavailable: {exc}",
            )

        if not callable(factory):
            return RuntimeCompatibility(
                runtime_name="hermes-agent",
                runtime_version=self._runtime_version,
                supported_contract=self._supported_contract,
                compatible=False,
                reason="Hermes runtime factory is not callable",
            )

        return RuntimeCompatibility(
            runtime_name="hermes-agent",
            runtime_version=self._runtime_version,
            supported_contract=self._supported_contract,
            compatible=True,
        )

    def attach_memory(self, memory_provider: Any) -> None:
        if self._runtime is None:
            self._pending_memory.append(memory_provider)
            return
        runtime = self._runtime
        if not hasattr(runtime, "attach_memory"):
            raise HermesRuntimeUnavailableError("Hermes runtime cannot attach memory")
        runtime.attach_memory(memory_provider)

    def load_plugin(self, name: str, plugin: Any | None = None) -> None:
        if self._runtime is None:
            self._pending_plugins.append((name, plugin))
            return
        runtime = self._runtime
        if not hasattr(runtime, "load_plugin"):
            raise HermesRuntimeUnavailableError("Hermes runtime cannot load plugins")
        runtime.load_plugin(name, plugin)

    def start(self, *, agent_name: str) -> None:
        try:
            runtime = self._runtime or self._build_runtime(agent_name=agent_name)
            for memory_provider in self._pending_memory:
                if not hasattr(runtime, "attach_memory"):
                    raise HermesRuntimeUnavailableError(
                        "Hermes runtime cannot attach memory"
                    )
                runtime.attach_memory(memory_provider)
            for name, plugin in self._pending_plugins:
                if not hasattr(runtime, "load_plugin"):
                    raise HermesRuntimeUnavailableError(
                        "Hermes runtime cannot load plugins"
                    )
                runtime.load_plugin(name, plugin)
            if not hasattr(runtime, "start"):
                raise HermesRuntimeUnavailableError("Hermes runtime cannot start")
            runtime.start(agent_name=agent_name)
            self._runtime = runtime
            self._pending_memory.clear()
            self._pending_plugins.clear()
            self._started = True
            self._startup_error = None
        except Exception as exc:
            self._startup_error = str(exc)
            raise

    def run(self, request: str, **kwargs: Any) -> Any:
        runtime = self._require_runtime()
        if not hasattr(runtime, "run"):
            raise HermesRuntimeUnavailableError("Hermes runtime cannot execute requests")
        return runtime.run(request, **kwargs)

    def health(self) -> RuntimeHealth:
        components: dict[str, RuntimeHealthState] = {
            "adapter": RuntimeHealthState.HEALTHY,
            "hermes_runtime": (
                RuntimeHealthState.HEALTHY
                if self._started
                else RuntimeHealthState.UNHEALTHY
            ),
        }
        details: dict[str, str] = {
            "factory_path": self._factory_path,
            "contract": self._supported_contract,
        }
        if self._startup_error:
            details["startup_error"] = self._startup_error
        try:
            compatibility = self.compatibility()
        except Exception as exc:
            compatibility = RuntimeCompatibility(
                runtime_name="hermes-agent",
                runtime_version=self._runtime_version,
                supported_contract=self._supported_contract,
                compatible=False,
                reason=str(exc),
            )
        if not compatibility.compatible:
            components["hermes_runtime"] = RuntimeHealthState.UNHEALTHY
            details["compatibility"] = compatibility.reason or "incompatible"
        return RuntimeHealth(
            state=(
                RuntimeHealthState.HEALTHY
                if all(state is RuntimeHealthState.HEALTHY for state in components.values())
                else RuntimeHealthState.UNHEALTHY
            ),
            components=components,
            details=details,
        )

    def stop(self) -> None:
        if self._runtime is not None and hasattr(self._runtime, "stop"):
            self._runtime.stop()
        self._started = False

    def _build_runtime(self, *, agent_name: str) -> Any:
        factory = self._resolve_factory()
        kwargs = dict(self._factory_kwargs)
        kwargs.setdefault("agent_name", agent_name)
        try:
            runtime = factory(**kwargs)
        except TypeError:
            kwargs.pop("agent_name", None)
            runtime = factory(**kwargs)
        return _normalize_hermes_runtime(runtime)

    def _resolve_factory(self) -> Callable[..., Any]:
        if self._factory is not None:
            return self._factory
        module_name, separator, attr_name = self._factory_path.partition(":")
        if not separator or not module_name or not attr_name:
            raise HermesRuntimeUnavailableError(
                "factory_path must use 'module:attribute' format"
            )
        module = import_module(module_name)
        factory = getattr(module, attr_name)
        if not callable(factory):
            raise HermesRuntimeUnavailableError(
                f"{self._factory_path} is not callable"
            )
        self._factory = factory
        return factory

    def _require_runtime(self) -> Any:
        if self._runtime is None:
            self._runtime = self._build_runtime(agent_name="project_maya.agent")
        return self._runtime


class HermesAIAgentRuntime:
    """Lifecycle shim for Hermes `run_agent.AIAgent` instances.

    Hermes' current public construction seam is chat-oriented: `AIAgent`
    exposes `chat()` / `run_conversation()` rather than an explicit
    start/stop lifecycle. This wrapper gives Maya a lifecycle boundary without
    inventing execution behavior.
    """

    def __init__(self, agent: Any) -> None:
        self._agent = agent
        self._started = False

    def start(self, *, agent_name: str) -> None:
        self._started = True

    def run(self, request: str, **kwargs: Any) -> Any:
        if not self._started:
            raise HermesRuntimeUnavailableError("Hermes AIAgent is not started")
        if hasattr(self._agent, "chat"):
            return self._agent.chat(request)
        result = self._agent.run_conversation(request, **kwargs)
        if isinstance(result, dict) and "final_response" in result:
            return result["final_response"]
        return result

    def stop(self) -> None:
        if hasattr(self._agent, "stop"):
            self._agent.stop()
        elif hasattr(self._agent, "close"):
            self._agent.close()
        self._started = False


def _normalize_hermes_runtime(runtime: Any) -> Any:
    if all(hasattr(runtime, name) for name in ("start", "run", "stop")):
        return runtime
    if hasattr(runtime, "chat") or hasattr(runtime, "run_conversation"):
        return HermesAIAgentRuntime(runtime)
    return runtime

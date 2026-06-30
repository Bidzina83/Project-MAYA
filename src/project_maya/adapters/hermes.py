"""Concrete adapter boundary for Hermes Agent runtime integration."""

from __future__ import annotations

import hashlib
import json
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
        self._memory_provider: Any | None = None
        self._hermes_memory_provider: Any | None = None
        self._started = False

    def attach_memory(self, memory_provider: Any) -> None:
        self._memory_provider = memory_provider
        if hasattr(self._agent, "attach_memory"):
            self._agent.attach_memory(memory_provider)
            return
        manager = getattr(self._agent, "_memory_manager", None)
        if manager is None or not hasattr(manager, "add_provider"):
            raise HermesRuntimeUnavailableError(
                "Hermes AIAgent memory manager is unavailable"
            )
        bridge = HermesMemoryProviderBridge(memory_provider)
        manager.add_provider(bridge)
        self._hermes_memory_provider = bridge

    def start(self, *, agent_name: str) -> None:
        if self._hermes_memory_provider is not None:
            session_id = getattr(self._agent, "session_id", None) or agent_name
            self._hermes_memory_provider.initialize(
                session_id=session_id,
                agent_name=agent_name,
                platform="project_maya",
            )
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
        if hasattr(self._agent, "shutdown_memory_provider"):
            self._agent.shutdown_memory_provider()
        if hasattr(self._agent, "stop"):
            self._agent.stop()
        elif hasattr(self._agent, "close"):
            self._agent.close()
        self._started = False


class HermesMemoryProviderBridge:
    """Hermes MemoryProvider-shaped adapter over Maya's governed memory provider."""

    name = "maya"

    def __init__(self, maya_memory_provider: Any) -> None:
        self._maya = maya_memory_provider
        self._session_id = ""

    def is_available(self) -> bool:
        return True

    def initialize(self, session_id: str, **kwargs: Any) -> None:
        self._session_id = session_id
        if hasattr(self._maya, "begin_session"):
            self._maya.begin_session(session_id, metadata=dict(kwargs))

    def system_prompt_block(self) -> str:
        return ""

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if not hasattr(self._maya, "prefetch"):
            return ""
        records = self._maya.prefetch(query, limit=5)
        if not records:
            return ""
        return "Maya governed memory context:\n" + json.dumps(
            records,
            sort_keys=True,
            ensure_ascii=True,
        )

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        return None

    def sync_turn(
        self,
        user_content: str,
        assistant_content: str,
        *,
        session_id: str = "",
        messages: list[dict[str, Any]] | None = None,
    ) -> None:
        if not hasattr(self._maya, "synchronize_turn"):
            return
        effective_session = session_id or self._session_id
        digest = hashlib.sha256(
            f"{effective_session}\0{user_content}\0{assistant_content}".encode(
                "utf-8"
            )
        ).hexdigest()[:16]
        self._maya.synchronize_turn(
            [
                {
                    "id": f"hermes-turn:{effective_session}:{digest}",
                    "category": "conversation_turn",
                    "source": "hermes-agent",
                    "session_id": effective_session,
                    "user_content": user_content,
                    "assistant_content": assistant_content,
                }
            ]
        )

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        return []

    def handle_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        raise HermesRuntimeUnavailableError(
            f"Maya memory provider does not expose Hermes tool: {tool_name}"
        )

    def shutdown(self) -> None:
        if not self._session_id:
            return
        if hasattr(self._maya, "end_session"):
            self._maya.end_session(self._session_id)
        self._session_id = ""


def _normalize_hermes_runtime(runtime: Any) -> Any:
    if all(hasattr(runtime, name) for name in ("start", "run", "stop")):
        return runtime
    if hasattr(runtime, "chat") or hasattr(runtime, "run_conversation"):
        return HermesAIAgentRuntime(runtime)
    return runtime

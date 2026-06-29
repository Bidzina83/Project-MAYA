"""Configuration-driven assembly for the minimal local Maya product."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .adapters import HermesRuntimeAdapter
from .agent import Agent, create_agent
from .agent.contracts import RuntimeHealth
from .audit import LocalJsonlAuditSink
from .config import MayaConfig
from .governance import (
    ActionAuthorizationGateway,
    DenyByDefaultGateway,
    load_policy_gateway,
)
from .local_api import BearerTokenAuthenticator, LocalAPI
from .memory import (
    GovernedMemoryRetriever,
    HermesMemoryProvider,
    LocalJsonRetriever,
    MemoryRetriever,
)
from .model_config import require_valid_model_config
from .runtime import GovernedAgentRuntime, ModelEgressPolicy
from .secrets import SecretStore, build_platform_secret_store


@dataclass(frozen=True)
class LocalMayaProduct:
    """Assembled local Maya components for Phase 1."""

    agent: Agent
    retriever: LocalJsonRetriever
    memory: GovernedMemoryRetriever
    memory_provider: HermesMemoryProvider
    runtime: GovernedAgentRuntime
    secret_store: SecretStore
    local_api: LocalAPI
    audit_sink: LocalJsonlAuditSink

    def start(self) -> None:
        """Start the assembled Maya runtime through the public Agent facade."""
        self.agent.start()

    def run(self, request: str, **kwargs: Any) -> Any:
        """Execute a request through the governed Agent lifecycle path."""
        return self.agent.run(request, **kwargs)

    def health(self) -> RuntimeHealth:
        """Return redacted runtime health for the assembled product."""
        return self.runtime.health()

    def stop(self) -> None:
        """Stop the assembled Maya runtime and release runtime resources."""
        self.agent.stop()

    def __enter__(self) -> "LocalMayaProduct":
        self.start()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.stop()


def build_local_product(
    config: MayaConfig,
    *,
    gateway: ActionAuthorizationGateway | None = None,
    actor_id: str = "local-user",
) -> LocalMayaProduct:
    """Assemble the minimal governed local Maya runtime from configuration."""

    config.validate()
    require_valid_model_config(config)
    secret_store = build_platform_secret_store(config.deployment.data_dir)
    retriever = _build_retriever(config)
    base_memory = MemoryRetriever(retriever)
    hermes = _build_hermes_runtime(config)
    audit_sink = _build_audit_sink(config)
    authorization_gateway = gateway or _build_gateway(config)
    memory = GovernedMemoryRetriever(
        base_memory,
        authorization_gateway,
        actor_id=actor_id,
        audit_sink=audit_sink,
    )
    memory_provider = HermesMemoryProvider(memory)
    governed = GovernedAgentRuntime(
        hermes,
        authorization_gateway,
        actor_id=actor_id,
        audit_sink=audit_sink,
        model_egress=_build_model_egress(config),
    )
    agent = create_agent(
        name=f"project_maya.{config.product.instance_id}",
        runtime=governed,
    )
    agent.attach_memory(memory_provider)
    local_api = LocalAPI(
        agent=agent,
        runtime=governed,
        authenticator=BearerTokenAuthenticator(secret_store),
    )
    return LocalMayaProduct(
        agent=agent,
        retriever=retriever,
        memory=memory,
        memory_provider=memory_provider,
        runtime=governed,
        secret_store=secret_store,
        local_api=local_api,
        audit_sink=audit_sink,
    )


def _build_retriever(config: MayaConfig) -> LocalJsonRetriever:
    if config.memory.retriever != "local_json":
        raise ValueError(
            "Phase 1 local product supports memory.retriever='local_json'"
        )
    store_path = config.deployment.data_dir / "memory" / "records.json"
    return LocalJsonRetriever(store_path)


def _build_gateway(config: MayaConfig) -> ActionAuthorizationGateway:
    if config.governance.policy_file.is_file():
        return load_policy_gateway(config.governance.policy_file)
    return DenyByDefaultGateway()


def _build_audit_sink(config: MayaConfig) -> LocalJsonlAuditSink:
    return LocalJsonlAuditSink(
        config.deployment.data_dir / "governance" / "audit" / "runtime.jsonl"
    )


def _build_model_egress(config: MayaConfig) -> ModelEgressPolicy | None:
    if config.llm.mode == "local":
        return None
    return ModelEgressPolicy(
        mode=config.llm.mode,
        provider=config.llm.provider,
        endpoint=config.llm.endpoint,
    )


def _build_hermes_runtime(config: MayaConfig) -> HermesRuntimeAdapter:
    factory_kwargs: dict[str, object] = {
        "model": config.llm.model,
        "provider": config.llm.provider,
    }
    if config.llm.endpoint:
        factory_kwargs["base_url"] = config.llm.endpoint
    if config.llm.timeout_seconds:
        factory_kwargs["request_overrides"] = {
            "timeout_seconds": config.llm.timeout_seconds
        }
    return HermesRuntimeAdapter(
        factory_path=config.runtime.hermes_factory,
        runtime_version=config.runtime.hermes_runtime_version,
        supported_contract=config.runtime.hermes_compatibility,
        factory_kwargs=factory_kwargs,
    )

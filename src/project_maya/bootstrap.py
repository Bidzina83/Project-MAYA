"""Configuration-driven assembly for the minimal local Maya product."""

from __future__ import annotations

from dataclasses import dataclass

from .adapters import HermesRuntimeAdapter
from .agent import Agent, create_agent
from .audit import LocalJsonlAuditSink
from .config import MayaConfig
from .governance import (
    ActionAuthorizationGateway,
    DenyByDefaultGateway,
    load_policy_gateway,
)
from .local_api import BearerTokenAuthenticator, LocalAPI
from .memory import LocalJsonRetriever, MemoryRetriever
from .runtime import GovernedAgentRuntime
from .secrets import SecretStore, build_platform_secret_store


@dataclass(frozen=True)
class LocalMayaProduct:
    """Assembled local Maya components for Phase 1."""

    agent: Agent
    retriever: LocalJsonRetriever
    memory: MemoryRetriever
    runtime: GovernedAgentRuntime
    secret_store: SecretStore
    local_api: LocalAPI
    audit_sink: LocalJsonlAuditSink


def build_local_product(
    config: MayaConfig,
    *,
    gateway: ActionAuthorizationGateway | None = None,
    actor_id: str = "local-user",
) -> LocalMayaProduct:
    """Assemble the minimal governed local Maya runtime from configuration."""

    config.validate()
    secret_store = build_platform_secret_store(config.deployment.data_dir)
    retriever = _build_retriever(config)
    memory = MemoryRetriever(retriever)
    hermes = _build_hermes_runtime(config)
    audit_sink = _build_audit_sink(config)
    governed = GovernedAgentRuntime(
        hermes,
        gateway or _build_gateway(config),
        actor_id=actor_id,
        audit_sink=audit_sink,
    )
    agent = create_agent(
        name=f"project_maya.{config.product.instance_id}",
        runtime=governed,
    )
    local_api = LocalAPI(
        agent=agent,
        runtime=governed,
        authenticator=BearerTokenAuthenticator(secret_store),
    )
    return LocalMayaProduct(
        agent=agent,
        retriever=retriever,
        memory=memory,
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

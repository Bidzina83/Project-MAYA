"""Typed Project MAYA configuration contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


class ConfigError(ValueError):
    """Raised when a configuration violates the product contract."""


SUPPORTED_SCHEMA_VERSION = 2


class Edition(str, Enum):
    STANDARD = "standard"
    ENTERPRISE = "enterprise"


class BrokerMode(str, Enum):
    RUNTIME = "runtime"
    SETUP_ONLY = "setup_only"
    DISABLED = "disabled"


class CredentialMode(str, Enum):
    BROKER = "broker"
    CUSTOMER_OWNED = "customer_owned"
    LOCAL_ONLY = "local_only"
    DISABLED = "disabled"


class ComponentProfile(str, Enum):
    CORE = "maya-core"
    METABASE = "maya-metabase"
    DOCUMENTS = "maya-documents"
    MESSAGING = "maya-messaging"
    BROWSER = "maya-browser"
    LOCAL_MODELS = "maya-local-models"


@dataclass(frozen=True)
class ProductConfig:
    edition: Edition
    instance_id: str


@dataclass(frozen=True)
class DeploymentConfig:
    deployment_class: str
    network_policy: str
    data_dir: Path


@dataclass(frozen=True)
class RuntimeConfig:
    hermes_compatibility: str
    enabled_profiles: tuple[ComponentProfile, ...] = (ComponentProfile.CORE,)
    hermes_factory: str = "run_agent:AIAgent"
    hermes_runtime_version: str | None = None


@dataclass(frozen=True)
class BrokerConfig:
    mode: BrokerMode = BrokerMode.DISABLED
    endpoint: str | None = None


@dataclass(frozen=True)
class ModelConfig:
    mode: str
    provider: str
    model: str
    credential_ref: str | None = None
    endpoint: str | None = None
    timeout_seconds: int = 60


@dataclass(frozen=True)
class IntegrationConfig:
    enabled: bool
    credential_mode: CredentialMode
    credential_ref: str | None = None


@dataclass(frozen=True)
class MemoryConfig:
    hermes_provider: str
    retriever: str
    registry: str
    governance_enabled: bool = True


@dataclass(frozen=True)
class GovernanceConfig:
    policy_file: Path
    audit_enabled: bool = True
    default_action: str = "deny"
    minimum_memory_trust: float = 0.7


@dataclass(frozen=True)
class MetabaseApplicationDatabaseConfig:
    engine: str
    credential_ref: str


@dataclass(frozen=True)
class MetabaseAnalyticsSourceConfig:
    name: str
    engine: str
    credential_ref: str


@dataclass(frozen=True)
class MetabaseConfig:
    enabled: bool
    deployment: str
    endpoint: str | None
    application_database: MetabaseApplicationDatabaseConfig | None = None
    analytics_sources: tuple[MetabaseAnalyticsSourceConfig, ...] = field(
        default_factory=tuple
    )


@dataclass(frozen=True)
class LocalAPIConfig:
    bind: str = "127.0.0.1"
    port: int | None = None
    remote_access: bool = False


@dataclass(frozen=True)
class MayaConfig:
    schema_version: int
    product: ProductConfig
    deployment: DeploymentConfig
    runtime: RuntimeConfig
    broker: BrokerConfig
    llm: ModelConfig
    integrations: Mapping[str, IntegrationConfig]
    memory: MemoryConfig
    governance: GovernanceConfig
    metabase: MetabaseConfig
    local_api: LocalAPIConfig

    def validate(self) -> None:
        if self.schema_version != SUPPORTED_SCHEMA_VERSION:
            raise ConfigError(
                f"schema_version must be {SUPPORTED_SCHEMA_VERSION}"
            )
        if not self.product.instance_id.strip():
            raise ConfigError("product.instance_id is required")
        if self.deployment.data_dir.is_absolute() is False:
            raise ConfigError("deployment.data_dir must be absolute")
        if ComponentProfile.CORE not in self.runtime.enabled_profiles:
            raise ConfigError("maya-core profile is required")
        if self.broker.mode is BrokerMode.DISABLED and self.broker.endpoint:
            raise ConfigError("broker.endpoint requires broker mode")
        if self.llm.timeout_seconds < 1:
            raise ConfigError("llm.timeout_seconds must be positive")
        if not 0 <= self.governance.minimum_memory_trust <= 1:
            raise ConfigError("governance.minimum_memory_trust must be 0..1")
        if self.local_api.remote_access and self.local_api.bind.startswith("127."):
            raise ConfigError("remote_access requires a non-loopback bind address")
        for name, integration in self.integrations.items():
            self._validate_integration(name, integration)
        if self.metabase.enabled:
            if self.metabase.application_database is None:
                raise ConfigError("metabase.application_database is required")
            for source in self.metabase.analytics_sources:
                _require_secret_ref(
                    source.credential_ref,
                    f"metabase.analytics_sources.{source.name}.credential_ref",
                )
            _require_secret_ref(
                self.metabase.application_database.credential_ref,
                "metabase.application_database.credential_ref",
            )

    def _validate_integration(
        self, name: str, integration: IntegrationConfig
    ) -> None:
        if name == "telegram" and integration.credential_mode is CredentialMode.BROKER:
            raise ConfigError("telegram must use a customer-owned credential")
        if integration.enabled and integration.credential_mode is CredentialMode.DISABLED:
            raise ConfigError(f"{name} is enabled with disabled credentials")
        if integration.credential_ref is not None:
            _require_secret_ref(integration.credential_ref, f"{name}.credential_ref")


def _require_secret_ref(value: str, field_name: str) -> None:
    if not value.startswith("secret://"):
        raise ConfigError(f"{field_name} must be a secret:// reference")


def config_from_mapping(data: Mapping[str, Any]) -> MayaConfig:
    """Build a typed config from a parsed JSON/YAML mapping."""

    if "schema_version" not in data:
        raise ConfigError("schema_version is required")
    try:
        schema_version = int(data["schema_version"])
    except (TypeError, ValueError) as exc:
        raise ConfigError("schema_version must be an integer") from exc

    integrations = {
        name: IntegrationConfig(
            enabled=bool(raw.get("enabled", False)),
            credential_mode=CredentialMode(raw["credential_mode"]),
            credential_ref=raw.get("credential_ref"),
        )
        for name, raw in data.get("integrations", {}).items()
    }
    metabase_raw = data["metabase"]
    app_db_raw = metabase_raw.get("application_database")
    analytics_sources = tuple(
        MetabaseAnalyticsSourceConfig(
            name=source["name"],
            engine=source["engine"],
            credential_ref=source["credential_ref"],
        )
        for source in metabase_raw.get("analytics_sources", ())
    )
    config = MayaConfig(
        schema_version=schema_version,
        product=ProductConfig(
            edition=Edition(data["product"]["edition"]),
            instance_id=data["product"]["instance_id"],
        ),
        deployment=DeploymentConfig(
            deployment_class=data["deployment"]["class"],
            network_policy=data["deployment"]["network_policy"],
            data_dir=Path(data["deployment"]["data_dir"]),
        ),
        runtime=RuntimeConfig(
            hermes_compatibility=data["runtime"]["hermes_compatibility"],
            enabled_profiles=tuple(
                ComponentProfile(profile)
                for profile in data["runtime"].get(
                    "enabled_profiles", [ComponentProfile.CORE.value]
                )
            ),
            hermes_factory=data["runtime"].get("hermes_factory", "run_agent:AIAgent"),
            hermes_runtime_version=data["runtime"].get("hermes_runtime_version"),
        ),
        broker=BrokerConfig(
            mode=BrokerMode(data.get("broker", {}).get("mode", "disabled")),
            endpoint=data.get("broker", {}).get("endpoint"),
        ),
        llm=ModelConfig(
            mode=data["llm"]["mode"],
            provider=data["llm"]["provider"],
            model=data["llm"]["model"],
            credential_ref=data["llm"].get("credential_ref"),
            endpoint=data["llm"].get("endpoint"),
            timeout_seconds=int(data["llm"].get("timeout_seconds", 60)),
        ),
        integrations=integrations,
        memory=MemoryConfig(**data["memory"]),
        governance=GovernanceConfig(
            policy_file=Path(data["governance"]["policy_file"]),
            audit_enabled=bool(data["governance"].get("audit_enabled", True)),
            default_action=data["governance"].get("default_action", "deny"),
            minimum_memory_trust=float(
                data["governance"].get("minimum_memory_trust", 0.7)
            ),
        ),
        metabase=MetabaseConfig(
            enabled=bool(metabase_raw["enabled"]),
            deployment=metabase_raw["deployment"],
            endpoint=metabase_raw.get("endpoint"),
            application_database=(
                MetabaseApplicationDatabaseConfig(**app_db_raw)
                if app_db_raw is not None
                else None
            ),
            analytics_sources=analytics_sources,
        ),
        local_api=LocalAPIConfig(**data.get("local_api", {})),
    )
    config.validate()
    return config

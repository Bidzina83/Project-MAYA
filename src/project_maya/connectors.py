"""Connector declaration contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .config import BrokerMode, ConfigError, CredentialMode, IntegrationConfig


@dataclass(frozen=True)
class ConnectorCapability:
    name: str
    scopes: tuple[str, ...] = ()
    can_read: bool = True
    can_write: bool = False


@dataclass(frozen=True)
class ConnectorManifest:
    name: str
    credential_mode: CredentialMode
    credential_ref: str | None
    capabilities: tuple[ConnectorCapability, ...]
    identity_mapping: Mapping[str, str] = field(default_factory=dict)
    allowlists: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    webhook_verification: str | None = None
    idempotency_required: bool = True
    revocation_supported: bool = True

    def validate(self) -> None:
        if not self.name.strip():
            raise ConfigError("connector name is required")
        if self.name == "telegram" and self.credential_mode is CredentialMode.BROKER:
            raise ConfigError("telegram cannot use broker credentials")
        if self.credential_mode is CredentialMode.DISABLED and self.credential_ref:
            raise ConfigError("disabled connectors must not declare credential_ref")
        if self.credential_ref and not self.credential_ref.startswith("secret://"):
            raise ConfigError("connector credential_ref must be a secret:// reference")
        if not self.capabilities:
            raise ConfigError("connector must declare at least one capability")
        if any(not capability.name.strip() for capability in self.capabilities):
            raise ConfigError("connector capability name is required")


class ConnectorValidationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"


class ConnectorHealthState(str, Enum):
    CONFIGURED = "configured"
    DISABLED = "disabled"
    UNAVAILABLE = "unavailable"
    INVALID = "invalid"


@dataclass(frozen=True)
class ConnectorValidation:
    """Redacted connector validation result for diagnostics."""

    name: str
    status: ConnectorValidationStatus
    enabled: bool
    credential_mode: CredentialMode
    credential_ref_state: str
    capabilities: tuple[str, ...]
    scopes: tuple[str, ...]
    allowlist_state: Mapping[str, str]
    health: ConnectorHealthState
    network_used: bool
    message: str

    @property
    def valid(self) -> bool:
        return self.status is ConnectorValidationStatus.VALID

    def redacted_summary(self) -> str:
        enabled_state = "enabled" if self.enabled else "disabled"
        capabilities = ",".join(self.capabilities) if self.capabilities else "none"
        scopes = ",".join(self.scopes) if self.scopes else "none"
        allowlists = (
            ",".join(
                f"{key}:{value}"
                for key, value in sorted(self.allowlist_state.items())
            )
            if self.allowlist_state
            else "none"
        )
        return (
            f"{self.name}:{enabled_state},"
            f"credential_mode={self.credential_mode.value},"
            f"credential_ref={self.credential_ref_state},"
            f"capabilities={capabilities},"
            f"scopes={scopes},"
            f"allowlists={allowlists},"
            f"health={self.health.value},"
            f"network_used={str(self.network_used).lower()},"
            f"message={self.message}"
        )


@dataclass(frozen=True)
class ConnectorCredentialContract:
    """Static credential and capability contract for a supported connector."""

    name: str
    supported_credential_modes: tuple[CredentialMode, ...]
    credential_required_modes: tuple[CredentialMode, ...]
    capabilities: tuple[ConnectorCapability, ...]
    allowlist_keys: tuple[str, ...] = ()
    broker_allowed_when_disabled: bool = False

    def validate_integration(
        self,
        integration: IntegrationConfig,
        *,
        broker_mode: BrokerMode,
    ) -> None:
        if (
            self.name == "telegram"
            and integration.credential_mode is CredentialMode.BROKER
        ):
            raise ConfigError("telegram must use a customer-owned credential")
        if integration.credential_mode not in self.supported_credential_modes:
            allowed = ", ".join(mode.value for mode in self.supported_credential_modes)
            raise ConfigError(
                f"{self.name}.credential_mode must be one of: {allowed}"
            )
        if integration.enabled and integration.credential_mode is CredentialMode.DISABLED:
            raise ConfigError(f"{self.name} is enabled with disabled credentials")
        if (
            integration.credential_mode is CredentialMode.BROKER
            and broker_mode is BrokerMode.DISABLED
            and not self.broker_allowed_when_disabled
        ):
            raise ConfigError(
                f"{self.name}.credential_mode=broker requires broker mode"
            )
        if integration.credential_mode is CredentialMode.DISABLED:
            if integration.credential_ref is not None:
                raise ConfigError(
                    f"{self.name}.credential_ref must be absent when disabled"
                )
            return
        if integration.credential_mode in self.credential_required_modes:
            if integration.credential_ref is None:
                raise ConfigError(
                    f"{self.name}.credential_ref is required for "
                    f"{integration.credential_mode.value}"
                )
            if not integration.credential_ref.startswith("secret://"):
                raise ConfigError(
                    f"{self.name}.credential_ref must be a secret:// reference"
                )
        elif (
            integration.credential_ref is not None
            and not integration.credential_ref.startswith("secret://")
        ):
            raise ConfigError(
                f"{self.name}.credential_ref must be a secret:// reference"
            )

    def manifest_for(self, integration: IntegrationConfig) -> ConnectorManifest:
        return ConnectorManifest(
            name=self.name,
            credential_mode=integration.credential_mode,
            credential_ref=integration.credential_ref,
            capabilities=self.capabilities,
            allowlists={key: () for key in self.allowlist_keys},
            revocation_supported=(
                integration.credential_mode
                in {CredentialMode.BROKER, CredentialMode.CUSTOMER_OWNED}
            ),
        )


GOOGLE_CONNECTOR_CONTRACT = ConnectorCredentialContract(
    name="google",
    supported_credential_modes=(
        CredentialMode.BROKER,
        CredentialMode.CUSTOMER_OWNED,
        CredentialMode.DISABLED,
    ),
    credential_required_modes=(
        CredentialMode.BROKER,
        CredentialMode.CUSTOMER_OWNED,
    ),
    capabilities=(
        ConnectorCapability(
            name="drive.read",
            scopes=("https://www.googleapis.com/auth/drive.readonly",),
            can_read=True,
        ),
        ConnectorCapability(
            name="calendar.read",
            scopes=("https://www.googleapis.com/auth/calendar.readonly",),
            can_read=True,
        ),
    ),
    allowlist_keys=("users", "resources"),
)


SLACK_CONNECTOR_CONTRACT = ConnectorCredentialContract(
    name="slack",
    supported_credential_modes=(
        CredentialMode.BROKER,
        CredentialMode.CUSTOMER_OWNED,
        CredentialMode.DISABLED,
    ),
    credential_required_modes=(
        CredentialMode.BROKER,
        CredentialMode.CUSTOMER_OWNED,
    ),
    capabilities=(
        ConnectorCapability(
            name="message.read",
            scopes=("channels:history",),
            can_read=True,
        ),
        ConnectorCapability(
            name="message.send",
            scopes=("chat:write",),
            can_read=False,
            can_write=True,
        ),
    ),
    allowlist_keys=("workspaces", "channels", "users"),
)


TELEGRAM_CONNECTOR_CONTRACT = ConnectorCredentialContract(
    name="telegram",
    supported_credential_modes=(
        CredentialMode.CUSTOMER_OWNED,
        CredentialMode.DISABLED,
    ),
    credential_required_modes=(CredentialMode.CUSTOMER_OWNED,),
    capabilities=(
        ConnectorCapability(name="message.receive", can_read=True),
        ConnectorCapability(
            name="message.send",
            can_read=False,
            can_write=True,
        ),
    ),
    allowlist_keys=("chats", "users"),
)


SUPPORTED_CONNECTOR_CONTRACTS = {
    contract.name: contract
    for contract in (
        GOOGLE_CONNECTOR_CONTRACT,
        SLACK_CONNECTOR_CONTRACT,
        TELEGRAM_CONNECTOR_CONTRACT,
    )
}


def get_connector_contract(name: str) -> ConnectorCredentialContract:
    try:
        return SUPPORTED_CONNECTOR_CONTRACTS[name]
    except KeyError as exc:
        raise ConfigError(f"unsupported connector: {name}") from exc


def build_connector_manifest(
    name: str,
    integration: IntegrationConfig,
    *,
    broker_mode: BrokerMode,
) -> ConnectorManifest:
    contract = get_connector_contract(name)
    contract.validate_integration(integration, broker_mode=broker_mode)
    manifest = contract.manifest_for(integration)
    manifest.validate()
    return manifest


def validate_connector(
    name: str,
    integration: IntegrationConfig,
    *,
    broker_mode: BrokerMode,
) -> ConnectorValidation:
    try:
        manifest = build_connector_manifest(
            name,
            integration,
            broker_mode=broker_mode,
        )
    except ConfigError as exc:
        return ConnectorValidation(
            name=name,
            status=ConnectorValidationStatus.INVALID,
            enabled=integration.enabled,
            credential_mode=integration.credential_mode,
            credential_ref_state=_credential_ref_state(integration.credential_ref),
            capabilities=(),
            scopes=(),
            allowlist_state={},
            health=ConnectorHealthState.INVALID,
            network_used=False,
            message=str(exc),
        )
    capabilities = tuple(capability.name for capability in manifest.capabilities)
    scopes = tuple(
        dict.fromkeys(
            scope
            for capability in manifest.capabilities
            for scope in capability.scopes
        )
    )
    health = (
        ConnectorHealthState.DISABLED
        if manifest.credential_mode is CredentialMode.DISABLED
        else ConnectorHealthState.UNAVAILABLE
    )
    message = (
        "connector disabled"
        if health is ConnectorHealthState.DISABLED
        else "live provider validation unavailable"
    )
    return ConnectorValidation(
        name=name,
        status=ConnectorValidationStatus.VALID,
        enabled=integration.enabled,
        credential_mode=integration.credential_mode,
        credential_ref_state=_credential_ref_state(integration.credential_ref),
        capabilities=capabilities,
        scopes=scopes,
        allowlist_state={
            key: ("configured" if values else "not_configured")
            for key, values in sorted(manifest.allowlists.items())
        },
        health=health,
        network_used=False,
        message=message,
    )


def validate_configured_connectors(
    integrations: Mapping[str, IntegrationConfig],
    *,
    broker_mode: BrokerMode,
) -> tuple[ConnectorValidation, ...]:
    return tuple(
        validate_connector(name, integration, broker_mode=broker_mode)
        for name, integration in sorted(integrations.items())
    )


def _credential_ref_state(value: str | None) -> str:
    if value is None:
        return "not_configured"
    if value.startswith("secret://"):
        return "configured"
    return "invalid"

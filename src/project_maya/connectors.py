"""Connector declaration contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
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

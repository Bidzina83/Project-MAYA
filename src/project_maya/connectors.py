"""Connector declaration contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .config import ConfigError, CredentialMode


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

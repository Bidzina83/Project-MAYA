"""Secret-reference contracts for Project MAYA configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class SecretReferenceError(ValueError):
    """Raised when a secret reference is malformed."""


@dataclass(frozen=True)
class SecretRef:
    name: str

    @classmethod
    def parse(cls, value: str) -> "SecretRef":
        prefix = "secret://"
        if not value.startswith(prefix) or value == prefix:
            raise SecretReferenceError("secret references must use secret://<name>")
        return cls(value.removeprefix(prefix))

    def __str__(self) -> str:
        return f"secret://{self.name}"


@runtime_checkable
class SecretStore(Protocol):
    """Platform or Enterprise vault interface. Values never live in config."""

    def read(self, ref: SecretRef) -> str:
        """Return a secret value for runtime use."""

    def write(self, ref: SecretRef, value: str) -> None:
        """Store or rotate a secret value."""

    def delete(self, ref: SecretRef) -> None:
        """Revoke a local secret value."""

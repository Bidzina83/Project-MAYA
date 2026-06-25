"""Secret-reference contracts and local backends for Project MAYA."""

from __future__ import annotations

import base64
import ctypes
import os
from ctypes import wintypes
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable


class SecretReferenceError(ValueError):
    """Raised when a secret reference is malformed."""


class SecretStoreError(RuntimeError):
    """Raised when a secret backend operation cannot be completed."""


class SecretStoreStatus(str, Enum):
    HEALTHY = "healthy"
    UNAVAILABLE = "unavailable"
    UNHEALTHY = "unhealthy"


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


@dataclass(frozen=True)
class SecretStoreHealth:
    backend: str
    status: SecretStoreStatus
    message: str


@runtime_checkable
class SecretStore(Protocol):
    """Platform or Enterprise vault interface. Values never live in config."""

    def read(self, ref: SecretRef) -> str:
        """Return a secret value for runtime use."""

    def write(self, ref: SecretRef, value: str) -> None:
        """Store or rotate a secret value."""

    def delete(self, ref: SecretRef) -> None:
        """Revoke a local secret value."""

    def contains(self, ref: SecretRef) -> bool:
        """Return whether a secret reference has a stored value."""

    def health(self) -> SecretStoreHealth:
        """Return redacted backend health for diagnostics."""


class UnavailableSecretStore:
    """Honest fallback when no approved local backend is available."""

    def __init__(self, reason: str) -> None:
        self._reason = reason

    def read(self, ref: SecretRef) -> str:
        _validate_secret_ref(ref)
        raise SecretStoreError(self._reason)

    def write(self, ref: SecretRef, value: str) -> None:
        _validate_secret_ref(ref)
        raise SecretStoreError(self._reason)

    def delete(self, ref: SecretRef) -> None:
        _validate_secret_ref(ref)
        raise SecretStoreError(self._reason)

    def contains(self, ref: SecretRef) -> bool:
        _validate_secret_ref(ref)
        return False

    def health(self) -> SecretStoreHealth:
        return SecretStoreHealth(
            backend="unavailable",
            status=SecretStoreStatus.UNAVAILABLE,
            message=self._reason,
        )


class WindowsDPAPISecretStore:
    """Windows DPAPI-backed secret store.

    Encrypted blobs live under the Maya data directory, while encryption keys
    are protected by Windows for the current user profile.
    """

    def __init__(self, root: Path) -> None:
        if os.name != "nt":
            raise SecretStoreError("Windows DPAPI is only available on Windows")
        self._root = root

    def read(self, ref: SecretRef) -> str:
        path = self._path_for(ref)
        try:
            ciphertext = base64.b64decode(path.read_bytes(), validate=True)
        except FileNotFoundError as exc:
            raise SecretStoreError(f"secret not found: {ref}") from exc
        except ValueError as exc:
            raise SecretStoreError(f"secret blob is not valid base64: {ref}") from exc
        return _dpapi_unprotect(ciphertext).decode("utf-8")

    def write(self, ref: SecretRef, value: str) -> None:
        path = self._path_for(ref)
        path.parent.mkdir(parents=True, exist_ok=True)
        ciphertext = _dpapi_protect(value.encode("utf-8"))
        path.write_bytes(base64.b64encode(ciphertext))

    def delete(self, ref: SecretRef) -> None:
        try:
            self._path_for(ref).unlink()
        except FileNotFoundError:
            return

    def contains(self, ref: SecretRef) -> bool:
        return self._path_for(ref).is_file()

    def health(self) -> SecretStoreHealth:
        try:
            self._root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return SecretStoreHealth(
                backend="windows-dpapi",
                status=SecretStoreStatus.UNHEALTHY,
                message=f"secret store path unavailable: {exc}",
            )
        return SecretStoreHealth(
            backend="windows-dpapi",
            status=SecretStoreStatus.HEALTHY,
            message="Windows DPAPI secret store available",
        )

    def _path_for(self, ref: SecretRef) -> Path:
        parts = tuple(_safe_secret_part(part) for part in ref.name.split("/"))
        if not parts:
            raise SecretReferenceError("secret reference name is required")
        base_path = self._root.joinpath(*parts)
        path = base_path.parent / f"{base_path.name}.secret"
        root = self._root.resolve()
        resolved = path.resolve()
        if root != resolved and root not in resolved.parents:
            raise SecretReferenceError("secret reference escapes secret store")
        return resolved


def build_platform_secret_store(data_dir: Path) -> SecretStore:
    if os.name == "nt":
        return WindowsDPAPISecretStore(data_dir / "secrets")
    return UnavailableSecretStore(
        "no approved platform secret backend is implemented for this OS"
    )


def _safe_secret_part(value: str) -> str:
    if not value or value in {".", ".."}:
        raise SecretReferenceError("secret reference contains an invalid path part")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
    if any(char not in allowed for char in value):
        raise SecretReferenceError("secret reference contains unsupported characters")
    return value


def _validate_secret_ref(ref: SecretRef) -> None:
    for part in ref.name.split("/"):
        _safe_secret_part(part)


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def _dpapi_protect(data: bytes) -> bytes:
    in_buffer = ctypes.create_string_buffer(data)
    in_blob = _DataBlob(len(data), ctypes.cast(in_buffer, ctypes.POINTER(ctypes.c_char)))
    out_blob = _DataBlob()
    if not ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    ):
        raise SecretStoreError("Windows DPAPI failed to protect secret")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)


def _dpapi_unprotect(data: bytes) -> bytes:
    in_buffer = ctypes.create_string_buffer(data)
    in_blob = _DataBlob(len(data), ctypes.cast(in_buffer, ctypes.POINTER(ctypes.c_char)))
    out_blob = _DataBlob()
    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    ):
        raise SecretStoreError("Windows DPAPI failed to unprotect secret")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)

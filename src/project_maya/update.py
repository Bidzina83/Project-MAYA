"""Local update status helpers for Project MAYA."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import MayaConfig


class UpdateError(RuntimeError):
    """Raised when local update metadata cannot be inspected safely."""


@dataclass(frozen=True)
class UpdateStatus:
    operation: str
    supported: bool
    status: str
    metadata_path: Path
    current_version: str | None = None
    available_version: str | None = None
    rollback_version: str | None = None
    signed_manifest: bool = False
    network_used: bool = False
    mutation: bool = False
    action_required: str | None = None


def check_updates(config: MayaConfig) -> UpdateStatus:
    """Inspect local update metadata without contacting update services."""
    config.validate()
    manifest_path = _updates_dir(config) / "update-manifest.json"
    if not manifest_path.exists():
        return UpdateStatus(
            operation="check",
            supported=False,
            status="unavailable",
            metadata_path=manifest_path,
            action_required="signed update manifest is not configured",
        )
    manifest = _read_json_object(manifest_path)
    signed = bool(manifest.get("signed"))
    return UpdateStatus(
        operation="check",
        supported=signed,
        status="available" if signed else "unsigned_manifest_rejected",
        metadata_path=manifest_path,
        current_version=_string_or_none(manifest.get("current_version")),
        available_version=_string_or_none(manifest.get("available_version")),
        signed_manifest=signed,
        action_required=None if signed else "provide a signed update manifest",
    )


def rollback_update(config: MayaConfig) -> UpdateStatus:
    """Inspect local rollback metadata without modifying installed artifacts."""
    config.validate()
    rollback_path = _updates_dir(config) / "rollback.json"
    if not rollback_path.exists():
        return UpdateStatus(
            operation="rollback",
            supported=False,
            status="unavailable",
            metadata_path=rollback_path,
            action_required="rollback metadata is not available",
        )
    metadata = _read_json_object(rollback_path)
    signed = bool(metadata.get("signed"))
    return UpdateStatus(
        operation="rollback",
        supported=signed,
        status="ready" if signed else "unsigned_rollback_rejected",
        metadata_path=rollback_path,
        current_version=_string_or_none(metadata.get("current_version")),
        rollback_version=_string_or_none(metadata.get("rollback_version")),
        signed_manifest=signed,
        action_required=None if signed else "provide signed rollback metadata",
    )


def _updates_dir(config: MayaConfig) -> Path:
    return config.deployment.data_dir / "updates"


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise UpdateError("update metadata path is not a file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UpdateError("update metadata is unreadable") from exc
    if not isinstance(value, dict):
        raise UpdateError("update metadata must be a JSON object")
    return value


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)

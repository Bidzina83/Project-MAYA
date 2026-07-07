"""Local update status helpers for Project MAYA."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import MayaConfig
from .release import (
    ReleaseMetadataError,
    ReleaseSignatureError,
    current_platform_id,
    verify_rollback_manifest,
    verify_update_manifest,
)


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
    platform: str | None = None
    sbom_ref: str | None = None
    provenance_ref: str | None = None
    artifact_sha256: str | None = None
    migration_compatibility: str | None = None
    release_manifest_ref: str | None = None
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
    try:
        verified = verify_update_manifest(
            manifest,
            expected_platform=current_platform_id(),
        )
    except ReleaseSignatureError:
        return UpdateStatus(
            operation="check",
            supported=False,
            status="signature_rejected",
            metadata_path=manifest_path,
            signed_manifest=False,
            action_required="provide trusted signed update metadata",
        )
    except ReleaseMetadataError:
        return UpdateStatus(
            operation="check",
            supported=False,
            status="metadata_rejected",
            metadata_path=manifest_path,
            signed_manifest=False,
            action_required="provide complete Phase 6 update metadata",
        )
    return UpdateStatus(
        operation="check",
        supported=True,
        status="available",
        metadata_path=manifest_path,
        current_version=verified.current_version,
        available_version=verified.available_version,
        signed_manifest=True,
        platform=verified.platform,
        sbom_ref=verified.sbom_ref,
        provenance_ref=verified.provenance_ref,
        artifact_sha256=verified.artifact.sha256,
        migration_compatibility=verified.migration_compatibility,
        release_manifest_ref=verified.release_manifest_ref,
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
    try:
        verified = verify_rollback_manifest(
            metadata,
            expected_platform=current_platform_id(),
        )
    except ReleaseSignatureError:
        return UpdateStatus(
            operation="rollback",
            supported=False,
            status="signature_rejected",
            metadata_path=rollback_path,
            signed_manifest=False,
            action_required="provide trusted signed rollback metadata",
        )
    except ReleaseMetadataError:
        return UpdateStatus(
            operation="rollback",
            supported=False,
            status="metadata_rejected",
            metadata_path=rollback_path,
            signed_manifest=False,
            action_required="provide complete Phase 6 rollback metadata",
        )
    return UpdateStatus(
        operation="rollback",
        supported=True,
        status="ready",
        metadata_path=rollback_path,
        current_version=verified.current_version,
        rollback_version=verified.rollback_version,
        signed_manifest=True,
        platform=verified.platform,
        sbom_ref=verified.sbom_ref,
        provenance_ref=verified.provenance_ref,
        artifact_sha256=verified.artifact.sha256,
        migration_compatibility=verified.migration_compatibility,
        release_manifest_ref=verified.release_manifest_ref,
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



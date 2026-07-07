"""Signed release metadata contracts for Project MAYA Phase 6."""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
else:
    Ed25519PrivateKey = Any
    Ed25519PublicKey = Any


PHASE6_METADATA_VERSION = 1
SUPPORTED_RELEASE_PLATFORMS = frozenset({"windows-desktop"})
NON_PRODUCTION_TEST_KEY_ID = "phase6-test-key"
_NON_PRODUCTION_TEST_PRIVATE_BYTES = bytes(range(1, 33))


class ReleaseMetadataError(ValueError):
    """Raised when release metadata is malformed or incomplete."""


class ReleaseSignatureError(ReleaseMetadataError):
    """Raised when signed release metadata cannot be trusted."""


@dataclass(frozen=True)
class SignatureEnvelope:
    algorithm: str
    key_id: str
    signature: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SignatureEnvelope":
        try:
            return cls(
                algorithm=str(data["algorithm"]),
                key_id=str(data["key_id"]),
                signature=str(data["signature"]),
            )
        except KeyError as exc:
            raise ReleaseSignatureError("signature envelope is incomplete") from exc

    def to_mapping(self) -> dict[str, str]:
        return {
            "algorithm": self.algorithm,
            "key_id": self.key_id,
            "signature": self.signature,
        }


@dataclass(frozen=True)
class ReleaseArtifact:
    name: str
    path: str
    sha256: str
    size_bytes: int
    kind: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ReleaseArtifact":
        return cls(
            name=str(data["name"]),
            path=str(data["path"]),
            sha256=str(data["sha256"]),
            size_bytes=int(data["size_bytes"]),
            kind=str(data["kind"]),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "name": self.name,
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "kind": self.kind,
        }


@dataclass(frozen=True)
class ReleaseProvenance:
    source: str
    commit: str
    builder: str
    hermes_runtime_commit: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ReleaseProvenance":
        return cls(
            source=str(data["source"]),
            commit=str(data["commit"]),
            builder=str(data["builder"]),
            hermes_runtime_commit=str(data["hermes_runtime_commit"]),
        )

    def to_mapping(self) -> dict[str, str]:
        return {
            "source": self.source,
            "commit": self.commit,
            "builder": self.builder,
            "hermes_runtime_commit": self.hermes_runtime_commit,
        }


@dataclass(frozen=True)
class PlatformQualification:
    platform: str
    advertised: bool
    status: str
    evidence: tuple[str, ...]
    boundary: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "PlatformQualification":
        return cls(
            platform=str(data["platform"]),
            advertised=bool(data["advertised"]),
            status=str(data["status"]),
            evidence=tuple(str(item) for item in data.get("evidence", ())),
            boundary=str(data.get("boundary", "")),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "platform": self.platform,
            "advertised": self.advertised,
            "status": self.status,
            "evidence": list(self.evidence),
            "boundary": self.boundary,
        }


@dataclass(frozen=True)
class OfflineEnterpriseBundle:
    included: bool
    path: str | None
    sha256: str | None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> "OfflineEnterpriseBundle":
        if data is None:
            return cls(included=False, path=None, sha256=None)
        return cls(
            included=bool(data.get("included", False)),
            path=_string_or_none(data.get("path")),
            sha256=_string_or_none(data.get("sha256")),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "included": self.included,
            "path": self.path,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class ReleaseManifest:
    metadata_version: int
    product: str
    version: str
    platform: str
    artifacts: tuple[ReleaseArtifact, ...]
    sbom_ref: str
    provenance_ref: str
    provenance: ReleaseProvenance
    platform_qualification: PlatformQualification
    offline_enterprise_bundle: OfflineEnterpriseBundle
    signature: SignatureEnvelope | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ReleaseManifest":
        signature = data.get("signature")
        return cls(
            metadata_version=int(data["metadata_version"]),
            product=str(data["product"]),
            version=str(data["version"]),
            platform=str(data["platform"]),
            artifacts=tuple(
                ReleaseArtifact.from_mapping(item)
                for item in data.get("artifacts", ())
            ),
            sbom_ref=str(data["sbom_ref"]),
            provenance_ref=str(data["provenance_ref"]),
            provenance=ReleaseProvenance.from_mapping(data["provenance"]),
            platform_qualification=PlatformQualification.from_mapping(
                data["platform_qualification"]
            ),
            offline_enterprise_bundle=OfflineEnterpriseBundle.from_mapping(
                data.get("offline_enterprise_bundle")
            ),
            signature=(
                SignatureEnvelope.from_mapping(signature)
                if isinstance(signature, Mapping)
                else None
            ),
        )

    def to_mapping(self, *, include_signature: bool = True) -> dict[str, object]:
        data: dict[str, object] = {
            "metadata_version": self.metadata_version,
            "product": self.product,
            "version": self.version,
            "platform": self.platform,
            "artifacts": [artifact.to_mapping() for artifact in self.artifacts],
            "sbom_ref": self.sbom_ref,
            "provenance_ref": self.provenance_ref,
            "provenance": self.provenance.to_mapping(),
            "platform_qualification": self.platform_qualification.to_mapping(),
            "offline_enterprise_bundle": self.offline_enterprise_bundle.to_mapping(),
        }
        if include_signature and self.signature is not None:
            data["signature"] = self.signature.to_mapping()
        return data


@dataclass(frozen=True)
class UpdateManifest:
    metadata_version: int
    current_version: str
    available_version: str
    platform: str
    artifact: ReleaseArtifact
    sbom_ref: str
    provenance_ref: str
    migration_compatibility: str
    rollback_ref: str
    release_manifest_ref: str
    signature: SignatureEnvelope | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "UpdateManifest":
        signature = data.get("signature")
        return cls(
            metadata_version=int(data["metadata_version"]),
            current_version=str(data["current_version"]),
            available_version=str(data["available_version"]),
            platform=str(data["platform"]),
            artifact=ReleaseArtifact.from_mapping(data["artifact"]),
            sbom_ref=str(data["sbom_ref"]),
            provenance_ref=str(data["provenance_ref"]),
            migration_compatibility=str(data["migration_compatibility"]),
            rollback_ref=str(data["rollback_ref"]),
            release_manifest_ref=str(data["release_manifest_ref"]),
            signature=(
                SignatureEnvelope.from_mapping(signature)
                if isinstance(signature, Mapping)
                else None
            ),
        )

    def to_mapping(self, *, include_signature: bool = True) -> dict[str, object]:
        data: dict[str, object] = {
            "metadata_version": self.metadata_version,
            "current_version": self.current_version,
            "available_version": self.available_version,
            "platform": self.platform,
            "artifact": self.artifact.to_mapping(),
            "sbom_ref": self.sbom_ref,
            "provenance_ref": self.provenance_ref,
            "migration_compatibility": self.migration_compatibility,
            "rollback_ref": self.rollback_ref,
            "release_manifest_ref": self.release_manifest_ref,
        }
        if include_signature and self.signature is not None:
            data["signature"] = self.signature.to_mapping()
        return data


@dataclass(frozen=True)
class RollbackManifest:
    metadata_version: int
    current_version: str
    rollback_version: str
    platform: str
    artifact: ReleaseArtifact
    sbom_ref: str
    provenance_ref: str
    migration_compatibility: str
    release_manifest_ref: str
    signature: SignatureEnvelope | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "RollbackManifest":
        signature = data.get("signature")
        return cls(
            metadata_version=int(data["metadata_version"]),
            current_version=str(data["current_version"]),
            rollback_version=str(data["rollback_version"]),
            platform=str(data["platform"]),
            artifact=ReleaseArtifact.from_mapping(data["artifact"]),
            sbom_ref=str(data["sbom_ref"]),
            provenance_ref=str(data["provenance_ref"]),
            migration_compatibility=str(data["migration_compatibility"]),
            release_manifest_ref=str(data["release_manifest_ref"]),
            signature=(
                SignatureEnvelope.from_mapping(signature)
                if isinstance(signature, Mapping)
                else None
            ),
        )

    def to_mapping(self, *, include_signature: bool = True) -> dict[str, object]:
        data: dict[str, object] = {
            "metadata_version": self.metadata_version,
            "current_version": self.current_version,
            "rollback_version": self.rollback_version,
            "platform": self.platform,
            "artifact": self.artifact.to_mapping(),
            "sbom_ref": self.sbom_ref,
            "provenance_ref": self.provenance_ref,
            "migration_compatibility": self.migration_compatibility,
            "release_manifest_ref": self.release_manifest_ref,
        }
        if include_signature and self.signature is not None:
            data["signature"] = self.signature.to_mapping()
        return data


def current_platform_id() -> str:
    if sys.platform == "win32":
        return "windows-desktop"
    if sys.platform == "darwin":
        return "macos-desktop"
    if sys.platform.startswith("linux"):
        return "linux-desktop"
    return "unknown"


def platform_qualification_for(platform: str | None = None) -> PlatformQualification:
    platform_id = platform or current_platform_id()
    if platform_id == "windows-desktop":
        return PlatformQualification(
            platform=platform_id,
            advertised=True,
            status="qualified",
            evidence=(
                "docs/examples/phase4_windows_operator_smoke.md",
                "scripts/verify_phase1_package.py",
                "scripts/verify_phase6_release.py",
            ),
            boundary="Windows desktop is the first advertised Phase 6 platform.",
        )
    return PlatformQualification(
        platform=platform_id,
        advertised=False,
        status="not_advertised",
        evidence=(),
        boundary=(
            "Platform support is not advertised until install, lifecycle, "
            "health, backup, restore, update, rollback, and clean-install "
            "qualification pass for that artifact."
        ),
    )


def verify_release_manifest(
    data: Mapping[str, Any],
    public_keys: Mapping[str, str | bytes | Ed25519PublicKey] | None = None,
    *,
    expected_platform: str | None = None,
) -> ReleaseManifest:
    manifest = ReleaseManifest.from_mapping(data)
    _verify_common_manifest(manifest.metadata_version, manifest.platform, expected_platform)
    if not manifest.artifacts:
        raise ReleaseMetadataError("release manifest must list at least one artifact")
    if not manifest.sbom_ref:
        raise ReleaseMetadataError("release manifest must include sbom_ref")
    if not manifest.provenance_ref:
        raise ReleaseMetadataError("release manifest must include provenance_ref")
    _verify_signature(
        manifest.to_mapping(include_signature=False),
        manifest.signature,
        public_keys,
    )
    return manifest


def verify_update_manifest(
    data: Mapping[str, Any],
    public_keys: Mapping[str, str | bytes | Ed25519PublicKey] | None = None,
    *,
    expected_platform: str | None = None,
) -> UpdateManifest:
    manifest = UpdateManifest.from_mapping(data)
    _verify_common_manifest(manifest.metadata_version, manifest.platform, expected_platform)
    _require_update_refs(
        manifest.sbom_ref,
        manifest.provenance_ref,
        manifest.rollback_ref,
        manifest.release_manifest_ref,
    )
    _verify_signature(
        manifest.to_mapping(include_signature=False),
        manifest.signature,
        public_keys,
    )
    return manifest


def verify_rollback_manifest(
    data: Mapping[str, Any],
    public_keys: Mapping[str, str | bytes | Ed25519PublicKey] | None = None,
    *,
    expected_platform: str | None = None,
) -> RollbackManifest:
    manifest = RollbackManifest.from_mapping(data)
    _verify_common_manifest(manifest.metadata_version, manifest.platform, expected_platform)
    _require_update_refs(
        manifest.sbom_ref,
        manifest.provenance_ref,
        manifest.release_manifest_ref,
    )
    _verify_signature(
        manifest.to_mapping(include_signature=False),
        manifest.signature,
        public_keys,
    )
    return manifest


def sign_mapping_for_release(
    payload: Mapping[str, Any],
    *,
    private_key: "Ed25519PrivateKey",
    key_id: str,
) -> dict[str, object]:
    data = dict(payload)
    data.pop("signature", None)
    signature = private_key.sign(canonical_json_bytes(data))
    data["signature"] = SignatureEnvelope(
        algorithm="ed25519",
        key_id=key_id,
        signature=_b64encode(signature),
    ).to_mapping()
    return data


def non_production_test_private_key() -> "Ed25519PrivateKey":
    _, private_key_type, *_ = _crypto()
    return private_key_type.from_private_bytes(_NON_PRODUCTION_TEST_PRIVATE_BYTES)


def default_release_public_keys() -> dict[str, str]:
    public_key = non_production_test_private_key().public_key()
    _, _, _, Encoding, _, PublicFormat, _ = _crypto()
    return {
        NON_PRODUCTION_TEST_KEY_ID: _b64encode(
            public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
        )
    }


def non_production_private_key_bytes_for_tests() -> bytes:
    _, _, _, Encoding, PrivateFormat, _, NoEncryption = _crypto()
    return non_production_test_private_key().private_bytes(
        Encoding.Raw,
        PrivateFormat.Raw,
        NoEncryption(),
    )


def canonical_json_bytes(data: Mapping[str, Any]) -> bytes:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseMetadataError("release metadata is unreadable") from exc
    if not isinstance(value, dict):
        raise ReleaseMetadataError("release metadata must be a JSON object")
    return value


def write_canonical_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(data) + b"\n")


def artifact_from_file(
    path: Path,
    *,
    name: str | None = None,
    path_ref: str | None = None,
    kind: str,
) -> ReleaseArtifact:
    stat = path.stat()
    return ReleaseArtifact(
        name=name or path.name,
        path=path_ref or path.name,
        sha256=sha256_file(path),
        size_bytes=stat.st_size,
        kind=kind,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_common_manifest(
    metadata_version: int,
    platform: str,
    expected_platform: str | None,
) -> None:
    if metadata_version != PHASE6_METADATA_VERSION:
        raise ReleaseMetadataError("unsupported release metadata version")
    if platform not in SUPPORTED_RELEASE_PLATFORMS:
        raise ReleaseMetadataError("release platform is not advertised")
    if expected_platform is not None and platform != expected_platform:
        raise ReleaseMetadataError("release platform does not match request")


def _require_update_refs(*values: str) -> None:
    if any(not value for value in values):
        raise ReleaseMetadataError(
            "update metadata must include sbom, provenance, release, and rollback refs"
        )


def _verify_signature(
    payload: Mapping[str, Any],
    signature: SignatureEnvelope | None,
    public_keys: Mapping[str, str | bytes | Ed25519PublicKey] | None,
) -> None:
    if signature is None:
        raise ReleaseSignatureError("release metadata is unsigned")
    if signature.algorithm != "ed25519":
        raise ReleaseSignatureError("unsupported release signature algorithm")
    keys = public_keys or default_release_public_keys()
    public_key = keys.get(signature.key_id)
    if public_key is None:
        raise ReleaseSignatureError("release signature key is not trusted")
    verifier = _public_key_from_value(public_key)
    invalid_signature, *_ = _crypto()
    try:
        verifier.verify(_b64decode(signature.signature), canonical_json_bytes(payload))
    except (invalid_signature, ValueError) as exc:
        raise ReleaseSignatureError("release signature verification failed") from exc


def _public_key_from_value(value: str | bytes | "Ed25519PublicKey") -> "Ed25519PublicKey":
    _, _, public_key_type, *_ = _crypto()
    if isinstance(value, public_key_type):
        return value
    if isinstance(value, str):
        raw = _b64decode(value)
    else:
        raw = value
    return public_key_type.from_public_bytes(raw)


def _crypto():
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey,
            Ed25519PublicKey,
        )
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            PrivateFormat,
            PublicFormat,
            NoEncryption,
        )
    except ModuleNotFoundError as exc:
        raise ReleaseSignatureError(
            "release signature support requires cryptography"
        ) from exc
    return (
        InvalidSignature,
        Ed25519PrivateKey,
        Ed25519PublicKey,
        Encoding,
        PrivateFormat,
        PublicFormat,
        NoEncryption,
    )


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padded = value + ("=" * (-len(value) % 4))
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)

"""Local backup helpers for Project MAYA."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import MayaConfig, config_to_mapping


class BackupError(RuntimeError):
    """Raised when a local backup cannot be created safely."""


class RestoreError(RuntimeError):
    """Raised when a local backup cannot be restored safely."""


@dataclass(frozen=True)
class BackupResult:
    archive_path: Path
    files: int
    manifest: "BackupManifest"


@dataclass(frozen=True)
class BackupManifest:
    schema_version: int
    created_at: str
    instance_id: str
    files: int
    included_roots: tuple[str, ...]
    excluded_roots: tuple[str, ...]
    package_version: str | None = None
    runtime_version: str | None = None

    def redacted_summary(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "instance_id": self.instance_id,
            "files": self.files,
            "included_roots": list(self.included_roots),
            "excluded_roots": list(self.excluded_roots),
            "package_version": self.package_version,
            "runtime_version": self.runtime_version,
        }


@dataclass(frozen=True)
class RestoreResult:
    archive_path: Path
    destination: Path
    files: int
    dry_run: bool
    conflicts: int = 0
    overwrite_required: bool = False
    manifest_status: str = "valid"
    destination_ref: str = "restore-destination"

    def redacted_summary(self) -> dict[str, object]:
        return {
            "archive": "backup-archive",
            "destination": self.destination_ref,
            "files": self.files,
            "dry_run": self.dry_run,
            "conflicts": self.conflicts,
            "overwrite_required": self.overwrite_required,
            "manifest_status": self.manifest_status,
        }


@dataclass(frozen=True)
class BackupInspection:
    archive_path: Path
    manifest: BackupManifest
    members: int

    def redacted_summary(self) -> dict[str, object]:
        return {
            "archive": "backup-archive",
            "members": self.members,
            "manifest": self.manifest.redacted_summary(),
        }


def plan_restore_backup(
    archive_path: Path,
    destination: Path,
    *,
    allow_overwrite: bool = False,
) -> RestoreResult:
    """Plan a local Maya restore without extracting archive contents."""

    source = archive_path.resolve()
    target = destination.resolve()
    if not source.is_file():
        raise RestoreError("backup archive does not exist")
    if target.exists() and not target.is_dir():
        raise RestoreError("restore destination is not a directory")
    try:
        with zipfile.ZipFile(source) as archive:
            members = _restore_members(archive)
            _read_manifest(archive)
            restore_plan = [
                (_restore_target(target, name), name)
                for name in members
            ]
    except zipfile.BadZipFile as exc:
        raise RestoreError("backup archive is unreadable") from exc
    conflicts = [
        path for path, _ in restore_plan if path.exists() and not allow_overwrite
    ]
    return RestoreResult(
        archive_path=source,
        destination=target,
        files=len(restore_plan),
        dry_run=True,
        conflicts=len(conflicts),
        overwrite_required=bool(conflicts),
        manifest_status="valid",
        destination_ref="restore-destination",
    )


def create_local_backup(
    config: MayaConfig,
    *,
    destination: Path | None = None,
) -> BackupResult:
    """Create a local archive of Maya state and normalized configuration."""

    config.validate()
    data_dir = config.deployment.data_dir
    if not data_dir.is_dir():
        raise BackupError("deployment.data_dir does not exist")

    archive_path = destination or _default_backup_path(config)
    archive_path = archive_path.resolve()
    if archive_path.exists():
        raise BackupError("backup destination already exists")
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    files = 0
    archived_files: list[Path] = []
    temporary = archive_path.with_suffix(archive_path.suffix + ".tmp")
    try:
        with tempfile.TemporaryDirectory(prefix="maya-backup-") as snapshot_dir:
            with zipfile.ZipFile(
                temporary,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as archive:
                archive.writestr(
                    "maya-config.json",
                    json.dumps(config_to_mapping(config), indent=2, sort_keys=True)
                    + "\n",
                )
                files += 1
                for path in _iter_backup_files(data_dir):
                    archive_source = path
                    if _is_memory_database(data_dir, path):
                        archive_source = Path(snapshot_dir) / "memory.sqlite3"
                        _snapshot_sqlite_database(path, archive_source)
                    archive.write(archive_source, _archive_name(data_dir, path))
                    files += 1
                    archived_files.append(path)
                manifest = _build_manifest(config, archived_files, files + 1)
                archive.writestr(
                    "maya-backup-manifest.json",
                    json.dumps(manifest.redacted_summary(), indent=2, sort_keys=True)
                    + "\n",
                )
                files += 1
        temporary.replace(archive_path)
    except Exception as exc:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise BackupError("backup creation failed") from exc

    return BackupResult(archive_path=archive_path, files=files, manifest=manifest)


def inspect_backup_archive(archive_path: Path) -> BackupInspection:
    """Inspect a local Maya backup archive without extracting it."""

    source = archive_path.resolve()
    if not source.is_file():
        raise RestoreError("backup archive does not exist")
    try:
        with zipfile.ZipFile(source) as archive:
            members = _restore_members(archive)
            manifest = _read_manifest(archive)
    except zipfile.BadZipFile as exc:
        raise RestoreError("backup archive is unreadable") from exc
    return BackupInspection(archive_path=source, manifest=manifest, members=len(members))


def restore_local_backup(
    archive_path: Path,
    destination: Path,
    *,
    apply: bool = False,
    allow_overwrite: bool = False,
) -> RestoreResult:
    """Validate and optionally restore a local Maya backup archive."""

    source = archive_path.resolve()
    target = destination.resolve()
    if not source.is_file():
        raise RestoreError("backup archive does not exist")
    if target.exists() and not target.is_dir():
        raise RestoreError("restore destination is not a directory")

    with zipfile.ZipFile(source) as archive:
        members = _restore_members(archive)
        _read_manifest(archive)
        restore_plan = [
            (_restore_target(target, name), name)
            for name in members
        ]
        conflicts = [
            path for path, _ in restore_plan if path.exists() and not allow_overwrite
        ]
        if conflicts:
            raise RestoreError("restore destination contains existing files")
        if not apply:
            return RestoreResult(
                archive_path=source,
                destination=target,
                files=len(restore_plan),
                dry_run=True,
                conflicts=len(conflicts),
                overwrite_required=bool(conflicts),
                manifest_status="valid",
            )
        for path, name in restore_plan:
            path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(name) as source_file:
                path.write_bytes(source_file.read())

    return RestoreResult(
        archive_path=source,
        destination=target,
        files=len(restore_plan),
        dry_run=False,
        conflicts=0,
        overwrite_required=False,
        manifest_status="valid",
    )


def _default_backup_path(config: MayaConfig) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    instance_id = config.product.instance_id.replace("/", "-")
    return config.deployment.data_dir / "backups" / f"{instance_id}-{stamp}.zip"


def _iter_backup_files(data_dir: Path):
    backups_dir = (data_dir / "backups").resolve()
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if resolved == backups_dir or backups_dir in resolved.parents:
            continue
        if _excluded_from_default_backup(data_dir, resolved):
            continue
        if _is_memory_database_sidecar(data_dir, resolved):
            continue
        yield resolved


def _archive_name(data_dir: Path, path: Path) -> str:
    return "maya-data/" + path.relative_to(data_dir.resolve()).as_posix()


def _is_memory_database(data_dir: Path, path: Path) -> bool:
    return path == (data_dir.resolve() / "memory" / "memory.sqlite3")


def _is_memory_database_sidecar(data_dir: Path, path: Path) -> bool:
    database = data_dir.resolve() / "memory" / "memory.sqlite3"
    return path in {
        database.with_name(database.name + "-wal"),
        database.with_name(database.name + "-shm"),
    }


def _snapshot_sqlite_database(source: Path, destination: Path) -> None:
    """Create a transaction-consistent SQLite snapshot, including WAL state."""

    source_connection = sqlite3.connect(source, timeout=30.0)
    destination_connection = sqlite3.connect(destination)
    try:
        source_connection.backup(destination_connection)
        integrity = destination_connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]
        if integrity != "ok":
            raise BackupError("memory database snapshot failed integrity check")
    finally:
        destination_connection.close()
        source_connection.close()


def _excluded_from_default_backup(data_dir: Path, path: Path) -> bool:
    relative_parts = path.relative_to(data_dir.resolve()).parts
    excluded_prefixes = (
        ("analytics", "sources"),
        ("metabase", "application"),
    )
    return any(relative_parts[: len(prefix)] == prefix for prefix in excluded_prefixes)


def _restore_members(archive: zipfile.ZipFile) -> list[str]:
    members: list[str] = []
    for info in archive.infolist():
        name = info.filename
        if info.is_dir():
            continue
        if name == "maya-config.json":
            members.append(name)
            continue
        if name == "maya-backup-manifest.json":
            continue
        if name.startswith("maya-data/"):
            _validate_relative_archive_name(name.removeprefix("maya-data/"))
            members.append(name)
            continue
        raise RestoreError("backup archive contains unsupported paths")
    if "maya-config.json" not in members:
        raise RestoreError("backup archive is missing maya-config.json")
    if "maya-backup-manifest.json" not in archive.namelist():
        raise RestoreError("backup archive is missing maya-backup-manifest.json")
    return members


def _restore_target(destination: Path, name: str) -> Path:
    if name == "maya-config.json":
        relative = Path("config") / "maya-config.json"
    elif name == "maya-backup-manifest.json":
        relative = Path("backup") / "maya-backup-manifest.json"
    else:
        relative = Path(name.removeprefix("maya-data/"))
    path = (destination / relative).resolve()
    root = destination.resolve()
    if path != root and root not in path.parents:
        raise RestoreError("backup archive path escapes destination")
    return path


def _validate_relative_archive_name(name: str) -> None:
    parts = Path(name).parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise RestoreError("backup archive contains unsafe paths")


def _build_manifest(
    config: MayaConfig,
    archived_files: list[Path],
    files: int,
) -> BackupManifest:
    roots = sorted(
        {
            f"maya-data/{path.relative_to(config.deployment.data_dir.resolve()).parts[0]}"
            for path in archived_files
            if path.relative_to(config.deployment.data_dir.resolve()).parts
        }
    )
    return BackupManifest(
        schema_version=1,
        created_at=datetime.now(timezone.utc).isoformat(),
        instance_id=config.product.instance_id,
        files=files,
        included_roots=("maya-config.json", *roots),
        excluded_roots=_excluded_roots(),
        package_version=None,
        runtime_version=config.runtime.hermes_runtime_version,
    )


def _read_manifest(archive: zipfile.ZipFile) -> BackupManifest:
    if "maya-backup-manifest.json" not in archive.namelist():
        raise RestoreError("backup archive is missing maya-backup-manifest.json")
    try:
        raw: Any = json.loads(
            archive.read("maya-backup-manifest.json").decode("utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise RestoreError("backup manifest is unreadable") from exc
    if not isinstance(raw, dict):
        raise RestoreError("backup manifest must be a JSON object")
    return BackupManifest(
        schema_version=int(raw.get("schema_version", 0)),
        created_at=str(raw.get("created_at", "")),
        instance_id=str(raw.get("instance_id", "")),
        files=int(raw.get("files", 0)),
        included_roots=tuple(str(item) for item in raw.get("included_roots", ())),
        excluded_roots=tuple(str(item) for item in raw.get("excluded_roots", ())),
        package_version=(
            str(raw["package_version"])
            if raw.get("package_version") is not None
            else None
        ),
        runtime_version=(
            str(raw["runtime_version"])
            if raw.get("runtime_version") is not None
            else None
        ),
    )


def _excluded_roots() -> tuple[str, ...]:
    return (
        "maya-data/backups",
        "maya-data/analytics/sources",
        "maya-data/metabase/application",
    )

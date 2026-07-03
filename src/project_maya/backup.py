"""Local backup helpers for Project MAYA."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import MayaConfig, config_to_mapping


class BackupError(RuntimeError):
    """Raised when a local backup cannot be created safely."""


class RestoreError(RuntimeError):
    """Raised when a local backup cannot be restored safely."""


@dataclass(frozen=True)
class BackupResult:
    archive_path: Path
    files: int


@dataclass(frozen=True)
class RestoreResult:
    archive_path: Path
    destination: Path
    files: int
    dry_run: bool


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
    temporary = archive_path.with_suffix(archive_path.suffix + ".tmp")
    try:
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
                archive.write(path, _archive_name(data_dir, path))
                files += 1
        temporary.replace(archive_path)
    except Exception as exc:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise BackupError("backup creation failed") from exc

    return BackupResult(archive_path=archive_path, files=files)


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
        yield resolved


def _archive_name(data_dir: Path, path: Path) -> str:
    return "maya-data/" + path.relative_to(data_dir.resolve()).as_posix()


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
        if name.startswith("maya-data/"):
            _validate_relative_archive_name(name.removeprefix("maya-data/"))
            members.append(name)
            continue
        raise RestoreError("backup archive contains unsupported paths")
    if "maya-config.json" not in members:
        raise RestoreError("backup archive is missing maya-config.json")
    return members


def _restore_target(destination: Path, name: str) -> Path:
    if name == "maya-config.json":
        relative = Path("config") / "maya-config.json"
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

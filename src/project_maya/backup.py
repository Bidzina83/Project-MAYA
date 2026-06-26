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


@dataclass(frozen=True)
class BackupResult:
    archive_path: Path
    files: int


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
        yield resolved


def _archive_name(data_dir: Path, path: Path) -> str:
    return "maya-data/" + path.relative_to(data_dir.resolve()).as_posix()

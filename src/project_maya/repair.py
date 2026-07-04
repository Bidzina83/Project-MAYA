"""Conservative local repair helpers for Project MAYA."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import MayaConfig


class RepairError(RuntimeError):
    """Raised when a local repair cannot be planned or applied safely."""


@dataclass(frozen=True)
class RepairAction:
    path: Path
    action: str
    status: str
    category: str = "filesystem"
    severity: str = "info"
    hint: str = "no action required"


@dataclass(frozen=True)
class RepairResult:
    dry_run: bool
    actions: tuple[RepairAction, ...]


REQUIRED_DIRECTORIES = (
    "memory",
    "memory/registry",
    "memory/vector",
    "memory/holographic",
    "memory/context",
    "governance",
    "governance/policies",
    "governance/audit",
    "tasks",
    "integrations",
    "integrations/google",
    "integrations/slack",
    "integrations/telegram",
    "analytics",
    "analytics/exports",
    "metabase",
    "metabase/provisioning",
    "documents",
    "documents/outputs",
    "documents/cache",
    "updates",
    "backups",
    "migrations",
    "logs",
    "cache",
)


def repair_local_state(config: MayaConfig, *, apply: bool = False) -> RepairResult:
    """Plan or create the minimal local state directories Maya expects."""
    config.validate()
    data_dir = config.deployment.data_dir
    planned: list[RepairAction] = []

    _ensure_repairable_root(data_dir)
    targets = (data_dir, *(data_dir / name for name in REQUIRED_DIRECTORIES))
    for target in targets:
        if target.exists():
            if not target.is_dir():
                raise RepairError(f"repair target exists but is not a directory: {target}")
            planned.append(
                RepairAction(
                    path=target,
                    action="none",
                    status="exists",
                    category=_repair_category(data_dir, target),
                    severity="info",
                    hint="directory already exists",
                )
            )
            continue
        planned.append(
            RepairAction(
                path=target,
                action="create_directory",
                status="planned" if not apply else "created",
                category=_repair_category(data_dir, target),
                severity="warn" if not apply else "info",
                hint=(
                    "run maya setup init --apply or maya repair --apply "
                    "to create this Maya-owned directory"
                    if not apply
                    else "created Maya-owned directory"
                ),
            )
        )
        if apply:
            target.mkdir(parents=True, exist_ok=True)

    return RepairResult(dry_run=not apply, actions=tuple(planned))


def _ensure_repairable_root(data_dir: Path) -> None:
    if data_dir.exists() and not data_dir.is_dir():
        raise RepairError("deployment.data_dir exists but is not a directory")
    parent = data_dir.parent
    if not parent.exists() or not parent.is_dir():
        raise RepairError("deployment.data_dir parent does not exist")


def _repair_category(data_dir: Path, target: Path) -> str:
    if target == data_dir:
        return "filesystem"
    try:
        first = target.relative_to(data_dir).parts[0]
    except (ValueError, IndexError):
        return "filesystem"
    return {
        "memory": "memory",
        "governance": "governance",
        "tasks": "tasks",
        "integrations": "connectors",
        "analytics": "analytics",
        "metabase": "metabase",
        "documents": "documents",
        "updates": "update",
        "backups": "backup",
        "migrations": "migration",
        "logs": "logs",
        "cache": "cache",
    }.get(first, "filesystem")

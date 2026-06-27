"""Local integration recovery helpers for Project MAYA."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .config import MayaConfig


class IntegrationResetError(RuntimeError):
    """Raised when an integration reset cannot be planned or applied safely."""


@dataclass(frozen=True)
class IntegrationResetResult:
    name: str
    dry_run: bool
    local_state_path: Path
    local_state_exists: bool
    files: int
    credential_ref_present: bool
    external_revocation_performed: bool = False


def reset_integration_state(
    config: MayaConfig,
    name: str,
    *,
    apply: bool = False,
) -> IntegrationResetResult:
    """Plan or remove local state for a configured integration."""
    config.validate()
    integration_name = _validate_integration_name(name)
    if integration_name not in config.integrations:
        raise IntegrationResetError("integration is not configured")

    state_path = _integration_state_path(config.deployment.data_dir, integration_name)
    integration = config.integrations[integration_name]
    if not state_path.exists():
        return IntegrationResetResult(
            name=integration_name,
            dry_run=not apply,
            local_state_path=state_path,
            local_state_exists=False,
            files=0,
            credential_ref_present=integration.credential_ref is not None,
        )
    if not state_path.is_dir():
        raise IntegrationResetError("integration state path is not a directory")

    files = sum(1 for path in state_path.rglob("*") if path.is_file())
    if apply:
        shutil.rmtree(state_path)
    return IntegrationResetResult(
        name=integration_name,
        dry_run=not apply,
        local_state_path=state_path,
        local_state_exists=not apply,
        files=files,
        credential_ref_present=integration.credential_ref is not None,
    )


def _validate_integration_name(name: str) -> str:
    value = name.strip()
    if not value:
        raise IntegrationResetError("integration name is required")
    if any(separator in value for separator in ("/", "\\")) or value in {".", ".."}:
        raise IntegrationResetError("integration name must be a configured name")
    return value


def _integration_state_path(data_dir: Path, name: str) -> Path:
    root = (data_dir / "integrations").resolve()
    path = (root / name).resolve()
    if path != root and root in path.parents:
        return path
    raise IntegrationResetError("integration state path escapes data directory")

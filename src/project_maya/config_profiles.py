"""Portable configuration profile loading for Project MAYA."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .config import MayaConfig, config_from_mapping


class ConfigProfileError(ValueError):
    """Raised when a configuration profile cannot be materialized safely."""


SUPPORTED_PROFILE_PLACEHOLDERS = frozenset(
    {
        "${MAYA_DATA_DIR}",
        "${MAYA_INSTANCE_ID}",
    }
)


def load_config_profile(
    path: Path | str,
    *,
    data_dir: Path | str,
    instance_id: str | None = None,
) -> MayaConfig:
    """Load a documented config profile and resolve portable placeholders."""

    data_dir_path = Path(data_dir)
    if not data_dir_path.is_absolute():
        raise ConfigProfileError("data_dir must be absolute")
    replacements = {
        "${MAYA_DATA_DIR}": str(data_dir_path),
        "${MAYA_INSTANCE_ID}": instance_id or data_dir_path.name,
    }
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ConfigProfileError("configuration profile must be a JSON object")
    resolved = _resolve_placeholders(raw, replacements)
    return config_from_mapping(resolved)


def _resolve_placeholders(value: Any, replacements: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        unknown = [
            placeholder
            for placeholder in _find_placeholders(value)
            if placeholder not in SUPPORTED_PROFILE_PLACEHOLDERS
        ]
        if unknown:
            raise ConfigProfileError(
                "unsupported profile placeholder: " + ", ".join(sorted(unknown))
            )
        for placeholder, replacement in replacements.items():
            value = value.replace(placeholder, replacement)
        return value
    if isinstance(value, list):
        return [_resolve_placeholders(item, replacements) for item in value]
    if isinstance(value, dict):
        return {
            key: _resolve_placeholders(item, replacements)
            for key, item in value.items()
        }
    return value


def _find_placeholders(value: str) -> set[str]:
    placeholders: set[str] = set()
    start = 0
    while True:
        open_index = value.find("${", start)
        if open_index == -1:
            return placeholders
        close_index = value.find("}", open_index + 2)
        if close_index == -1:
            return placeholders
        placeholders.add(value[open_index : close_index + 1])
        start = close_index + 1

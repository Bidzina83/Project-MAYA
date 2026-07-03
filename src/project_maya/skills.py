"""Project MAYA skill artifact boundary contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath


class SkillContractError(ValueError):
    """Raised when a skill artifact violates the Maya packaging boundary."""


class SkillOrigin(str, Enum):
    """Approved origins for Maya skill artifacts."""

    HERMES_DEFAULT = "hermes_default"
    MAYA_TRAINED = "maya_trained"


_SKILL_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*(/[a-z0-9][a-z0-9_.-]*)*$")
_VERSION_PATTERN = re.compile(r"^[0-9]+(\.[0-9]+){0,2}([+-][a-z0-9_.-]+)?$")
_FORBIDDEN_TEXT_MARKERS = (
    "@gmail.com",
    "@googlemail.com",
    "oauth_token",
    "refresh_token",
    "client_secret",
    "bot_token",
    "api_key",
    "/opt/hermes",
    "/opt/data",
    "/home/",
    "/root/",
    "c:\\users\\",
)


@dataclass(frozen=True)
class MayaSkillArtifact:
    """Versioned skill artifact approved for later Maya/Hermes discovery."""

    skill_id: str
    origin: SkillOrigin
    version: str
    source_path: str
    capabilities: tuple[str, ...] = ()

    def validate(self) -> None:
        if not _SKILL_ID_PATTERN.fullmatch(self.skill_id):
            raise SkillContractError("skill_id must be a stable portable identifier")
        if not _VERSION_PATTERN.fullmatch(self.version):
            raise SkillContractError("version must be a stable artifact version")
        _validate_relative_source_path(self.source_path)
        if not self.capabilities:
            raise SkillContractError("capabilities must be explicitly declared")
        for capability in self.capabilities:
            if not _SKILL_ID_PATTERN.fullmatch(capability):
                raise SkillContractError(
                    f"capability must be a stable identifier: {capability}"
                )


DOCUMENT_SKILL_ALLOWLIST: tuple[MayaSkillArtifact, ...] = (
    MayaSkillArtifact(
        skill_id="documents/pdf",
        origin=SkillOrigin.MAYA_TRAINED,
        version="0.1.0",
        source_path="skills/pdf/SKILL.md",
        capabilities=(
            "documents.inspect",
            "documents.extract-text",
            "documents.create-pdf",
        ),
    ),
)


def document_skill_allowlist() -> tuple[MayaSkillArtifact, ...]:
    """Return approved document skill metadata without loading skill files."""

    validate_skill_artifacts(DOCUMENT_SKILL_ALLOWLIST)
    return DOCUMENT_SKILL_ALLOWLIST


def validate_skill_artifacts(artifacts: tuple[MayaSkillArtifact, ...]) -> None:
    """Validate a future product skill allowlist without loading the skills."""

    seen: set[str] = set()
    for artifact in artifacts:
        artifact.validate()
        if artifact.skill_id in seen:
            raise SkillContractError(f"duplicate skill_id: {artifact.skill_id}")
        seen.add(artifact.skill_id)


def validate_skill_text_is_sanitized(text: str) -> None:
    """Reject common personal, secret, and machine-specific markers in skills."""

    lower_text = text.lower()
    for marker in _FORBIDDEN_TEXT_MARKERS:
        if marker in lower_text:
            raise SkillContractError(
                "skill artifact contains personal, secret, or machine-specific data"
            )


def _validate_relative_source_path(source_path: str) -> None:
    normalized = source_path.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ":" in normalized:
        raise SkillContractError("source_path must be relative and portable")
    if ".." in path.parts:
        raise SkillContractError("source_path must not traverse directories")
    if not path.parts or path.name != "SKILL.md":
        raise SkillContractError("source_path must point to a SKILL.md artifact")

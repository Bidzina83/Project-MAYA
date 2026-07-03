# Phase 4 Document Skill Allowlist

## Status

Metadata-only allowlist for future document/PDF skill packaging.

## Decision

Project MAYA now declares an approved document skill allowlist through
`project_maya.skills`.

The initial allowlist contains one eligible trained skill artifact:

| Skill | Origin | Source path | Capabilities |
| --- | --- | --- | --- |
| `documents/pdf` | `maya_trained` | `skills/pdf/SKILL.md` | `documents.inspect`, `documents.extract-text`, `documents.create-pdf` |

This is product metadata only. It does not copy the skill from
`Bidzina83/Hermes-Agent-Maya-Skills`, bundle it in the wheel, load it through
Hermes, or report the skill as installed.

## Boundary

Future packaging of this skill must still verify:

- sanitized `SKILL.md` content;
- portable helper scripts;
- no personal accounts, raw credentials, absolute machine paths, or platform
  assumptions;
- governance-mediated calls into `project_maya.documents`;
- no direct connector, file, memory, or model bypass.

## Verification

The clean package verifier imports `document_skill_allowlist()` from the built
wheel and validates the metadata without requiring a local skills checkout.

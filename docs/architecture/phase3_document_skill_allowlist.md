# Phase 3 Document Skill Allowlist

## Status

Packaged trained document/PDF skill artifact.

## Decision

Project MAYA declares and packages an approved document skill artifact through
`project_maya.skills`.

The initial allowlist contains one eligible trained skill artifact:

| Skill | Origin | Source path | Capabilities |
| --- | --- | --- | --- |
| `documents/pdf` | `maya_trained` | `packaged_skills/pdf/SKILL.md` | `documents.inspect`, `documents.extract-text`, `documents.create-pdf`, `documents.convert` |

The curated artifact is packaged in the Project MAYA wheel and is tied to the
approved `Bidzina83/Hermes-Agent-Maya-Skills` trained-skill source role. Maya
reports it as packaged and discoverable. It is not reported as runtime-loaded
or healthy until the Hermes adapter verifies actual loading.

## Boundary

Packaging verifies:

- sanitized `SKILL.md` content;
- portable helper scripts;
- no personal accounts, raw credentials, absolute machine paths, or platform
  assumptions;
- governance-mediated calls into `project_maya.documents`;
- no direct connector, file, memory, or model bypass.

## Verification

The clean package verifier imports `document_skill_allowlist()` and
`packaged_document_skill_status()` from the built wheel, validates the bundled
artifact metadata, and verifies that skill status is discoverable without
requiring a local skills checkout.

# Phase 3 Documents and PDF Readiness

## Status

Documents/PDF readiness slice for Phase 3 Capability Dependency and Readiness
Foundation.

## Decision

Maya exposes document and PDF runtime requirements through the dependency
contract layer before document workflows are treated as product-complete.

The install package declares two optional extras:

- `project-maya[documents]` for Python packages required by the documents
  profile: `reportlab`, `pypdf`, `Markdown`, and `Pillow`.
- `project-maya[documents-preview]` for the same packages plus optional
  `PyMuPDF` preview support.

System commands and local applications remain readiness checks, not silent
install actions:

- Poppler `pdftoppm` is optional for PDF preview rendering.
- LibreOffice `soffice` is required when the `maya-documents` profile performs
  governed Office/document conversion.
- Microsoft Office is customer-managed and may be detected or validated by
  later setup flows, but Maya does not install it.

## Skill Boundary

This readiness slice defined the runtime dependency surface for trained Maya
document skills from `Hermes-Agent-Maya-Skills`. Final Phase 3 capability work
packages the approved `documents/pdf` skill artifact through
`project_maya.packaged_skills` and reports it as packaged, allowlisted, and
discoverable only after product validation.

Packaged skills must use these dependency contracts and must not hardcode
machine-specific paths, customer accounts, or operating-system assumptions.

## Verification

The clean package verifier checks that:

- the built wheel declares `documents` and `documents-preview` extras;
- the installed package imports dependency contracts from the wheel;
- installed `maya doctor` reports `maya-documents` dependency readiness from a
  non-editable install;
- missing Poppler, LibreOffice, Microsoft Office, Java, Metabase, browsers, or
  document extras are reported, not installed.

## Known Limits

This readiness slice does not install system dependencies or implement
installer-level dependency setup. Final Phase 3 document capability covers
governed extraction, PDF creation, LibreOffice conversion, and the packaged
approved trained document skill while preserving these readiness boundaries.

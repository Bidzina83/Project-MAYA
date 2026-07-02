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
- LibreOffice `soffice` is optional for Office document conversion.
- Microsoft Office is customer-managed and may be detected or validated by
  later setup flows, but Maya does not install it.

## Skill Boundary

This slice does not package trained Maya skills from
`Hermes-Agent-Maya-Skills`. It defines the runtime dependency surface those
skills can rely on when the `maya-documents` profile is enabled.

Skill inclusion remains a later product decision. Any skill packaged later must
use these dependency contracts and must not hardcode machine-specific paths,
customer accounts, or operating-system assumptions.

## Verification

The clean package verifier checks that:

- the built wheel declares `documents` and `documents-preview` extras;
- the installed package imports dependency contracts from the wheel;
- installed `maya doctor` reports `maya-documents` dependency readiness from a
  non-editable install;
- missing Poppler, LibreOffice, Microsoft Office, Java, Metabase, browsers, or
  document extras are reported, not installed.

## Known Limits

This slice does not implement PDF extraction, PDF rendering, document
conversion, trained skill packaging, or installer-level system dependency
installation.

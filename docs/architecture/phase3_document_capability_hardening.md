# Phase 3 Document Capability Hardening

## Status

Incremental hardening after the initial V2 Phase 3 document foundation.

## Decision

Document operations now use a stable output convention:

```text
maya-data/documents/outputs/
```

Bare output filenames passed to `create-pdf` or `extract-text --to` are
resolved into that directory. Explicit relative subpaths remain under
`maya-data/documents`, and absolute paths must already resolve inside that
document root.

## Hardened Behavior

- `maya documents extract-text` accepts `--to <file.txt>` and writes extracted
  text only after governance authorization succeeds.
- `maya documents create-pdf --output out.pdf` writes to
  `maya-data/documents/outputs/out.pdf`.
- Doctor reports:
  - `documents.documents-root`;
  - `documents.documents-cache`;
  - `documents.documents-outputs`;
  - `documents.pdf-extraction`;
  - `documents.pdf-creation`.
- Installed package verification checks the create/extract CLI surfaces from a
  clean no-dependency install and verifies failures are secret-safe.
- Unit tests cover real PDF create/extract round-trip when `reportlab` and
  `pypdf` are available in the test environment.

## Boundaries

This hardening step still does not:

- require document extras in the default core wheel verifier;
- install system packages;
- automate LibreOffice or Microsoft Office;
- package trained document skills;
- read arbitrary customer directories.

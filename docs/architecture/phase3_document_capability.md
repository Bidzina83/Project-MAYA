# Phase 3 Document Capability

## Status

Final V2 Phase 3 governed document capability.

## Decision

Project MAYA now owns a `project_maya.documents` capability layer for local
document operations. This layer is product code, not a trained skill bundle,
and it is the boundary future document skills should call through.

- inspect document metadata;
- extract PDF text with `pypdf` when available;
- optionally write extracted PDF text to a governed `.txt` output;
- create PDF output from plain text or Markdown with document extras when
  available;
- convert supported local documents through LibreOffice when `soffice` is
  available;
- report dependency-unavailable states honestly.

## Governance Boundary

Every document operation creates an authorization request with:

- actor;
- capability such as `documents.inspect`, `documents.extract-text`,
  `documents.create-pdf`, or `documents.convert`;
- redacted source and output references;
- data classification;
- file type;
- mutation flag.

Audit records include these redacted fields but not document contents, raw
extracted text, prompts, secrets, or full local filesystem paths.

## Path Boundary

V2 Phase 3 document operations read and write only under:

```text
maya-data/documents/
```

This keeps the first product surface deterministic and backup-safe. Future
customer-approved document roots require an explicit configuration contract and
governance policy.

Bare output filenames are written under:

```text
maya-data/documents/outputs/
```

`maya doctor` reports the document root, cache directory, output directory,
PDF extraction dependency readiness, PDF creation dependency readiness, and
LibreOffice conversion readiness as separate checks.

## Local API

V2 Phase 3 exposes document operations through the CLI and product module first.
Local API routes are deferred until the route versioning, request-size limits,
and browser/client authorization shape for document uploads and downloads are
specified.

## Deferred Work

- Poppler or PyMuPDF preview rendering;
- Microsoft Office conversion automation;
- arbitrary customer document roots;
- document indexing into persistent memory.

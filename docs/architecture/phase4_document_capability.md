# Phase 4 Document Capability

## Status

Initial governed document capability foundation.

## Decision

Project MAYA now owns a `project_maya.documents` capability layer for local
document operations. This layer is product code, not a trained skill bundle,
and it is the boundary future document skills should call through.

Initial operations are intentionally narrow:

- inspect document metadata;
- extract PDF text with `pypdf` when available;
- create PDF output from plain text or Markdown with document extras when
  available;
- report dependency-unavailable states honestly.

## Governance Boundary

Every document operation creates an authorization request with:

- actor;
- capability such as `documents.inspect`, `documents.extract-text`, or
  `documents.create-pdf`;
- redacted source and output references;
- data classification;
- file type;
- mutation flag.

Audit records include these redacted fields but not document contents, raw
extracted text, prompts, secrets, or full local filesystem paths.

## Path Boundary

Phase 4 document operations read and write only under:

```text
maya-data/documents/
```

This keeps the first product surface deterministic and backup-safe. Future
customer-approved document roots require an explicit configuration contract and
governance policy.

## Local API

Phase 4 exposes document operations through the CLI and product module first.
Local API routes are deferred until the route versioning, request-size limits,
and browser/client authorization shape for document uploads and downloads are
specified.

## Deferred Work

- Poppler or PyMuPDF preview rendering;
- LibreOffice and Microsoft Office conversion automation;
- trained PDF/document skill packaging;
- arbitrary customer document roots;
- document indexing into persistent memory.

# Phase 3 Scope: Metabase and Document Capability Integration

## Status

Approved implementation scope for Product Spec V2 Phase 3.

## Objective

Product Spec V2 Phase 3 turns prior readiness checks into first usable capability surfaces
for `maya-documents` and `maya-metabase`.

Maya must be able to run safe local document workflows and Metabase
integration/provisioning flows from the installed package, through governance,
with audit records and without exposing memory, secrets, prompts, raw files, or
unapproved records.

## Accepted Capabilities

- Governed local document operations:
  - inspect redacted metadata;
  - extract text from local PDFs when `pypdf` is installed;
  - create PDFs from plain text or Markdown when required document packages are
    installed;
  - validate paths under `maya-data/documents`;
  - emit audit records without document contents or full local paths.
- Metabase integration contracts:
  - secret-safe health validation;
  - customer-managed and managed-local lifecycle mode reporting;
  - redacted provisioning plans for approved analytics sources;
  - explicit apply authorization for provisioning.
- Doctor and installed package checks for the implemented capability surfaces.

## Safety Boundaries

- Local governance authorizes every document mutation, document read, and
  Metabase provisioning apply action.
- Document operations may not read or write outside `maya-data/documents` in
  this phase.
- Metabase provisioning may not expose Maya persistent memory, prompts,
  secrets, raw files, or customer records by default.
- Metabase application database, analytics data sources, and Maya persistent
  memory remain separate stores.
- Live Metabase HTTP checks are deferred unless separately approved and bounded
  by timeout, redaction, and opt-in policy.

## Non-Goals

V2 Phase 3 does not:

- silently install Poppler, LibreOffice, Microsoft Office, Java, Metabase,
  browsers, or local model runtimes;
- bulk-package trained Maya skills;
- automate Microsoft Office or LibreOffice conversion;
- perform live Metabase dashboard creation by default;
- bundle a production Metabase runtime artifact;
- implement signed production installers or update channels;
- claim platform support beyond tested artifact surfaces.

## Exit Criteria

V2 Phase 3 exits when:

- document and Metabase capability modules ship in the wheel;
- CLI surfaces can run installed-package smoke checks without repository path
  shims;
- doctor reports implemented V2 Phase 3 capability checks;
- audit records are redacted and governance-mediated;
- closure evidence maps scope, tests, docs, package verification, and known
  limits.

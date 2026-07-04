# Phase 5 Scope: Setup, Recovery, Backup, and Health Experience

## Status

Approved implementation scope for Phase 5.

## Objective

Phase 5 turns existing Maya lifecycle primitives into an operator-friendly
experience for setup, recovery, backup, restore, update readiness, and health
inspection.

The phase is Windows-first for installed-package smoke testing while keeping
contracts portable.

## Accepted Capabilities

- Setup planning and initialization through `maya setup plan` and
  `maya setup init`.
- Operator health summary through `maya health summary`.
- Repair output with categories, severity, and suggested next commands.
- Backup archives with a redacted manifest and `maya backup inspect`.
- Local update and rollback readiness diagnostics with no network use and no
  mutation.
- Installed-package smoke coverage for the Phase 5 CLI surfaces.

## Safety Boundaries

- Setup and repair remain dry-run by default.
- Mutating setup creates only Maya-owned directories already covered by repair
  contracts.
- Maya does not create credentials, contact providers, install dependencies,
  generate production secrets, or configure OAuth in this phase.
- Backup and health output must not print secret values, prompt contents,
  document contents, or customer records.
- Restore remains dry-run by default and still requires explicit overwrite
  consent.

## Non-Goals

Phase 5 does not:

- create a production installer;
- create signed update artifacts;
- perform automatic updates or rollback;
- implement broker setup or OAuth flows;
- silently install Poppler, LibreOffice, Microsoft Office, Java, Metabase,
  browsers, local model runtimes, or connector applications;
- claim full Windows, macOS, Linux, server, or container support.

## Exit Criteria

Phase 5 exits when:

- setup and health modules ship in the wheel;
- installed CLI smoke checks cover setup, health, backup inspect, restore
  dry-run, and update readiness;
- backup manifest inspection is secret-safe;
- recovery docs cover common operator paths;
- closure evidence maps accepted capabilities to tests, docs, package
  verification, and known limits.

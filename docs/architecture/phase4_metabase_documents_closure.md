# Phase 4 Closure Audit

Phase 4 is implementation-complete for the first Metabase and Document
Capability Integration checkpoint.

## Objective

```text
Maya can run safe document workflows and Metabase integration/provisioning
flows from the installed package, through governance, with audit records and
without exposing memory, secrets, prompts, or unapproved records.
```

## Evidence

| Step | Evidence |
| --- | --- |
| Scope gate | `docs/architecture/phase4_metabase_documents_scope.md` |
| Document capability core | `src/project_maya/documents.py`, `tests/test_phase4_documents.py` |
| Document governance and audit | `src/project_maya/documents.py`, `tests/test_phase4_documents.py` |
| Document CLI surface | `src/project_maya/cli.py`, `scripts/verify_phase1_package.py` |
| Skill inclusion boundary | `docs/architecture/phase4_document_capability.md` |
| Metabase integration contract | `src/project_maya/metabase.py`, `tests/test_phase4_metabase.py` |
| Metabase health | `src/project_maya/metabase.py`, `tests/test_phase4_metabase.py` |
| Metabase provisioning foundation | `src/project_maya/metabase.py`, `src/project_maya/cli.py`, `tests/test_phase4_metabase.py` |
| Doctor and package verification | `src/project_maya/doctor.py`, `scripts/verify_phase1_package.py` |
| Documentation | `docs/architecture/phase4_document_capability.md`, `docs/architecture/phase4_metabase_capability.md`, `docs/examples/phase4_documents_metabase_operator_smoke.md` |

## Completed Surfaces

- `project_maya.documents` provides governed document inspect, PDF text
  extraction, PDF creation, redacted summaries, and path validation under
  `maya-data/documents`.
- `project_maya.metabase` provides secret-safe health validation,
  customer-managed and managed-local mode reporting, redacted provisioning
  plans, and governed apply recording.
- `maya documents` and `maya metabase` CLI groups expose the implemented
  surfaces.
- `maya doctor` reports Phase 4 document and Metabase capability checks.
- Clean package verification imports the installed capability modules and runs
  installed CLI smoke checks without repository path shims.

## Known Limits

Phase 4 intentionally does not:

- silently install document or Metabase dependencies;
- package trained Maya skills;
- automate LibreOffice or Microsoft Office;
- render previews with Poppler or PyMuPDF;
- perform live Metabase HTTP checks;
- create live Metabase dashboards, users, collections, or permissions;
- bundle a production Metabase runtime;
- claim OS/platform installer support.

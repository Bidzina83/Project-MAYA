# Phase 3 Closure Audit

Product Spec V2 Phase 3 is complete for the approved Metabase and Document Capability
Integration scope.

## Objective

```text
Maya can run safe document workflows and Metabase integration/provisioning
flows from the installed package, through governance, with audit records and
without exposing memory, secrets, prompts, or unapproved records.
```

## Approved Step Evidence

| Step | Evidence |
| --- | --- |
| 1. Phase 3 scope gate | `docs/architecture/phase3_metabase_documents_scope.md` |
| 2. Document capability core | `src/project_maya/documents.py`, `tests/test_phase3_documents.py`, `docs/architecture/phase3_document_capability.md`, `docs/architecture/phase3_document_capability_hardening.md` |
| 3. Document governance and audit | `src/project_maya/documents.py`, `tests/test_phase3_documents.py` |
| 4. Document CLI/API surface | `src/project_maya/cli.py`, `scripts/verify_phase1_package.py`, `docs/architecture/phase3_document_capability.md` |
| 5. Skill inclusion boundary for documents | `docs/architecture/phase3_document_skill_allowlist.md`, `src/project_maya/skills.py`, `tests/test_hermes_skills_boundary.py` |
| 6. Metabase integration contract | `src/project_maya/metabase.py`, `tests/test_phase3_metabase.py`, `docs/architecture/phase3_metabase_capability.md` |
| 7. Metabase client and health | `src/project_maya/metabase.py`, `tests/test_phase3_metabase.py`, `docs/architecture/phase3_metabase_capability_hardening.md` |
| 8. Metabase provisioning foundation | `src/project_maya/metabase.py`, `src/project_maya/cli.py`, `tests/test_phase3_metabase.py` |
| 9. Metabase CLI surface | `src/project_maya/cli.py`, `scripts/verify_phase1_package.py`, `docs/examples/phase3_documents_metabase_operator_smoke.md` |
| 10. Doctor, repair, backup, and package verification | `src/project_maya/doctor.py`, `src/project_maya/backup.py`, `tests/test_phase3_backup_boundaries.py`, `scripts/verify_phase1_package.py`, `docs/architecture/phase3_backup_boundary.md` |
| 11. Documentation and closure | `docs/architecture/phase3_metabase_documents_closure.md`, `tests/test_phase3_metabase_documents_closure.py`, `docs/examples/phase3_documents_metabase_operator_smoke.md` |

## Completed Surfaces

- `project_maya.documents` provides governed document inspect, PDF text
  extraction, extraction-to-file, PDF creation, redacted summaries, stable
  outputs under `maya-data/documents/outputs`, and path validation under
  `maya-data/documents`.
- `project_maya.skills` declares a metadata-only allowlist for the future
  trained `documents/pdf` skill without bundling or loading it.
- `project_maya.metabase` provides secret-safe health validation,
  customer-managed and managed-local lifecycle reporting, redacted persisted
  provisioning plans, and governed apply recording.
- Local backup includes Maya document outputs/caches and Metabase provisioning
  metadata while excluding customer analytics sources and Metabase application
  database state by default.
- `maya documents` and `maya metabase` CLI groups expose the implemented
  surfaces.
- Local API document and Metabase routes are deferred by design. The CLI and
  product modules are the V2 Phase 3 supported surfaces until route versioning,
  request-size limits, upload/download handling, and client authorization are
  specified.
- `maya doctor` reports V2 Phase 3 document and Metabase capability checks.
- Clean package verification imports the installed capability modules and runs
  installed CLI smoke checks without repository path shims.

## Known Limits

V2 Phase 3 intentionally does not:

- silently install document or Metabase dependencies;
- package trained Maya skills;
- automate LibreOffice or Microsoft Office;
- render previews with Poppler or PyMuPDF;
- perform live Metabase HTTP checks;
- create live Metabase dashboards, users, collections, or permissions;
- bundle a production Metabase runtime;
- silently back up customer analytics databases or Metabase application
  databases;
- expose document upload/download or Metabase provisioning through the local
  API;
- claim OS/platform installer support.

# Phase 3 Closure Audit

Phase 3 is implementation-complete for the Capability Dependency and Readiness
Foundation checkpoint.

Phase name: Capability Dependency and Readiness Foundation.

The Phase 3 objective was:

```text
Maya can declare, evaluate, and safely report dependency readiness for every
component profile without silently installing software or claiming incomplete
capabilities.
```

This closure audit supersedes the interim Phase 3 closure checkpoint. It maps
the approved Phase 3 plan to implemented code, documentation, package
verification, and tests.

## Approved Step Evidence

| Step | Evidence |
| --- | --- |
| 1. Scope gate and contract document | `docs/architecture/phase3_dependency_readiness_scope.md`, `docs/architecture/phase3_dependency_contracts.md`, `tests/test_phase3_package_verification.py` |
| 2. Dependency contract module | `src/project_maya/dependencies.py`, `src/project_maya/__init__.py`, `tests/test_phase3_dependency_readiness.py` |
| 3. Doctor readiness integration | `src/project_maya/doctor.py`, `tests/test_phase3_dependency_readiness.py` |
| 4. Install hints | `src/project_maya/dependencies.py`, `docs/architecture/phase3_dependency_contracts.md`, `tests/test_phase3_dependency_readiness.py` |
| 5. Package verification and docs | `scripts/verify_phase1_package.py`, `tests/test_phase3_package_verification.py`, `docs/architecture/phase3_dependency_contracts.md` |
| 6. Documents/PDF readiness | `setup.py`, `src/project_maya/dependencies.py`, `docs/architecture/phase3_documents_pdf_readiness.md`, `tests/test_phase3_dependency_readiness.py`, `tests/test_phase3_package_verification.py` |
| 7. Metabase readiness | `src/project_maya/dependencies.py`, `docs/architecture/phase3_metabase_readiness.md`, `tests/test_phase3_dependency_readiness.py` |
| 8. Browser readiness | `src/project_maya/dependencies.py`, `docs/architecture/phase3_browser_readiness.md`, `tests/test_phase3_dependency_readiness.py` |
| 9. Local model readiness | `src/project_maya/dependencies.py`, `docs/architecture/phase3_local_model_readiness.md`, `tests/test_phase3_dependency_readiness.py`, `tests/test_phase2_local_model_endpoint_readiness.py` |
| 10. Messaging readiness | `src/project_maya/dependencies.py`, `docs/architecture/phase3_messaging_readiness.md`, `tests/test_phase3_dependency_readiness.py`, `tests/test_phase2_connector_validation.py`, `tests/test_phase2_connector_contracts.py` |
| 11. Closure audit | `docs/architecture/phase3_dependency_readiness_closure.md`, `tests/test_phase3_closure.py` |

## Acceptance Evidence

| Acceptance criterion | Evidence |
| --- | --- |
| Dependency contracts are typed, deterministic, and importable from the installed package | `src/project_maya/dependencies.py`, `src/project_maya/__init__.py`, `scripts/verify_phase1_package.py`, `tests/test_phase3_dependency_readiness.py`, `tests/test_phase3_package_verification.py` |
| Contracts distinguish Python packages, system commands, local applications, service runtimes, external services, model endpoints, and customer-managed dependencies | `src/project_maya/dependencies.py`, `docs/architecture/phase3_dependency_readiness_scope.md`, `tests/test_phase3_dependency_readiness.py` |
| `maya doctor` reports readiness for enabled profiles without leaking secrets or raw credential references | `src/project_maya/doctor.py`, `scripts/verify_phase1_package.py`, `tests/test_phase3_dependency_readiness.py`, `tests/test_phase3_package_verification.py` |
| Missing optional dependencies warn rather than failing core runtime | `src/project_maya/dependencies.py`, `src/project_maya/doctor.py`, `tests/test_phase3_dependency_readiness.py` |
| Missing required dependencies fail only when the enabled profile cannot operate without them | `src/project_maya/dependencies.py`, `src/project_maya/doctor.py`, `tests/test_phase3_dependency_readiness.py` |
| Disabled profiles and disabled connectors do not fail doctor | `src/project_maya/dependencies.py`, `tests/test_phase3_dependency_readiness.py` |
| Install hints are OS-specific and informational only | `src/project_maya/dependencies.py`, `docs/architecture/phase3_dependency_contracts.md`, `tests/test_phase3_dependency_readiness.py` |
| Clean package verification proves dependency metadata ships in the wheel and installed `maya doctor` reports profile readiness | `scripts/verify_phase1_package.py`, `tests/test_phase3_package_verification.py`, `docs/architecture/phase3_dependency_contracts.md` |

## Completed Phase 3 Surfaces

- `project_maya.dependencies` exposes typed dependency contracts and readiness
  reports for all component profiles.
- `maya doctor` reports stable dependency checks for enabled profiles:
  `maya-core`, `maya-documents`, `maya-metabase`, `maya-browser`,
  `maya-messaging`, and `maya-local-models`.
- Document/PDF readiness covers `reportlab`, `pypdf`, `Markdown`, `Pillow`,
  optional `PyMuPDF`, optional Poppler `pdftoppm`, required LibreOffice
  `soffice` for governed conversion, and customer-managed Microsoft Office.
- Package metadata declares `project-maya[documents]` and
  `project-maya[documents-preview]` extras without making document tooling a
  hidden core dependency.
- Metabase readiness distinguishes Java runtime, Metabase service
  configuration, Metabase application database, and approved analytics
  sources while preserving the separation from Maya persistent memory.
- Browser readiness distinguishes supported browser executable,
  customer-managed automation driver/runtime, and governance policy readiness
  without launching or installing browsers.
- Local model readiness distinguishes OpenAI-compatible endpoint
  configuration, runtime family, and customer-managed model artifact state
  without endpoint probing or inference.
- Messaging readiness uses existing Phase 2 connector validators and reports
  Google, Slack, and Telegram service, contract, and governance/allowlist
  readiness without provider network calls.
- Clean installed-package verification builds a wheel, installs it in a
  temporary environment, and verifies dependency metadata plus installed
  `maya doctor` readiness for documents, Metabase, browser, local models, and
  messaging profiles.

## Readiness Check Families

| Profile | Representative checks |
| --- | --- |
| `maya-core` | `dependencies.python.project_maya` |
| `maya-documents` | `dependencies.python.reportlab`, `dependencies.python.pypdf`, `dependencies.python.markdown`, `dependencies.python.pillow`, `dependencies.command.pdftoppm`, `dependencies.command.soffice`, `dependencies.application.ms-office` |
| `maya-metabase` | `dependencies.runtime.java`, `dependencies.service.metabase`, `dependencies.database.metabase-application`, `dependencies.database.metabase-analytics-sources` |
| `maya-browser` | `dependencies.browser.executable`, `dependencies.browser.automation-driver`, `dependencies.browser.governance-policy` |
| `maya-local-models` | `dependencies.endpoint.local-model`, `dependencies.runtime.local-model-family`, `dependencies.model.local-model-artifact` |
| `maya-messaging` | `dependencies.service.google`, `dependencies.connector.google-contract`, `dependencies.connector.google-governance`, `dependencies.service.slack`, `dependencies.connector.slack-contract`, `dependencies.connector.slack-governance`, `dependencies.service.telegram`, `dependencies.connector.telegram-contract`, `dependencies.connector.telegram-governance` |

## Verification Commands

The closure evidence is covered by:

```text
python -m unittest tests.test_phase3_dependency_readiness tests.test_phase3_package_verification tests.test_phase3_closure -v
python -m unittest tests.test_phase2_connector_validation tests.test_phase2_connector_contracts tests.test_phase2_local_model_endpoint_readiness -v
python -m py_compile src/project_maya/dependencies.py scripts/verify_phase1_package.py
python scripts/verify_phase1_package.py
python scripts/validate_project_maya_context.py
git diff --check
```

## Readiness Foundation Limits

This readiness-foundation checkpoint intentionally did not implement:

- automatic installation of Poppler, Java, LibreOffice, browsers, Metabase,
  Docker, Ollama, LM Studio, vLLM, Microsoft Office, browser drivers, or
  system packages;
- browser launch, browser automation workflows, or browser profile/session
  inspection;
- local model runtime installation, model pulls, endpoint probing, or live
  inference;
- live Google, Slack, or Telegram OAuth/token validation, webhook verification,
  provider events, message send/receive, or provider revocation;
- production broker-assisted Standard OAuth;
- signed installers, SBOMs, release provenance, or automatic updates;
- platform support claims for Windows, macOS, Linux, servers, or containers.

Final V2 Phase 3 capability work supersedes this foundation-only boundary for
governed document extraction, PDF creation, LibreOffice conversion, packaged
approved trained document skill discovery, bounded Metabase live health, and
governed Metabase view/card/dashboard provisioning. It still does not silently
install dependencies, expose memory or secrets, claim platform support, or
perform production installer/update work.

## Exit Statement

Phase 3 exits with a cross-profile dependency/readiness foundation in place.
Maya can now explain what each enabled capability profile needs, what is
available, missing, optional, customer-managed, disabled, unsupported, or
unknown, and can do so from a clean installed package without leaking secrets
or silently installing software.

Final V2 Phase 3 builds real Metabase and document capability workflows on top
of these readiness contracts while preserving the same boundaries: explicit
dependencies, local governance, customer control, secret-safe diagnostics,
package verification, and no false support claims.

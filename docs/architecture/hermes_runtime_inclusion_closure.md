# Hermes Runtime Inclusion Closure Audit

## Status

Step 11 of the approved Hermes Runtime Inclusion phase.

## Closure Decision

The Hermes Runtime Inclusion phase is complete for its approved scope.

Project MAYA now installs from a clean package artifact with the selected
Hermes runtime declared as a pinned dependency, verifies installed Hermes
availability without path shims, adapts the selected `run_agent:AIAgent`
surface through `HermesRuntimeAdapter`, wires Maya-governed memory into the
Hermes memory-provider lifecycle, and records a Windows installed-package
smoke result.

This closure does not claim full product completion. It closes the practical
runtime-inclusion gap before the next Product Specification V2 work continues.

## Step Evidence Map

| Step | Evidence | Result |
| --- | --- | --- |
| 1. Scope Gate | `docs/architecture/hermes_runtime_inclusion_scope.md` | Acceptance criteria and non-goals recorded. |
| 2. Hermes Source Strategy | `docs/architecture/hermes_source_strategy.md` | `Bidzina83/hermes-agent` selected as integration source; upstream and trained-skills roles documented. |
| 3. Runtime Contract Inventory | `docs/architecture/hermes_runtime_contract_inventory.md` | Selected Hermes `run_agent:AIAgent`, memory, skills, plugin, packaging, and Python contracts inventoried. |
| 4. Adapter Contract Update | `src/project_maya/adapters/hermes.py`, `docs/architecture/hermes_adapter_contract_update.md` | Maya adapter binds to real Hermes factory and normalizes `AIAgent` lifecycle without creating a fake runtime. |
| 5. Package Inclusion | `setup.py`, `scripts/verify_phase1_package.py`, `docs/architecture/hermes_package_inclusion.md` | Maya declares pinned Hermes Git dependency and Python `>=3.11,<3.14`. |
| 6. Skills Inclusion Boundary | `src/project_maya/skills.py`, `docs/architecture/hermes_skills_inclusion_boundary.md` | Skill artifact contract, origin allowlist, and sanitization boundary defined. |
| 7. Memory Hook Wiring | `src/project_maya/adapters/hermes.py`, `docs/architecture/hermes_memory_hook_wiring.md` | Maya `HermesMemoryProvider` is exposed as Hermes provider `maya` with governed tools. |
| 8. Governed Execution Smoke Path | `tests/test_hermes_governed_execution_smoke.py`, `docs/architecture/hermes_governed_execution_smoke.md` | Product and CLI smoke paths reach Hermes adapter through governed runtime and audit boundaries. |
| 9. Installed Package Verification | `scripts/verify_phase1_package.py`, `docs/architecture/hermes_installed_package_verification.md` | Verifier installs clean wheel, resolves pinned Hermes, checks installed metadata and adapter compatibility. |
| 10. Windows Manual Smoke Test | `docs/architecture/hermes_windows_manual_smoke.md` | Windows smoke finding recorded; hardened verifier passed with real Hermes dependency. |

## Acceptance Criteria Audit

| Criterion | Status | Evidence |
| --- | --- | --- |
| Clean installed Maya resolves compatible Hermes without `PYTHONPATH`, repository-relative imports, `/opt/hermes`, or local checkout assumptions. | Met | `scripts/verify_phase1_package.py --with-hermes-runtime`; `docs/architecture/hermes_installed_package_verification.md`; `docs/architecture/hermes_windows_manual_smoke.md`. |
| `maya doctor` no longer reports `Hermes runtime factory unavailable` for the supported packaged configuration. | Met at compatibility boundary | Installed verifier imports `run_agent:AIAgent` and `HermesRuntimeAdapter().compatibility()` reports compatible. Full interactive doctor UX remains a later setup/health experience. |
| `maya doctor` reports Hermes runtime health as healthy or intentionally degraded with redacted reasons, not missing. | Partially met | Adapter health reports compatibility and startup state without secrets. End-to-end doctor health in a fully configured Hermes home remains later setup/health work. |
| `maya run --config ... --input ...` executes through public `Agent`, `GovernedAgentRuntime`, `HermesRuntimeAdapter`, and Hermes-shaped runtime. | Met by governed smoke | `tests/test_hermes_governed_execution_smoke.py`; `docs/architecture/hermes_governed_execution_smoke.md`. |
| Runtime execution produces local authorization and audit records before model inference, connector call, tool use, workflow execution, or memory write. | Met for runtime/model-egress smoke path | Governed execution smoke tests assert runtime and model-egress authorization records and secret-safe audit output. |
| Customer-owned model and connector credential references remain `secret://...` references and are never logged or packaged as raw values. | Met for this phase | Existing Phase 1/2 secret-safe CLI tests plus Hermes smoke audit tests; package verifier rejects non-product leaks. |
| Maya `HermesMemoryProvider` participates in real Hermes lifecycle without duplicate authoritative memory store. | Met at adapter boundary | `HermesMemoryProviderBridge` registers one provider named `maya`; memory docs state Maya remains authoritative. |
| Approved Maya skills are discoverable as versioned product artifacts and exclude operator-specific account details or machine-specific paths. | Contract met; packaging deferred | `src/project_maya/skills.py`; `docs/architecture/hermes_skills_inclusion_boundary.md`. Actual skill packaging/loading remains later work. |
| Broker-disabled Enterprise configuration remains valid and runnable without Maya cloud services. | Preserved | Phase 2 broker-disabled runtime tests remain part of package verifier coverage. |
| Clean package verification covers Hermes availability and controlled governed execution smoke path. | Met | `scripts/verify_phase1_package.py`, `tests/test_hermes_governed_execution_smoke.py`, and runtime inclusion scope tests. |

## Verification Commands

The following commands were used during this phase:

```text
python -m unittest tests.test_hermes_runtime_inclusion_scope -v
python -m unittest tests.test_hermes_governed_execution_smoke -v
python scripts/validate_project_maya_context.py
python scripts/verify_phase1_package.py
python scripts/verify_phase1_package.py --with-hermes-runtime
```

On Windows, the Hermes runtime verifier is intentionally quiet on success. A
zero exit code is the acceptance signal.

## Known Limits

This closure does not claim:

- live model inference with real provider credentials;
- production connector OAuth or webhook execution;
- packaged trained Maya skills;
- Metabase runtime packaging or dashboard provisioning;
- signed production installers, SBOMs, provenance, update, or rollback;
- full Windows, macOS, Linux, server, or container support;
- production-grade Hermes home migration or setup UX;
- final broker protocol, Standard OAuth, or Maya-managed model billing.

## Next Phase Direction

Return to the Product Specification V2 implementation sequence after this
runtime-completion phase. The practical next product work should continue with
Metabase and document capabilities, setup/recovery/backup/health experience,
and later broker protocol and production installers, while preserving the
Hermes adapter, governance, memory, and packaging boundaries closed here.

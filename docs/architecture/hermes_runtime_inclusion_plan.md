# Hermes Runtime Inclusion Plan

## Status

Approved corrective runtime-completion phase.

This phase begins after Phase 2. It closes the practical gap exposed by
installed-package smoke testing: Maya installs, validates Enterprise BYO
configuration, and assembles the governed local product, but the clean
installed package does not yet include or resolve a compatible Hermes runtime.

This phase is intentionally narrow. It does not replace the Product
Specification V2 implementation sequence. It completes the concrete Hermes
runtime requirement before downstream Metabase, document, setup, broker, and
installer work is treated as product-complete.

## Objective

Maya installs from a clean artifact and executes through a real compatible
Hermes runtime while preserving local governance, customer control, secret
references, audit, and broker-disabled operation.

## Approved Step Order

Work this phase in the following order unless the operator approves a change.

1. **Scope Gate**

   Define what "Hermes included" means for this phase, including acceptance
   criteria, known non-goals, and the expected installed-package behavior.

2. **Hermes Source Strategy**

   Decide how Hermes enters the Maya product. The preferred direction is to
   use `Bidzina83/hermes-agent` as the practical integration source, preserve
   compatibility with `NousResearch/hermes-agent`, and avoid copying arbitrary
   runtime folders into `project_maya`.

3. **Runtime Contract Inventory**

   Inspect the actual Hermes runtime surface in the selected source and map
   startup, `run_agent:AIAgent`, model configuration, memory hooks,
   skill/plugin loading, shutdown, health, compatibility, and dependencies.

4. **Adapter Contract Update**

   Tighten `HermesRuntimeAdapter` against the real Hermes runtime, including
   factory resolution, constructor arguments, model/provider/base URL handoff,
   memory-provider attachment, skill/plugin registration, run/session
   execution, stop/cleanup, and redacted health.

5. **Package Inclusion**

   Make the built Maya package install with the required Hermes runtime
   available. This must not rely on `PYTHONPATH` shims, repository-relative
   imports, `/opt/hermes`, or local checkout paths.

6. **Skills Inclusion Boundary**

   Define how Maya skills are shipped and discovered. Only approved
   Maya/IM AI Employee skills may be included, skills are versioned product
   artifacts, personal account details stay out, and skill loading is mediated
   by the Maya/Hermes adapter.

7. **Memory Hook Wiring**

   Connect Maya's `HermesMemoryProvider` to the real Hermes lifecycle.
   Retrieval and write decisions continue to pass through Maya governance, and
   no duplicate memory store is introduced.

8. **Governed Execution Smoke Path**

   Prove that `build_local_product(config).run(...)` and
   `maya run --config ... --input ...` reach Hermes through the public Agent
   facade and governed runtime wrapper, producing runtime authorization and
   model-egress audit records.

9. **Installed Package Verification**

   Extend clean package verification to install Maya and prove Hermes
   availability without editable installs or path shims.

10. **Windows Manual Smoke Test**

    Repeat the Windows installed-package smoke test, now expecting Hermes
    compatibility to pass and runtime health to be healthy or intentionally
    degraded rather than missing.

11. **Closure Audit**

    Add a closure document mapping this phase's acceptance criteria to tests,
    docs, implemented code, and known limits.

## Guardrails

- Do not create a fake parallel Hermes runtime.
- Do not bypass the local action authorization gateway.
- Do not move memory authority into Hermes-only transient state.
- Do not store raw secrets in configuration, logs, diagnostics, fixtures, or
  package artifacts.
- Do not claim support for a platform or installer until the corresponding
  artifact has passed installation, lifecycle, health, backup, restore,
  update, and rollback tests.
- Do not package personal account details or operator-specific paths with Maya
  skills.


# Hermes Runtime Inclusion Scope Gate

## Status

Step 1 of the approved Hermes Runtime Inclusion phase.

## Scope

This step defines the acceptance gate for including and wiring Hermes Agent as
Maya's real execution runtime in a clean installed package.

The phase is successful only when Maya can be installed from a built artifact,
resolve a compatible Hermes runtime, execute through the public Agent facade,
and preserve the mandatory governance boundary.

## Acceptance Criteria

1. A clean installed Maya package can resolve a compatible Hermes runtime
   without `PYTHONPATH` shims, repository-relative imports, `/opt/hermes`, or
   local checkout assumptions.
2. `maya doctor` no longer reports `Hermes runtime factory unavailable` for
   the supported packaged configuration.
3. `maya doctor` reports Hermes runtime health as healthy or intentionally
   degraded with redacted reasons, not missing.
4. `maya run --config ... --input ...` executes through the public Maya
   `Agent`, `GovernedAgentRuntime`, `HermesRuntimeAdapter`, and real Hermes
   runtime.
5. Runtime execution produces local authorization and audit records before any
   model inference, connector call, tool use, workflow execution, or memory
   write.
6. Customer-owned model and connector credential references remain
   `secret://...` references and are never logged or packaged as raw values.
7. Maya's `HermesMemoryProvider` participates in the real Hermes lifecycle
   without introducing a duplicate authoritative memory store.
8. Approved Maya skills are discoverable as versioned product artifacts and do
   not contain operator-specific account details or machine-specific paths.
9. Broker-disabled Enterprise configuration remains valid and runnable without
   Maya cloud services.
10. Clean package verification covers Hermes availability and a controlled
    governed execution smoke path.

## Non-Goals

This phase does not implement:

- Metabase service packaging or dashboard provisioning;
- document processing or browser automation product capability;
- production Maya OAuth Broker protocol;
- broker-assisted Standard Google or Slack OAuth;
- Maya-managed model billing or model proxying;
- production provider token refresh;
- production connector webhooks or event ingestion;
- signed production installers, SBOMs, release provenance, or automatic
  updates;
- broad platform qualification beyond the artifacts explicitly tested in this
  phase.

## Required Evidence

Closure for this phase must include:

- source strategy documentation for the selected Hermes integration path;
- runtime contract inventory against the selected Hermes source;
- adapter and package-inclusion tests;
- installed-package verification evidence;
- Windows manual smoke-test result summary;
- closure audit mapping acceptance criteria to tests, docs, code, and known
  limits.

## Decision Rule

When implementation choices conflict, prefer the option that preserves, in
order:

1. local governance and customer control;
2. real Hermes execution rather than a placeholder;
3. secret safety;
4. package reproducibility;
5. memory integrity;
6. auditability;
7. cross-platform compatibility;
8. future compatibility with upstream Hermes.


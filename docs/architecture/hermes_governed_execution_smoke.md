# Hermes Governed Execution Smoke Path

## Status

Step 8 of the approved Hermes Runtime Inclusion phase.

## Decision

Project MAYA now has a smoke path proving that both product assembly and the
CLI execute through the governed public runtime path before reaching Hermes.

The covered path is:

```text
build_local_product(config)
  -> public Agent facade
  -> GovernedAgentRuntime
  -> HermesRuntimeAdapter
  -> Hermes AIAgent-shaped runtime
```

The CLI path covers:

```text
maya run --config ... --input ...
  -> build_local_product(config)
  -> public Agent facade
  -> GovernedAgentRuntime
  -> HermesRuntimeAdapter
  -> Hermes AIAgent-shaped runtime
```

## Required Evidence

The smoke tests prove that:

- `build_local_product(config).run(...)` reaches the Hermes adapter through
  the public Agent facade;
- `maya run --config ... --input ...` reaches the same governed path;
- `runtime.execute` authorization is recorded before execution;
- external `model.egress` authorization is recorded before inference;
- audit records include idempotency key, data classification, runtime target,
  and model target;
- prompt text and `secret://...` references are not written to audit output.

## Boundary

This step uses a Hermes `AIAgent`-shaped runtime double so the test is
deterministic and does not depend on network model calls. It does not prove
installed-package Hermes dependency resolution; that remains Step 9.

The runtime double still exercises the same Maya adapter boundary used for
the selected Hermes `run_agent:AIAgent` surface, including the public Agent
facade and governed runtime wrapper.

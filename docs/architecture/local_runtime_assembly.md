# Local Runtime Assembly

## Decision

Phase 1 assembles the minimal local Maya product from typed configuration with
`project_maya.bootstrap.build_local_product()`.

The assembled object contains:

- public `Agent` facade;
- governed Hermes runtime wrapper;
- Hermes adapter configured from `runtime.hermes_factory`;
- governed memory retriever;
- local persistent retriever;
- local secret store;
- authenticated local API handler;
- local JSONL audit sink;
- product-level lifecycle methods.

## Configuration Inputs

Phase 1 accepts only `schema_version: 2`. Missing, malformed, or unsupported
configuration schema versions fail before runtime assembly so migrations can be
introduced explicitly instead of silently interpreting stale contracts.

Runtime binding uses:

- `runtime.hermes_factory`, defaulting to `run_agent:AIAgent`;
- `runtime.hermes_runtime_version`, used for diagnostics;
- `runtime.hermes_compatibility`, used as the supported adapter contract;
- `llm.model`, `llm.provider`, `llm.endpoint`, and `llm.timeout_seconds`.

For non-local model modes, assembly also derives a redacted model-egress
authorization policy from `llm.mode`, `llm.provider`, and whether
`llm.endpoint` is configured. This preserves the Product Specification V2
requirement that external model inference is governed and audited without
logging prompts or credential references.

Memory binding currently supports `memory.retriever: local_json`, which stores
records under:

```text
<deployment.data_dir>/memory/records.json
```

Assembly wraps the governed memory facade in `HermesMemoryProvider` and
attaches it to the public `Agent` before startup. Hermes sees the runtime
memory provider, while product code still uses the governed Maya memory facade
directly.

## Governance

The assembled runtime always passes execution through
`GovernedAgentRuntime`. If no policy engine is supplied, the default gateway is
deny-by-default. Runtime execution and non-local model egress are separate
authorization decisions, so an allow rule for `runtime.execute` does not
implicitly allow external inference. This preserves the mandatory
authorization boundary while the real policy engine is still being
implemented.

## Lifecycle

`LocalMayaProduct` is the Phase 1 control surface for the assembled local
product. Its `start()`, `run()`, and `stop()` methods delegate through the
public `Agent` facade, which preserves compatibility checks, startup ordering,
runtime execution, rollback, shutdown, and authorization.

`LocalMayaProduct.health()` returns the redacted runtime health report exposed
by the governed runtime wrapper. Product-level health reporting must not expose
secrets, raw prompts, memory contents, or connector tokens.

`LocalMayaProduct` also supports context-manager use so callers can guarantee
shutdown after a local run:

```python
with build_local_product(config) as maya:
    maya.run("prepare the briefing")
```

The installed `maya run --config <path> --input <text>` command uses this same
assembly path for a single request. It starts the local product, executes
through the public Agent facade, prints a JSON result, and stops the runtime
before exiting. Failures are reported with secret-safe generic errors rather
than prompt text, secrets, or connector payloads.

## Limits

This assembly does not install Hermes or start a network listener for the local
API. It creates the smallest governed local runtime shape that can be validated
from configuration and extended in later Phase 1 slices.

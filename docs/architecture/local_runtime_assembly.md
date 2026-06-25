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

Runtime binding uses:

- `runtime.hermes_factory`, defaulting to `run_agent:AIAgent`;
- `runtime.hermes_runtime_version`, used for diagnostics;
- `runtime.hermes_compatibility`, used as the supported adapter contract;
- `llm.model`, `llm.provider`, `llm.endpoint`, and `llm.timeout_seconds`.

Memory binding currently supports `memory.retriever: local_json`, which stores
records under:

```text
<deployment.data_dir>/memory/records.json
```

## Governance

The assembled runtime always passes execution through
`GovernedAgentRuntime`. If no policy engine is supplied, the default gateway is
deny-by-default. This preserves the mandatory authorization boundary while the
real policy engine is still being implemented.

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

## Limits

This assembly does not install Hermes or start a network listener for the local
API. It creates the smallest governed local runtime shape that can be validated
from configuration and extended in later Phase 1 slices.

# Local Runtime Assembly

## Decision

Phase 1 assembles the minimal local Maya product from typed configuration with
`project_maya.bootstrap.build_local_product()`.

The assembled object contains:

- public `Agent` facade;
- governed Hermes runtime wrapper;
- Hermes adapter configured from `runtime.hermes_factory`;
- local persistent retriever;
- public memory vocabulary.

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

## Limits

This assembly does not install Hermes, manage secrets, or start a local API.
It creates the smallest governed local runtime shape that can be validated
from configuration and extended in later Phase 1 slices.

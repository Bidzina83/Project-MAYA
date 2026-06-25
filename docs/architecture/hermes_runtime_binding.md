# Hermes Runtime Binding

## Decision

Project MAYA binds to the current Hermes Agent Python runtime through
`run_agent:AIAgent`.

The Hermes fork currently exposes a chat-oriented runtime object rather than a
small lifecycle factory. `project_maya.adapters.hermes.HermesRuntimeAdapter`
therefore loads `run_agent:AIAgent`, constructs it with explicit factory
arguments, and wraps chat-style objects in a Maya lifecycle boundary.

## Contract

Maya owns the product-facing lifecycle:

```text
compatibility -> configure memory/plugins -> start -> run -> stop -> health
```

Hermes owns execution:

- model-provider interaction;
- tool selection;
- skill execution;
- conversation loop;
- Hermes-native memory-provider participation.

The adapter must not create a fake Hermes runtime. If `run_agent:AIAgent` is
not importable, `maya doctor` reports Hermes compatibility and health failures.

## Current Limits

The current Hermes `AIAgent` seam does not expose first-class startup,
shutdown, plugin-loading, or memory-provider attachment methods. The adapter
therefore supports lifecycle wrapping for request execution and only delegates
memory/plugin configuration when the concrete Hermes object exposes those
methods.

Future Hermes work should provide a smaller versioned factory contract for
Maya, for example:

```text
create_runtime(config) -> start/run/stop/health/attach_memory/load_plugin
```

Until that exists, `run_agent:AIAgent` is the supported compatibility seam.

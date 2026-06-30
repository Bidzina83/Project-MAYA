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
therefore supports lifecycle wrapping for request execution.

For memory, the adapter binds Maya's governed `HermesMemoryProvider` into the
Hermes `MemoryManager` through a small Hermes `MemoryProvider`-shaped bridge
named `maya`. This bridge uses Hermes' real provider lifecycle
(`initialize`, `prefetch`, `sync_turn`, and `shutdown`) while reads and writes
continue to pass through Maya's governed memory facade.

Plugin loading remains intentionally conservative. Until the selected Hermes
runtime exposes a versioned plugin-loading seam that Project MAYA can govern
and audit, arbitrary plugin loading through the public Maya API reports
unavailable instead of pretending that a plugin was loaded.

Future Hermes work should provide a smaller versioned factory contract for
Maya, for example:

```text
create_runtime(config) -> start/run/stop/health/attach_memory/load_plugin
```

Until that exists, `run_agent:AIAgent` is the supported compatibility seam.

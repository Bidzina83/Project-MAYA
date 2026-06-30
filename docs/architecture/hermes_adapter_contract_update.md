# Hermes Adapter Contract Update

## Status

Step 4 of the approved Hermes Runtime Inclusion phase.

## Decision

`HermesRuntimeAdapter` now binds to the selected Hermes fork's actual
chat-oriented `run_agent:AIAgent` surface rather than expecting a native
`start/stop/attach_memory/load_plugin` runtime.

Maya continues to own the product lifecycle:

```text
compatibility -> configure memory -> start -> run -> stop -> health
```

Hermes owns request execution through `chat()` or `run_conversation()`.

## Runtime Mapping

| Maya runtime contract | Selected Hermes surface |
| --- | --- |
| `compatibility()` | resolves `run_agent:AIAgent` and reports import/callability failures |
| `start(agent_name=...)` | constructs `AIAgent`, registers pending memory, initializes Maya-owned lifecycle state |
| `run(request, **kwargs)` | calls the normalized Hermes chat runtime |
| `stop()` | calls Hermes memory shutdown when available, then `close()` or `stop()` |
| `health()` | reports adapter, factory, contract, compatibility, and startup state without secrets |

## Memory Bridge

The selected Hermes `AIAgent` does not expose `attach_memory()`. Hermes memory
participates through `MemoryProvider` and `MemoryManager`.

Project MAYA now wraps Maya's governed `HermesMemoryProvider` in a
Hermes-shaped provider named `maya` and registers it through
`AIAgent._memory_manager.add_provider()` when that manager is available.

The bridge exposes:

- `name = "maya"`;
- `is_available()`;
- `initialize(session_id, **kwargs)`;
- `system_prompt_block()`;
- `prefetch(query, session_id="")`;
- `queue_prefetch(query, session_id="")`;
- `sync_turn(user_content, assistant_content, session_id="", messages=None)`;
- `get_tool_schemas()`;
- `handle_tool_call(...)`;
- `shutdown()`.

Maya memory remains authoritative. The bridge calls Maya's governed memory
provider for session start, prefetch, turn synchronization, and session end.
It does not create a second memory store.

## Plugin Boundary

The selected Hermes `AIAgent` does not expose a versioned plugin-loading
method suitable for Project MAYA's public API.

Therefore, arbitrary plugin loading remains unavailable unless a concrete
runtime exposes a supported `load_plugin()` method. This preserves honest
health reporting and avoids creating a fake plugin registry.

## Deferred Work

This step does not package Hermes into Maya.

It also does not:

- install Hermes as a dependency;
- include default or trained Maya skills;
- define product skill bundles;
- resolve Python `<3.14` packaging constraints;
- claim full Windows runtime health for Hermes.

Those remain later approved steps.

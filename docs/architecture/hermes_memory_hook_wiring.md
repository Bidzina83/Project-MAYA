# Hermes Memory Hook Wiring

## Status

Step 7 of the approved Hermes Runtime Inclusion phase.

## Decision

Maya's governed `HermesMemoryProvider` is now wired into the Hermes
`MemoryProvider` lifecycle through the adapter bridge for both prompt memory
hooks and Hermes memory tool calls.

The bridge continues to register one external provider named `maya` through
`AIAgent._memory_manager.add_provider()` when the selected Hermes
`run_agent:AIAgent` surface exposes its memory manager.

## Wired Hooks

The adapter bridge maps Hermes-facing hooks to Maya-governed operations:

| Hermes-facing hook | Maya-governed operation |
| --- | --- |
| `initialize(session_id, **kwargs)` | `HermesMemoryProvider.begin_session(...)` |
| `prefetch(query, session_id=...)` | `HermesMemoryProvider.prefetch(...)` |
| `sync_turn(user_content, assistant_content, ...)` | `HermesMemoryProvider.synchronize_turn(...)` |
| `shutdown()` | `HermesMemoryProvider.end_session(...)` |
| `get_tool_schemas()` | exposes Maya memory search, recall, and remember tools |
| `handle_tool_call(...)` | dispatches tool calls back to Maya governed memory |

## Memory Tools

Hermes may discover these memory tools from the Maya provider:

- `maya_memory_search`
- `maya_memory_recall`
- `maya_memory_remember`

These are not independent stores and do not bypass Maya. Reads continue
through governed memory search and recall. Writes continue through governed
memory remember. Authorization, audit, stable identifiers, and persistence
remain owned by Project MAYA's `GovernedMemoryRetriever` and configured
retriever.

## Authority Boundary

Hermes may request memory context or propose a memory write, but Maya remains
the authority that decides whether memory is read or written. The bridge does
not create a second memory database, does not persist Hermes-only state as
authoritative memory, and does not expose raw secrets or prompt bodies through
tool schemas.

## Current Limits

This step does not:

- prove installed-package Hermes execution;
- package or load Maya skills;
- implement vector ranking beyond the configured retriever;
- add retention or conflict-resolution policy;
- change migration, backup, or restore behavior.

Those remain later approved implementation steps.

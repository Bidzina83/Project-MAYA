# Project MAYA public API architecture

## Decision

`project_maya` is the canonical product namespace. Its public `Agent` is a
lifecycle facade over an injected execution runtime; it is not a replacement
for Hermes Agent.

The package separates two memory roles:

- A Hermes `MemoryProvider` is attached to the execution runtime and
  participates in session lifecycle, prompt prefetch, turn synchronization,
  and tool handling.
- A Project MAYA `Retriever` stores and searches normalized persistent-memory
  records through `upsert`, `get`, and `search`.

Key-value `read` and `write` methods are not the persistent-memory contract.

## Dependency direction

```text
consumer
  -> project_maya public API
    -> AgentRuntime protocol
      -> Hermes adapter
        -> Hermes Agent runtime
    -> MemoryRetriever
      -> canonical Retriever implementation
```

The public package may depend on protocols and adapters. It must not import a
concrete optional provider at module import time.

## Lifecycle

An Agent moves through these states:

```text
created -> starting -> running -> stopping -> stopped
                    \-> failed <-/
```

Memory and startup plugins are configured while the agent is `created`.
Startup configures memory, loads plugins, and then starts the runtime. Any
failure attempts runtime shutdown and leaves the agent in `failed`; failed
plugins are never reported as loaded.

## Hermes integration rule

A concrete Hermes adapter may only be implemented against a versioned Hermes
construction and lifecycle contract. Until that contract is available as an
installed dependency, `create_agent()` returns a configurable facade but
`start()` fails clearly without an injected runtime. No fallback runtime or
silent import shim is permitted in the public API.

## Packaging transition

Existing `maya`, `maya_dev`, `hermes`, and top-level `plugins` imports remain
temporarily for compatibility. New product APIs belong under `project_maya`.
Removing legacy roots requires a separate compatibility inventory and release
plan; they must not be silently remapped.

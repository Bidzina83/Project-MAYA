# Native Hermes Governance

## Status

Stage 1 implemented: the Maya-owned plugin, execution adapters, request identity
scope, secret-safe auditing, startup compatibility gate, installer registration,
and qualification blocking. This is not a completed production enforcement system.
The current Hermes pin `b13e2fd6948a59eeb59fe618914147d97a2ee90a` is incompatible:
middleware exceptions can continue execution, and auxiliary inference bypasses
the main conversation middleware. No replacement Hermes artifact is qualified.

## Implementation

`project_maya.hermes_plugins.governance` uses native `register_middleware` for
`llm_execution` and `tool_execution`. The existing Maya gateway decides each
action; there is no parallel policy registry or authoritative state store.
Callbacks receive a trusted identity from the Maya host's ContextVar scope,
not caller-provided actor fields. Missing identity denies execution. The public
governed runtime binds and resets that identity per request. Future Hermes
workers must explicitly preserve it, and scheduled work needs an authenticated
job identity. Thread-local inheritance is not assumed.

Model execution checks each effective request's configured provider, endpoint,
and model before calling the provider callback. Maya-managed mode is blocked
until a governed gateway exists. Known credential patterns and secret-bearing
fields block payloads; this conservative detector is not a complete PII/DLP
classifier. The existing request classification is not independently verified;
production requires content-derived classification and disclosure policy.

The initial action map covers Maya business-memory search, ingestion, embedding
rebuild, and document-root-confined native read/write operations. Paths are
canonicalized before authorization and passed to execution in canonical form.
This is not an OS sandbox: protection against filesystem races and hostile
same-user processes is not claimed. The starter policy does not grant file
operations. Unknown connectors, terminal, execute_code, delegation, and cron
are denied even if a general policy rule would allow them. Their bounded
adapters and worker identity handling are subsequent implementation work.

All non-ALLOW decisions stop execution. Confirmation, constraints, and redaction
are not interpreted as permission. An approval coordinator, immutable approved
action binding, and governed redaction are not yet implemented. No automatic
approval or provider fallback is introduced. Results containing detected secrets
are withheld from Hermes; result validation cannot undo an already executed
mutation. Every later model request is independently evaluated.

Audit records include actor, capability, operation, classification, fixed reason
codes, and hashed targets. They exclude request/response bodies, paths, arguments,
provider credentials, and policy exception text. Policy/audit failures stop the
operation with fixed secret-safe errors. Successful auditing is mandatory.

## Required Hermes Contract

The future pinned runtime must expose, in `hermes_cli.middleware`:

```python
MAYA_GOVERNANCE_CONTRACT = {
    "version": "project-maya.hermes-governance.v1",
    "capabilities": [
        "fail_closed_execution", "mandatory_middleware", "auxiliary_sync",
        "auxiliary_async", "trusted_context_propagation",
    ],
}
```

`require_middleware(kind, callback)` binds a mandatory callback to a supported
boundary. `validate_mandatory_middleware()` returns True only when both required
execution gates are registered and required on all dispatch paths. Missing,
removed, replaced, disabled, or failed gates must stop execution. Required
callback errors must propagate; they must never invoke the downstream operation.
Retry, streaming, non-streaming, fallback, compression, and plugin LLM paths
must all preserve the gate and actual provider/endpoint context. SDK-internal
retries must not bypass approval validity or change the authorized payload.

These capability declarations are compatibility metadata, not security proof.
They require source review and behavioral qualification against the pinned
artifact before the release flag can change. No monkey-patching, BaseException
escape trick, fabricated provider response, or network-dependent self-test is
used to work around the unsafe current pin.

The canonical product factory receives a startup guard before AIAgent
construction. Noncanonical injected factories used by existing contract tests
are not production-qualified Hermes integrations. Installer first-run writes
the native `maya-governance` plugin entry point and blocks on an unsupported
runtime. Installed qualification has a separate governance-boundary probe.
Current release manifests remain `local_smoke_blocked`, even with every runtime
artifact supplied. Installed customer secrets/configuration are not altered by
this repository change. No installer has been rebuilt as part of Stage 1.

## Remaining Stages

1. Implement and review the required fail-closed contract in the selected Hermes
   repository; cover synchronous/asynchronous auxiliary calls and worker identity.
2. Add immutable approval bindings, content classification/redaction, scoped
   connector/file adapters, result provenance, and bounded delegation/cron.
3. Build the revised pinned Hermes wheel and test the real loop offline using
   inert transports/tools: denial before side effects, policy crash, audit crash,
   missing/removed plugin, repeated model calls, concurrent tools, retries,
   compression, auxiliary inference, delegated workers, and scheduled jobs.
4. Rebuild and qualify the installer using clean and upgraded customer state.
   Preserve independent review, signing, lifecycle, backup/restore, update, and
   rollback gates. Local unit tests alone do not qualify production governance.

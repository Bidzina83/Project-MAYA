# Native Hermes Governance

## Status

Current reassessment: see the [2026-10-03 integration assessment](maya_governance_integration_assessment_20261003.md)
and [approved gated product plan](maya_governance_integration_plan.md). Source
patches 13-23 do not change the installed twelve-patch artifact. Further candidate
work follows the user-approved G0-G7 sequence; G0 is current, activation is blocked.
Historical scoped qualification below must not be read as full product readiness.

Installed candidate qualification now has four process-isolated scenarios:
model denial, allowed model/output, and denied/allowed native `read_file` proposals.
The latter three use the real OpenAI-compatible SDK with explicit zero retries
and synthetic HTTP/SSE responses through `httpx.MockTransport`. Authorization
is checked before fixture dispatch; the denied file handler must not run and
no second inference is permitted. This tests native SDK parsing and loop/gate
ordering, not network sockets, a live provider, model reasoning, general tool
capabilities, or recovery. No customer credentials are used. The dedicated
test installer runs all four; each report remains `test_only_unqualified`.
Production pin, compatibility marker and activation guard are unchanged.

The fourth installed scenario grants `file.read/read` only for one freshly
created synthetic document. It executes the native handler once, validates its
actual result, checks that the second SDK request contains that tool result
only after tool-result validation and renewed model-egress authorization, and
validates the final answer. The test host has an explicit 1-3 iteration limit;
normal production construction is unchanged. On Windows the native file reader
requires Git Bash, which this core-only candidate does not bundle. An existing
customer-managed installation is a qualification dependency, not evidence of
clean-machine readiness. No general shell or additional file permissions are
granted; recovery and production qualification remain blocked.
The test host selects Git Bash through native `HERMES_GIT_BASH_PATH` rather than
accepting Windows's WSL `System32/bash.exe` shim. File authorization retains the
canonical policy target; the effective tool path uses forward slashes for the
native Bash reader. Shell home and working directory use newly created test
state, never customer profiles. Missing Git Bash reports blocked readiness.

Stage 1 implemented: the Maya-owned plugin, execution adapters, request identity
scope, secret-safe auditing, startup compatibility gate, installer registration,
and qualification blocking. This is not a completed production enforcement system.
The current Hermes pin `b13e2fd6948a59eeb59fe618914147d97a2ee90a` is incompatible:
middleware exceptions can continue execution, and auxiliary inference bypasses
the main conversation middleware. No replacement Hermes artifact is qualified.

Stage 2a implemented as a reviewable candidate patch in `patches/hermes/`:
opt-in mandatory dispatch, live callback validation, final-payload authorization
ordering, fixed secret-safe failures, and single-use execution protection.
Offline tests apply it to the real pinned middleware source and compare selected
legacy behavior with the unmodified module. Real Maya gateway callbacks are also
exercised against the patched dispatcher with inert transports.

Stage 2b adds `0002-governed-auxiliary-inference.patch`: an asynchronous dispatcher
and gates on each central auxiliary attempt, including parameter retries,
credential refresh, pool rotation, and fallback clients. Typed mandatory failures
stop before retry classification. Effective endpoint/model metadata is captured
per attempt; a declared direct OpenAI alias is preserved instead of being
misattributed as Hermes' internal `custom` routing label. Automatic routes with
no retained selected-provider identity are blocked, not guessed from hostnames.
Injected plugin LLM test callers are denied in mandatory mode. Outside mandatory
mode the auxiliary calls retain their legacy request/error behavior.

Maya's model callback now separates authorization failure from transport failure.
This permits Hermes to reauthorize legitimate retries instead of treating SDK
failures as policy denials. The mandatory auxiliary public boundary redacts
exhausted errors. Main-loop transport-error redaction and explicit mandatory
no-retry/no-fallback handling are still required before activation.

This is not the complete Stage 2 runtime. No full compatibility marker is
published, no Hermes pin changes, and startup/production gates remain blocked.
The isolated network source checkout did not complete; the exact source from
the existing pinned wheel was used instead, with provenance and MIT license
retained in the test fixture. Full fork regression tests have not run.

## Implementation

`project_maya.hermes_plugins.governance` uses native `register_middleware` for
`llm_execution`, `tool_execution`, and the candidate fork's `tool_result` boundary.
The existing Maya gateway decides each
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
        "auxiliary_async", "trusted_context_propagation", "tool_result_validation",
    ],
}
```

`require_middleware(kind, callback)` binds a mandatory callback to a supported
boundary. `validate_mandatory_middleware()` returns True only when all three
required callbacks (model execution, tool execution, final tool result) are
registered. Full dispatch coverage remains an artifact qualification requirement. Missing,
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

### Isolated Candidate Startup (2026-10-02)

`project_maya.hermes_plugins.candidate.build_test_only_product` is an explicit
qualification entry point, separate from `build_local_product`. It verifies the
exact SHA256 of the eleven-patch candidate wheel and compares its Python files to
the selected installed runtime. It enables native mandatory mode and registers
the actual Maya callbacks through Hermes `PluginContext` before construction;
all four live bindings are checked before and after construction and during
subsequent compatibility checks. Removed bindings are not silently repaired.
This host registers directly in the native registry; automatic production
plugin discovery is still a separate qualification gate.

The shared assembly retains the public Agent lifecycle, local authorization,
secret store, Local API object, audit and governed SQLite memory. The host uses
Hermes's real MemoryManager when construction has not selected an external
provider. Maya's bridge implements native no-op turn-start/session-end hooks;
these notifications do not ingest conversations. Hermes's own built-in memory
and session persistence are retained. This is not an approval to expose business
memory through unqualified tools or background work.

Constraints: explicit `unqualified-governance-candidate` acknowledgement, a new
marked test-data root, matching isolated `HERMES_HOME`, no ambient credentials
or external Hermes configuration, canonical factory, local OpenAI-compatible
loopback endpoint, core-only profile and disabled broker/connectors/Metabase.
Health includes `qualification=test_only_unqualified` and
`production_qualified=false`, even when lifecycle initialization succeeds.
Scope and artifact checks repeat at startup; the production contract guard,
capability marker and runtime pin are unchanged. This is a qualification host,
not a security sandbox for malicious Python or plugins. Run it in a fresh process.

For a dedicated installed-candidate launcher:

```powershell
python -m project_maya.hermes_plugins.candidate --config <isolated-config.json> --wheel <candidate.whl> --acknowledge unqualified-governance-candidate --actor <test-actor> --initialize-test-home
```

The launcher starts, reports candidate lifecycle and stops; it does not serve
the Local API, authorize cloud services or contact a real provider for a test
conversation. Prepare the declared policy under the test root after creating
that root with `initialize_test_only_home`, then omit `--initialize-test-home`
on launch. No production shortcut selects this module. Full-loop testing uses
the public product's `run` method through the opt-in test below:

```powershell
$env:MAYA_HERMES_CANDIDATE_ROOT = '<extracted-candidate-wheel-directory>'
$env:MAYA_HERMES_CANDIDATE_WHEEL = '<exact-candidate-wheel-file>'
python -m unittest tests.test_hermes_candidate_denial.TestHermesCandidateDenial.test_explicit_candidate_product_startup -v
```

This test starts/stops the actual product and Hermes with inert external
transports, proves binding before SDK construction, allows runtime/memory reads,
and verifies native model denial is audited with zero provider requests. It does
not qualify positive provider operation, tools, recovery, all data sinks,
background work, automatic plugin discovery or a clean installed product.

Stage 2c's first increment adds patch 3: explicit `MandatoryMiddlewareError`
handlers before provider retry classification and before the outer conversation
error handler. These rethrow fixed codes without exception chaining, so a denial
does not enter credential rotation, compression, fallback, synthetic tool-result
recovery, or successful-turn finalization through those handlers. Ordinary
Hermes errors retain their existing handling. Focused tests compile and execute
the exact handler sequences from the patched pinned source; AST comparison
verifies that unrelated loop logic is unchanged. These are handler-boundary
tests, not an end-to-end conversation test or worker/tool-dispatch qualification.

General provider failures still have raw error/log/dump paths in the pinned loop.
Outer auxiliary consumers, remaining tool callbacks, spinner
cleanup, host error presentation, and turn finalization need separate review.
This increment deliberately propagates denial rather than fabricating a healthy
conversation result. No full compatibility marker, new wheel, pin change, or
installer activation is authorized by this patch.

Stage 2c's second increment adds patch 4 against pinned `tool_executor.py`,
`turn_context.py`, and `memory_manager.py`. The tool-request adapter and execution
error handlers propagate typed mandatory denials rather than logging them or
creating ordinary tool results. Preflight's exception handlers preserve typed
denials. Memory provider turn-start and prefetch failures become fixed mandatory
errors before non-fatal logging; this includes ordinary provider exceptions,
because failure to retrieve authorized context must not appear as empty memory.
Normal Hermes optional-memory handling is unchanged outside mandatory mode.

In mandatory mode the concurrent entry point uses the existing native sequential
dispatcher before parsing, callbacks, or worker submission. No new dispatcher or
implicit worker identity is introduced. This is a temporary performance limit,
not a claim that parallel workers are qualified. Normal-mode concurrent execution
is unchanged. Sequential execution cannot undo a mutation already authorized and
performed before a later failure; durable mutation recovery remains necessary.

Tests apply all four patches and execute complete pinned preflight/sequential
functions with inert dependencies, the real patched middleware engine, and memory
manager turn-start/prefetch functions. Cases cover memory/context-engine/regular
tool denial, quiet/verbose paths, stopping a batch before later calls, compression
denial, hook denial, memory failures, normal prefetch, and serial batch routing.
No network, model credentials, or customer state is used. This is not a complete
Hermes agent-loop integration test. Internal observer-hook suppression, background
memory work, result transformations, ancillary callbacks, cleanup exceptions,
provider error disclosure, and full fork regressions remain review gates.
At the end of patch 4, `model_tools.handle_function_call` still had an outer generic
exception-to-tool-result handler around native execution middleware. Patch 4
tests the regular-tool caller with an inert typed-denial dispatcher, not that
lower-level implementation. That handler must be patched and tested against
the real execution gate before ordinary registered tools are qualified. Tool
registry handlers and observer-hook internals also require source review.

Stage 2c's third increment adds patch 5 against pinned `model_tools.py` and
`tools/registry.py`. Typed mandatory errors propagate through the registry's
sync/async dispatch and the model-tools outer handler instead of being logged or
returned as ordinary tool-error JSON. Request middleware, pre-tool hooks, edit
approval, and result-transform typed errors also propagate. The dispatcher checks
both live mandatory gates before argument preparation. Catalog bridge dispatch
returns before the execution gate in the pinned source, so those operations are
explicitly blocked in mandatory mode before catalog discovery; this does not
invent authority for tool-search or recursively unwrap unqualified tool calls.

Tests apply all five patches and run the complete pinned `handle_function_call`,
real `ToolRegistry`, native mandatory middleware, and real Maya policy gateway.
The patch-4 sequential caller is tested with that actual dispatcher. Inert tool
handlers record side effects; tests require denied/missing-identity/missing-gate/
removed-gate/policy-crash/audit-crash cases not to call them. Authorized file-read
arguments are canonicalized; results with detected secrets are withheld before
post-tool observation. Post-execution denial does not reexecute the handler.
The isolated async registry test uses an inert coroutine bridge, not the full
Hermes worker-loop implementation. No provider calls or customer state are used.

At patch 5 this qualified focused denial propagation, not all tool behavior.
Generic tool errors still entered upstream logging/sanitization; content added by successful
result-transform hooks occurs after the Maya result gate and needs its own
validation. Observer-hook internals may suppress exceptions, and cleanup or
background handlers need review. Those issues, provider-error redaction, worker
context, direct SDK paths, and full-loop/fork qualification remain blockers.

Stage 2c's fourth increment adds patch 6, including a candidate native
`tool_result` middleware kind in Hermes's existing registry. This is not an
upstream feature or a second Maya plugin registry. Maya registers a final-result
validator there and the unreleased required contract now includes
`tool_result_validation` and `run_tool_result_middleware`. All three live bindings
must be present before mandatory dispatch. No full compatibility marker is added.

Registered-tool results are checked before post-tool observation and again after
result-transform hooks. The native dispatcher snapshots effective arguments
before the handler runs, so later mutation cannot rewrite the validation target.
Agent-owned tool middleware helpers also validate their final result. Ordinary
result callbacks run before the required validator, with independent argument
copies; callback errors, removal, or validation/audit failure withhold the result.
The validator receives no tool-execution callback. Validation
cannot reverse an already executed mutation and is not an approval-binding scheme.

Patched registry/dispatcher generic tool errors, request/pre-tool/edit-approval/
result-transform errors, and execution-error handlers stop with fixed codes in
mandatory mode before their prior exception-text logs. Normal-mode error handling,
successful transformations, and argument-reference behavior remain unchanged.
This is scoped diagnostic protection, not complete runtime log sanitization:
observer internals, ancillary callbacks, prompts, compression, model transport,
streaming, and main-loop provider diagnostics remain unqualified.

Patch-6 tests apply the entire series to the pinned source and exercise real
registry/dispatcher/middleware/Maya-policy paths. Safe transforms pass; detected
secret-bearing transforms and ordinary middleware injections are withheld;
validator removal/crash, missing binding, and generic errors stop with fixed
messages. Executed-argument snapshots and normal-mode behavior are tested. The
secret detector is still conservative pattern/field checking, not complete DLP.
Final validators on later conversation-layer transformations, independent fork
regressions, trusted workers, full-loop tests and installer qualification remain
required before activation or support claims.

Stage 2c's fifth increment adds patch 7 for scoped main-loop provider diagnostics.
Mandatory-mode terminal/retry summaries use `model.provider_error`, and the
API-error observer receives an empty request body, fixed error type/message and
a bounded HTTP status. Both main-loop request-debug dump sites are suppressed;
route displays and retry diagnostic context are redacted. Unexpected outer-loop
errors stop with a fixed mandatory error before traceback logging or synthesis
of exception-bearing tool results. Normal-mode diagnostics retain upstream
behavior. Existing provider classification and retry/fallback activation calls
are unchanged: this is not a new retry engine or blanket rejection of transport
errors.

Tests apply patch 7 after the complete pinned patch series, compile the loop,
execute the native diagnostic helpers and selected actual call-site statements,
and check classification/retry call preservation. They do not execute the full
conversation loop. Streaming errors, earlier recovery branches, retry helpers,
observer internals, cleanup/background work, SDK diagnostics and raw provider
metadata elsewhere remain unqualified. This scoped patch must not be described
as complete secret-safe runtime output or unlock activation, a runtime pin, or
installer production qualification.

The initial source review of streaming, recovery and background paths is recorded
in [the path review](hermes_streaming_recovery_background_review.md). It identifies
per-attempt authorization gaps, direct iteration-limit summary calls, prevalidation
response delivery, swallowed mandatory failures, remaining diagnostic disclosure,
and unqualified background identity/lifecycle. Bounded native-function probes
reproduce selected failures; they do not qualify the full loop. Follow its ordered
remediation and regression requirements before activating or publishing a runtime.

Stage 2c's sixth increment adds patch 8. Each native iteration-limit summary
attempt, including the empty-response retry in chat/Codex/Anthropic branches,
uses existing model execution middleware with effective payload and route.
Typed denials stop before generic summary recovery; unexpected mandatory-mode
summary errors use fixed codes. Normal summary dispatch remains direct as before.

Mandatory chat/Anthropic streaming helpers and Codex helpers do not retry
internally. Any subsequent attempt must return through the native outer gate.
The inline Anthropic stream-to-create fallback propagates failure instead of
issuing a second request. SDK clients must explicitly expose integer
`max_retries=0` before the patched primary/summary/stream request sites; unknown
or retry-enabled clients are rejected, not silently cloned or reconfigured.
Bedrock Converse is blocked before worker dispatch in mandatory mode until its
transport/retry contract is qualified. Mandatory worker errors are not converted
to partial-stream success. Cancellation checks and ordinary-mode retry/fallback
behavior remain native.

The unreleased draft contract now requires `iteration_limit_summary`,
`single_transport_attempt` and `require_single_attempt_client`. No complete
compatibility marker, runtime pin or production gate is published. Artifact-level
SDK options/adapters and effective-client route attribution remain qualification
requirements, as do worker context, streaming output, recovery consumers and
background work. The client retry attribute is a supported-SDK contract check,
not a sandbox against malicious in-process wrappers or proof of all network calls.

Tests apply all eight patches to pinned snapshots and execute complete native
summary and transport helper functions with inert SDKs and real worker threads.
Real Maya policy/audit authorizes summaries. Tests cover empty-response retry,
missing identity, denied actor, policy/audit crash, gate removal, route change,
SDK retry rejection, one-attempt streams, cancellation, unsupported transport,
normal retry/fallback behavior and a second outer dispatch blocked after removal.
This is focused call-path coverage, not full-loop or full SDK qualification.

Stage 2c's seventh increment adds patch 9, the first part of R3 remediation.
Mandatory mode withholds live display/TTS deltas, reasoning deltas, interim
commentary and tool-generation names in the native AIAgent delivery methods.
Tracking resets discard scrubber tails without flushing callbacks. Native
transport response assembly is retained; there is no second Maya response buffer
or delayed replay. Selected conversation-loop assistant/progress/quiet-commentary
display and guardrail-response callbacks are also suppressed. Normal-mode
delivery and tail flushing remain unchanged.
The non-streaming message builder withholds its reasoning callback and verbose
reasoning log, and the transport's muted-stream display fallback is guarded.
Internal reasoning fields and replay data remain unchanged, not authorized for
disclosure merely because they are retained.

Tests apply the complete nine-patch series, execute complete native delivery
methods, and execute the five exact changed conversation display statements.
They also execute the complete native message builder and the exact muted-stream
fallback guard.
They cover split credential-like chunks, tails, reasoning, interim commentary,
gate removal, provider-thread delivery without identity inheritance, callback
failures and normal-mode compatibility. They do not execute the full loop or
claim that worker transport authorization is qualified.

This is suppression of reviewed early-publication sinks, not a model-output
validator or full R3 closure. Final transformed text, returned reasoning/messages,
post-model/API observers, incremental session persistence, trajectories, cleanup
diagnostics and background callbacks remain unqualified. A versioned final
disclosure contract must validate effective output before these sinks, using the
existing gateway and audit. No new output capability marker, activation, runtime
pin, wheel or installer qualification is introduced by this patch.

Stage 2c's eighth increment adds patch 10, a candidate `model_output` kind in
Hermes's existing middleware registry. Mandatory mode requires a fourth live
binding. The native call is validation-only: ordinary callbacks cannot replace
the payload and Maya's required callback runs last. Maya checks the assembled
JSON-shaped payload with its existing conservative secret detector, compares
the configured provider/model/endpoint, and authorizes `model.output` / `disclose`
through the local policy gateway with body-free audit records. Output
authorization is distinct from model egress authorization. The draft capability
is `model_output_validation`; no full compatibility marker is published.

The native finalizer checks response and messages before trajectory save,
rechecks them immediately before session persistence, checks transformed text
before `post_llm_call`, and checks the result (including reasoning and metadata)
before subsequent sync/background/session-end activity and return. Mandatory
denials propagate through the touched finalizer cleanup, persistence and observer
exception handlers. A denied transform does not publish transformed text, though
the already validated original conversation may have been saved. Normal-mode
finalization remains unchanged.

Focused tests apply all ten patches to pinned sources and execute the complete
native finalizer and model-output dispatcher with Maya's real policy/audit
adapter, inert hooks and no network or credentials. They cover policy denial,
missing identity, sensitive source and transformed output, audit failure,
binding removal, attempted middleware replacement, invalid returned metadata,
and ordinary-mode behavior. These are not full-loop tests. Hermes's earlier
incremental writes, raw API/observer paths, unqualified background activity,
cleanup diagnostics and content classification beyond conservative patterns
remain blockers. This does not claim complete DLP, safe release of Hermes
session history, or authorization of every data sink. No runtime pin, wheel,
installer or production gate changes are authorized.

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

The detailed follow-on patch order and review instructions are in
`patches/hermes/README.md`. Mandatory errors must receive explicit no-retry,
no-fallback handling in the main loop as well as in auxiliary transports.
Unsupported workers stay blocked rather than receiving an invented actor.

Stage 2c's ninth increment, patch 11, preserves typed denials through the native
compression-summary consumer and observer dispatcher. Native memory/skills
background review is blocked before thread/agent construction in mandatory mode,
including worker entry if a target was prepared before opt-in. The complete
finalizer propagates that typed failure instead of ignoring it; earlier validated
saves are not undone. Focused tests
apply the full eleven-patch series and execute complete native consumer methods
with normal-mode controls and actual Maya policy denial. This does not qualify
outer callers, all recovery, incremental persistence or other background jobs.
The dedicated test host now binds the eleven-patch candidate. An isolated
eleven-patch wheel, `0.17.0+maya.gov11.candidate.20261002`, was built offline from
the pinned Git tree. Its 17 patched modules match source bytes; extracted-wheel
model-denial and recovery-consumer probes pass. Those probes are not clean-install,
full-loop recovery or production qualification. The ignored artifact directory
is `.codex-build/hermes-governance-candidate-gov11-20261002/`; provenance records
the wheel and patch hashes. Its new dedicated test installer adds compression
denial at the native consumer seam and finalizer-triggered background denial.
These are scoped installed-artifact tests, not full recovery/worker qualification.
Older installed builds are unchanged. No production pin, capability marker or
activation changes.

Stage 2c's tenth increment, patch 12, adds content checks before native session
assignment and SQLite flushes, transformed session JSON and trajectory writes.
It suppresses raw pre/post/error API observers in mandatory mode rather than
making observer hooks security gates. Ordinary Hermes behavior and separate
Hermes session storage are retained. Maya SMB persistent memory is unchanged.
The checks use existing `model.output` authorization; they are not a complete
session-write policy. Fifteen focused tests execute complete native methods
with actual Maya gates and inert storage effects. Real SQLite backend, direct
gateway writers, transformed row validation and outer denial propagation remain
unqualified. The dedicated test host now binds the separately versioned
twelve-patch wheel; older eleven-patch installers are unchanged. See the observer/persistence inventory in the streaming,
recovery and background review. No production pin, marker or activation change.

Patch 13 adds scoped outer-caller typed-denial propagation for native incremental
tool flush, compression rotation/boundary callbacks, reviewed loop hook/flush
catches and CLI session operations. Existing compression locks are released on
the touched denial exits. Normal-mode generic recovery remains unchanged; earlier
mutations are not undone. Complete helper/method tests and a scoped native catch
probe are not full-loop, frontend or installed-artifact qualification. This
source-only patch does not change build 013, the twelve-patch wheel or production
activation. Direct database writers and other worker/caller paths remain open.

Stage 2b does not cover every direct SDK consumer or prove the full conversation
loop. Compression's central `call_llm` path and plugin LLM facades use the patched
router; outer consumers' exception handling still needs review. The mixture of
agents tool contains direct SDK calls and remains an unbounded denied tool.
Provider-resolution control-plane calls and SDK-internal retries/translations
also require artifact-level review. Host opt-in, selected-route retention,
trusted workers, full fork regressions, and clean installer qualification remain
open. No full runtime compatibility marker or replacement wheel is published.
## Patch 14: Effective SQLite Append Arguments (Candidate)

The source-only patch validates the exact native AIAgent `append_message` keyword
arguments after content conversion and tool-call attribute extraction. It reuses
`model.output` validation and propagates canonical mandatory denials through the
append catch. Native SQLite tests check successful mapping and deduplication,
secret-bearing derived arguments, unchanged prior rows on denied append, and
ordinary-mode compatibility. Schema initialization and storage ownership are
unchanged. Hermes conversations remain in Hermes storage, not Maya SMB memory.

This is deliberately a bounded first stage, not direct-writer qualification.
`SessionDB` does not receive trusted actor/provider context at its direct gateway,
CLI, compaction or mirror entry points. Inferring it from stored session metadata
would not establish authority. Build 013 and its twelve-patch wheel are unchanged.
Production activation remains blocked.

Remaining implementation sequence:

1. Define a versioned session-write contract through the existing native middleware
   registry and Maya gateway. Bind trusted request identity and storage purpose at
   the frontend; never infer authority from SQLite contents or environment. Define
   separate initialization, content-write, rewrite and deletion permissions.
2. Gate final serialized rows and session content at direct SessionDB entry points
   before mutation. Validate complete batches before destructive operations and
   retain native atomic rollback. Missing context/callbacks must fail closed.
3. Exercise actual append, replacement, compaction, session prompt updates, mirror,
   CLI/gateway caller propagation, transaction failure and worker isolation. Only
   then rebuild the candidate wheel and installed qualification scenarios.

Current append flushes are not batch-atomic: a prior approved row can be committed
before a later row fails validation. Direct writers, session metadata, complete
frontend recovery and workers remain open; no session-write capability is claimed.

Patch 15 implements the first session-write stage: a distinct mandatory native
boundary, trusted request-scoped host binding, serialized atomic append batches
and post-commit flush tracking. Unmapped native writes are blocked. The contract,
audit semantics and remaining stages are documented in
`hermes_session_write_contract.md`. Frontend bindings, non-append descriptors,
schema provisioning and durable audit reconciliation remain unqualified. It is
source-only and does not change build 013 or production activation.

Patches 16-17 implement reviewed native session mutation descriptors and scoped
initializer/transcript/mirror denial propagation. Real SQLite tests cover
destructive rollback and complete callers with explicit synthetic host bindings.
Gateway session-index mutations, authenticated frontend binding, other metadata,
locks, schema operations and audit reconciliation remain open. See the stage 2a
matrix in `hermes_session_write_contract.md`. No wheel/installer update or
production activation is implied by these source-only candidates.

Patch 18 extends metadata descriptors to end/reopen, cwd, model/config and
token accounting. Mandatory accounting cannot implicitly create sessions.
Native close reports finalization denial after resource cleanup; it does not
provide lifecycle rollback. Ten scoped real-SQLite/close tests do not qualify
authenticated frontends, locks, shutdown callers or durable audit outcomes.
Stage 2 remains partial, with the wheel, installer 013 and production gate unchanged.

Patch 19 gates native compression-lock writes and removes the mandatory caller's
unlocked fallback on denied/missing/broken storage. Contention and release failure
stop with fixed errors; ordinary native recovery remains. Scoped real-SQLite and
complete-caller tests are not full compression, worker or frontend qualification.
Denied cleanup can leave a lock until expiry. See the session-write contract;
production activation and built artifacts remain unchanged.

Current work is session-write Stage 2 Step 1. The existing Local API has an
explicit source-candidate single-owner authenticated session binding; per-write
policy authorization remains mandatory. Patch 20 blocks unqualified native
gateway create/reset/switch before index mutation. This is partial frontend
evidence, not allowed gateway transitions, setup/maintenance authentication,
full-loop or installed-product qualification. See the Step 1 acceptance table
in `hermes_session_write_contract.md`; do not advance without meeting that gate
or explicit approval to revise the sequence. Built artifacts remain unchanged.

Step 1 continuation adds an explicit source-candidate authenticated CLI client
through the bound Local API. Binding readiness and a required execution contract
prevent ordinary-endpoint fallback; tokens are stdin-only and responses/errors
are secret-checked. Real loopback/native SQLite tests are not full-loop or normal
CLI qualification. Gateway and setup/maintenance identity work remains in Step 1.

Patches 22-23 add source-only, single-use executor and main-conversation task
handoffs under an authenticated root session lease. The native scheduling site
selects one closure; cancellation expires its authority before delivery and
unrelated/background workers stay blocked. Real SQLite and complete helper/seam
tests do not qualify the full native conversation caller or Telegram-to-agent
composition. Stay in Step 1's second approved sub-item for that evidence; no
allowed index transitions, wheel/installer or production activation changes.

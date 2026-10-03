# Hermes Governance Candidate Patch Series

## Status

Stage 2a/2b/2c candidates only. A separately versioned test-only wheel was built
from the pinned Git tree with all ten patches on 2026-10-02. It is not applied to
the installed product or published to the Hermes fork. No Nous Research
verification or upstream compatibility is claimed. The production runtime pin
and activation guard stay unchanged.

The generated artifact and `candidate-provenance.json` are under the ignored
`.codex-build/hermes-governance-candidate-20261002/` directory. Candidate version:
`0.17.0+maya.gov10.candidate.20261002`. Packaging-only changes identify the
candidate and exclude bundled plugin tests; dependency pins are unchanged.
All 14 patched modules match the reviewed source byte-for-byte. The offline
denial probe also passed using modules extracted from the wheel, with zero
provider calls and safe audit output. It manually binds callbacks for testing;
normal startup binding, full runtime coverage and installer qualification remain
open. This artifact does not publish the production compatibility marker.

The explicit test-only startup host now lives in
`project_maya.hermes_plugins.candidate`; it binds native gates before construction
through the normal Maya lifecycle assembly. It is limited to an isolated,
acknowledged, exact-wheel, loopback-only core test profile. Production automatic
discovery and full qualification remain open. See the native-governance ADR for
the candidate launcher and opt-in product-startup test.

`0001-opt-in-mandatory-middleware.patch` targets `hermes_cli/middleware.py` from
Hermes commit `b13e2fd6948a59eeb59fe618914147d97a2ee90a`. Source and wheel hashes
are recorded in `tests/fixtures/hermes_middleware/README.md`.

`0002-governed-auxiliary-inference.patch` applies after patch 1. It modifies
`hermes_cli/middleware.py`, `agent/auxiliary_client.py`, and `agent/plugin_llm.py`
from the same pinned baseline. Both patches must be reviewed as a series.

The initial network checkout did not complete, so this candidate was developed
against the exact pinned source from the existing built artifact. The complete
series has since applied cleanly to an isolated checkout of the pinned fork.
Selected native Hermes regressions passed there; the full fork suite and
production qualification remain open.

## Contract

### Eleven-Patch Wheel Build

The follow-on test-only wheel was built offline from the same pinned Git tree
with patches 1-11 on 2026-10-02, leaving the user's Hermes clone unchanged:

- Version: `0.17.0+maya.gov11.candidate.20261002`
- Directory: `.codex-build/hermes-governance-candidate-gov11-20261002/` (ignored)
- Wheel SHA256: `87b179a95df49b08d6b40b70892d667cb8ba29fab150c53a0b8c0b8ceb5216f4`
- Provenance: `candidate-provenance.json` in that directory, including all patch
  hashes and 17 patched module hashes.

All patched modules match source bytes and compile; tests, caches, private-key
files and repository metadata are excluded. The extracted wheel passes the
offline native model-denial probe and scoped recovery-consumer checks:
compression and observer denials propagate, and no background thread or agent
is created. The complete finalizer caller is covered by the 14 source tests,
not a full-loop installed-artifact recovery scenario. Dependencies are unchanged.

The dedicated candidate startup host and new test installer bind the eleven-patch
wheel, adding scoped compression and finalizer-background denial scenarios.
Older installed builds are unchanged. This does not change the production pin, activation guard or
compatibility marker. Full runtime, recovery/worker and clean-install gates
remain open. No upstream/Nous Research qualification is claimed.

Normal Hermes mode remains unchanged. The host explicitly calls
`enable_mandatory_middleware()` before discovery/construction. In mandatory mode:

- After patch 6, model execution, tool execution, and final tool result callbacks
  must be bound with `require_middleware` in the same native registry.
- Removal, replacement, duplication, or plugin-manager reset blocks dispatch.
- Required callbacks run after ordinary execution middleware transformations.
- Callback failures propagate as fixed `MandatoryMiddlewareError` codes without
  logging callback exception text, including failures after execution.
- A caller cannot swallow a failed gate and return a healthy-looking result.
- Downstream calls are single-use and must execute inside the required callback.
- Provider/tool failures remain provider/tool failures, not callback failures.
- There is no runtime disable/reset API. Restart is needed to exit this mode.

The patches intentionally do not publish `MAYA_GOVERNANCE_CONTRACT`: host opt-in,
main-loop error handling, direct SDK paths, automatic-route attribution, and
workers are not yet qualified.
Maya's existing startup guard therefore still rejects it. This is not a sandbox
against malicious plugins or Python code running with host authority.

## Stage 2b Coverage

Patch 2 adds an async dispatcher accepting async callbacks or synchronous
authorization callbacks that return `next_call`'s awaitable. Synchronous response
post-processing is not supported on the async path. Cancellation propagates.

Central `call_llm`/`async_call_llm` attempts enter the execution gate independently:
initial calls, transient/parameter retries, model refresh, credential refresh,
pool recovery, and fallback clients. The gate sees the actual client's endpoint
and the effective model after async fallback conversion. Mandatory failures never
trigger provider retry, refresh, or fallback. Exhausted mandatory-mode auxiliary
errors expose fixed codes, not provider error bodies. Normal-mode request and
error behavior remains unchanged; ordinary conversation middleware is not newly
applied to legacy auxiliary calls outside mandatory mode.

The private task resolver still returns its original five-item tuple. Optional
internal route metadata retains the declared provider before direct API alias
expansion. Ambiguous `auto` routes are blocked until the selected provider id is
retained by the resolution contract. This does not qualify every backend wire
adapter or SDK-internal retry/redirect. Direct SDK consumers remain a review gate.

Plugin LLM facades' normal callers use the router. Injected test callers are
blocked in mandatory mode; legacy tests remain usable outside that mode. Maya's
callback separates authorization from provider execution so authorized retries
are possible and still checked each time. Main-loop provider-error redaction is
not yet implemented; activation must remain blocked.

## Follow-On Patches

Patch 3 (`0003-stop-main-loop-on-governance-failure.patch`) is the first Stage 2c
increment. Apply after patches 1 and 2. It adds explicit mandatory-error stops
before the main retry classifier and outer error recovery. Neither handler
logs the exception or synthesizes a successful conversation. Focused tests
exercise those exact handlers; the full loop, tool consumers, provider-error
redaction, cleanup, and host presentation are not yet qualified. Activation
remains blocked.

Patch 4 (`0004-tool-and-preflight-denial-propagation.patch`) adds tool execution
and preflight typed-error propagation. Mandatory-mode memory turn-start/prefetch
failures stop before optional-memory logging. Mandatory tool batches temporarily
use Hermes's existing serial dispatcher: worker exception collection and identity
are not yet qualified. Normal-mode concurrency and optional-memory behavior are
preserved. Tests execute complete native preflight and serial-dispatch functions
with inert dependencies; they do not qualify the whole agent loop, background
memory, ancillary callbacks, or provider-error disclosure.
The lower-level `model_tools.handle_function_call` exception-to-result handler
was a follow-on blocker at patch 4; patch 4's regular-tool tests use an inert
typed-denial dispatcher. Do not infer complete registered-tool coverage from it.

Patch 5 (`0005-native-tool-dispatch-denial-propagation.patch`) preserves typed
denials through the actual model-tools dispatcher and real registry. Both live
gates are checked before argument preparation. Catalog bridge operations bypass
execution middleware in the pinned implementation, so mandatory mode blocks them
before catalog access until a governed route is implemented. Normal-mode catalog
handling and ordinary tool errors retain their upstream behavior. Tests execute
the complete dispatcher, native registry and middleware, real Maya policy, and
the patch-4 serial caller together. Generic tool diagnostics and successful
result-transform payload validation remain unqualified; no activation is unlocked.

Patch 6 (`0006-final-tool-result-validation.patch`) adds candidate `tool_result`
middleware and requires all three live bindings. Registered-tool output is
validated before post-tool observation and after result transforms, using a
snapshot of actual executed arguments. Agent-owned tool middleware helpers also
validate final results. Maya implements the validator using existing result
checking/audit; no execution callback is supplied to it. This extends the draft
contract with `tool_result_validation` and `run_tool_result_middleware`, without
publishing a full compatibility marker. Patched generic tool-error paths stop
with fixed codes in mandatory mode. Normal mode preserves upstream behavior.

This is not complete diagnostics/DLP or whole-loop qualification. Model-provider,
compression, streaming, observer-internal, ancillary callback and later
conversation-layer transformations remain review gates. No installer is rebuilt.

Patch 7 (`0007-provider-diagnostic-boundaries.patch`) redacts scoped main-loop
provider summaries and error-hook request/error fields in mandatory mode, skips
both request debug dumps, and stops unexpected outer-loop errors before raw
traceback logging/history injection. Provider classification and retry/fallback
activation calls are unchanged; normal diagnostics retain upstream behavior.
Tests execute helpers and selected native statements and apply the complete
series. Streaming, earlier recovery branches, retry helpers, observer internals
and full-loop behavior remain unqualified. Activation remains blocked.

Patch 8 (`0008-summary-and-single-transport-attempts.patch`) authorizes each
native iteration-limit summary attempt, disables mandatory-mode internal stream
retries, and prevents the Anthropic inline stream-to-create fallback from issuing
a second request. Patched SDK request sites require explicit `max_retries=0`;
unknown/retry-enabled clients are blocked rather than silently modified.
Bedrock Converse is unqualified and blocked in mandatory mode. Typed summary and
stream-worker errors propagate without generic summary recovery or partial-success
conversion. Normal-mode dispatch/retries/fallback remain native.

The draft required contract adds `iteration_limit_summary`,
`single_transport_attempt` and `require_single_attempt_client`. No full marker,
wheel/pin update, installer rebuild or activation is unlocked. Tests execute
native functions and actual gates with inert SDKs; full SDK, worker identity,
effective-client route and output/recovery qualification remain open.

Patch 9 (`0009-defer-early-response-publication.patch`) suppresses native live
text/TTS, reasoning, interim and tool-generation delivery in mandatory mode.
Tracking reset discards unvalidated scrubber tails. Five direct conversation
display/progress paths are also guarded. Native response assembly and normal-mode
delivery remain unchanged; no second buffer or unvalidated replay is introduced.
The message builder's non-streaming reasoning callback/log and transport's
muted-stream display fallback are guarded too; replay fields remain native.
Tests execute complete native delivery methods and selected exact loop statements.
This is the first part of output hardening, not a final model-output validator.
Transforms, observers, returned messages/reasoning, persistence and diagnostics
remain qualification blockers. No capability marker or activation is unlocked.

Patch 10 (`0010-governed-final-model-disclosure.patch`) extends the existing
Hermes registry with a mandatory, validation-only `model_output` boundary.
Maya requires a fourth binding and authorizes disclosure using the existing
gateway and audit, separately from model egress. The native finalizer checks
content before its saves, again after transforms, and before returning the
result. Touched generic handlers propagate typed denials. Full-loop incremental
persistence, observer delivery, diagnostics and background work remain open.
No full compatibility marker, pin or installer changes.

1. Review outer auxiliary consumers and direct SDK paths, retain selected-provider
   metadata for automatic routes, and qualify adapter translations/SDK retries.
   Central sync/async attempt gates and plugin LLM facade coverage are now coded;
   this alone does not establish full-runtime coverage.
2. Wire mandatory mode before plugin discovery and agent construction in Maya.
   Handle mandatory failures separately in the main conversation and tool loops.
   Do not silently enable a missing plugin or turn a denied request into success.
3. Preserve trusted request context across supported workers; deny unsupported
   subprocess/background paths. Scheduled jobs require authenticated job identity;
   no implicit local-user identity. Keep unbounded tools denied.
4. Apply the complete series to the pinned fork, run its existing middleware,
   auxiliary, tool, streaming, retry, delegation, and scheduler suites plus offline
   Maya loop tests. Review before publishing the new immutable fork revision.
5. Build/hash the wheel from that revision, qualify the actual artifact, then
   update Maya's pin. Only then may the full capability marker be introduced.
   Installer and production-signing/qualification remain separate gates.

## Review and Test

In a clean, isolated checkout of the exact pinned Hermes revision:

```powershell
git apply --check <absolute-path-to-0001-opt-in-mandatory-middleware.patch>
git apply <absolute-path-to-0001-opt-in-mandatory-middleware.patch>
git apply --check <absolute-path-to-0002-governed-auxiliary-inference.patch>
git apply <absolute-path-to-0002-governed-auxiliary-inference.patch>
git apply --check <absolute-path-to-0003-stop-main-loop-on-governance-failure.patch>
git apply <absolute-path-to-0003-stop-main-loop-on-governance-failure.patch>
git apply --check <absolute-path-to-0004-tool-and-preflight-denial-propagation.patch>
git apply <absolute-path-to-0004-tool-and-preflight-denial-propagation.patch>
git apply --check <absolute-path-to-0005-native-tool-dispatch-denial-propagation.patch>
git apply <absolute-path-to-0005-native-tool-dispatch-denial-propagation.patch>
git apply --check <absolute-path-to-0006-final-tool-result-validation.patch>
git apply <absolute-path-to-0006-final-tool-result-validation.patch>
git apply --check <absolute-path-to-0007-provider-diagnostic-boundaries.patch>
git apply <absolute-path-to-0007-provider-diagnostic-boundaries.patch>
git apply --check <absolute-path-to-0008-summary-and-single-transport-attempts.patch>
git apply <absolute-path-to-0008-summary-and-single-transport-attempts.patch>
git apply --check <absolute-path-to-0009-defer-early-response-publication.patch>
git apply <absolute-path-to-0009-defer-early-response-publication.patch>
git apply --check <absolute-path-to-0010-governed-final-model-disclosure.patch>
git apply <absolute-path-to-0010-governed-final-model-disclosure.patch>
git apply --check <absolute-path-to-0011-recovery-and-background-denial.patch>
git apply <absolute-path-to-0011-recovery-and-background-denial.patch>
git apply --check <absolute-path-to-0012-native-persistence-and-raw-observer-boundaries.patch>
git apply <absolute-path-to-0012-native-persistence-and-raw-observer-boundaries.patch>
git apply --check <absolute-path-to-0013-outer-caller-denial-propagation.patch>
git apply <absolute-path-to-0013-outer-caller-denial-propagation.patch>
```

Do not apply to an arbitrary upstream revision or overwrite existing edits.
The Maya repository carries the reviewable patch instead of generated runtimes.

An opt-in offline full-loop denial probe uses the patched Hermes checkout,
Hermes's real `AIAgent.run_conversation`, Maya's actual policy gateway and
governance callbacks, and an inert recording transport. It verifies that a
denied model request is audited and never reaches the provider transport.
It does not bypass Maya's production startup guard, test real provider traffic,
qualify tools/background workers, or authorize a wheel/pin/installer update.

```powershell
$env:MAYA_HERMES_CANDIDATE_ROOT = '<absolute-path-to-isolated-patched-hermes-checkout>'
python -m unittest tests.test_hermes_candidate_denial -v
```

Without that environment variable, the probe is skipped in ordinary CI.

```powershell
python -m unittest tests.test_hermes_mandatory_middleware_patch tests.test_hermes_auxiliary_governance_patch tests.test_hermes_conversation_governance_patch tests.test_hermes_governance_plugin -v
python -m unittest tests.test_hermes_tool_preflight_governance_patch -v
python -m unittest tests.test_hermes_native_dispatch_governance_patch -v
python -m unittest tests.test_hermes_final_result_governance_patch -v
python -m unittest tests.test_hermes_provider_diagnostics_patch -v
python -m unittest tests.test_hermes_summary_attempts_patch -v
python -m unittest tests.test_hermes_output_deferral_patch -v
python -m unittest tests.test_hermes_model_output_patch -v
python -m unittest tests.test_hermes_recovery_background_patch -v
python -m unittest tests.test_hermes_persistence_observer_patch -v
python -m unittest tests.test_hermes_caller_denial_patch -v
```

Reference: [official Hermes middleware contract](https://hermes-agent.nousresearch.com/docs/developer-guide/middleware).
It documents the default fail-open behavior preserved outside mandatory mode.
The pinned source, not the latest documentation, controls this patch's baseline.
Patch 11 preserves typed mandatory failures through compression-summary recovery
and observer dispatch. It blocks native memory/skills background review before
thread creation, and rechecks at worker entry for targets prepared before opt-in.
Its finalizer caller propagates the block instead of downgrading it to success;
already validated saves are not undone.
Ordinary-mode behavior is retained. This is not a security observer hook: the
execution gates remain the enforcement boundaries. Other outer catches,
memory-manager jobs, delegation, cron, diagnostics and incremental persistence
remain unqualified. The dedicated test host/installer bind the eleven-patch wheel,
without changing the production pin or activation.
Also reviewed: [official plugin LLM access](https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access).

Patch 12 checks content before incremental session assignment, direct native
SQLite flushes, transformed JSON logs and trajectory writes. It reuses the
existing model-output gate; it does not establish a separate session-write
authorization contract or move Hermes history into Maya SMB memory. Mandatory
mode suppresses raw pre/post/error API observers; ordinary observer behavior is
preserved. Tests execute complete native helper methods with Maya gates and
inert storage sinks, not the real database backend or installed runtime.
Direct gateway writers, post-mapping SQLite rows, outer denial catches and
unqualified workers remain open. This does not change the production pin or
capability marker.

### Twelve-Patch Test Artifact

The dedicated test host now binds `0.17.0+maya.gov12.candidate.20261002`, built
offline from a fresh export of the same pinned Git tree with patches 1-12.
Wheel SHA256: `af979f8445e56e0379c7ad5252a228be5e7cf924c86f37c3c76a85ade867a323`.
The ignored `.codex-build/hermes-governance-candidate-gov12-20261002/` directory
contains the wheel and hash provenance. All 17 patched modules match source
bytes and compile; the extracted-wheel model-denial and recovery probes pass.
The synthetic model-denial fixture permits `model.output` for its test actor
so a persistence checkpoint does not obscure the intended egress denial.
It does not grant model egress or change production policy.
The installer qualification adds native persistence-denial and raw API observer
suppression checks to each of the existing six scenarios. Those scoped probes
do not qualify direct gateway writers, real database behavior, complete recovery,
live providers or clean-install lifecycle. Older installed artifacts are unchanged.
Build `0.1.0+govtest.20261002.013` passed all six packaged offline scenarios with
these additional checks. Builds 011/012 are superseded probe-development builds.
The delivered executable is unsigned local-smoke only; production remains blocked.

### Patch 13 Caller Scope

Patch 13 propagates canonical mandatory failures through incremental tool flush,
compression rotation and boundary callbacks, reviewed main-loop hook/flush catches,
and CLI new-session, boundary notification, manual compression and close-persist
helpers. Touched compression exits release the existing lock. Normal-mode
best-effort recovery is retained; no earlier mutation is undone. This does not
authorize compression's direct database writes, CLI shell/session changes,
other observers, shutdown completion or worker execution. Full conversation-loop
and frontend outermost error handling remain unqualified. Build 013 and the
twelve-patch wheel are unchanged. No production pin, marker or activation change.

### Patch 14 Effective Row Scope

Apply `0014-effective-session-row-validation.patch` after patches 1-13.
The complete native AIAgent flush validates the final `append_message` arguments
after multimodal and attribute-based tool-call transformations, using the existing
model-output gate. Typed denials propagate instead of entering the append warning.
`tests.test_hermes_session_row_patch` exercises native schema, transactions and
SQLite rows, approved mapping/deduplication, transformed-content denial and normal
mode. This is not a new session-write permission or direct SessionDB enforcement.
Earlier rows in a batch may already be committed when a later row is denied.
Build 013, the twelve-patch wheel and production activation are unchanged.

### Patch 15 Trusted Session Writes And Atomic Appends

Apply `0015-trusted-session-write-and-atomic-append.patch` after patches 1-14.
This candidate adds a fifth mandatory boundary through the existing registry,
atomic native append batches, and post-commit incremental flush tracking.
Maya registers its candidate callback explicitly and binds authenticated session
write authority; `session.write` is distinct from `model.output`. Unmapped writes
are blocked before mutation. The old four-boundary candidate host cannot activate
this patch; it needs stage 2 caller/context integration before rebuilding.
Run `tests.test_hermes_session_write_patch` for real SQLite/FTS/counter/rollback
checks. See `docs/architecture/hermes_session_write_contract.md` for scope and the
remaining frontend, rewrite/compaction, schema and audit reconciliation gates.
No production marker, pin, wheel, installer or policy grant is changed.

### Patches 16-17 Native Mutations And Scoped Callers

Apply `0016-native-session-mutation-descriptors.patch` after patch 15, then
`0017-session-writer-caller-denial-propagation.patch`. Patch 16 gates final session
creation/prompt metadata and prepared rewrite/compaction/clear operations. Patch
17 propagates mandatory failures through initialization, transcript and mirror
callers. Native storage, ordinary recovery and independent session ownership stay
intact. Both are source-only; gateway identity/session-index lifecycle and other
writers/callers remain unqualified. Do not rebuild a ready product from these alone.

Run `tests.test_hermes_session_mutation_patch` and
`tests.test_hermes_session_writer_callers_patch` for complete native SQLite and
scoped caller checks. The stage 2a matrix and remaining acceptance work are in
`docs/architecture/hermes_session_write_contract.md`.

### Patch 18 Metadata And Close Reporting

Apply `0018-session-metadata-and-close-reporting.patch` after patches 1-17.
Final end/reopen, cwd, model/config and accounting metadata use the candidate
session-write boundary. Mandatory accounting requires an existing session and
does not implicitly create one; ordinary native behavior is retained.
Native close propagates finalization failure after resource cleanup, not as
atomic lifecycle rollback. Run `tests.test_hermes_session_metadata_patch` for
real SQLite, denial/rollback, accounting and complete close-method checks.
Frontend bindings, remaining locks/callers, provisioning and audit reconciliation
remain open. No wheel, installer, production pin or activation changes.

### Patch 19 Compression Locks

Apply `0019-compression-lock-authorization.patch` after patches 1-18. Native
acquisition/release use scoped metadata descriptors. Mandatory compression stops
on missing/broken/denied lock storage or contention; release failures propagate
with fixed errors. Ordinary mode retains native fallback. Run
`tests.test_hermes_compression_lock_patch` for native SQLite and complete caller
checks. An inert compressor does not qualify full compression or a provider.
Denied release may leave a lock until expiry. Frontend bindings, other writers,
provisioning and audit reconciliation remain open; build 013 is unchanged.

### Patch 20 Unqualified Gateway Routing

Apply `0020-unqualified-gateway-session-routing.patch` after patches 1-19.
Mandatory gateway create/reset/switch stop before index or database access.
This is a fail-closed blocker while authenticated frontend/session mapping is
unfinished, not a functioning gateway replacement. Ordinary mode remains native.
`tests.test_hermes_authenticated_session_requests` covers those guards and the
explicit Maya-owned source-candidate Local API binding using bearer auth and real
SQLite. See Stage 2 Step 1 acceptance in the session-write contract. The old
four-boundary installed host, twelve-patch wheel and build 013 remain unchanged.

### Patches 21-23 Authenticated Intake And Bounded Handoffs

Apply `0021-telegram-polling-intake-registration.patch` after patches 1-20,
then `0022-bounded-request-executor-handoff.patch` and
`0023-bound-conversation-request-task.patch`. Patch 21 requires candidate polling
registration before application start. Patch 22 requires an explicit executor
handoff; Patch 23 binds only the main native conversation scheduling site to a
host-selected Task/executor lease. Ordinary scheduling remains native. Separate
background jobs receive no authority. Per-write policy still applies.

Run `tests.test_hermes_telegram_registration`, `tests.test_hermes_telegram_intake`
and `tests.test_hermes_session_handoff` for scoped SDK/SQLite/seam evidence.
SDK dispatcher tests require the exact pinned 22.6 test dependency and explicitly
skip if absent. These are source candidates, not live Telegram, full native
conversation, installed-product or production qualification. Stay in Stage 2
Step 1's second sub-item; see the session-write contract. Do not rebuild or change
production activation based on these tests alone.

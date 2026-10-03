# Hermes Streaming, Recovery, and Background Review

Date: 2026-09-29

Status: initial source review completed; remediation and full-loop qualification
remain open. This is not independent security certification or a complete review
of every Hermes provider, gateway, SDK, plugin, or scheduled-job implementation.

## Baseline and Method

Review target: the prepared Hermes 0.17.0 wheel attributed by the release process
to `b13e2fd6948a59eeb59fe618914147d97a2ee90a`, plus Maya's candidate patches 1-7.
Wheel SHA256:
`ee806be8b2f81359e36b114d03c4681da756150df522b30ebc45a29c2dbb04f2`.
This review does not independently establish equivalence to a clean fork build.

Unpatched sources were read from the prepared payload's `runtime/site-packages`.
Patched conversation-loop, memory-manager, middleware and tool-dispatch sources
were checked separately: untouched functions remain subject to these findings.
Line references below are artifact-relative, using unpatched source except where
explicitly marked patch 7. Source hashes at the end make the baseline identifiable.

Method: call-path inspection, bounded offline execution of selected native
functions, comparison with Maya's existing authorization contract, and review of
the [official agent-loop documentation](https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop/)
and [middleware documentation](https://hermes-agent.nousresearch.com/docs/developer-guide/middleware).
Latest documentation is orientation, not evidence that the pinned artifact has a
particular implementation. No real model, token, customer data, or network
transport was used by the offline probes. No runtime changes were made here.

## Findings

### R1: Additional Provider Attempts Bypass Per-Attempt Authorization

Priority: high; activation blocker.

The patched conversation loop authorizes once around `_perform_api_call`
(patch-7 `agent/conversation_loop.py:1161`). Inside that call,
`agent/chat_completion_helpers.py:2252` performs streaming retries and opens
fresh requests through `_call_chat_completions` / `_call_anthropic`. The actual
chat request is at line 1864; retry decisions and client replacement occur at
lines 2341-2460. Those internal attempts do not reenter execution middleware.
Similarly, `agent/codex_runtime.py:679` retries `responses.create` at line 688.
`agent/anthropic_adapter.py:2646` can change from streaming to `messages.create`
at line 2660 inside one outer call.

This is not evidence that the first normal request bypasses authorization.
It means the current outer gate cannot prove authorization of every subsequent
attempt, its effective client/route, or a policy change between attempts.
SDK-internal retries require separate inspection as well.

Required fix: gate each effective attempt at one documented native boundary, or
disable unqualified inner retries in mandatory mode and let the already-governed
outer loop perform them. Do not double-execute a single-use `next_call` or create
a parallel Maya retry engine. Qualify cancellation and client cleanup together.

Tests: initial allow then revoke/remove gate before retry; route/client change;
policy/audit crash; cancellation between attempts; no second transport call on
denial; normal-mode retry compatibility.

### R2: Iteration-Limit Summary Is a Direct Model-Egress Path

Priority: high; activation blocker.

`agent/chat_completion_helpers.py:1338`, `handle_max_iterations`, assembles a
summary request from conversation history and calls Codex, Anthropic, or chat
clients directly (lines 1437, 1499, 1503 and retry lines 1519, 1529, 1546).
It is reached through `agent/turn_finalizer.py:70` on budget exhaustion.
It does not call the central auxiliary router or execution middleware. Existing
auxiliary-call patch tests therefore do not establish coverage of this path.

Required fix: use the existing native execution gate for every summary attempt
with effective provider/endpoint/model and authenticated context. Until qualified,
mandatory mode must stop before this extra call and return a fixed bounded
failure through the existing failure contract, not silently send a summary.

Tests: iteration exhaustion, alternate API modes, malformed first response,
summary retry, missing identity, denial and audit failure before transport.

### R3: Streaming and Later Output Transformations Are Not Output Gates

Priority: high; activation blocker for response-disclosure claims.

`run_agent.py:4231` delivers text through `_fire_stream_delta` after think/context
scrubbing; `_fire_reasoning_delta` delivers reasoning separately at line 4284.
Tail flushes in `_reset_stream_delivery_tracking` and interim callbacks also
deliver content. Scrubbing known markup is not customer-policy authorization or
general secret detection. Model execution in Maya's plugin validates outgoing
requests, then returns `next_call(request)`; it is not a model-output validator.

`agent/turn_finalizer.py:316` allows `transform_llm_output` to replace the final
text, then passes it and conversation history to `post_llm_call` at line 342.
Patch 6's final *tool*-result gate does not cover these model-response paths.
The result also exposes `last_reasoning`, messages and route metadata.

Required fix: define a versioned model-output/disclosure contract before callbacks,
observers, persistence and publication. Initially buffer mandatory-mode output
and disable live text/reasoning/tail/interim publication until the final effective
output is validated. Disabling one streaming flag alone is not sufficient.
Do not label this as complete DLP; tool results and model output are distinct.

Tests: a secret split across chunks, tail flush, reasoning, interim commentary,
transform injection, callback failure, and no disclosure before validation.

### R4: Recovery Consumers Can Swallow Mandatory Denials

Priority: high; activation blocker.

`agent/context_compressor.py:1668` uses the patched auxiliary router, but its
generic catch at line 1700 can classify a mandatory denial as a summary failure,
retry on the main model, or enter cooldown/static-summary behavior. Patch 4's
preflight propagation cannot recover an exception already swallowed here.

`hermes_cli/plugins.py:1705`, `PluginManager.invoke_hook`, catches every callback
exception at line 1733, logs it and returns other results. Callers' typed handlers
do not help when this inner dispatcher consumes the denial first. Observers are
not authority, but a mandatory failure must not be downgraded to observer success.

Required fix: preserve canonical mandatory exceptions before generic recovery in
these consumers and observer dispatch. Keep ordinary best-effort observer behavior
outside mandatory mode. Prevent denial-triggered compression, fallback, or
success finalization without changing normal transport classification.

Tests: real mandatory exception through compression and hook dispatcher; no
second inference, cooldown-induced context loss, or final success after denial.

### R5: Provider and Cleanup Diagnostics Still Expose Arbitrary Text

Priority: high for secret-safe output; activation blocker.

Patch 7 protects selected exception summaries/hooks and two request-dump sites,
not all diagnostics. Its conversation loop still sends `api_kwargs` and raw
invalid-response details through `_invoke_api_request_error_hook` at line 1286;
the content-filter/refusal observer at line 1507 also receives request and output
text. Codex failure details are logged earlier at line 1227.

`agent/stream_diag.py:100` formats exception chains using `str(error)`; its retry
logger at line 134 includes error summaries, route and upstream header values.
`chat_completion_helpers.py:2353`, `2518`, `2671`, `2678` logs stream errors.
`codex_runtime.py:691`, `717`, `727` logs transport/terminal response details.
`turn_finalizer.py:152`, `159`, `193` logs tracebacks and adds raw cleanup error
text to the result. Recovery/fallback helpers also have generic error logging.

Required fix: extend fixed-code diagnostics to actual sinks, including invalid
response observers, response metadata, cleanup results and chained exceptions.
Keep original exceptions available privately to existing classifiers; truncation
and key masking are not sufficient redaction. The native debug-dump helper does
apply Hermes's own redactor, but that is not permission to persist full prompts.

Tests: synthetic sensitive marker in message/body/cause/header/route/cleanup
exception; absence from callbacks, logs, reports, returned results and files.

### R6: Background Context, Failure Reporting, and Shutdown Are Unqualified

Priority: high; activation blocker.

`chat_completion_helpers.py:358`, `1713`, `2565` creates provider worker threads
without explicit request-context copying. The outer gate executes on the caller;
placing new gates inside these workers without trusted propagation would fail
identity checks. Do not infer an actor from session ID or operating-system user.

`run_agent.py:1460` starts a background-review thread. The review constructs an
`AIAgent` in `agent/background_review.py:641`, inherits provider credentials and
conversation context, then runs a new conversation at line 750. Its outer generic
catch at line 807 reports a best-effort failure. A tool whitelist is not a Maya
job-authorization contract. Built-in memory and skill writes are consequential;
the existing Maya tool policy denies unbounded memory/skill-management tools.

`agent/memory_manager.py:475`, `516`, `576` queues prefetch/sync jobs, catches
provider errors, ignores the submitted future, and falls back to inline execution
on executor failure. Shutdown uses bounded draining, not proof every running job
has stopped. `run_agent.py:3136` additionally suppresses external-memory sync
exceptions. Maya's adapter `queue_prefetch` and `sync_turn` are deliberately
no-ops: this finding must not be used to start copying Hermes conversations into
Maya business memory. Preserve Hermes sessions/MEMORY.md/USER.md ownership.

Required fix: initially block unsupported review/job dispatch before agent
construction in mandatory mode. Supported workers need a captured immutable
authenticated job envelope, policy recheck, explicit lifecycle/failure reporting,
bounded shutdown and no late callbacks/writes after cancellation. Never silently
fall back to a different execution context. Preserve normal Hermes behavior.

Cron inventory found existing `copy_context` at `cron/scheduler.py:2163` and
`:2545`; this is useful transport plumbing, not proof of authenticated job
identity or permission. Cron, plugin async commands, gateway workers and provider
control-plane calls remain follow-on review scopes, not qualified by this pass.
Finalization also has implicit Kanban failure-state changes after budget
exhaustion (`turn_finalizer.py:85` onwards). Such worker-owned side effects need
explicit authorization; denying a named tool alone does not cover them.

Tests: absent/stale identity, actor isolation, cancellation before dispatch,
future failure visibility, executor creation/shutdown races, review construction
blocked, no late write/callback, unchanged no-op Maya conversation sync.

## Offline Evidence

Selected native functions were compiled directly from the reviewed source with
inert surrounding dependencies. Three checks passed:

1. `flatten_exception_chain` retains a synthetic sensitive marker.
2. Actual candidate `MandatoryMiddlewareError` is swallowed by native
   `PluginManager.invoke_hook`, with a warning and an empty result.
3. The same real error is swallowed by `_submit_background`'s inline fallback,
   with a debug log and no caller-visible failure.

These are bounded behavioral reproductions, not a full agent execution test.
Other findings are source-verified call paths, not exercised provider calls.
No new production readiness or compatibility evidence is claimed.

## Remediation Order and Acceptance

### Patch 8 Progress

R2's identified native summary dispatch sites now pass through model execution
middleware on every attempt, including the summary retry. Mandatory failures
propagate instead of entering generic summary recovery. R1's reviewed native
stream retry loops are disabled in mandatory mode, the Anthropic inline fallback
does not issue a second request, and SDK clients at patched request sites must
have explicit integer `max_retries=0`. Bedrock Converse is blocked before dispatch
until a qualified transport contract exists. Normal-mode behavior is retained.

These are scoped candidate-code closures, not production qualification. The
new test suite uses complete native helper functions, real mandatory middleware
and Maya summary policy with inert SDKs. It does not qualify SDK options,
effective-client route attribution, all providers/control-plane calls, full
outer-loop recovery, streaming output or trusted worker/background identity.
R3-R6 remain open. Activation remains blocked.

### Patch 9 Progress

R3's reviewed AIAgent early-delivery methods now suppress live text/TTS,
reasoning, interim messages and tool-generation names in mandatory mode.
Stream tracking reset discards scrubber state without publishing tails.
Native transports retain response assembly; no duplicate buffer or unvalidated
replay is added. Five direct conversation-loop display/progress paths are also
guarded. Ordinary-mode delivery remains unchanged.
Non-streaming reasoning callback/logging and the muted-stream display fallback
are also suppressed. Native message/reasoning assembly is preserved; this does
not authorize publication or persistence of those fields.

Focused tests execute the complete native delivery methods and the exact changed
display statements after applying all nine patches. A provider-thread test proves
these delivery methods suppress publication without assuming inherited actor
context; it does not qualify authorization inside provider workers.

R3 is not closed: a final effective-output/disclosure boundary still must cover
transforms, returned reasoning/messages, observers and persistence. API-response
hooks, other diagnostics, full-loop behavior and R4-R6 remain blockers. The
candidate suppresses only the identified sinks and does not establish DLP,
production support or authorization to activate.

### Patch 10 Progress

The candidate native `model_output` gate now validates finalizer payloads
before trajectory save, before finalizer session persistence, after native
transform hooks and before return. Maya uses the existing gateway to authorize
`model.output` disclosure and audits without recording output bodies. Typed
denials propagate through touched finalizer handlers, and normal mode retains
its prior behavior. Tests run the complete native finalizer with inert effects.

This closes only the reviewed finalizer ordering. The conversation loop still
has incremental persistence and raw observers before finalization; other
recovery, diagnostics, worker and background paths remain open. R3-R6 and
activation remain blocked pending those paths and full-loop qualification.

1. Close direct summary egress and inner retry authorization gaps; define
   authenticated request/worker context at the actual transport boundary.
2. Preserve mandatory failures through compression, observers and finalizers;
   cover invalid-response diagnostics missed by patch 7.
3. Buffer/validate effective model output before any disclosure; cover all delta,
   tail, reasoning, interim and transformed-final paths.
4. Disable unsupported background work in mandatory mode, then qualify explicitly
   supported jobs with lifecycle, result, cancellation and audit contracts.
5. Run complete-loop offline tests plus upstream/fork regressions for streaming,
   retries, provider adapters, memory, scheduler and cancellation. Only after
   independent review build and qualify a new immutable wheel and installer.

For each fix, retain opt-in mandatory behavior, normal Hermes regressions, real
native functions rather than only AST substitutions, and no network/credential
requirements in safety tests. Full model/tool loop, artifact and clean-install
qualification remain separate gates. No activation or pin update is authorized
by this review alone.

### Patch 11 Scoped Progress

The compression summary consumer now propagates typed mandatory denials before
provider classification, fallback, retry, cooldown or summary replacement.
The native observer dispatcher propagates the same denial before logging or
invoking later observers. This does not turn observers into security gates or
qualify outer hook callers, earlier observers, or earlier compression mutations.

Native memory/skills background review is blocked in mandatory mode before the
thread target is returned and before worker imports, approval setup or AIAgent
construction. The second check covers targets prepared before opt-in. A fixed,
allowlisted readiness code identifies the block; no invented worker identity is
introduced. The finalizer caller propagates this typed failure rather than
swallowing it; previously validated saves are not rolled back. Normal-mode
summary fallback, observer best-effort behavior and
background thread construction retain their native behavior.

Tests apply all eleven patches to pinned fixtures and execute complete native
consumer methods/module with inert dependencies, including Maya policy denial.
They are not full-loop recovery or installed-artifact qualification. R4-R6 remain
open: memory-manager jobs, delegation, cron, outer catches, worker attribution,
diagnostics and incremental persistence still require review and tests. The
dedicated test host now requires the eleven-patch wheel. A separately versioned
eleven-patch wheel was subsequently built and passed scoped extracted-artifact
model-denial and recovery-consumer probes, with all 17 patched modules matching
the reviewed source. It does not qualify full-loop recovery or installed startup.
The dedicated test installer adds scoped compression-consumer and
finalizer-background denial scenarios. This does not close R4-R6 or qualify the
normal Standard installer. No production runtime pin, capability marker or
activation changes.

### Patch 12 Observer/Persistence Review

The user reports all six build 010 installed scenarios passed: model denial,
model allow, tool denial, tool allow, compression denial and background denial.
These scoped synthetic/offline checks do not establish production qualification.

Patch 12 is a source-only candidate applied after patches 1-11. It checks the
effective messages/history before `_persist_session` assigns session state and
before `_flush_messages_to_session_db` creates rows, updates cursors or appends.
The latter check also covers direct helper entry from tool-loop and compression
callers. JSON logs are checked after native cleanup/redaction; trajectory source
and converted trajectory are checked before their file sink. Typed mandatory
errors escape the touched JSON error handler without verbose payload logging.

Raw `pre_api_request`, `post_api_request` and `api_request_error` observer
callbacks are suppressed in mandatory mode. This prevents these callbacks from
receiving unvalidated request/response bodies; it does not turn observers into
security gates or stop payload construction at their callers. Ordinary-mode
observer dispatch and persistence remain unchanged.

Fifteen tests execute complete pinned native helper methods and observer
dispatch with actual Maya policy/audit gates and inert writers. They cover
denial before storage, missing identity/gate, audit failure, native user
override, transformed content, allowed SQLite deduplication, disabled-store
no-ops and normal-mode controls. This is not real SQLite or full-loop testing.
The gate is existing `model.output` content authorization, not a complete local
session-write policy. Hermes retains conversation history and MEMORY.md/USER.md;
Maya's governed business memory remains a separate subsystem.

Remaining source inventory and qualification blockers:

- Native message cleanup/user overrides can mutate input before the check;
  denied operations do not promise rollback of earlier in-memory mutations.
- SQLite per-row mappings occur after the whole-message check and require
  effective-row validation against the actual backend.
- Direct writers bypass these helpers: `gateway/session.py` session creation
  and append, `gateway/mirror.py` append, `gateway/slash_commands.py` session
  clone/append, and `gateway/platforms/api_server.py` session creation.
- Compression, tool executor and CLI flush callers need full-loop typed-denial
  propagation tests; observer outer catches and `on_session_start` are not
  qualified by dispatcher tests.
- Generic native database diagnostics, other observer/persistence sinks,
  memory-manager jobs, delegated/scheduled workers and cancellation remain open.
- Synthetic installed checks do not qualify live providers, managed shell,
  clean-install lifecycle, updates, rollback or backup/restore.

Patch 12 is now in a separately versioned twelve-patch candidate wheel. Build
010 remains unchanged. The next dedicated test installer binds the new hash
and adds scoped native persistence-denial and raw API observer checks. No
production activation, pin, capability marker or support claim changes. R4-R6
remain open. Next qualify caller propagation and direct writers; the new
artifact is only an intermediate test build, not closure of those paths.

Build `0.1.0+govtest.20261002.013` subsequently passed all six packaged offline
scenarios, each including persistence-denial and raw-observer checks. The native
SessionDB is opened only in isolated test state, and observer registration uses
PluginContext. Zero denied append calls does not qualify allowed SQLite writes,
direct gateway writers or full-loop denial propagation. Builds 011/012 failed
probe development and are superseded. The executable remains unsigned local-smoke
only; no clean installed-desktop or production qualification is claimed.

### Patch 13 Caller Review

The user reports all six build 013 installed scenarios passed with the patch-12
persistence/observer checks. Patch 13 is the next source-only candidate.

Reviewed swallowed denials occur in the tool progress flush helper, the
conversation-loop pre-tool flush, compression rotation's nested flush and outer
database handler, context/memory/event compaction callbacks, session-start and
pre/post API hook callers, and CLI session-boundary/new-session/manual-compression/
close-persist helpers. The patch checks canonical typed failures before warning,
printing, generic recovery or continuing. Touched compression exits release the
existing native lock. Ordinary-mode recovery remains best-effort.

Complete native caller tests use inert storage/callbacks and one actual Maya
policy-denied persistence call through the tool progress helper. The main-loop
flush test executes its exact native catch body, not the entire loop. Two new
pinned snapshots contain unchanged CLI and compression source for offline CI;
they are test evidence, not installer payload or replacement runtime code.

This is not a transaction rollback: prompt rebuilding, memory notifications or
database mutations before a later boundary denial can already have occurred.
Compression in-place archive/rotation writes and prompt snapshots still need
their own authorization contract; post-mapping row validation and direct gateway
writers remain open. Other catches, frontend command/exit wrappers, provider
diagnostics, worker jobs and full-loop cancellation/shutdown remain unqualified.
No new wheel/installer, production pin, compatibility marker or activation.

## Source Hashes

SHA256 of the prepared unpatched source bytes:

| Path | SHA256 |
| --- | --- |
| `run_agent.py` | `7a36be48ffdc0fe62b855263683d55c1c7138cc65acf597175920fcf86b45bd5` |
| `agent/chat_completion_helpers.py` | `ff17762913d3e38aefa57fa22b56048f99d09fc18d189ab6441bf9c69433a76c` |
| `agent/stream_diag.py` | `80405602a3c459ee2ebfd6a70c22537e533314600847475fd1c81bd08dfe05a2` |
| `agent/turn_finalizer.py` | `71ddf4e5245fe1302056290b95011aefc57909ad12485f8198a64ff46dbc709c` |
| `agent/background_review.py` | `afb05223518c3ea945bdb40da1af133431c1eb86146dd80c43054777a131170c` |
| `agent/context_compressor.py` | `c83042885c66f13b9ffb3b94da763f8a4240c6bfdc81b9e5c98ff172a20d8733` |
| `agent/agent_runtime_helpers.py` | `1a0fb199102e02261d22bfaa7b64e5d3bb8e9fd6642696551e6b0ff7f278dac9` |
| `agent/codex_runtime.py` | `3878e102cd53dd7e4dd5d767ca5b1e0f0f2778e16e521f4e37a11a1826c1d357` |
| `agent/anthropic_adapter.py` | `c7541f69e5dd8515c6b8cf4afd93e38e66d25fbab86eef2a6b32a2249fb2b054` |
| `hermes_cli/plugins.py` | `fb60534b86b403778232eb63842bba563448a15419b1a43c7fced2274b7601c4` |
| `cron/scheduler.py` | `42847e1679612c5f7324259240b64501419e49fb7c86266840f790398ba4ae89` |
## Patch 14 Row Mapping Review

The native incremental flush now checks effective append arguments after mapping,
including attribute-derived tool-call arguments and multimodal summaries. Typed
denials escape its generic append handler. Tests run native SQLite schema and
storage rather than inert append mocks, and retain ordinary Hermes behavior.
This source-only candidate is not in installer build 013. It does not gate direct
SessionDB writers, authorize rewrites/deletion, make incremental batches atomic,
or qualify frontends/workers. The staged session-write work is recorded in
`hermes_native_governance.md`; production activation remains blocked.

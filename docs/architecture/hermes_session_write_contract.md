# Candidate Hermes Session-Write Contract

## Status

The [2026-10-03 assessment](maya_governance_integration_assessment_20261003.md)
and [approved integration plan](maya_governance_integration_plan.md) identify
complete-caller gaps beyond the scoped source tests. The user approved G0-G7 on
2026-10-03; G0 is current and the earlier sequence is superseded. Session-write
contracts remain in force. No wheel/installer rebuild or activation is authorized.

Approved implementation direction; stage 1 is a source-only candidate, patch 15
after patches 1-14 at Hermes commit `b13e2fd6948a59eeb59fe618914147d97a2ee90a`.
It is not upstream-qualified or installed-product qualification. Production
activation, the production pin, candidate wheel and installer build 013 are
unchanged. Hermes owns conversation storage; Maya SMB memory remains separate.

## Trusted Authority

Contract: `project-maya.hermes-session-write.v1`. The native `session_write`
boundary uses the existing middleware registry and Maya action gateway.
It is mandatory alongside the four existing candidate boundaries; missing or
removed callbacks stop all mandatory dispatch rather than falling back.

An authenticated Maya host binds `bind_request_identity` and `bind_session_write`
before a storage operation. The immutable binding contains request ID, session ID,
exact resolved database path, allowed operations and classification. The actor
comes only from the authenticated identity. Thread/task ownership prevents an
inherited context authorizing an unqualified worker. A scope lease expires on
exit, including exceptional exit, so a captured context cannot outlive the request.
This is trusted in-process host authority, not a sandbox against arbitrary Python.
Unknown/unbounded execution tools remain denied.

The gateway action is `session.write`, target `session:<id>`. Operations are
`create`, `append`, `rewrite`, `compact`, `delete`, and `metadata`. Authorization
for `model.output` never substitutes for this permission. Schema provisioning is
a distinct setup concern, not a conversation append or LLM-supplied operation.
No production policy grants are added by this change.

## Atomic Appends

Native `SessionDB.append_messages` prepares the complete batch using the existing
append serialization and field mappings. It validates the final serialized values
before `BEGIN IMMEDIATE`. Immutable prepared values are the actual inserted rows;
callbacks receive copies and cannot replace the authorized batch. The write uses
the native SQLite transaction/rollback machinery, inserting all rows and updating
session counters together. Single-row `append_message` retains its public signature
and row-ID return value by delegating to this batch writer.

Mandatory incremental AIAgent flush gathers all pending mapped rows, invokes one
batch, and updates identity deduplication state and cursor only after commit.
Database failures propagate as fixed mandatory errors, without raw diagnostics.
Ordinary-mode incremental behavior remains best-effort. Empty batches are no-ops.

Any native `_execute_write` call lacking a reviewed descriptor is rejected in
mandatory mode before transaction start. Stage 1 supplies only append descriptors.
Create, rewrite, compaction, deletion, metadata, locks and other direct writes are
therefore blocked. This is not a functioning replacement installer yet. Direct SQL
outside `_execute_write`, schema repair/migrations and frontend denial handling
still require inventory and qualification.

## Audit Semantics

The existing local audit records authorization/validation attempts before writes,
using fixed reason codes, hashed targets/request correlation, actor, classification
and operation. It does not log rows, conversation text, database paths or secrets,
and it does not claim that an authorized write committed. Audit failure prevents
transaction start. A subsequent SQLite failure can leave an authorization attempt
in the audit but zero committed rows; this is intentional, not a commit receipt.

Audit and SQLite are separate stores. Durable commit/outcome reconciliation remains
a production blocker. A later stage must add transactionally durable outcome
correlation or a reviewed outbox design; do not label an authorization audit as
proof of commit or assume a cross-store atomic transaction.

## Qualification And Next Stages

Stage 1 tests use native schema, transactions, counters and FTS rows. They cover
allowed batches/restart, denied first/middle/last rows, final serialization,
second-row SQLite failure, flush-state rollback/deduplication, missing/removed
callbacks, policy/audit failure, session/path/operation/actor mismatch, captured
context expiration, thread/task isolation, unmapped direct writers and ordinary
mode. Home discovery and unrelated read sanitization are inert; no live provider,
customer state, installed artifact or background execution is qualified.

Stage 2 must:

1. Bind authenticated frontend requests and explicitly authorized setup/maintenance
   identities without deriving authority from DB records, model output or tool args.
2. Prepare final create/metadata/rewrite/compaction/delete descriptors. Validate
   complete replacements before destructive statements; preserve atomic rollback.
3. Integrate CLI, gateway, mirror, compression and close/recovery callers. Typed
   denials must escape outer catches without retry, fallback or premature state
   updates. Unqualified worker and direct-SQL paths stay blocked.
4. Qualify audit outcome reconciliation and provisioning/migration boundaries.

Stage 3 builds a separately versioned wheel from the pinned source with the full
reviewed series, binds all five callbacks before Hermes construction, then rebuilds
the isolated governance-test installer. Installed tests must exercise real SQLite
batch/caller paths, not only middleware fixtures. Signing, lifecycle and independent
production gates remain required even if those candidate checks pass.

## Stage 2a: Reviewed Native Mutations And Callers

Patches 16-17 extend the source candidate after patch 15. They do not change
the installed wheel, build 013 or production activation.

| Native Entry | Descriptor | Scoped Result |
| --- | --- | --- |
| `_insert_session_row` / `create_session` | `create` | Final serialized metadata checked before insertion |
| `update_system_prompt` | `metadata` | Prompt snapshot checked before update |
| `replace_messages` | `rewrite` | Complete immutable replacement prepared before deletion |
| `archive_and_compact` | `compact` | Complete immutable replacement prepared before archival |
| `clear_messages` | `delete` | Explicit permission to clear messages, not delete sessions/files |
| Other native write methods | Unmapped | Still blocked in mandatory mode |

Replacement and compaction share the native field mapping, with timestamps,
reasoning, tool calls, Codex fields and platform IDs serialized once. Actual
inserts use those prepared values, so no transformation happens after validation.
Normal-mode native mappings remain intact. Mandatory transactional failures use
fixed error codes after rollback rather than exposing SQLite exception details.

Reviewed caller integration:

- Complete native `_ensure_db_session` propagates typed denials and fixed storage
  failures, without next-turn fallback. The mandatory incremental flush may now
  invoke that descriptor-backed initializer under explicit `create` authority.
- Native `SessionStore.append_to_transcript` and `rewrite_transcript` propagate
  denials rather than silently discarding them. Their ordinary recovery remains.
- Both native mirror layers propagate mandatory failures, and close their native
  SQLite connection in the existing finalizer. Normal mode remains best-effort.

Missing native databases also block reviewed initialization/flush/transcript writes
in mandatory mode rather than returning apparent success. Intentional `skip_db`
no-ops remain distinct from a required write to an absent database.

Tests use actual native SQLite schema/transactions/FTS and complete caller
methods/functions. Host identity and session binding are supplied explicitly by
the synthetic harness. Mirror session lookup is inert routing, not proof of a
connector user's identity. These are not full gateway/CLI entrypoint tests.

Session creation is its own authorized transaction. A successful create can
remain if a subsequent append fails; atomic append/rewrite does not claim atomic
rollback of an entire user turn or lifecycle transition.

Remaining work before wheel/installer integration:

1. Authenticated Maya frontend bindings and owner/session mapping, plus gateway
   session-index JSON creation/reset/switch ordering. Some native gateways save
   that index before SQLite authorization; typed catch propagation alone does not
   make those operations safe or qualify their frontend.
2. Remaining CLI, slash-command/API-server callers, rewind, compression locks,
   remaining metadata and worker paths. Unmapped native writes stay
   blocked. Other outer catches can still swallow denials or mutate earlier state.
3. Schema provisioning/repair/migrations and direct SQL outside `_execute_write`.
4. Durable audit outcome reconciliation and full clean-install/lifecycle tests.

Do not infer actors from session records, allowlist an entire frontend to make
tests pass, or register a privileged fallback identity. The five-boundary candidate
host and installed probes are updated only after these required paths are reviewed.

## Stage 2b: Scoped Metadata And Close Reporting

Apply patch 18 after patches 1-17. This remains source-only; the twelve-patch
wheel, installer 013 and production activation are unchanged.

| Native Entry | Descriptor | Scoped Result |
| --- | --- | --- |
| `end_session` / `reopen_session` | `metadata` | Exact end/reopen values checked; first end reason still wins |
| `update_session_cwd` | `metadata` | Final cwd checked before update |
| `update_session_meta` / `update_session_model` | `metadata` | Serialized config and model checked before update |
| `update_token_counts` | `metadata` | Complete delta/absolute counters and costs checked before update |

Mandatory accounting no longer implicitly creates a session. Its transaction
requires an existing session and fails with a fixed error if absent. Ordinary
mode retains native implicit creation. Nested serialized metadata is checked
for secrets; denied writes do not begin a transaction. SQL failure rolls back.

The complete native `AIAgent.close` now propagates final session-write denial or
a fixed storage failure after its existing resource cleanup. Cleanup deliberately
continues: authorization denial must not leave clients or processes alive. This
is not atomic lifecycle rollback; memory cleanup and other earlier state changes
are not reversed. Frontend shutdown callers and background cleanup are not
qualified by testing this method.

Ten scoped tests use real native SQLite and the complete close method with inert
resource cleanup. They cover allowed/denied metadata, secret rejection, accounting
semantics, absent-session refusal, SQL rollback, close propagation and ordinary
recovery. Identity binding remains synthetic, not authenticated frontend evidence.

Stage 2 acceptance remains incomplete:

1. Authenticated frontend/setup/maintenance bindings: incomplete.
2. Native descriptors: partially implemented; additional writers, locks and
   direct SQL require review.
3. Caller integration: partially implemented; session-index ordering, full
   frontend recovery and worker paths remain open.
4. Durable audit outcome reconciliation and provisioning qualification: incomplete.

An authorization audit is still not a commit receipt. Do not rebuild or activate
the five-boundary candidate until the required integration gates are satisfied.

## Stage 2c: Compression Lock Authorization

Patch 19 follows patches 1-18. Native acquisition and release use `metadata`
authorization for the exact bound session/database. The descriptor includes the
lock operation, holder and final acquisition/expiry timestamps. Reclaiming an
expired lock is limited to that session; ownership checks and the native atomic
delete/insert transaction remain intact. SQL failure rolls back reclamation.
Mandatory mode rejects empty/non-string holders and invalid/nonpositive lifetimes
before writing; nonfinite expiry values are rejected by payload validation.
The holder is native concurrency state, not a source of authenticated identity.

The complete native compression caller no longer continues unlocked on denied,
missing or broken storage in mandatory mode. Contention stops with the fixed
`session_lock_busy` error before invoking the compressor. Release denials and
generic storage failures propagate with fixed errors rather than raw diagnostics.
Ordinary-mode recovery remains unchanged. Existing status/diagnostic callbacks
before acquisition and full compression/state rotation are not qualified here.

Tests use real native SQLite and the complete compression function, with an inert
compressor at its summary boundary. They check lock ownership, expiry, rollback,
secret rejection, missing context/callbacks, session mismatch, denial propagation,
contention, successful release and ordinary fallback. They do not test a provider,
background worker, authenticated frontend or complete compression transaction.

Release authorization is not a privileged cleanup bypass. If release is denied,
the lock may remain until its expiry; earlier state changes are not rolled back.
Durable outcome reconciliation and recovery qualification remain required.
Stage 2 stays partial. No wheel, installer 013 or production activation changes.

## Current Work: Stage 2 Step 1

The agreed order is authoritative. Steps 2-3 received earlier scoped source
changes before Step 1 was completed. That does not satisfy Step 1 or authorize
further reordering. Current work stays on Step 1 until its acceptance criteria
are met. Any proposed deviation requires explicit approval before implementation.

### Scoped Local API Binding

`BearerTokenAuthenticator.authenticate_identity` maps a validated secret-store
token to a host-configured actor/classification. Existing boolean authentication
remains compatible; production composition supplies its configured actor to the
authenticator. No identity is extracted from headers, prompts or session records.

An explicitly acknowledged `CandidateSessionRequestBinding` may be supplied to
the existing Local API. It binds one host-approved owner, fixed Hermes session,
preprovisioned exact database and frozen operations. The request cannot select
these or lower classification. Boolean-only authenticators cannot activate it.
It requires the five-boundary native candidate contract and active callbacks.
Session-write permissions still require a gateway decision for every mutation.

Each request has a fresh host-generated ID, with scope revocation on return/error.
Overlapping use of the same binding is denied; this is not a global multi-user
session registry or worker qualification. Request idempotency keys are hashed
before forwarding to runtime/audit surfaces; they do not become authority.
Authentication binding is audited through the existing sink with hashed session
and request correlation, no tokens/prompts/paths. Audit failure prevents dispatch.
This records binding, not commit outcomes or complete authentication auditing.

The normal product composition does not select this candidate option. No installer,
environment switch, production marker or policy grant is added. Source tests cover
the handler and loopback HTTP using real bearer comparison and native SQLite,
with a storage-only execution harness; they do not qualify a complete Hermes loop.

### Native Gateway Routing

Patch 20 follows patches 1-19. Mandatory `get_or_create_session`, `reset_session`
and `switch_session` are rejected before session-key generation, entry mutation,
index saving or database access. A supplied Local API binding cannot authorize
these unqualified frontend transitions. Ordinary native behavior is unchanged.
This prevents the reviewed premature-index paths; it does not implement allowed
gateway routing or qualify every index writer/reader and frontend outer catch.

### Step 1 Acceptance

| Requirement | Current Evidence | Status |
| --- | --- | --- |
| Local API authenticated actor binding | Scoped handler/HTTP plus native SQLite tests | Partial: source candidate, not full product loop |
| Owner/session/database/operation binding | Fixed host-selected single-owner binding; body/header spoofing and expiry tests | Partial: multi-user mapping and rotation remain open |
| Native gateway index ordering | Create/reset/switch blocked before any mutation | Blocked: allowed authenticated transitions not implemented |
| CLI and connector frontend identity | No privileged fallback | Incomplete |
| Candidate CLI request authentication | Explicit CLI through bound Local API; token stdin and readiness/contract enforcement | Partial: normal CLI and connectors unchanged |
| Explicit setup/maintenance authority | No identity inferred from OS username, environment or records | Incomplete |

Next work remains inside Step 1: authenticated gateway/CLI/connector owner mapping,
safe allowed index transitions, and explicit setup/maintenance identity flows.
Do not resume remaining descriptors/caller work or outcome reconciliation until
Step 1 is complete or an alternative sequence is explicitly approved.

### Scoped CLI Continuation

`project_maya.hermes_plugins.session_client` is an explicit source-candidate CLI,
not a replacement for the normal product CLI or an installer shortcut. It reads
the existing JSON config and a user-selected request file; the local API token is
accepted only through stdin. No actor, session, database or permissions are CLI
arguments. Identity and ownership remain host-selected at the authenticated API.

The client first authenticates `GET /v1/session-binding`, which reports only the
fixed request-binding contract and `source_candidate_only` label. It then sends
`POST /v1/run` with the required binding header. Both responses must carry the
same contract and candidate label. The API rejects a required binding when it is
absent; removing the binding after readiness cannot silently execute unbound.
Readiness binding is audited but performs no runtime execution or SQLite writes.

The client accepts only a configured loopback address/port with remote access off,
uses the standard HTTP client without proxy discovery, redirects or automatic
retries, bounds request/response sizes and rejects token echoes (including JSON
escaped values) or secret-bearing results. Error output uses fixed codes, never
server diagnostics, token values, raw request files or argument-error text.
Tests use real loopback HTTP, existing bearer authentication and native SQLite;
transport fixtures additionally check redirect refusal and decoded token rejection.
No provider, live connector or full model/tool loop is qualified.

This remains Step 1 work. Normal CLI authenticated routing, gateway/connector
owner mapping, allowed index transitions and explicit setup/maintenance identity
flows remain incomplete. There is no new privileged identity, policy grant,
Hermes patch, wheel, launcher change or installer rebuild in this continuation.

### Pinned Gateway Inspection: Step 1 Design Decision

Source inspected at `b13e2fd6948a59eeb59fe618914147d97a2ee90a`, not the
latest upstream or an unspecified local checkout. This is source evidence,
not runtime qualification or approval of a new authority contract.

| Pinned Source | Finding | Binding Consequence |
| --- | --- | --- |
| `plugins/platforms/telegram/adapter.py:2341-2418` | Native polling exists; webhook mode refuses a missing secret and supplies it to the Telegram library | Authentication must originate at the configured transport intake; constructing a `MessageEvent` is not proof of verified intake |
| `plugins/platforms/telegram/adapter.py:6995` | Event construction obtains sender/chat IDs from the Telegram message | Names, message text, forwarded identity, and serialized session sources must not establish a Maya actor |
| `gateway/authz_mixin.py:176` | Native access policy includes pairing, allow-all flags and chat-only admission, including traffic without a user ID | A native allow result does not prove an individually mapped Maya principal; Maya needs explicit stable user and chat constraints |
| `gateway/platforms/base.py:4229` | Adapter dispatch can queue tasks, rewrite topic routing and process active-session commands | Wrapping only `GatewayRunner._handle_message` misses earlier state changes and handoffs |
| `gateway/run.py:7308` | Pre-dispatch plugin hooks run before native user authorization; internal events skip it | Observer/plugin results and `internal=True` cannot confer session-write authority |
| `gateway/run.py:12852` | Executor dispatch copies context variables into another thread | Current thread/task-owned Maya bindings correctly reject that copy; blanket context inheritance must not be enabled |
| `gateway/session.py:997,1271,1323` | Create/reset/switch save the index before SQLite operations; an existing-session resume also updates and saves the index | Patch 20 stays in place until allowed index transitions have explicit authorization and failure handling |

The existing connector manifest exposes identity-mapping metadata, but messaging
readiness does not authenticate received events. Neither can substitute for a
verified native transport boundary. Session-index contents may route an already
authenticated principal; they must not authenticate one or grant ownership.

Approved Step 1 sub-sequence (user approval received before implementation):

1. Define a source-candidate intake contract for customer-owned Telegram polling,
   initially private text messages only. A trusted adapter maps the exact bot
   instance, stable sender ID and chat ID through host-approved configuration to
   a Maya actor/classification. Missing mappings, anonymous/channel/group traffic,
   synthetic events and unsupported ingress remain blocked. No live bot setup or
   network authorization is performed by the qualification tests.
2. Define and test a bounded host-only handoff to the specific native request task
   and model executor. The recipient rebinds authority locally; it does not inherit
   general worker privilege. Handoffs are scoped to one request/session/database,
   expire on completion/cancellation, cannot widen operations, and do not authorize
   background reviewers, recovery replay or arbitrary tool-created workers.
3. Replace the reviewed gateway routing blockers only after owner-scoped index
   transitions are authorized before mutation. Test native create/resume/reset/
   switch, cross-owner refusal and index/SQLite failures. JSON and SQLite are
   separate stores: define recoverable failure behavior without claiming atomic
   cross-store commits or silently taking authority from either store.
4. Complete the normal CLI and explicit setup/maintenance identity paths, then
   assess every Step 1 acceptance row before proceeding to Steps 2-4.

This sequence narrows the first connector qualification; it does not declare
other product connectors removed or healthy. Approval must precede implementing
the new intake/handoff/index contract. Current candidate bindings, patch 20,
wheel, installer 013 and production gate are unchanged.

### First Approved Item: Source Intake Contract

`project_maya.hermes_plugins.telegram_intake` implements the explicit candidate
`project-maya.telegram-polling-intake.v1` callback contract. The trusted host
selects an existing native polling adapter/application/bot and an immutable
mapping from exact stable user/chat IDs to Maya identities. Bot identity and
connection objects are checked again on each callback. Webhook mode, replacement
connections and custom Bot API endpoints are not admitted. No second poller,
token storage, network setup, bot registration or production switch is added.

The callable is for registration at the trusted polling application's intake,
not a public API, tool or plugin entrypoint. Transport provenance comes from
that registration boundary; structurally matching Python objects do not prove
Telegram authentication. Arbitrary in-process Python remains outside the sandbox
claim. The scoped native registration added below does not qualify live transport.

Private plain-text messages require both user and chat mapping. Commands, replies,
forwarded messages, anonymous/bot senders, groups/channels, edited/business updates,
media and callback queries remain blocked. Message fields cannot select actor,
classification, session, database or operations. A mapped identity is audited
through the existing sink before the fixed host-selected consumer runs; audit
failure prevents dispatch. Records exclude text, bot credentials and raw platform
IDs. This is an allowed-binding audit, not complete rejected-intake auditing.

The consumer is a trusted host callback, not a request-selected handler. Do not
connect it to native text batching, plugin dispatch or model execution until the
scoped handoff is qualified: copied identity context alone is not a qualified
request lease. This module does not solve queued delivery or revoke arbitrary
identity context copied by an unqualified consumer.

Identity scope ends on callback completion/error/cancellation. No session-write
scope is created, and no worker authority is delegated. The monotonic update
high-water mark refuses duplicates/out-of-order updates within this callback
instance and consumes admitted updates before dispatch. It is not durable replay
protection; restart, polling offsets, failure recovery and queued delivery need
qualification before activation. Concurrent callback dispatch is refused rather
than silently sharing context. Failed uncertain dispatch is not automatically retried.

Thirteen tests cover the contract with polling-shaped fixtures and actual local
audit files, plus native SQLite rejection of an authenticated but session-unbound
request. The Telegram SDK is not installed in the development test environment;
no SDK dispatcher, live Telegram connection or full native message pipeline was
tested. The first item is therefore partial source evidence, not completed ingress
qualification. Next work stays on this item: native polling callback registration
and its provenance tests, before the approved scoped executor handoff. The Step 1
acceptance table, wheel, installer and production gate remain incomplete/unchanged.

### First Item Continuation: Native Polling Registration

Patch 21 follows patches 1-20 at the same pinned Hermes commit. In mandatory mode,
native Telegram `connect` requires a host-supplied
`_maya_polling_intake_factory` with the exact
`project-maya.telegram-polling-registration.v1` contract. After SDK initialization,
but before `Application.start` or polling, it invokes that factory. Missing,
failed or mismatched factories and configured webhook mode stop startup. Ordinary
mode retains the native handler catalogue. This is a source patch only; the
user's Hermes checkout, twelve-patch wheel and installer 013 are not modified.

`CandidateTelegramPollingRegistration` implements that host factory using the
existing SDK Application, bot and updater. It requires SDK 22.6 (the Hermes pin),
stopped application/updater, no SDK persistence and serial update processing.
It replaces the candidate application's ordinary handlers with one blocking
`TypeHandler`, using `ApplicationHandlerStop` on both allow and deny. It does not
forward into native text batching or model execution. Non-SDK update objects,
changed registration, later catalogue changes, invalid transport and failed intake
are rejected without falling through to ordinary handlers or raw SDK error hooks.
Rejected-intake audits use fixed codes and no raw update or platform IDs. If that
audit fails, dispatch still stops. The consumer remains a trusted host choice;
arbitrary Python mutation or installing a preceding handler is not sandboxed.
Do not expose SDK catalogue mutation to unqualified plugins or tools.

The implementation follows the pinned SDK documentation for
[handler ordering](https://docs.python-telegram-bot.org/en/v22.6/telegram.ext.application.html#telegram.ext.Application.add_handler)
and [blocking handler stop](https://docs.python-telegram-bot.org/en/v22.6/telegram.ext.applicationhandlerstop.html).
Nine additional tests run the real 22.6 Application dispatcher and Update/Message
types, with a synthetic SDK request implementation supplying only `getMe` and
socket connection attempts forbidden. They cover allowed identity mapping, denied
messages, synthetic non-SDK objects, replay/failure, changed registration, ordinary
mode and the exact added native registration block. The full native `connect`
method, polling origin authentication, transport failures, reconnect, remote bot
command registration and webhook cleanup are not exercised or authorized by these
tests. The seam tests execute the added block, not the complete native method.

The SDK was downloaded with approval into an ignored, isolated test directory;
the normal development environment and product dependencies were not changed.
SDK-dependent tests explicitly skip when the exact SDK is unavailable; the local
verification run executed all nine rather than skipping them. No live bot token,
network authorization, tenant resources or cloud state were used or created.

Scoped source intake/registration evidence now exists, but the first item and
overall Step 1 are not production-qualified. The next dependency is the approved
bounded request-task/executor handoff; native queued delivery must not be enabled
before that contract is implemented and tested. Full connector/lifecycle and
durable replay qualification remain open. No session-write authority, policy
grant, production capability marker, wheel or installer change is introduced.

### Second Item: Bounded Executor Source Candidate

Patch 22 follows patches 1-21. The complete native
`GatewayRunner._run_in_executor_with_context` method no longer treats copied
context as mandatory-mode authority. It requires a host-installed
`_maya_request_executor` with contract
`project-maya.session-executor-handoff.v1`; absent/unqualified handoffs stop with
a fixed native mandatory error. Ordinary context-copy behavior is unchanged.
The exact helper is tested through a small pinned-source fixture, not a substitute
agent implementation or complete gateway loop.

`CandidateSessionExecutorHandoff` captures an existing authenticated session scope
and one exact synchronous callable chosen by the trusted host. Creation and
submission require the source thread/task, actor and active root lease. The
handoff is single-use, audited before scheduling and cannot select another actor,
session, database, classification or operation set. It rebinds those same limits
inside the executor thread; each native write still requires a gateway decision.
It does not infer authority from job arguments or storage records. Missing audit
storage prevents scheduling. Lazy awaitable/generator results cannot escape the
receiver scope as later executable work.

Receiver leases depend on both the root request and the handoff lease. Completion,
error or cancellation expires the handoff; root-scope exit expires all dependent
leases. Captured receiver contexts, nested delegation, inherited descendant threads
and unrelated async tasks remain denied. The plugin's shared actor boundary also
checks an existing session lease's lifetime/thread/task/identity, so a cancelled
bound executor cannot retain model/tool authority merely through copied identity.
Identity-only production composition is unchanged and remains unqualified; this
does not sandbox arbitrary Python that modifies private host state.

Cancellation cannot forcibly terminate Python executor threads. A running job
may finish a transaction already authorized before cancellation; no cross-store
rollback or preemptive revocation is claimed. Subsequent authorization checks
fail after lease expiration. Recovering prior side effects is separate lifecycle
and audit-outcome work. No generic privileged cleanup bypass is introduced.

Twelve source tests use actual native SQLite and the complete patched executor
helper. They cover an allowed write, mismatched callable/session/operations,
single-use/expiry, captured contexts, unrelated tasks, nested/descendant workers,
request cancellation with later write/identity denial, unavailable audit, fixed
errors, lazy-result rejection and ordinary behavior. No live model/provider or
complete native task/agent lifecycle is exercised.

The second approved item remains partial: the explicit authenticated request-task
hop and host selection/binding of the actual native conversation closure are not
implemented. Do not attach this to arbitrary executor jobs, background reviewers,
recovery tasks or native text batching. The next work remains in this second item,
before allowed session-index transitions (third item). Patches 20's routing blocks,
the twelve-patch wheel, installer 013 and production activation stay unchanged.

### Second Item Continuation: Native Conversation Task Scheduling

Patch 23 follows patches 1-22 at the same pinned Hermes source. It replaces only
the main conversation's `ensure_future(_run_in_executor_with_context(run_sync))`
site with `_schedule_maya_conversation_executor(run_sync)`. In mandatory mode
that helper requires an explicit host-installed factory with the
`project-maya.conversation-executor-schedule.v1` contract. Ordinary mode still
creates a native async Task around the existing executor helper. The separate
background-task `run_sync` site is not changed or authorized.

`CandidateConversationExecutorFactory` installs once on one trusted runner. It
accepts scheduling only from a live authenticated root session scope, on its
owning thread/task, and selects that exact synchronous closure once per request.
An authentication audit must succeed before the Task is created. A task-local
selection permits exactly one executor handoff for that callable and no supplied
arguments. The runner's executor resolver is stable across requests; it does not
hold a mutable shared per-request authority slot. Neither task nor thread can
select a new actor, session, path, classification or operation set. Native writes
still require the existing gateway's individual authorization decision.

The selected receiver uses a real asyncio Task with a narrow cancellation override
that revokes its lease before native cancellation delivery. Python documents that
[Task cancellation can be suppressed by a coroutine](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.Task.cancel);
authority must not depend on that coroutine eventually exiting. Root scope exit,
receiver exit and cancellation invalidate descendants. Running threads cannot be
forcibly terminated, and already-authorized transactions are not rolled back.
Private host objects and arbitrary Python mutation are not a sandbox boundary.

The complete added scheduling helper and complete patched executor helper are
tested with actual native SQLite. The fixture's surrounding scheduling method is
explicit scaffolding containing the exact pinned call-site statements, not a fake
agent or a complete native conversation. Checks cover task/thread rebinding,
single-use scheduling, source expiry, cancellation before start and during a
worker, cancellation suppression, nested/unrelated work, fixed audit errors,
per-write session denial and ordinary mode. Patch application is checked against
the pinned source separately. No live provider, sockets or platform resources are
used. Audit records represent authorized handoff attempts, not commit receipts.

The scheduling seam now exists as a source candidate, but the second item remains
partial. Next stay here: exercise the complete native conversation caller under
the authenticated host binding, including caller cancellation/error cleanup and
the Telegram intake-to-conversation composition. Do not enable queued delivery,
allowed session-index transitions or generic workers from these seam tests.
Gateway routing blocks, twelve-patch wheel, installer 013 and production
activation remain unchanged. Overall Stage 2 Step 1 acceptance is still open.

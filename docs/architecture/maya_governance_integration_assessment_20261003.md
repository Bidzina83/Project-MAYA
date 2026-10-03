# Maya Governance Integration Assessment

## Decision Summary

Assessment date: 2026-10-03. User-authorized reassessment, not authorization to
activate production governance or implement the proposed replacement sequence.

Maya has substantive local policy, memory and native enforcement code. It does
not yet have a qualified end-to-end governed Hermes product runtime. The 23
patches are useful source candidates, not 23 completed product capabilities.

The principal process failure was incremental boundary discovery without a
complete lifecycle and supported-capability map. Focused tests repeatedly closed
local gaps while ingress, authority, caller recovery and installed composition
remained incomplete. Hermes complexity contributes to uncertainty, but does not
justify treating those local closures as an integration plan.

Recommendation: retain the existing policy engine and native Hermes integration,
freeze the candidate series, and qualify complete vertical product paths under
an explicit supported profile. Do not attempt to make every Hermes feature
governed in the first milestone. Excluded features must be demonstrably blocked
at their real entrypoints, not merely hidden from the tool menu.

See [the detailed proposed plan](maya_governance_integration_plan.md).

## Four Assessment Steps

| Step | Outcome |
| --- | --- |
| 1. Map runtime lifecycle and material boundaries | Source/caller map below; concrete proxy, cancellation, schema and identity gaps identified |
| 2. Map patches, coverage, overlaps and regression risk | All 23 patches applied sequentially to Git-object baseline; coverage/evidence matrix below |
| 3. Revise completion strategy and acceptance gates | Proposed milestone plan written separately; no production architecture replacement |
| 4. Establish controlled implementation re-entry | Freeze and approval checkpoint established; implementation does not resume automatically |

This is a bounded integration assessment. It is not an exhaustive adversarial
security audit or proof that every dynamically loaded Hermes extension is safe.
Unresolved paths are recorded, not inferred healthy from absence of a finding.

## Exact Evidence Identity

- Maya checkout HEAD: `de087cff42bf36f175756ecbf8a64bc4ff5e007b` plus the
  existing uncommitted candidate work. GitHub CI at that HEAD was not fetched.
- Hermes baseline: `b13e2fd6948a59eeb59fe618914147d97a2ee90a` from the local Git
  object database, not assumed from the working checkout's HEAD alone.
- Ordered patches: `patches/hermes/0001-*.patch` through `0023-*.patch`.
- SHA256 of their exact bytes concatenated in filename order:
  `483d09e5fc0bd10fa2af752d192a7b29427fa398be4f523262b30c7695739668`.
- The series modifies 24 native Python files. All 23 patches applied sequentially
  with whitespace checking, and every modified Python file compiled.
- Staging was generated under ignored `.codex-build/`; neither the source
  checkout nor a wheel/installer was modified.

Important correction: `.codex-build/hermes-fork-candidate-20261002` has the pinned
HEAD but also modified working files from earlier patches. Applying patch 1 to
those files failed. The assessment consequently reconstructed the affected files
with `git show <pin>:<path>` before applying the complete series. Previous claims
of a clean working checkout must not be used as provenance. This correction does
not by itself invalidate a separately hashed wheel or the scoped tests.

Current built candidate remains `0.17.0+maya.gov12.candidate.20261002`, SHA256
`af979f8445e56e0379c7ad5252a228be5e7cf924c86f37c3c76a85ade867a323`.
Installer 013 and the production pin/gate are unchanged. Source patches 13-23
are not evidence about that installed wheel's behavior.

## Documentation Check

Official documentation was consulted on the assessment date:

- [Plugin discovery and registration](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins/).
- [Execution middleware and its failure behavior](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/#middleware-change-what-happens).
- [External memory providers](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers/).

The developer guide distinguishes observers from execution middleware and
describes ordinary callback failures as skipped rather than mandatory stops.
That supports using native interfaces but not assuming ordinary plugins are
fail-closed security gates. Current online documentation is not version-pinned:
the selected Git source and executable tests govern this assessment. No upgrade
to current upstream or undocumented new interface is recommended implicitly.

## Lifecycle And Boundary Map

Paths below are Hermes-relative unless prefixed `src/project_maya/`. Source
anchors refer to baseline symbols; patch application changes line numbers.

| Lifecycle | Actual roots/callers | Required authority or validation | Current conclusion |
| --- | --- | --- | --- |
| Setup/provision | `SessionDB.__init__`, `_init_schema`, repair helpers; Maya first-run | Explicit local setup/maintenance identity, data-root and migration policy | Conversation write gate does not cover direct schema initialization |
| Startup | Maya `bootstrap._build_hermes_runtime`; native plugin discovery; `GatewayRunner.start` | Qualified artifact, five mandatory callbacks before construction, verified capability exclusions | Normal Maya blocks unsupported Hermes; installed test host binds only its four-boundary wheel |
| Local API | `LocalAPI.handle`, `BearerTokenAuthenticator`, public `GovernedAgentRuntime.run` | Authenticated caller, fixed owner/session/database scope; no body authority | Candidate API binding exists; normal product does not select it |
| Telegram ingress | Native adapter `connect`, SDK dispatcher, `BasePlatformAdapter.handle_message`, gateway `_handle_message` | Exact customer-owned bot/user/chat mapping and transport provenance | Candidate polling registration is tested; complete connection and conversation composition are not |
| Other ingress | Native CLI, API server, slash/plugin commands, MCP/ACP/batch and platform adapters | Explicit principal and supported request contract | Not qualified; must not become fallback execution routes |
| Session selection | `SessionStore.get_or_create_session`, `reset_session`, `switch_session`; post-compression entry updates | Owner-scoped lifecycle permission and recoverable DB/index ordering | Patch 20 blocks three methods; other index writers are not covered |
| Profile/provider selection | `_run_agent`, `_resolve_session_agent_runtime`, profile scope, cached agents | Principal must survive profile/cache selection; exact configured route | Multiplexing, reuse, ambient credentials and automatic routes unqualified |
| Task/thread hop | `_run_agent_inner` -> main `run_sync` -> `_run_in_executor_with_context` | Immutable lease, exact callable, per-write gates, cancellation revocation | Patches 22-23 cover scheduling/helper seams, not full caller lifecycle |
| Context assembly | `prepare_turn`, system prompt/context files, MemoryManager, Maya provider | Governed reads and provenance; classification before disclosure | Prefetch exists; fixed memory principal and classification are not frontend-bound |
| Main inference | Conversation loop -> execution middleware -> selected transport | Final effective payload/provider/model/endpoint authorization, zero hidden retries | Scoped native/SDK evidence exists; complete transport/provider matrix incomplete |
| Auxiliary inference | `call_llm`, `async_call_llm`, compression, title/plugin/summary callers | Each attempt separately authorized; purpose and effective route retained | Central/summary gates exist; direct clients and all outer consumers not qualified |
| Tool dispatch | Tool executor -> `model_tools` -> registry/provider/plugin tools | Final arguments, bounded target, approval, idempotency and actual handler mediation | Bounded file/business-memory map exists; most native tools deliberately denied |
| Result/output | Tool result gate, finalizer, observers, stream/interim/progress callbacks, adapter sends | Validate final disclosure before each externally visible or persistent sink | Selected streaming suppression/finalizer gates do not cover every gateway send/error sink |
| Persistence | SessionDB writes, transcript/index JSON, trajectories, built-in memory/skills, Maya SMB memory | Separate storage-purpose/operation grants, serialized-value checks and recoverability | Atomic append/replacement scope exists; direct SQL, index and other file writes remain open |
| Recovery | Retry/fallback, compression rotation, queue/steer/interrupt, resume/handoff | Reauthorization; no authority transfer from queued/stored event fields | Fixed-session lease is incompatible with implicit rotation/re-entry until explicitly designed |
| Workers | Background review, MemoryManager pool, delegation, cron, Kanban/process watchers | Authenticated job identity, bounded scope, cancellation and outcome reporting | Review/tool batches are partially blocked; no general worker qualification |
| Shutdown/update | Gateway stop, adapter stop, `AIAgent.close`, locks, backup/restore/update | Resource cleanup without privileged writes; accurate failure/outcome reporting | Scoped close reporting exists; full shutdown and clean-install lifecycle unqualified |

### Relevant Baseline Anchors

| Source | Anchor |
| --- | --- |
| `gateway/run.py` | `start` line 5348; startup worker dispatch lines 5905-5966; background task line 11261 |
| `gateway/run.py` | Executor helper line 12852; proxy caller line 14163; `_run_agent` line 14457; `_run_agent_inner` line 14515 |
| `gateway/run.py` | Main closure line 15359; task scheduling line 16602; post-compression index update around line 16168; outer finally around line 17038 |
| `agent/turn_context.py` | `prepare_turn`, provider notification/prefetch before loop |
| `agent/memory_manager.py` | `prefetch_all`, `_submit_background`, `_get_sync_executor`, `shutdown_all` |
| `hermes_state.py` | `SessionDB.__init__` line 690; `_execute_write` line 928; `_init_schema` line 1113 |
| `agent/turn_finalizer.py` | `finalize_turn`: implicit Kanban change, save, resource cleanup, persistence and transformed return |

Line numbers are navigation aids, not proof of a qualified call path. Reconstruct
the pinned source before using them; do not inspect an already patched checkout
as if its offsets were baseline offsets.

## Findings And Confidence

### F1: Runtime Proxy Escapes The Tested Entry Path

Confirmed behavioral branch probe. The complete 23-patch `_run_agent_inner`
method entered `_run_agent_via_proxy` without any authenticated scope or candidate
factory. Only the transport target was an inert AsyncMock; there were no sockets,
credentials or provider calls. This proves entry-path bypass, not a live exfiltration
test. The proxy return occurs before the patched conversation scheduling site.

This is Hermes remote-runtime proxying, not Maya's permitted managed model-billing
proxy. Those are different contracts. Initially block the former in the governed
profile; do not accidentally remove the latter from Product Spec V2.

### F2: Native Caller Does Not Cancel Its Executor

Confirmed source path. The outer finally cancels progress, interrupt, stream,
tracking and notification tasks but not `_executor_task`; cleanup itself awaits.
Cancelling a caller waiting through `asyncio.wait` is not the same as invoking the
leased child's `cancel`. The child therefore need not lose authority immediately
when the parent begins unwinding. Root scope exit eventually revokes it, but that
does not qualify the intervening cleanup interval. Patch 23 tests child cancellation,
not this complete caller cancellation path. Timeout and interrupt also need review.

### F3: Schema/Repair Writes Are Outside Session Authorization

Confirmed scoped native-SQLite probe. With mandatory middleware active and no
request binding, the complete native SessionDB constructor from the existing
patch-19 fixture created a new database schema. Patches 20-23 do not modify that
constructor. Schema, column reconciliation, FTS repair, direct SQL and maintenance
cannot inherit conversation append authority. This is an unqualified boundary,
not evidence that ordinary explicit first-run provisioning should be prohibited.

### F4: Gateway Errors And Implicit Side Effects Remain Outside Closure

Confirmed source evidence, not full-loop fault-injection qualification. In the
23-patch source, provider-resolution errors become a response containing `{exc}`.
Finalizer generic cleanup errors still interpolate exception text. Timeout and
notification paths can publish activity descriptions. Post-compression handling
mutates a session-index entry and calls `_save` outside Patch 20's three guards.
The finalizer can change Kanban state independently of a named tool invocation.

Fix disclosure and lifecycle boundaries at these actual sinks. Blanket exception
suppression, hiding commands, and matching tool names do not close these paths.

### F5: Authenticated Identity Is Not Unified Across Product Composition

Confirmed source difference. `CandidateSessionRequestBinding` retains one owner
and exact session/database. `GovernedAgentRuntime` instead binds its configured
actor per run; normal bootstrap does not select the candidate session binding.
`MayaHermesMemoryPlugin.initialize` uses `actor_id="local-user"`.
`GovernedMemoryRetriever` authorizes with its configured actor and classification
`internal`, not the authenticated frontend identity/classification.

For a single local-user installation these values may coincide. That is not
evidence for Telegram user attribution or multi-user isolation. Define requester,
Maya execution principal and any delegated service principal explicitly. Do not
silently turn a remote user into `local-user`, weaken classification or grant
setup privilege. Automatic memory prefetch needs this contract too, since it is
not merely an explicit model-proposed tool call.

### F6: A Fail-Closed Plugin Can Still Be Functionally Unusable

Confirmed action-map limitation. Native governance maps only three business-memory
tools and bounded `read_file`/`write_file`. Shell, code, delegation, cron, connector
operations, built-in `memory`, session search and skill-management tools are not
authorized by that map. Existing skills can contain workflows requiring those
capabilities. A model/tool catalogue loading successfully is not usable IM work.

The fallback `HermesMemoryProviderBridge` advertises `maya_memory_search/recall/
remember`, while the native action map recognizes `maya_business_memory_*`.
That fallback is not interchangeable with the installed provider. Reconcile or
explicitly exclude it; do not add an alias that accidentally grants broad writes.

Hermes MEMORY.md, USER.md and conversation sessions must remain Hermes-owned.
Preserving their storage is not the same as qualifying the operations that write
them. Approved builtin-memory behavior needs its own bounded compatibility tests,
not relocation into Maya SMB memory and not a silent permanent feature loss.

### F7: The Fork Has Unqualified Parallel Entry And Worker Paths

Source inventory identifies startup resume/process/Kanban/handoff/delegation
watchers, MemoryManager background fallback, CLI/plugin/slash commands, native API
server and provider-specific/direct SDK consumers. The separate background
executor call is not the main closure selected by Patch 23. Some paths will fail
when they reach a native gate; others can perform side effects before it.

This inventory is not a claim that each path demonstrably bypasses every gate.
For each, demonstrate full mediation or block its real startup/dispatch path.
Do not qualify arbitrary Python plugins, shell hooks, MCP tools or workers by
assuming all their I/O goes through the agent's named tool dispatcher.

### F8: Audit Attempts, Storage Outcomes And Release Readiness Differ

Confirmed design limitation. Existing audit records describe authorization and
validation attempts, not SQLite commit receipts. Index JSON, native SQLite,
Maya memory and JSONL audit are separate stores. Atomic append/rewrite does not
provide an atomic turn, session rotation, migration or cross-store rollback.

The deployed test host validates its exact four-boundary wheel; source tests
register session_write separately. Normal production compatibility requires a
qualified marker that the patch series intentionally does not publish. Therefore
production remains blocked correctly. Do not solve usability by removing that
guard or updating a hash to imply qualification.

## Patch Coverage And Regression Map

All rows are opt-in candidates. "Tests" describes observed scope, not a completed
product capability. Wheel inclusion is 1-12 only; 13-23 are source-only.

| Patch | Change / relevant callers | Evidence and remaining risk | Disposition |
| --- | --- | --- | --- |
| 1 | Native mandatory dispatcher/live callback binding | Dispatcher tests; activation/startup/completeness not proved | Retain primitive; qualify discovery and all five gates |
| 2 | Central sync/async auxiliary attempts and plugin LLM | Native helper/route tests; direct SDK callers and automatic attribution open | Retain; enumerate effective transports |
| 3 | Main-loop typed denial stop handlers | Scoped catches; full loop/recovery open | Retain; prove whole-loop zero denied effects |
| 4 | Tool/preflight and memory-prefetch failure propagation | Native methods; provider jobs/outer consumers open | Retain; qualify context/memory identity |
| 5 | Native dispatcher/registry denial propagation | Dispatcher tests; commands/direct handlers not uniformly covered | Retain; test actual handler entry roots |
| 6 | Final tool-result validation and fixed generic failures | Result tests; validation cannot undo mutations | Retain; add outcome/idempotency contracts |
| 7 | Selected provider diagnostics/error observers | Scoped redaction; raw gateway/cleanup/stream sinks remain | Extend only mapped sinks; no blanket catch replacement |
| 8 | Per-summary authorization, no native inner retries, zero-SDK-retry requirement | Native consumers/transports; actual final wire payload and redirects unresolved | Retain; qualify selected provider API explicitly |
| 9 | Suppress early text/reasoning/interim/display | Source methods; not a final delivery permission or observer policy | Retain initial suppression; qualify full delivery |
| 10 | Finalizer model-output gate | Complete finalizer with inert effects; gateway formatting/recovery/late sinks open | Retain; distinguish output from egress and writes |
| 11 | Compression denial propagation, raw observer errors, review blocked | Native consumers; other workers and full recovery open | Retain review block; add explicit exclusion evidence |
| 12 | Helper persistence checks and raw API observer suppression | Helper/installed scenarios; uses model.output rather than full storage authority | Retain content checks; clarify purpose alongside Patch 15 |
| 13 | Outer tool/compression/CLI catch propagation | Complete selected callers and catch seams; not all frontends | Retain; full caller matrix required |
| 14 | Effective mapped SQLite append-row validation | Real native SQLite; intermediate row-wise approach superseded by atomic path | Retain historical dependency; consolidation only after behavioral equivalence |
| 15 | Fifth session_write boundary and atomic append/flush | Native transactions/FTS/counters; schema/direct SQL/audit outcomes open | Retain; integrate all host bindings |
| 16 | Create/prompt/rewrite/compact/clear descriptors | Native replacement rollback; full lifecycle/index ordering open | Retain; no blanket delete or maintenance grant |
| 17 | Initializer/transcript/mirror caller propagation | Real DB + complete scoped callers; identity/routing synthetic | Retain; authenticate actual frontend composition |
| 18 | Metadata/accounting/end/reopen/close reporting | Native DB/close tests; earlier cleanup not rolled back | Retain; full shutdown failures need qualification |
| 19 | Compression lock authorization and fail-closed caller | Native locks/inert summary; denied release can leave lock until expiry | Retain; qualify recovery/lease expiry |
| 20 | Block create/reset/switch before index mutation | Guard tests; other direct index writers and allowed transitions absent | Keep blocker until lifecycle design passes |
| 21 | Telegram polling registration before application start | Real pinned SDK dispatcher plus registration seam; no live connect/reconnect | Retain; bind native conversation without ordinary fallback |
| 22 | Exact single-use executor rebinding | Real DB + complete helper; no generic worker permission | Retain; lifecycle owner must revoke |
| 23 | Main native closure scheduling/task lease | Scheduling/helper seams; full caller proxy/cancellation not closed | Revise caller integration before qualification |

Overlaps are intentional in some places: tool execution/result checks, finalizer
output checks and pre-persistence content checks defend distinct downstream
transformations. Do not remove checks merely because one payload passes several
gates. Patch 14 is an intermediate evolution of append mapping; Patches 15-19
replace parts of that implementation. After the full path passes, consolidate
the series by responsibility against one baseline, preserving equivalent behavior
and provenance. Do not silently renumber, squash or delete patches now.

## Risk Assessment

- Impact if wrong: high. Model disclosure, unauthorized writes, user isolation,
  lost conversation history, stuck workers and broken startup are material.
- Regression likelihood: not established by full-fork evidence; meaningful
  risk exists because mandatory checks cross storage, recovery and concurrency.
- Protection: useful dispatcher, native-function and native-SQLite coverage;
  weak for complete frontends, deployment, all transports and ordinary-mode parity.
- Recoverability: opt-in behavior preserves a useful comparison mode, but native
  writes can persist before later denial. Reverting code is not a data rollback.
- Confidence: high in reproduced branches and cited source differences; limited
  in whole-product safety/compatibility. No automatic merge/activation recommendation.

This is not a formal immutable-PR security scan. The runtime product must not be
released with governance disabled as a workaround. Ordinary mode is a regression
control in an isolated test environment, not an acceptable production fallback.

## Checks Executed During Assessment

| Check | Result | Limit |
| --- | --- | --- |
| Git-object baseline + sequential patches 1-23 + compilation | Passed; 24 changed files | Textual/compilation compatibility, not functional equivalence |
| Handoff, authenticated API, candidate transport and governance suites | 66 discovered, 65 passed, 1 skipped | Installed-loop test skipped because its payload input was not supplied |
| Telegram intake + registration suites with isolated SDK 22.6 | 22 passed, none skipped | Synthetic SDK request/dispatcher, no live polling/network |
| Required Phase 6/update/setup-health/closure suites | 47 passed | Existing artifact/lifecycle contracts, not full 23-patch product |
| Complete 23-patch native caller proxy branch probe | Bypass reproduced with inert transport | No live provider/exfiltration test |
| Native caller cancellation cleanup inspection | Missing executor cancellation confirmed | Full cancellation race not exercised |
| Mandatory-mode native SQLite constructor probe | Schema initialization without binding reproduced | Existing native fixture through Patch 19 |

Total: 134 passing tests and one explicit skip. Full upstream/fork regression,
full authenticated Telegram-to-AIAgent path, live provider, complete 23-patch
installed payload and clean Windows lifecycle were not run or qualified.

## Re-entry Control

Subsequent decision: the user approved the revised G0-G7 plan and G0 implementation
on 2026-10-03. See [G0 progress](governance_g0_baseline.md). The following records
the assessment's original boundary, not a continuing approval requirement for G0.

No new runtime patch, public compatibility marker, policy permission, secret,
customer configuration, wheel, installer or production pin is changed by this
assessment. The proposed plan must be approved before its execution sequence
replaces the existing Stage 2 Step 1 order. An implementation turn must name its
milestone/work package and acceptance gate before editing.

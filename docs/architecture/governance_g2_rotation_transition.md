# G2 Session Rotation Contract Review

Review date: 2026-10-14. G2 work package 3, rotation Step 1. Status: proposed,
pending explicit approval of the bounded profile and ordered Steps 1-4 below.
The user authorized contract review, not implementation or rotation activation.

## Purpose And Milestone Boundary

Rotation creates a new continuation child for the same authenticated owner,
preserving the parent and changing the verified routing slot. It is not reset,
switch to an existing session, credential rotation or replacement of Maya SMB
memory. Hermes conversation stores, MEMORY.md/USER.md, Maya business memory,
governance records and Metabase stores keep their distinct roles.

The approved ownership design requires separate source-finalization, child-create
and route permissions before native compression mutations. The integration plan
also explicitly assigns full compression and new in-flight session authority to
G3 work package 5. G2 must not silently consume that later work by retargeting a
fixed-session G1 lease or declaring compressed-context generation qualified.

Recommendation: first qualify one explicit, between-turn rotation with a pinned
synthetic continuation-context fixture. Actual native SQLite, publication, caller,
reader and AIAgent paths will be required; no fake runtime or compressor is added.
The fixture is test data, not a claimed LLM summary or production context producer.
Full automatic/manual/hygiene compression, in-place compaction, real context
generation and in-flight authority handoff remain blocked for their G3/G4 gates.
This bounded profile needs approval; it is not predetermined by switch acceptance.

## Reviewed Source

Reviewed effective source is the unchanged accepted Patch 37 stage
`.codex-build/governance-g2-switch-composition-20261008-a`, descended from Hermes
commit `b13e2fd6948a59eeb59fe618914147d97a2ee90a`. Full frozen ancestry and native/
host inventories were verified during this review. The source search updates the
earlier G2 writer inventory's line offsets; observations below are not native
execution or qualification results.

| Effective source location | Observed behavior and contract consequence |
| --- | --- |
| `source/agent/conversation_compression.py:281-349` | Feasibility probing, diagnostics and status delivery precede compression lock acquisition. `compression_in_place` selects a different path; the pinned default is false. An exclusion gate must precede these effects, not only child creation. |
| `source/agent/conversation_compression.py:350-471` | Lock is keyed on the parent; mandatory missing/broken/busy lock paths deny. Memory pre-compression callbacks run before summarization. Locks and callbacks are separate operations, not permission to rotate. |
| `source/agent/conversation_compression.py:472-545` | Compressor runs and may abort or fall back; todo/context rebuilding follows. Summary inference and context quality are outside the initial G2 fixture producer. |
| `source/agent/conversation_compression.py:579-684` | Legacy rotation flushes the parent, reads its title, ends it, changes agent/session/log context, independently creates a child, then migrates goals/title and stores a prompt. Child-create failure restores the live ID and tries to reopen the parent. These separately committed effects cannot be reused as an atomic mandatory transition. |
| `source/agent/conversation_compression.py:685-829` | Outer catches, context-engine/memory/session-compress callbacks, counters and file dedup bookkeeping follow mutation; the lock is released late. Typed-denial handling does not establish complete rollback or qualification of every side effect. |
| `source/agent/conversation_loop.py:2833,3046,3213,4233` | Main/recovery paths call compression inside an existing conversation, and may continue/retry with changed messages. A fixed-session root cannot become child authority by changing an agent field. |
| `source/gateway/run.py:16406-16472` | Native closure reads the agent's changed ID, mutates a cached entry, calls `_save`, may sync Telegram bindings, then selects transcript offsets/effective ID. Neither agent output nor a result ID is authorization. |
| `source/gateway/run.py:9772-9778` | Outer result handler also copies a returned ID into routing and saves. Both inner and outer writers must remain blocked or validate the same correlated transition; fixing one is insufficient. |
| `source/gateway/run.py:9330-9420` | Hygiene compression constructs a separate agent/executor and may save routing, rewrite a transcript and update token state. It is not the authenticated selected conversation executor. |
| `source/gateway/slash_commands.py:2814-2910` | Manual `/compress` similarly constructs a temporary agent, invokes an executor, updates routing, rewrites context and token state. It cannot borrow conversation/admin authority implicitly. |
| `source/hermes_state.py:1396-1442,2556-2783` | Public create/end/reopen methods independently commit. Native message preparation/insertion helpers are available, but their existence does not authorize copying/seed insertion or make a batch qualified. |
| `host/src/project_maya/hermes_plugins/session_readers.py:156-190` and `session_requests.py` | The selected conversation retains projection exclusion and a fixed-session append root. Existing create/reset/switch preparations reject active request authority. An in-turn rotation is not a safe reuse of those preparations. |

Reviewed file SHA256 values:

```text
source/agent/conversation_compression.py
da0caf7a7f1f4df6ff144fed7bad78e625b2df44a66f3bcf2ab1df5b616bfd92
source/gateway/run.py
d3299bf8d4f0ab7867a436c290af7bdaa1be4e60743befb090f2201dea8cc7b0
source/gateway/slash_commands.py
8679fb5307d9bd673ef3addf925854c41ac8401f215d3d5f01be0a250ee62f1c
host/src/project_maya/hermes_plugins/session_readers.py
188b44f9385a693eb756555ba7ac2f668bbb0cc4a943cf4d54a5aebdb1f88b76
```

Native tests reviewed as control inputs include compression rotation-state,
concurrent-fork, logging-context, in-place, persistence, failure/session-sync and
compression-lock tests. Some use mocked compressors/agents; they are ordinary
regression controls, not proof of governed complete-loop behavior. No native
rotation/compression suite was executed or newly qualified by this design review.

## Proposed Initial Profile

One acknowledged create S, then one rotation S-to-new-child C, in the same
instance/database/slot and for the same freshly authenticated principal and
classification floor. S is active, unarchived, parentless and selected by the
exact acknowledged create receipt, route version one and projection generation
one. An eligible slot has no pending/uncertain receipt, active request, registered
running agent, pending source execution or compression-lock row. An expired or
unknown lock is not automatically cleared as conversation authority.

The selected parent turn has fully exited and its G1 root is revoked. Acquire
the existing cross-process projection exclusion rather than forcibly terminating
a request or borrowing its root. Another host holding the exclusion makes the
operation busy. Foreign owners, reset/switch sources, an existing child, repeated
rotation, arbitrary lineage/target selectors and background/queued execution are
outside this first profile. Accepted create/reset/switch checks are not relaxed.

The host generates a fresh child ID and unique transition correlation. Proposed
contract identifier is `project-maya.native-session-rotation.v1`, operation
`rotate`; this is design only, not an implemented capability marker. A separately
versioned preparation/reader branch must be reviewed and qualified before use.

For this source-test profile only, the trusted test host provides a pinned,
bounded, text-only continuation-context artifact. Its producer is explicitly
`source_test_fixture`, not Hermes inference. It binds fixture version/hash,
source S, authorized source transcript snapshot digest, classification and the
exact prepared native child-message values. Unknown fields, tools, attachments,
reasoning, callbacks, paths, caller-chosen timestamps or arbitrary request-supplied
context are rejected. Row/byte limits are fixed in the qualification input before
running tests. Preparing native timestamps/serialization occurs once before
sealing the descriptor; mutable re-serialization cannot change approved bytes.

The fixture is not evidence of useful summarization, token reduction, SMB context
accuracy, residency or production model-output validation. It must never become
a configurable production producer or automatic fallback. Production readiness
remains blocked for real context production/handoff; report this explicitly.
Do not call a mocked compressor to make full native compression appear qualified.

## Authority And Exact Permissions

The single-use descriptor binds contract/operation, instance/canonical database,
principal/classification, source/child IDs, host slot, both owner-binding versions,
expected route/projection versions, prior create correlation, request/correlation
IDs, source snapshot and fixture/effective seed digests, fixed purpose and limits.
Task/thread/process, expiry, revocation synchronization and registration are
host-owned authority constraints, not fields a request can enlarge.

Every effect uses Maya's existing local action gateway and available required
audit. Proposed distinct operations are not policy defaults or current grants:

| Permission | Restricted purpose |
| --- | --- |
| `session.read/route_state` | Resolve this owned current slot and exact published receipt. |
| `session.read/transition_state` | Check the current source owner/lifecycle and historical create evidence. |
| `session.read/history` | Authorize the selected parent snapshot used to bind the test fixture's lineage; no foreign enumeration. |
| `session.transition/rotate` | Replace this slot with this newly allocated child only. |
| `session.write/end` | Finalize S with fixed candidate reason `session_rotation`; do not claim native compression has completed. |
| `session.write/create` | Allocate C with the same owner/floor and `parent_session_id=S`; no schema provisioning or arbitrary metadata. |
| `session.write/append` | Insert only the sealed fixture seed into the newly created child as part of this exact atomic transition. This descriptor grants no subsequent general append lease. |
| `session.transition/acknowledge_rotation` | Confirm exact publication/seed and native source-security cleanup after normal caller exit. |

Seed authority is a planned dependency of Step 2, not an existing G1 permission.
Validate effective native serialized rows through the existing governance boundary
under an explicit rotation-transition context; do not fabricate a G1 append scope
for an uncreated child or substitute `model.output` permission for session writes.
The native sink must require that sealed authority independently of a caller's
claim to have validated data. If exact context/serialization binding requires a
broader contract than this proposal, stop and seek approval before expanding it.

No permission implies deletion, parent compaction/rewrite/clear, ownership transfer,
classification lowering, credential access, title/goal/accounting migration,
memory-provider writes, model/tool execution, connector mutations or recovery.
The candidate end reason does not change ordinary Hermes `compression` semantics
or qualify native automatic compression-lineage lookup.

## Ordered Transition And Visibility

1. Authenticate the host-bound owner afresh. Under projection/store/SQLite locks,
   verify mandatory gate registrations, canonical safe paths, exact acknowledged
   create lineage, idle source and absence of compression locks/pending receipts.
   Authorize source reads and each effect; prepare/seal the bounded native seed.
   Release native database locks before any caller execution; no inference occurs.
2. In one `BEGIN IMMEDIATE` transaction recheck all versions, ownership, source
   snapshot, registration, expiry/revocation and exact seed serialization. End S,
   create C and its matching owner/parent linkage, insert the authorized seed using
   native message/FTS mechanisms, replace the slot via compare-and-swap, increment
   route/projection versions to two and insert one `rotate` pending receipt. Every
   expected update must affect exactly one row. Synchronize revocation with commit.
   Public independently committing create/end/append methods must not be nested.
3. Native SQLite commit is authoritative. Strictly publish the complete projection
   using the accepted Patch 35 helper; verify bytes/hash/generation and required
   audit before advancing the exact receipt through projection verification and
   pending caller. Do not replay historical create projection or manufacture rollback.
4. Normal-exit acknowledgement requires independent permission, fixed audit,
   exact native approval/cache/security cleanup, seed-prefix/parent-lineage checks
   and complete authority/lock cleanup. Only afterward issue live host confirmation
   bound to process/registration, current receipt and native seed provenance.
   Store effective seed row identities/digest without logging text; bind them to
   the receipt/confirmation, and distinguish the immutable seed prefix from later
   independently authorized child appends. Missing provenance denies.
5. A rotation-specific reader joins through the current `rotate` correlation,
   verifies parent S ended for this rotation, active child C with matching owner/
   classification/parent fields, immutable historical create receipt, versions,
   projection, live confirmation and authorized seed provenance. It must not
   reinterpret rotate as reset/create or weaken accepted reader predicates.
6. Only after separate fresh authentication/history permission issue a new C-bound
   G1 request root and construct a fresh actual AIAgent. Old S roots remain revoked;
   no agent, prompt snapshot, approval, queued event, model/provider override or
   current-session context is silently transferred. The test-only model fixture
   may consume C's authorized seed with zero SDK retries and synthetic HTTP, after
   independent model/output gates. S's raw history must not be silently attached.

Parent messages, FTS/search state, unrelated metadata and historical receipts
remain unchanged; no SMB memory store, preferences, goal, title or Metabase data
is migrated. Child seed insertion is part of the native transaction, not a second
memory system. New-host/restart eligibility remains blocked without live confirmation
pending explicit G3 maintenance/outcome reconciliation. Receipt acknowledgement
is neither fresh authentication nor general conversation/model readiness.

## Failure Contract

| Failure boundary | Required observed outcome |
| --- | --- |
| Identity/permission/audit/path/idle/lock/seed preflight | Prior native records, projection, caches and agent IDs unchanged; zero allocation or dispatch. |
| Seed serialization, native SQL/effect counts, stale versions or revocation before commit | All child/messages/FTS/lifecycle/route/receipt effects roll back; parent remains intact and selected. |
| Commit succeeds but reports error | Retain actual correlated outcome, quarantine/deny; no blind retry or automatic parent reopen. |
| Publication/write/flush/fsync/replace failure | Prior or new complete projection only; native committed lineage remains blocked. No copy fallback or partial file. |
| Seed/projection/audit/cleanup/acknowledgement uncertainty | No live confirmation or child scope. Even an acknowledged durable row cannot grant dispatch. Preserve the original failure if quarantine fails. |
| Cancelled/expired/revoked caller or late old executor | No borrowing C authority, root retargeting, second child or additional unauthorized model/tool/storage effect. |
| New host, forged result/agent ID, corrupt seed/lineage/projection or replay | Refuse adoption without authoritative mutations, fallback, title lookup or repair; no production readiness. |

Diagnostic output and audit contain fixed codes, hashes and classifications, never
seed/parent text, API keys, bot tokens or private error details. A previously
authorized committed effect is not falsely described as undone. Native ordinary
compression recovery remains ordinary behavior, not a mandatory-mode fallback.

## Excluded Native Entry Points

Within the proposed G2 candidate, real `_compress_context` calls remain denied
before feasibility probing, status/diagnostic delivery, memory callbacks, lock
mutations, summary SDK/transport or session-ID changes. `in_place=True` must not
bypass the exclusion. This early consumer guard is planned negative qualification,
not proof that those paths are already fully covered today.

Main-loop preflight/recovery compression, manual `/compress`, hygiene, background
review and nested workers gain no rotation authority. Inner/outer gateway returned-
ID synchronization, direct `_save`, ordinary reset/switch and transcript writers
must either be explicitly receipt-validated within this fixed profile or deny
before route/cache mutation. Do not authorize a writer because an agent/result
reports a new ID. Include actual caller-side denial propagation, not sink-only
tests or a declaration that disabling one UI command covers all roots.

G3 must later qualify a real context producer, protected tool-result boundaries,
parent flush, native compression locks/callbacks, prompt/accounting persistence,
new in-flight child authority and outer-caller propagation. G4 retains provider/
fallback/error/egress/output qualification. No additional between-turn seed or
unqualified root is automatically allowed by this design.

## Ordered Steps And Acceptance Gates

1. **Contract review, current:** approve the one-create/one-child, between-turn,
   fixture-only profile, explicit seed authority, G2/G3 split and Steps 2-4 order.
   Gate: explicit user approval of this contract, not a generic instruction to
   proceed with review. No source candidate or patch is implemented at this step.
2. **Authority and atomic native sink:** create a separately versioned/hashed
   source candidate over unchanged Patch 37. Implement only the sealed owner/
   source/target/seed authority and one actual native SQLite transaction. Gate:
   allowed atomic lineage/seed with complete parent preservation; independent
   permission and malformed/foreign/stale/replayed/expired/revoked seed/descriptor
   denials; real SQL/effect-count/FTS rollback; active-source/lock contention denies.
   Commit alone grants no routing/readiness. Review before Step 3.
3. **Publication, caller/reader and exclusion composition:** qualify strict file
   publication, exact pending/acknowledged receipts, native cleanup, live confirmation,
   immutable seed provenance and fresh child-bound caller/AIAgent/SDK fixture.
   Gate: only C seed enters the independently allowed model request; model denial
   produces zero transport; no S root/history/approval/cache transfer. Native
   compression consumers and all excluded returned-ID/index writers deny before
   effects. Fixture context is reported test-only, never a qualified summary.
   Missing confirmation/seed/caller failure stays blocked. Review before Step 4.
4. **Failure matrix, parity and acceptance:** execute ordered batches for actual
   process crash/fresh-host restart; process contention; late S/C callers,
   cancellation and descriptor/seed faults; combined commit/publication/ack/audit/
   quarantine uncertainty; separate storage/audit/unsafe-path faults; final ordinary
   parity and criterion review. Gate: exact native records/messages/FTS, complete
   files, dispatch counts and redacted audit/output match the contract. Explicit
   bounded rotation acceptance follows review, not implementation or green CI.

Steps are sequential. Freeze exact test identities/counts after source-informed
collection; do not invent totals, accept skips or quietly drop a failing root.
Retain unchanged create/reset/switch native replays on the combined candidate.
Compare ordinary session/approval/cache controls and relevant native compression/
rotation/in-place/lock/persistence controls against pinned unpatched Hermes. Preserve
the nine known Windows shell-path failures and any explicitly reviewed baseline
limitations; new candidate-only failures or uncovered required paths block the gate.

Each implementation gate runs the required release/update/setup/closure regressions,
context guard and release-script syntax checks plus scoped native/provenance checks.
Unknown dependencies or a needed change to scope/order return for specific approval;
they are not silently inserted as extra patches or treated as later acceptance.

## Decision And Remaining Limits

This review recommends the bounded profile above without changing the G0-G7 order.
It is a proposal, not approval or qualification. Approve this contract before
Step 2; alternatively, request a revised rotation profile explicitly. Enabling
full automatic compression during G2 would require a separately approved plan
change because the current plan assigns the real handoff/producer work to G3.

Live provider/connectors, production context generation, repeated/combined rotation,
reset/switch source rotation, arbitrary tools/workers, title/goal migration,
in-place compaction, normal ingress/setup/maintenance authentication, schema
provisioning, durable audit reconciliation, automatic failover, hostile file/ACL
races and power-loss durability remain outside this first profile. Test artifacts
stay isolated; ordinary Hermes behavior and customer installations are untouched.
WP3/G2, production activation, runtime pin, wheel and installer readiness remain open.

## Review Verification

2026-10-14: full frozen Patch 37 ancestry/native/host inventory verification passes.
All 49 portable tests pass: the 47 required release/update/setup/closure regressions
and two actual Windows-style Git checkout checks, including this LF-protected
document. Product-context validation, required release-script syntax checks and
whitespace checks pass. These verify existing product behavior and documentation
consistency, not the proposed rotation contract's native execution or acceptance.
No rotation/compression native suite was run, no source candidate or new patch was
authored, and accepted inputs/runtime modules/wheels/installers remain unchanged.

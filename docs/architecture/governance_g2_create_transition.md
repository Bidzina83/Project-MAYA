# G2 Create Transition Implementation

## Current Step

G2 work package 3, create only, under the approved integration plan and
`governance_g2_session_consistency.md`. Host authority/preflight and an explicit
source-candidate native create/SQLite/publication path are now implemented. This
is not the complete qualified native create transition. Work package
3 and G2 remain open. No reset/switch/rotation, frontend composition, maintenance
identity, schema provisioning, production activation, wheel or installer change.

## Implemented Boundary

`src/project_maya/hermes_plugins/session_transitions.py` adds a source-candidate
`project-maya.session-transition.v1` create descriptor and host binding:

- Explicit configured owner, classification, instance, canonical existing database,
  host-selected routing slot and binding version. No request payload selects them.
- Host-generated target/request/correlation IDs and canonical descriptor digest.
  These IDs are preparations, not allocated native rows or authority to dispatch.
- Separate `session.read/route_state`, `session.transition/create` and
  `session.write/create` decisions through
  Maya's existing gateway. Non-exact allows, constrained/redacted decisions, policy
  failures and unavailable audit deny. Audits use fixed codes and hashed selectors.
- Single owning task/thread, finite expiry, pending-cancellation checks, one active
  scope per binding and revocation on exit. Copied/replaced descriptors do not grant
  authority. A binding-version/configuration change invalidates prepared authority.
- A single-use synchronous commit guard rechecks policy and serializes cross-thread
  revocation. A failed guard also consumes authority, without declaring any database
  effect undone. Publication uses the same revocable authority after a consumed
  commit; no second allocation/commit attempt is permitted.

This binding requires fresh authentication by its trusted host caller, just as the
G1 binding does; identity equality is not itself a credential authenticator. No
product frontend registers it yet. G1's fixed-session binding and hashed source
inputs are unchanged. No append/model/tool/session scope is issued by preflight.
The new bounded authority precedes first-session allocation; composing it with
frontend cancellation and issuance of the G1 conversation root remains unqualified.

## Evidence And Limitations

`tests/test_hermes_session_transition_authority.py` covers host permission, owner,
classification, replay, expiry, pending cancellation, task/thread isolation,
revocation ordering, configuration changes and secret-safe errors/audits. Its path
fixture deliberately is not a SQLite schema and proves no native persistence.

`tests/hermes_g2_create_preflight_native.py` verifies the complete existing Patch 26
native export, constructs actual SessionStore and SessionDB in isolated state and
asserts preflight cannot bypass native create/reset/switch denial. It checks native
database contents, index absence and unchanged routing cache. This is denial-only
evidence, not an allowed create or complete caller-loop qualification.

Use a fresh export reconstructed by the existing lifecycle preparation tool.
Run native diagnostics from that export with `--import-mode=importlib` to avoid
the repository's legacy `hermes_cli` namespace shadowing pinned Hermes. Disable
bytecode and pytest cache generation so verification of the exact export remains
meaningful. Do not weaken inventory checks to tolerate contaminated source trees.

Verification on 2026-10-04: 18 host authority tests, 4 actual native denial
controls, 25 unchanged G0/G1 provenance checks and 47 required product regression
tests passed. Product-context validation, syntax and whitespace checks passed.
The native suite used a fresh Patch 26 export at
`.codex-build/governance-g2-create-preflight-20261004-c`; its lifecycle manifest
SHA256 was `93355be4627859615d9755f808883433ecb330df93c431a3152c9ea6b40d0d9e`.
The native run reported one pytest configuration warning: disabling the cache
plugin leaves the existing `cache_dir` option unrecognized. No tests were skipped.
Earlier attempts were rejected for namespace shadowing, temporary-directory
permissions and extra generated files in the reused export; none count as evidence.
The complete G1 caller/ordinary suites were not rerun in that preflight increment; their
frozen inputs and native source patches remain unchanged.

## Native Persistence Increment

Patch 27 adds only an explicit `SessionStore.create_owned_session_candidate`
entry. It requires mandatory gate integrity and the exact Maya coordinator type;
it cannot become the ordinary get/create fallback. The accepted Patch 26 inputs,
production runtime pin and installed artifacts are unchanged.

`session_creation.py` coordinates the actual native SessionDB connection:

- Requires existing schema, projection, lockfile and matching database/instance/
  projection path; no directory or schema provisioning occurs on the request.
- Uses prepared portalocker 3.2.0 for bounded OS-backed file exclusion, then native
  store and SQLite locks. Foreign/unowned records, missing schema, unsupported
  schema version, stale/forged projection or unfinished receipts block.
- Rechecks durable state inside BEGIN IMMEDIATE. Session, owner, route, correlated
  receipt and projection generation/hash commit together under the single-use
  authority guard. A native SQL failure rolls back the whole transaction.
- Writes/fsyncs a same-directory temporary file, then uses strict os.replace and
  byte verification. No native helper's copy fallback is used. Symlink/reparse
  paths and network UNC paths are rejected; platform path-race/ACL/filesystem
  durability qualification remains open, not claimed from these checks.
- Records `committed_pending_projection`, then `projection_verified`. Only after
  successful outcome audit and another state recheck is the receipt `published`.
  Unknown commit outcomes and publication/audit failures retain quarantined
  authority records. Later create attempts cannot silently replay or repair them.
- Returns a source-only receipt with `dispatch_allowed=false`; it deliberately
  does not issue a conversation scope, return an operational SessionEntry or load
  the projection through ordinary readers. Cache/reader and scope composition are
  the remaining part of implementation step 3, before full failure qualification.

The fixture tables are versioned native extensions in the Hermes conversation
database, not Maya SMB memory. Projection authority now also records the exact
index path. The transition receipt's policy-decision reference correlates the
preflight audit IDs; it is not proof of atomic SQLite/audit persistence. The
profile currently rejects any foreign owner or differing classification/binding
in this store; shared/multi-owner routing is not supported by this increment.
All other native writer roots remain unqualified; existing _save/load behavior
must not consume this envelope until the mandatory reader contract is implemented.

Reviewed inputs are fixed in `governance-g2-create.json`. Preparation and native
verification reconstruct the accepted parent, apply only Patch 27, compare the
complete native inventory and check host/test hashes. Generated manifests cannot
override those reviewed hashes. The artifact is source-only, not a new wheel.

Seventeen native diagnostics pass: allowed create, pre-mutation policy/audit/gate/
schema/legacy-owner/projection denials, rollback after native INSERT, revocation,
repeat allocation denial, pending publication, unknown commit outcome, strict
replacement failure, OS-lock contention and outcome-audit quarantine. They inspect
the actual database, index and unchanged native cache, not a replacement store.
Lock contention currently uses independent handles in one process: crash release,
multiple processes, expiry at actual commit and cancellation races still need
their own tests. No process-crash/restart or complete create caller is qualified.

All 88 ordinary session controls pass on the patched and exact unpatched source.
The controls write an adapter guard marker into their disposable export even with
pytest caching disabled; this correctly prevents reuse as an immutable-input tree.
Final candidate diagnostics must run on a separately reconstructed clean export.
The 47 required product regression tests and 45 host/provenance checks pass.
The native run has one known cache_dir configuration warning and no skipped tests.

Final pinned-input verification on 2026-10-04 repeats all 17 create diagnostics
on `.codex-build/governance-g2-create-20261004-final`, lifecycle/create manifest
SHA256 `e8eaf3a4f58e8e55ab7d869d4a441db7557b6ea70381c5d6dcf9398d06b1c253`.
The separate four Patch 26 preflight-denial controls also pass with the updated
host binding. These results do not accept the create transition or G2. The
ordinary session-control parity is 88 passed on each tree, with no skips.
Context validation, syntax and whitespace checks pass. No generated source
exports or runtime artifacts are committed; all source inputs remain test-only.

## Remaining Create Work, In Order

1. Implemented, scoped: connect the prepared descriptor to a source-candidate native create entry/sink,
   with exact store/database/instance and fresh durable owner/route validation.
   Keep all other native writers denied. Use explicitly provisioned test fixtures;
   production setup/schema permissions remain G3.
2. Implemented, scoped: the protocol's bounded OS-backed projection lock and one native
   SQLite transaction for session, owner, route, receipt and projection generation.
   The synchronous authority guard surrounds actual commit; the remaining race
   and multi-process evidence belongs to step 4, not an implementation claim.
3. Implemented, scoped: strict publication, acknowledgement, outcome audit and
   Patch 28's mandatory reader/cache and fixed-session scope composition exist
   only on verified success. No copy fallback, ordinary
   recovery, JSONL fallback, blind replay or conversation-authorized repair.
4. Qualify allowed/denied create, stale versions, crash/restart, concurrent writers,
   unknown commit outcomes, failed publication/acknowledgement/audit and unsafe
   paths against actual native state and dispatch counts. Recovery is quarantined
   until an explicit authorized maintenance binding exists; no invented admin.

These are implementation details of the already approved create work, not new
milestones or a reordered plan. Do not advance to another transition or package
4 until scoped create evidence is reviewed. Full G2 acceptance requires the
remaining agreed transitions and frontend/identity work.

## Published Reader Increment

Source-only Patch 28 adds explicit native reader and scope entries. The Maya
reader checks the exact coordinator, host owner, native database, projection
bytes/generation, published receipt and fixed route before returning a detached
native SessionEntry. Cached entries are not authority; the ordinary loader fast
path, index writer, list/lookup and existence paths remain denied in mandatory
mode. History requires a separate `session.read` decision and audit.

The fixed-session request scope reuses the frozen G1 binding with append-only
limits. The projection OS lock spans selection/execution; native SQLite/store
locks do not cross execution. Native history reads validate task/thread, lease
ancestry, request, identity and database before reading and revalidate afterward.
Bounded G1 executor handoff can read the selected history. Exit clears detached
cache state and G1 revokes authority; captured expired contexts cannot read or
append. This does not authorize a general resume transition or other workers.

Reviewed reader inputs are in `governance-g2-reader.json`; preparation reconstructs
the unchanged create parent and verifies full native inventory plus reader hashes.
All 22 native diagnostics pass on the fresh reader export, manifest SHA256
`037c8f59a32ee05504569a95d45c7d85985ce280608bb398644c000e35c17797`.
The first run's allowed-append fixture used the old create-only plugin policy;
that failed run is not acceptance evidence. The corrected run changes fixture
policy only, not the frozen governance plugin. One known pytest cache_dir warning
remains; no native cases were skipped. All 47 host/provenance checks and all 47
required product regression tests pass; context, syntax and whitespace checks pass.
All 88 ordinary session controls pass on both Patch 28 and exact unpatched
Hermes. The reader export was then consumed as a disposable ordinary-control tree;
its generated adapter guard marker prevents further immutable-input reuse.

Direct SessionDB readers, other gateway index consumers, live frontend identities,
cached agent/provider approvals and full native caller composition remain outside
this increment. Cleanup failure precedence, process crash/restart, simultaneous
read/write processes, cancellation/expiry races and filesystem durability still
require step 4 evidence. No G2 acceptance, production activation, wheel or installer
change follows. Do not advance to another transition before the create gate.

## Step 4: Process-Crash Increment

On 2026-10-04 four real child-process diagnostics passed in
`tests/hermes_g2_create_crash_native.py` (SHA256
`7176b52e357c9f2a8bef145731fa154dd215771cf9e0ac8f614c245a16b5393f`).
They ran against a fresh verified Patch 28 source reconstruction with reader
manifest `037c8f59a32ee05504569a95d45c7d85985ce280608bb398644c000e35c17797`.
Accepted parent source and runtime inputs were unchanged.

The worker terminates with os._exit at four coordinator boundaries: immediately
before/after actual SQLite commit and before/after strict projection publication.
Fresh SQLite connections after process exit verify integrity and foreign keys,
native session/owner/route counts, projection generation and receipt state.
Before commit, all allocation rows roll back. After commit, the correlated
receipt remains `committed_pending_projection`; the projection is the complete
old file, or complete new file after replacement. No successful outcome audit
exists. A fresh OS-lock handle acquires exclusion after each process exit.

This is process termination and database reopen evidence, not power-loss
durability or complete host restart qualification. No agent is constructed, so
these tests do not measure full caller dispatch. Fresh-host reader/dispatch
denial after restart, concurrent native writers/readers, cancellation/expiry,
acknowledgement failure and unsafe-path races remain Step 4 work. There is no
automatic recovery or fabricated maintenance identity. Step 4 and the create
transition are not accepted; do not advance to another transition.

The initial child import failure occurred before injection and is excluded from
evidence. Corrected children use only the verified native source and Maya src
on their explicit import path. Four provenance controls, syntax, context and
whitespace checks passed. The known pytest cache_dir warning remains; no cases
were skipped. Product regressions were not rerun in this test-only increment.
No production code, patch, wheel, installer or activation gate changed.

## Step 4: Fresh-Host Restart Denial

The next increment extends the same native diagnostic file (current SHA256
`859d6c32c35bfbb37f2f4a09f9098c490c1f9a7b9c96735fd22a86604a07574a`).
All seven cases pass: the four prior crashes plus a separate fresh host after
each of the three post-commit crash boundaries. The native reader reconstruction
and accepted parent hashes remain unchanged. One known cache_dir warning occurs;
there are no skips.

The restart process opens the retained native SessionDB, binds real Maya
governance callbacks and the exact native coordinator/reader, then attempts a
route read, fixed-session scope entry and blind create. All three attempts deny.
The caller body immediately inside scope entry executes zero times. Native SQL
dump and projection bytes remain unchanged by these attempts, cache is empty
and reader authority is inactive. No fixture extension schema is provisioned
on restart and no pending receipt is repaired or replayed.

This qualifies bounded restart selection denial, not the complete native agent
loop or platform power-loss recovery. The counter measures caller-body entry,
not SDK transport or native agent construction. Tests use a trusted fixture
identity, not live connector authentication. Four provenance checks, context,
syntax and whitespace pass; product regressions are not rerun for this test-only
increment. Next within Step 4 is concurrent-process writer/reader contention,
then cancellation/expiry and the remaining failure cases. Step 4, create and G2
remain unaccepted. Production sources, wheel, installer and gates are unchanged.

## Step 4: Cross-Process Lock Contention

The diagnostic file now has SHA256
`e247961001f303edfb5c56bf48001bb25ead57dbf1a87e64a45c4112d35c4a71`.
All eight native cases pass on the same verified source reconstruction: prior
crash/restart evidence plus a two-process projection-lock contention control.
The known cache_dir warning remains and no cases are skipped.

An isolated parent native host publishes one route, then holds the coordinator's
actual OS-backed projection lock. A separate native host opens the same database
and attempts route read, fixed-session scope entry and blind create. These native
entries deny, and an additional direct coordinator probe verifies the exact
`governance.transition_busy` error rather than mistaking duplicate-route denial
for lock evidence. The denied scope body executes zero times. SQL dump and index
bytes remain unchanged; no additional native session is allocated.

After lock release a fresh host selects that same published route and enters its
bounded scope once. Duplicate create remains denied, durable state is unchanged
and cache/authority clear on scope exit. This positive control distinguishes lock
exclusion from a permanently broken reader. No model or agent loop runs.

This is cross-process lock-holder/reader/writer contention, not simultaneous
committing-writer race qualification. Simultaneous allocation/version races and
cancellation/expiry are still Step 4 work, followed by the remaining failure
matrix. Four provenance checks, syntax, context and whitespace pass. Product
regressions were not rerun for this test-only change. No production source,
native patch, wheel, installer or activation gate changed; G2 is not accepted.

## Step 4: Competing Allocation Hosts

The extended native diagnostic file has SHA256
`b9df761672d01e840d5e94ac8b18839d8651e93a6bba787db5a9f988f6d1c660`.
All nine cases pass against the unchanged verified Patch 28 reconstruction,
including the earlier crash/restart and lock-contention controls. The known
cache_dir warning remains; no cases are skipped.

Two independent native hosts open one explicitly provisioned empty fixture
database and prepare distinct fresh create authorities for the same route.
Both signal readiness before the parent releases their input barriers. The
actual native create entry publishes exactly one result and denies the other.
SQLite integrity/foreign keys remain valid; native session, owner, route and
receipt counts are each one. The receipt is published at route version one,
and generation-one projection bytes identify the same winning session. The
parent cache stays empty and independent worker audit files contain exactly
one successful outcome record. No agent or model transport runs.

Child readiness and completion are bounded; failed workers are killed and
reaped in cleanup. This is a bounded competing-allocation diagnostic, not a
fairness, stress, general transition, multi-owner or power-loss qualification.
It does not test reset/switch or recovery over newer versions. Next within
Step 4 is cancellation/expiry, then remaining acknowledgement, unsafe-path and
caller-failure cases. Step 4, create and G2 remain unaccepted.

Four provenance controls, context, syntax and whitespace checks pass. Product
regressions were not rerun for this test-only increment. Prior uncommitted test
and documentation changes were preserved. No production source, native patch,
runtime pin, wheel, installer or activation gate changed.

## Step 4: Authority Loss At Native Boundaries

Nine diagnostics in `tests/hermes_g2_create_authority_loss_native.py` pass
(SHA256 `f32b7d5a8a8550c33db9b48d5f2bd393c2b73649abd44a0bcb3092ee7ca9e76f`).
They exercise expiry, actual asyncio Task.cancel(), and explicit revocation at
three native boundaries. The verified source reconstruction and frozen parent
inputs remain unchanged. The earlier nine process diagnostics also pass. One
known pytest cache_dir warning remains; no tests are skipped.

Before commit, the native SQLite trace triggers authority loss after allocation
statements but before commit_guard reauthorization. The entire transaction rolls
back, restoring the prior SQL dump and projection. After commit, injection occurs
at publication-guard entry, outside commit_guard. After replacement, it occurs
when the acknowledgement transaction begins, outside publication_guard. Both
post-commit paths preserve one session/owner/route and a
`committed_pending_projection` receipt. Projection generation is respectively
zero or one. No successful outcome audit is written, native cache remains empty,
repeat authority use denies, no transaction remains active and OS exclusion can
be reacquired. No effect is falsely described as rolled back after commit.

Expiry uses a deterministic monotonic-clock boundary, not elapsed-time sleeps.
Cancellation is requested on the actual calling task during synchronous native
execution; the governance check observes cancellation before the next await,
and CancelledError is delivered afterward. This does not qualify unrelated-thread
revocation interleavings inside a guard or full native conversation cancellation.
No await or reentrant revoke is inserted inside commit/publication guards.
Earlier harness runs using reentrant injection are excluded as final evidence.

Four provenance controls, context, syntax and whitespace checks pass. Product
regressions were not rerun for these test-only changes. Next within Step 4 is
the remaining acknowledgement/caller-failure and unsafe-path matrix before
the create acceptance review. Step 4, create and G2 remain unaccepted. No
production source, native patch, runtime pin, wheel, installer or gate changed.

## Step 4: Acknowledgement, Caller And Path Diagnostics

Five cases in `tests/hermes_g2_create_failures_native.py` pass (SHA256
`9ffef641af1da58f159d3b5d07e1238167c39a28febd0720b4ba325160af3305`).
The combined failure, authority-loss and process suite reports 23 passed with
one known cache_dir warning and no skips on the unchanged verified Patch 28
reconstruction. Four provenance checks, syntax, context and whitespace pass.
Product regressions were not rerun for this test-only increment.

Native SQLite triggers reject receipt acknowledgement and final publication.
Acknowledgement failure retains `committed_pending_projection`; final publication
failure retains `projection_verified` even though the outcome audit was written.
Both preserve the generation-one file and allocated session, deny blind create
retry without mutation, release exclusion and expose only fixed native errors.
These cases demonstrate why an audit event alone is not dispatch authority.

Real directory replacement uses a Windows junction (directory symlink on other
platforms). Replacement before the request denies with no allocation; replacement
after actual commit denies publication with the old file and pending receipt.
These are path-validation checkpoints, not continuous path-race, ACL, hostile
lockfile replacement or power-loss guarantees. Other platforms were not run.

### Create Acceptance Blocker: Caller Completion

The caller-exception diagnostic deliberately raises after the native entry
returns its published receipt. The receipt has dispatch_allowed=false and no
caller body/agent scope is entered. No automatic compensation or second create
occurs. However, the durable receipt remains published: the current entry has
no acknowledgement of later caller completion and no durable caller-failure
quarantine. A future reader would not learn of that exception from this receipt.
The test documents this limitation; its passing status does not close the
protocol matrix's committed-but-blocked caller-failure requirement.

Recommendation, subsequently approved by the user: define a bounded host-owned caller
acknowledgement/quarantine contract within the current create work, then implement
and qualify it through a separate source overlay without rewriting accepted
parent inputs. Do not silently reinterpret every published receipt as proof of
caller completion, invent maintenance authority, or compensate automatically.
No revised contract or production behavior is implemented by this recommendation.

Step 4 and create remain unaccepted pending this contract decision and the
remaining acceptance review, including filesystem limitations and full-caller
coverage. Do not advance to another transition or frontend composition. No
production source, native patch, wheel, installer or activation gate changed.

## Approved Caller Contract Definition

The user approved the caller-acknowledgement/quarantine refinement. The first
ordered step is defined in `governance_g2_caller_acknowledgement.md` and its
machine-readable design companion. Pending caller publication is distinct from
acknowledged completion of one synchronous preparation scope; neither yields
model/tool permission. Old `published` outcomes cannot be adopted by the future
overlay. Failure-path cleanup is authority-reducing and pending remains blocked
even if cleanup fails. Later independent request failures belong to G1.

The contract validator and unit tests check design consistency and parent hashes
only, not native enforcement. Next is the separately hashed source overlay, then
native caller/reader/failure qualification before create acceptance review.
No accepted parent input, runtime enforcement, native patch, wheel, installer or
production gate is changed by this design increment.
Validation: all eight design/parent-provenance tests and all 47 required product
regression tests pass. The dedicated design validator, coupled-context validator,
syntax compilation and whitespace checks pass. Native tests are not rerun for
this definition-only increment, and no new native behavior is claimed.

## Caller Refinement Step 2: Separate Source Overlay

Source-only Patch 29 implements the bounded caller refinement in a separately
prepared native/Maya tree. Accepted G0/G1/Patch 27/28 source and their reviewed
input hashes remain unchanged. `prepare_governance_g2_caller.py` first reconstructs
the reviewed reader parent, copies the reviewed canonical Maya host sources, then
applies the exact native and staged-host patch. The full native inventory, full
portable host inventory and caller/test hashes are checked against
`governance-g2-caller-overlay.json`. Text newline normalization in the staged host
and explicit LF attributes keep reviewed inputs portable. No source export,
wheel or installer is committed.

The staged native create sink writes `published_pending_caller` directly after
publication; it never first exposes a legacy selectable `published` receipt.
The staged reader recognizes only `caller_acknowledged`, with the existing
per-read gateway/audit checks. Direct create remains pending even if it bypasses
the new bounded preparation entry, and old published rows are not adopted.

The explicit native `prepare_owned_session_candidate` entry binds the exact
Maya `CandidateCallerPreparation`. Its immutable pending receipt grants no
conversation scope, append, model or tool permission. No native SQLite/store
locks or transaction cross the body. Normal exit uses fresh acknowledge_create
policy and audit, exact native route/receipt/generation/hash checks, and guarded
SQLite compare-and-swap. Helper calls must match the exact live host scope and
its acknowledgement phase; they cannot acknowledge from inside the body.

Exception/cancellation invokes only the exact host-created cleanup descriptor,
bound to its thread/task and failure phase. Cleanup changes that pending receipt
to quarantined, never acknowledges, repairs or compensates. Cleanup failure leaves
pending blocked and preserves the original exception. Cross-store durable audit
reconciliation, production schema provisioning and frontend identities remain open.

Final reconstructed manifest SHA256:
`934b304ca0feb8b42a8997d98e466bc4e54f918340d5e59bab63326f61ba8c9f`.
Eight scoped native probes pass: normal-exit acknowledgement with pre-ack reader
denial/post-ack selection, original caller exception and CancelledError preservation,
quarantine SQL failure, acknowledgement-policy denial, direct-create pending,
legacy-published denial and early-helper denial. One known cache_dir warning
occurs; no cases are skipped. These are not the complete required-case matrix.

All ten design/overlay/parent provenance tests and all 47 required product
regressions pass. All 88 ordinary session controls pass on both patched and exact
unpatched native sources, using a separate disposable tree so the final reviewed
export remains clean. Context, syntax and whitespace checks pass. Earlier
implementation probes precede the final scoped-host/inventory checks and are
not the final pinned evidence.

Next is caller-refinement Step 3 in the agreed order: process exit before
acknowledgement, actual task cancellation, expiry/revocation, audit/SQL/unknown
commit failures, duplicate/foreign/stale descriptors and complete caller evidence.
The preparation body is trusted host-owned synchronous work, not a sandbox for
arbitrary Python or unqualified async/background jobs. No full-loop, path-race,
power-loss or production platform qualification follows from these probes.
Create Step 4/G2 acceptance, production activation, runtime pin, wheel and
installer remain unchanged and blocked.

## Caller Refinement Step 3: Bounded Failure Matrix

The separate qualification inputs and native-case mapping are in
`governance_g2_caller_qualification.md` and its machine-readable input manifest.
All twenty native cases pass: eight unchanged Step 2 probes and twelve new
failure cases. Actual task cancellation, expiry/revocation, audit/SQL failures,
unknown commit outcomes, duplicate/foreign/stale acknowledgement and process exit
before acknowledgement have bounded native evidence. The restart helper is also
hash-pinned; no implementation source or parent input changed.

The matrix covers the seventeen required scenario names, not the complete native
agent loop. Create-to-agent caller composition remains Step 3 work in the agreed
sequence before Step 4/create acceptance review. This is not a new stage or an
authorization to advance to another transition, frontend, wheel or installer.

## Approved Read-Only Recognition Dependency

The empty-history agent-loop diagnostic found native lazy recreation after a
successful create/acknowledgement. The user approved the bounded read-only fix.
Source-only Patch 30 and its separate hashed native/Maya overlay recognize exact
acknowledged state under fresh read policy/audit and a live reader-rooted executor
lease. The native cached flag cannot grant or skip recognition. No create or
metadata operation is added to the append-only G1 lease; ordinary mode is preserved.

| Boundary | Current source scope |
| --- | --- |
| Native lazy initialization | Read-only existing-session recognition in Patch 30; no mandatory lazy allocation. |
| New empty-history caller loop | Actual native acknowledgement/reader/task/executor/AIAgent with real SDK, synthetic HTTP and zero retries. |
| Optional prompt-cache metadata | Write denied; native prompt-building caller catches/logs and continues. Catch and omission semantics remain unqualified. |
| Provisioning, metadata lifecycle, frontends and production | Still outside recognition; no G2 or installer acceptance. |

Consult `governance_g2_existing_session_recognition.md` before further changes.
Review the optional cache boundary before declaring complete create-loop evidence;
do not widen metadata authority or proceed to another transition implicitly.

The final recognition manifest SHA256 is
`89446a4f051e42884cc525623efa48c0e73f4336575cf0f9305dc0a688e620b0`.
Twenty-four native recognition/loop cases pass with no skips, including actual
empty-history allowed inference/persistence and independently denied model egress
after successful recognition. The denied egress produces zero synthetic HTTP
requests. Recognition happens before model authorization; no lazy native create
is called on the allowed path. Thread/task/request/classification, foreign-root,
cached-flag, pending/legacy/stale state, gate/policy/audit and audit-time revocation
denials are covered without broadening the lease.

Three actual lazy-initialization ordinary controls pass on both the patched
overlay and a fresh exact-pin unpatched export. The twenty frozen caller/failure
cases pass against the unchanged reconstructed parent. Fifteen repository
provenance/design checks pass. Native pytest runs have only the known cache_dir
configuration warning. This is bounded source evidence, not full-fork, live-provider,
prompt-cache catch, frontend, platform or product qualification.

All 47 required product regressions pass. The context validator, release-tool and
new Python syntax checks, whitespace checks and full post-test parent/native/host
inventory verification also pass. Generated source exports remain uncommitted
under the ignored build directory. No production runtime, wheel or installer was
modified or rebuilt by this increment.

## No-Snapshot And Process-Restart Caller Evidence

The approved optional-cache dependency is now implemented as source-only Patch 31;
its scoped mode/catch tests and limitations are in `governance_g2_prompt_cache_review.md`.
Separate two-process qualification over that unchanged overlay is in
`governance_g2_restart_loop.md`. Four native cases cover allowed continuation,
wrong owner, denied cache mode and stale projection with actual persisted history.
The restarted host issues fresh append-only request authority and grants no
create/acknowledgement permission. No projection repair or legacy adoption occurs.

This closes the identified bounded process-restart conversation evidence gap,
not production schema/provisioning, frontend identities, general resume or
complete create acceptance. The next approved action is reconciliation of
Step 3/create-loop evidence with the Step 4 acceptance criteria and exclusions.
Do not advance to another transition, work package 4, activation or installers.

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

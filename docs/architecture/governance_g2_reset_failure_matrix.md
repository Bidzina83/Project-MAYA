# G2 Reset Step 4 Failure Matrix

## Current Scope

The user accepted bounded reset Step 3 and authorized Step 4 on 2026-10-07.
The original batches use the unchanged, inventory-verified Patch 34 source.
On 2026-10-08 the user approved the bounded host-only Patch 35 publisher correction
and affected create/reset requalification before remaining path/parity checks.
Hermes source remains unchanged; no installer, production activation, schema
provisioning or maintenance identity is authorized. Earlier inputs remain frozen.

## Agreed Matrix

| Step 4 gate item | Progress |
| --- | --- |
| Actual process crash and fresh-host restart | Initial eight-boundary batch passes; remaining combined-fault qualification is still open. |
| Process contention, competing reset and busy old request | Four bounded native process cases pass; broader worker and combined-fault coverage remains open. |
| Late executor and cancellation outliving its caller | Three bounded old/new native caller cases pass; general workers and remaining cancellation/fault combinations stay open. |
| Revoke, expiry, cancellation and stale/replayed/foreign descriptors | Eighteen combined-candidate descriptor/revocation/expiry cases pass, with the preceding three late-caller cancellation cases. Scope and remaining combined faults are below. |
| Unknown commits and combined commit/publication/acknowledgement faults | Thirteen bounded combined-failure cases pass, including four fresh-process probes; separate lower-level storage and audit failures remain next. |
| Separate write/flush/fsync/replace/acknowledgement/audit failures | Frozen Patch 34 passes eleven of twelve; short write corrupts the projection. Approved host-only Patch 35 passes all twelve unchanged storage cases and 200 total affected requalification cases; separate evidence is below. |
| Unsafe paths and ordinary-mode parity | Twenty-six corrected-profile path cases pass. All 331 ordinary outcomes match pinned unpatched Hermes, including nine unchanged Windows shell-path failures; exclusions and criterion review are documented separately. |
| Bounded reset acceptance | Pending full criterion review and user decision. |

This is the existing Step 4 gate, not a new milestone or reordered dependency.
The first batch follows its process crash/restart item before contention work.
Do not describe first-batch success as complete Step 4 or advance to another
transition until the full matrix and acceptance review are complete.

## Process Boundary Contract

Terminate real workers without Python cleanup at eight boundaries: before/after
native reset commit, before/after the strict projection publication helper, pending caller
body, before/after acknowledgement commit and after confirmed preparation.
Independent SQLite connections check integrity, retained source messages and
metadata, owner/parent lineage, route version, receipt and projection generation.
Kernel lock release is checked without repair or takeover of a live request.

A precommit crash must leave the complete original database/projection unchanged;
fresh authenticated selection of the still-acknowledged create source is allowed.
Every postcommit crash retains committed reset effects but denies fresh-host
routing, including acknowledged receipts whose process-local confirmation died.
Restart cannot reopen the source, allocate a new session, replay publication or
fabricate reconciliation authority. No agent, model or tool is run in this batch.

Production storage durability, power loss, live frontend credentials, full
workers/tools and maintenance reconciliation remain excluded by existing gates.

## First Batch Evidence

2026-10-07: all eight cases in `tests/hermes_g2_reset_crash_native.py` pass on
the unchanged final Patch 34 stage. Sixteen independent workers execute actual
termination/restart, not mocked rollback. Each worker verifies the effective
source/host inventories and fixture hashes; the supervisor also verifies the
frozen source ancestry. Boundaries and retained outcomes are:

| Crash boundary | Durable reset receipt | Fresh authenticated host |
| --- | --- | --- |
| Before native commit | None; complete original database/projection unchanged | May select the original acknowledged create source. |
| After native commit | committed_pending_projection; old projection | Denied, no repair. |
| Before publication helper | committed_pending_projection; old projection | Denied, no repair. |
| After publication helper | committed_pending_projection; new projection | Denied, no repair. |
| Pending caller body | published_pending_caller | Denied. |
| Before acknowledgement commit | published_pending_caller after native SQLite rollback | Denied. |
| After acknowledgement commit | caller_acknowledged, no surviving confirmation | Denied. |
| After confirmed preparation | caller_acknowledged, previous process confirmation lost | Denied. |

The before-publication case stops before the helper begins; it is not a crash
between temporary-file write/fsync and replacement. Those separate fault points
remain in the pending matrix. Checks confirm integrity, foreign keys, retained
messages/source metadata, reset parent/owner/route version, projection generation,
kernel lock release, and no row/projection mutation by restart. No agents, model
requests or tools execute. The one pytest cache-provider configuration warning
is unchanged from earlier native runs; there are no skipped cases.

All 50 required product/manifest regression cases pass (47 product plus three
new manifest checks). Context, syntax and whitespace checks pass. The
machine-readable evidence is `governance-g2-reset-crash.json`; it preserves
`pending_review` and does not change Patch 34 or its acceptance record.

The next batch in the existing Step 4 sequence was process contention, competing
resets and busy old requests; its evidence is recorded below. No next transition,
installer or production activation is authorized by the crash/restart batch.

## Contention Batch Evidence

2026-10-07: four cases in `tests/hermes_g2_reset_contention_native.py` pass on
the unchanged Patch 34 profile. Five separate worker processes reopen explicitly
provisioned native fixtures. File-based readiness/release barriers synchronize
actual processes; they do not simulate storage contention with timing assertions.
Every worker verifies effective source/host and fixture hashes before native use;
the supervisor also verifies the frozen source ancestry.

| Contention boundary | Observed outcome |
| --- | --- |
| Old authenticated G1 request holds projection exclusion | Another process's reset denies without changing the complete database/projection or old cache/lease. The lease revokes on normal exit; the host can then reset and acknowledge. |
| Native reset paused immediately before real commit, with its transaction and projection lock held | Competing preparation denies; an independent SQLite reader still sees the complete original committed state. The original native transaction then commits and preparation acknowledges. |
| Two independently prepared descriptors for the same acknowledged create source | Exactly one atomic reset commits; the other denies. One target, receipt, route increment and generation increment exist. Publication stays pending and the original projection remains unchanged; routing is denied. |
| First reset's caller body remains pending | Competing reset denies even though no SQLite transaction spans the caller body. Database/projection remain unchanged by the contender; the original preparation can subsequently acknowledge. |

Checks include integrity/foreign keys, full retained source metadata except the
authorized end fields, all original message rows, empty target transcript, same
owner/parent lineage, receipt/version/generation, and actual host-confirmed reader
selection after successful acknowledgement. No agents, model requests or tools
execute. Started workers are reaped; native fixture resources are closed. The
unchanged cache-provider configuration warning remains; there are no skips.

All 53 required product/provenance regression cases pass (47 product, three new
contention-manifest checks and three unchanged crash-manifest checks). The final
contention input contract is `governance-g2-reset-contention.json`, retaining
`pending_review` and `production_qualified=false`. Context, syntax, whitespace and
post-run source/host inventory checks pass. Earlier patches, manifests and tests
remain frozen; no new runtime overlay is introduced.

This is one same-owner, initial create-to-reset profile, not general worker,
fairness/stress, repeat-reset, cancellation, maintenance or power-loss
qualification. Next in the existing Step 4 sequence: late executors and
cancellation outliving their caller. Remaining descriptor/fault/path/parity
combinations and the explicit acceptance review remain open. Step 4, bounded
reset, G2 and production are not accepted by this batch.

## Late Executor Batch Evidence

2026-10-07: three cases in `tests/hermes_g2_reset_late_executor_native.py` pass
on unchanged Patch 34. Each runs two actual native gateway callers, AIAgents,
selected executor threads and native SQLite, using the real SDK with synthetic
HTTP stream responses. The old caller is cancelled while its already-authorized
request is paused in synthetic transport. After caller exit and lease revocation,
the host performs one acknowledged reset and starts a freshly authenticated
request. The old thread resumes while that new request is still active.
Identity is explicitly host-bound by the isolated fixture; this is not live
frontend or connector authentication qualification.

| Cancellation scenario | Observation |
| --- | --- |
| Native caller cancellation | Caller exits, root authority revokes and old runtime slot releases before reset; the still-running old thread cannot borrow the fresh request's authority. |
| Repeated cancellation during native cleanup | A second cancellation interrupts a test-held cleanup await after native synchronous revocation. Caller scope/exclusion still release, and the same late-action denials hold across reset. |
| Selected child temporarily swallows cancellation | A test wrapper holds the actual selected receiver after its original handoff has revoked authority. The caller can exit while that child/thread remain alive; resumed child actor access and old-thread late actions deny. |

Repeated/swallowed cancellation are explicit test fault injections around the
existing native cleanup/handoff, not new runtime behavior or a claim that normal
Hermes deliberately swallows cancellation. No accepted source or fixture is edited.
The final input contract hashes the unchanged source/host inventories, earlier
fixtures and the separate contention fixture; source ancestry is verified too.

All seven old-thread probes deny: model execution, tool execution, output
validation, append to the old session, append to the new session, ordinary native
route reset, and candidate reset preparation. Inert model/tool handlers are never
called. While the new request remains active, the complete SQLite dump, routing
file, detached cache and fresh root authority remain unchanged by the old thread;
the audit suffix contains only denials. The old context retains its old session
and revoked lease, and cannot acquire the new request/session identity.

Each case observes exactly two actual SDK transport attempts: the old request
authorized before cancellation and the separately authorized fresh request. Native
agent initialization and per-request stream setup create four SDK client objects,
but the two initialization clients make no requests. All four have zero SDK retries;
no late transport attempt is made. Request cancellation does not undo the first
authorized request or kill a Python thread. A fresh agent completes normally with
initially empty target history, no old-history sentinel, retained old messages, one reset
receipt, route version two, and clean native integrity/foreign-key checks.

The test socket guard is installed after Windows asyncio initializes its internal
wake-up connection, and removed before event-loop teardown. Product socket attempts
are denied; synthetic HTTP does not use network sockets. Native threads are observed
to finish before SDK/database fixture cleanup. Private late-output/write sentinels
are absent from captured stdout, stderr and logs. This is a scoped sentinel check,
not qualification of every production diagnostic or provider error path.

All 56 required product/provenance regressions pass (47 product plus nine manifest
checks across crash, contention and late-executor batches). The final native run
has the unchanged cache-provider configuration warning and no skips. Context,
syntax, whitespace and post-run frozen inventory checks pass. Evidence is
`governance-g2-reset-late-executor.json`, with `pending_review` and
`production_qualified=false`. Initial harness failures were corrected without a
runtime patch: Windows loop initialization was incorrectly socket-blocked, and
client-object construction was incorrectly counted as an API request.

Next in the existing Step 4 matrix: final combined revocation/expiry and
stale/replayed/foreign descriptor qualification, followed by remaining commit,
publication/acknowledgement/audit, path and ordinary-mode parity cases. These
three cases do not qualify arbitrary/background workers, live providers, connector
delivery, general tools, production provisioning or thread termination. Bounded
reset acceptance, G2, wheels, installers and production activation remain open.

## Descriptor and Authority Batch

2026-10-07: all 18 cases in `tests/hermes_g2_reset_descriptors_native.py` pass
against unchanged frozen Patch 34, using native SessionStore/SQLite and the
existing host fixtures. The manifest is `governance-g2-reset-descriptors.json`;
it remains `pending_review`, with `production_qualified=false`.

- Revocation and expiry before atomic consumption preserve the complete SQL dump
  and original projection, with the original acknowledged create still readable.
- Revocation and expiry before publication retain the committed pending reset,
  original projection and blocked routing; no fake rollback or acknowledgement.
- Revocation and expiry during the pending caller body quarantine the receipt,
  retain source metadata/history and the empty target, and deny routing.
- Changed principal, database, instance, route, binding version, source, target
  and operation descriptors cannot allocate. These exercise prepared-descriptor
  identity enforcement, not resistance to arbitrary trusted-host code mutation.
- A genuinely consumed authority cannot replay; an exited authority cannot borrow
  a fresh preparation; an unrelated thread cannot inherit reset authority.
- A separate real process completes and acknowledges a reset while the original
  descriptor remains live. Its subsequent stale attempt cannot allocate or alter
  SQL/projection state. Durable acknowledgement alone does not replace the
  exited process's host confirmation, so the original host still denies routing.

No model or tool execution occurs in this batch. Cancellation evidence remains
the preceding native caller batch, not newly qualified arbitrary worker behavior.
The native run has no skips and the existing cache-provider configuration warning.
Its initial harness run rejected an incorrect manifest reference before executing
tests; the reference was corrected without changing native sources.

All 59 product/provenance regressions pass (47 product and twelve manifest
checks). Context validation, syntax checks, whitespace checks and post-run
frozen native/host inventory checks pass. Earlier evidence inputs are unchanged.

Next in the agreed Step 4 sequence is combined unknown-commit and publication/
acknowledgement fault qualification, then separate storage/audit failures,
unsafe paths, ordinary-mode parity and explicit acceptance review. These cases
do not close reset Step 4, G2 or production qualification. No runtime patch,
production gate, wheel or installer changed.

## Combined Outcome Fault Batch

2026-10-08: all 13 cases in `tests/hermes_g2_reset_combined_faults_native.py`
pass on unchanged frozen Patch 34. Four independent restart processes also deny
selection without changing SQL/projection state. The input manifest is
`governance-g2-reset-combined-faults.json`, still `pending_review` and
`production_qualified=false`.

| Injected failure | Observed durable reset receipt and readiness |
| --- | --- |
| Native commit succeeds but reports failure | `committed_pending_projection`, original projection, no publication or retry. |
| Strict publication helper succeeds but reports failure | `committed_pending_projection`, complete new projection, blocked. |
| Publication-state commit succeeds but reports failure | `projection_verified` or `published_pending_caller`, no host confirmation. |
| Acknowledgement commit fails before/after commit, normal cleanup | `caller_quarantined`, retained committed lifecycle state. |
| Same acknowledgement failures plus unavailable quarantine helper | `published_pending_caller` before commit, or `caller_acknowledged` after commit; both blocked without host confirmation. |
| Same acknowledgement failures plus failed cleanup audit writer | `caller_quarantined`; reducing readiness is still permitted, without claiming a durable cleanup audit. |
| Required publication audit fails | `projection_verified`, no pending-caller advancement. |
| Required acknowledgement audit and cleanup audit both fail | `caller_quarantined`, never ready. |
| Caller raises and quarantine helper also fails | Original caller exception preserved; `published_pending_caller`, blocked. |

The tests use real native SessionStore/SQLite. They inspect retained source
metadata/transcript, empty target, owner lineage, single receipt, route/generation
increments, integrity, no transaction leak, missing confirmation, empty cache
and zero agent/model dispatch. Both reader entries and a new reset preparation
deny; complete SQL/projection snapshots remain unchanged during those attempts.
Fresh processes check the unknown native commit, uncertain publication, and both
before/after acknowledgement cases with unavailable quarantine. No automatic
reconciliation, source reopening or blind retry is granted.

Audit faults are injected into the actual audit sink writer, allowing the native
typed-error handling to execute. Unavailable quarantine is a helper-boundary
failure, not qualification of every cleanup SQL or storage failure. The first
diagnostic version injected raw errors at the audit wrapper and produced three
incorrect quarantine expectations; the final exact-hashed suite corrects that
injection and passes all cases. No native candidate bytes were changed.

All 62 product/provenance regressions pass (47 product and fifteen manifest
checks). The final native run has no skips and the existing cache-provider
configuration warning. Source ancestry, frozen inventories, context, syntax and
whitespace checks pass; earlier evidence inputs remain unchanged.

Next is the existing separate write/flush/fsync/replace and remaining audit-fault
matrix, followed by unsafe paths, ordinary-mode parity and explicit acceptance
review. No live provider, arbitrary worker, storage power-loss, durable audit
reconciliation, production provisioning or maintenance recovery is qualified.
Reset Step 4, G2 and production remain unaccepted; runtime pin, wheels and
installers are unchanged.

## Storage Qualification Blocker

2026-10-08: `tests/hermes_g2_reset_storage_native.py` runs all twelve cases against
unchanged frozen Patch 34: eleven pass and one fails. The evidence input is
`governance-g2-reset-storage.json`, with `pending_review` and
`production_qualified=false`. The failing regression is preserved, not skipped,
xfail-marked or weakened. This is not a passed qualification batch.

All 65 product/provenance regressions pass (47 product and eighteen manifest
checks); that does not override the failing native gate. Context, syntax,
whitespace and post-run frozen inventory checks pass. The native run has no
skips and the existing disabled-cache-provider configuration warning.

Passing cases inject temporary-file creation failure, partial write plus error,
flush failure, fsync failure, EXDEV/EBUSY replacement failures, actual authorization
audit-writer failure at route-read/source-end/acknowledgement, and native SQLite
authorizer denial of acknowledgement or quarantine receipt updates. Precommit
audit failure preserves the complete original SQL/projection; postcommit failures
retain one reset, source history and an empty target with blocked routing. Temporary
files are removed; failed strict replacement does not use a copy fallback.

### Reported Short Write

The real publication helper in staged
`src/project_maya/hermes_plugins/session_creation.py`, `_publish`, calls
`stream.write(raw)` without checking its returned byte count. It flushes/fsyncs
and replaces the old index before checking installed bytes. The injected stream
writes half the bytes to the real temporary file and reports that short count.
The candidate replaces the index with those incomplete bytes and only then raises
the typed failure. The actual caller does not become ready, but the original
complete projection is lost. An independent read-only SQLite inspection confirms
two sessions, route version two and `committed_pending_projection`; the published
projection is truncated. This violates the consistency protocol's old-or-new
complete-file requirement, not its deny-on-uncertain-readiness rule.

This is fault-injection evidence at the writer contract, not a claim that normal
blocking buffered file writes routinely return short counts, or evidence of a live
customer incident. The defect is in the shared Maya-owned candidate helper; no
change to the upstream Hermes runtime or installed wheel is inferred.

### Approved Correction Order

1. Review a bounded separately versioned correction over frozen Patch 34: require
   a complete reported write and verify completed temporary-file bytes before
   strict replacement. Preserve locks, lifecycle records, typed errors, temporary
   cleanup, no-copy behavior and post-replacement verification. No automatic repair.
2. Requalify this unchanged failing regression and the affected reset/create
   publication and failure profiles on the new candidate. Preserve accepted
   earlier manifests and source bytes; do not retrofit their evidence hashes.
3. Only then resume the existing unsafe-path and ordinary-mode parity matrix,
   followed by explicit bounded reset acceptance review.

The user approved this exact order on 2026-10-08. Patch 35 only changes the shared
Maya-owned publication helper; Hermes execution source remains identical to Patch
34. See `governance_g2_publisher_correction.md` for the separately versioned
candidate and requalification results. No new milestone, transition, schema,
maintenance identity, production gate, runtime pin, wheel or installer is
authorized. Reset Step 4 remains open.

### Corrected Candidate Requalification

2026-10-08: all 167 create/reset requalification and all 33 earlier Step 4 replay
cases pass on the separately versioned Patch 35 host-only correction. This
includes the unchanged short-write regression, six new complete-byte/count
checks across create and reset, crash/restart, process contention, descriptor
authority and actual native late-caller cancellation. There are no skips; each
native run retains the existing disabled-cache-provider configuration warning.
All 71 product/provenance regression tests, context, syntax and whitespace checks
pass. Source/host inventories and frozen parent ancestry are verified separately.
See `governance_g2_publisher_correction.md` and its two hashed input contracts.

The corrected profile does not change Hermes source or installed artifacts.
Unsafe paths and ordinary-mode parity are the next agreed Step 4 checks;
explicit bounded reset acceptance review follows them. The correction and replay
do not accept Step 4, G2, full-fork governance or production support.

### Final Paths And Ordinary Parity

2026-10-08: the remaining bounded path/parity item is qualified on unchanged
Patch 35. All 26 path cases pass, including five actual Windows directory-junction
boundaries and separately labelled attribute probes. The final ordinary runner
executes 331 cases on each disposable corrected/unpatched source: identical 322
passes and nine known Windows shell-path failures, no skips/errors, and unchanged
source inventories. Native tests are the original pinned bytes. Existing shell
failures are retained, not presented as healthy platform behavior.

All 77 product/provenance regression cases pass. Evidence, reproducible commands
and limits are in `governance_g2_reset_paths_parity.md`; the immutable input is
`governance-g2-reset-paths.json`. No runtime patch or installed artifact changes.
The criterion reconciliation and bounded acceptance recommendation are in
`governance_g2_reset_acceptance_review.md`. The next action is the user's explicit
bounded reset acceptance decision, not another transition or installer rebuild.

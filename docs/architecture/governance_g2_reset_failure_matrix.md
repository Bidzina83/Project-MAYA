# G2 Reset Step 4 Failure Matrix

## Current Scope

The user accepted bounded reset Step 3 and authorized Step 4 on 2026-10-07.
Use the unchanged, inventory-verified Patch 34 source. No new runtime patch,
installer, production activation, schema provisioning or maintenance identity is
authorized by these tests. Earlier accepted inputs remain frozen.

## Agreed Matrix

| Step 4 gate item | Progress |
| --- | --- |
| Actual process crash and fresh-host restart | Initial eight-boundary batch passes; remaining combined-fault qualification is still open. |
| Process contention, competing reset and busy old request | Four bounded native process cases pass; broader worker and combined-fault coverage remains open. |
| Late executor and cancellation outliving its caller | Three bounded old/new native caller cases pass; general workers and remaining cancellation/fault combinations stay open. |
| Revoke, expiry, cancellation and stale/replayed/foreign descriptors | Existing scoped evidence; final combined qualification pending. |
| Unknown commits and combined commit/publication/acknowledgement faults | Existing Step 3 counterexample regression; remaining combinations pending. |
| Separate write/flush/fsync/replace/acknowledgement/audit failures | Pending final matrix. |
| Unsafe paths and ordinary-mode parity | Existing controls/exclusions; final qualification pending. |
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

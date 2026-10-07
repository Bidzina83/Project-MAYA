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
| Process contention, competing reset and busy old request | Pending. |
| Late executor and cancellation outliving its caller | Pending. |
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

Next in the existing Step 4 sequence: process contention, competing resets and
busy old requests. Late executors, cancellation, remaining combined failures,
unsafe paths and final parity/acceptance still require qualification. No next
transition, installer or production activation is authorized by this batch.

# G2 Create Caller Acknowledgement

## Status And Boundary

The user approved this refinement of G2 work package 3, create Step 4.
This document defines the contract. Its machine-readable
companion is `governance-g2-caller-contract.json`. The validator checks design
consistency, not runtime behavior. Source-only Patch 29 implements a separate
staged native/Maya overlay; scoped probes are not complete qualification.
No acceptance, wheel, installer or production activation is established.

Caller completion means normal exit from one host-owned synchronous preparation
scope. It does not mean successful future conversation, delivery or application
execution. The scope may prepare detached caller-local metadata but may not
construct/run an agent, select a conversation, append messages, call a model/tool,
disclose business data or perform external side effects. New async suspension,
executor handoff and frontend identity composition are outside this increment.
Failures after successful scope exit belong to a separate governed request/G1
lifecycle, not retroactive failure of this preparation scope.

## Receipt States

Use the existing correlated receipt in the native Hermes SQLite database.
No second registry or SMB-memory table is introduced.

| State | Meaning | Reader selection |
| --- | --- | --- |
| committed_pending_projection | Native allocation committed, projection unfinished. | Denied |
| projection_verified | Projection verified, publication audit unfinished. | Denied |
| published_pending_caller | Publication/audit complete; preparation not acknowledged. | Denied |
| caller_acknowledged | Host preparation exited normally and guarded acknowledgement committed. | Separately authorize |
| caller_quarantined | Scoped caller failed/cancelled and safe quarantine marking succeeded. | Denied |
| published | Legacy Patch 27/28 outcome with no caller acknowledgement proof. | Denied in the new overlay |

Old source artifacts keep their original semantics and hashes. The new overlay
must not adopt or backfill old `published` rows. Missing, unknown or unsupported
states block. No automatic schema provisioning, administrative identity or repair
is introduced. Fixture schema preparation is explicit; production provisioning
and durable cross-store audit reconciliation remain G3.

## Host-Owned Preparation Scope

1. Authenticate the configured owner and mint fresh single-use create authority.
2. Validate exact store/database/instance, route/version, classification and
   binding. Allocate and publish through the native guarded transaction protocol.
   Its final pre-return state is `published_pending_caller`, never selectable.
3. Yield an immutable pending receipt to the bounded host preparation body.
   IDs and receipts are correlation data, not bearer authority. No conversation
   scope, operational cache, model or tool privilege is issued.
4. On normal exit, recheck same thread/task, cancellation, expiry, revocation,
   descriptor digest, principal, classification, binding, route, target, generation
   and projection hash under projection/store/database exclusion. No locks or
   SQLite transaction are held across the preparation body. A competing operation
   cannot acknowledge or repair its pending receipt.
5. Reauthorize exact `session.transition` operation `acknowledge_create` through
   the existing gateway. The original create permission is not acknowledgement
   permission. Constrained/redacted/confirmation/deferred decisions do not grant
   acknowledgement. Audit acceptance must succeed before the guarded SQLite CAS.
6. Within BEGIN IMMEDIATE revalidate durable state and authority, then CAS only
   that correlated `published_pending_caller` row to `caller_acknowledged`.
   Serialize revocation with actual commit; do not await or revoke reentrantly.
   Unknown commit outcome reports uncertainty and grants no caller dispatch.
7. Successful completion reports the durable acknowledged outcome. It still
   does not dispatch or grant model/tool permissions. A separate native reader
   must authenticate/authorize and verify the acknowledged route before issuing
   a G1 append-only scope. Reader checks are not skipped because of a receipt.

The exact scope/reader entry and overlay source inventory must be defined and
hashed during implementation. It must make legacy native create entries unable
to bypass the pending-caller state. Do not implement this only as an outer wrapper
around an entry that first writes selectable `published` state.

## Failure And Cleanup

Exception, BaseException cancellation, expiry or revocation prevents normal-exit
acknowledgement. Committed records and transcripts are retained, not rolled back
or deleted after commit. The already durable pending state is fail-closed even
if cleanup never executes, the process exits or quarantine storage fails.

Quarantine is an authority-reducing cleanup operation for that one still-pending
receipt. A host-owned descriptor binds the same native database, instance, owner,
route/version, target and correlation/digest. It grants no append, lifecycle,
repair, replay or acknowledgement permission. The implementation must distinguish
this cleanup descriptor from expired/revoked create authority. Under exclusion,
CAS pending to quarantined only if its exact durable bindings still match.
Never alter newer routes or acknowledged outcomes; mismatch leaves routing blocked
and reports cleanup failure, without inventing maintenance authority.

Use fixed failure codes only. Failure-path audit must be attempted without raw
caller exceptions, prompts or credentials. Audit/storage/lock failures during
cleanup must not replace the original typed denial, caller exception or
CancelledError. Pending remains blocked. Audit events are not proof of SQLite
outcome. Cross-store durable reconciliation remains G3.

A repeat acknowledgement is not another grant or write. A bound status check
may confirm the same acknowledged correlation; foreign, mismatched or stale
receipts deny. Conversation authority cannot retry allocation, repair an index,
adopt legacy receipts or clear quarantine.

## Ordered Implementation And Acceptance

1. Completed design increment: this contract, machine-readable states and
   consistency tests. These tests do not enforce Hermes behavior.
2. Implemented, scoped: separate source overlay and immutable preparation inputs over the
   unchanged accepted parent. Enforce pending state at the native sink; implement
   the bounded host scope, acknowledgement CAS and authority-reducing cleanup;
   update the exact native reader to require acknowledged state.
3. Next: qualify all machine-readable required cases with actual native SessionStore,
   SQLite, publication and caller scope: success, failure/cancellation/expiry,
   process exit, policy/audit/SQL/unknown commit outcomes, quarantine failure,
   duplicate/foreign/stale acknowledgement and before/after-ack reader denial/allow.
   Observe native rows, file bytes, audit outcomes and caller/dispatch counters.
   Preserve ordinary controls on pinned unpatched Hermes.
4. Review create acceptance against the full Step 4 matrix and remaining path,
   caller and platform limitations before any other G2 transition. Acceptance
   of this bounded design does not accept create, G2 or production governance.

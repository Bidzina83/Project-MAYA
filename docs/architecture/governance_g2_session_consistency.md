# G2 Session Consistency Protocol

## Status And Scope

G2 work package 2, 2026-10-04. Design deliverable following
`governance_g2_session_ownership.md`; no native implementation or runtime
qualification is claimed. Work package 3 implements and tests one transition at
a time. Frontend composition remains package 4, administrative identities package
5, and production schema provisioning and durable audit reconciliation remain G3.
No production activation, runtime pin, wheel or installer changes follow.

## Native Evidence

Reviewed effective Patch 26 source at
`.codex-build/governance-g1-lifecycle-20261004-b/source`, based on pinned Hermes
`b13e2fd6948a59eeb59fe618914147d97a2ee90a`:

- `gateway/session.py`, `SessionStore._save`: replaces the whole sessions.json
  file after temporary-file flush/fsync; its lock is process-local.
- `utils.py`, `atomic_replace`: follows symlinks and falls back to copy for
  EXDEV/EBUSY. The fallback is not an atomic replacement and is unsuitable for
  the mandatory routing projection.
- `SessionStore.get_or_create_session`, reset and switch: index mutations precede
  separate SQLite operations; ordinary catches can leave a route without its row.
- `hermes_state.py`, `SessionDB._execute_write`: BEGIN IMMEDIATE, callback, commit
  and rollback; governance precedes lock acquisition. Existing authorization alone
  does not establish an in-transaction version/revocation check.
- Compression and inner/outer gateway callers can separately change session IDs
  and save the index. The package 1 inventory identifies these additional roots.

These are source observations, not crash tests or platform durability evidence.

## Authority And Records

Use the existing Hermes conversation SQLite database. Maya SMB memory stays
separate. Neither sessions.json, cached entries nor caller-supplied IDs authorize
a session. Proposed versioned native extension tables (not yet provisioned):

| Record | Required fields and constraints |
| --- | --- |
| `maya_session_owners_v1` | Unique native session ID, instance/database identity, principal, classification floor, binding version, lifecycle status, optional parent; foreign key to native sessions. |
| `maya_session_routes_v1` | Unique host-selected route slot, owner, target session, monotonically increasing route version and correlated operation; target must have the same verified owner. |
| `maya_session_transitions_v1` | Unique correlation ID, descriptor digest, actor/binding versions, operation, source/target, expected/result route versions, policy decision reference, state and projection generation/hash. No prompts, tokens or secrets. |
| `maya_session_projection_v1` | Singleton instance/database-bound generation and hash of the canonical complete routing projection. |

Foreign-key enforcement, supported schema version and database identity are
verified before use. Missing/corrupt/unowned legacy records block, without schema
creation, automatic adoption, JSONL fallback or repair by conversation authority.
Tests may explicitly provision isolated fixtures; product provisioning stays G3.
This extends native session state, not a second session engine or plugin registry.

## Serialization And Authorization

The candidate host is the only mandatory writer to this projection. An exclusive,
bounded cross-process lock on the canonical database/projection pair covers the
complete transition through projection acknowledgement. Lock order is projection
lock, then native SQLite write lock/transaction. No async suspension or external
call occurs while a SQLite transaction is held. Busy, unsafe lock storage or
unknown lock ownership blocks; a process-local threading lock is insufficient.
The platform lock implementation and crash-release behavior require package 3
evidence. Unsupported filesystems remain blocked.

Under that lock authenticate afresh, resolve owned sessions and authorize the
exact descriptor through Maya's existing gateway, including consequential reads
and native create/end/reopen permissions. Audit acceptance must be available
before mutation. Capture immutable decision references, not reusable privileges.
Prepare replacement rows and canonical projection bytes before destructive writes.

Inside BEGIN IMMEDIATE recheck owner, route, binding and schema versions, exact
descriptor digest, expiry and the G1 root lease. Lease revocation and commit must
share an explicit host synchronization boundary: revocation linearized before
commit prevents commit; revocation after commit prevents further dispatch but
does not erase the committed effect. Package 3 must prove this race contract;
checking a flag before waiting for the SQLite lock is insufficient.

## Commit And Publication

1. Validate the descriptor and permissions without changing route, cache or IDs.
2. In one native SQLite transaction write permitted native session lifecycle
   changes, owner/route records, the next projection generation/hash and a
   `committed_pending_projection` correlation receipt. Compare-and-swap the
   expected versions; any failed check rolls back all these changes. Do not call
   independently committing public methods inside this transaction.
3. SQLite commit is the authoritative state boundary. It is not atomic with JSON
   or audit storage. Unknown commit outcome requires a receipt lookup, not replay.
4. Publish the complete derived projection using a same-directory restrictive
   temporary file, flush/fsync, then strict same-filesystem replacement. Reject
   symlink/reparse escapes and cross-device/copy fallback. Preserve approved
   directory/file access controls; do not inherit arbitrary host permissions.
   Verify the installed generation, instance/database identity and canonical hash.
5. A second guarded SQLite transaction records `published`, conditioned on the
   unchanged generation/hash. Required outcome audit must succeed before dispatch.
   If audit outcome is unavailable, report committed-but-blocked, not success.
6. Refresh caches from authoritative state, revoke the old fixed-session scope,
   and issue a new scope only after identity, publication and outcome checks pass.

The JSON representation includes a versioned projection envelope. Native loading
must explicitly recognize it rather than misreading metadata as session entries.
Every mandatory reader verifies SQLite generation/ownership and the projection
hash before returning routes or disclosing metadata. Foreign/forged entries,
stale cache and unbound direct writers block; no ordinary-mode fallback.

Flush/replace is not a portable power-loss durability guarantee. Directory
durability and Windows replacement semantics require platform evidence. A restart
always compares the actual file to authoritative SQLite. No cross-store atomicity
or production Windows support is asserted.

## Recovery, Replay And Compensation

On startup, mismatched/missing projection or pending receipts quarantine routing
before any agent construction. Recovery requires a separately host-authenticated,
explicitly authorized maintenance identity; an expired conversation descriptor
cannot become repair authority. Until package 5 qualifies that binding, fail
closed and report recovery required. Package 3 may use explicit isolated fixture
authority, not a fabricated product administrator.

Recovery validates the database, owner constraints and receipts, acquires the
same lock, and regenerates the complete projection from current committed routes.
It never replays stale receipt bytes over newer routes. It verifies publication,
acknowledges the current generation and audits recovery with original correlation
IDs. Corrupt/missing SQLite authority cannot be reconstructed from JSON alone.

The same correlation ID with a different descriptor digest is denied. An owned,
authorized status lookup may return the recorded outcome; it does not rerun writes
or confer dispatch authority. Duplicate recovery/publication is idempotent.
Receipt retention must outlive the supported replay/recovery interval; deletion
is maintenance work, not part of a request. Unknown receipts block blind retry.

A committed reset/switch/create is not silently rolled back after publication
failure. Retain prior transcripts and quarantine undispatched targets. Reverting
a route is a new, authorized compensating transition with current version checks
and lineage linking the original operation. No deletion, ownership transfer,
classification lowering or transcript rewrite is implied. Revoked actors cannot
authorize compensation. Native compression rollback and transcript rewrite remain
unqualified until their later agreed work packages.

The SQLite receipt records local transition outcome, not proof that an external
audit sink committed atomically. G3 must qualify durable audit reconciliation;
missing or ambiguous audit outcomes remain blocked until separately reconciled.

## Failure Matrix For Package 3

| Failure boundary | Required observable outcome |
| --- | --- |
| Authentication/policy/audit/lock failure | No database, index, cache or agent mutation. |
| Preparation/CAS/native SQL/revocation before commit | Complete SQLite rollback; old projection/cache unchanged; no dispatch. |
| Commit outcome unknown | Quarantine; inspect correlated receipt under authorized recovery; never blind retry. |
| Commit before file publication, crash or cancellation | Committed receipt and route retained; no new dispatch; recovery required. |
| Temporary write/fsync/replace failure | Old or new complete file only; no copy fallback; quarantine until verified recovery. |
| Replace succeeds but acknowledgement fails | Verify current generation and receipt; idempotent recovery, no repeated lifecycle writes. |
| Published but outcome audit/caller fails | Report committed-but-blocked; no false success or automatic compensation. |
| Newer transition, stale cache, late executor or forged file | Reject stale versions/authority; never overwrite the newer route. |
| Missing/corrupt authority or unsafe path | Block; do not adopt JSON/legacy rows or create a fallback store. |

Package 3 must exercise actual native SessionStore/SQLite with process-crash and
restart injection, concurrent writer contention, cancellation/expiry/revocation,
replacement failures and duplicate descriptors. Observe file bytes, native rows,
versions, receipts, audit outcomes and agent dispatch counts. Test same-owner
allowed transitions and wrong-owner/permission denials; preserve ordinary controls
against the pinned unpatched source. Begin with create only; reset/switch/rotation
follow individually, not as an unqualified combined patch.

All index mutation roots in the package 1 inventory must either participate in
this contract or remain explicitly denied. Touch/suspend/recovery flags and prune
cannot bypass it; compression callers cannot mint authority from returned IDs.
Package 3 acceptance must distinguish scoped create evidence from full G2
acceptance. Frontend identity composition, provisioning, compression, audit
reconciliation and clean-install qualification remain open.

## Work Package 2 Exit

The authority, SQLite transaction boundary, strict projection replacement,
correlation, crash recovery and compensation protocol are specified. This is a
design completion only: no tables, transitions, locks or recovery code have been
implemented by this document. Next is G2 work package 3 in the approved order.

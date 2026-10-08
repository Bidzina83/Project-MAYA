# G2 Reset Transition

## Current Step

2026-10-06: G2 work package 3, reset Step 1 was explicitly approved by the user.
Step 2's scoped atomic-sink gate passed; the user authorized Step 3 after committing
the changes and reporting green CI. The user explicitly closed bounded Step 3
on 2026-10-07 and authorized Step 4. Patch 34 is the frozen combined source for
the original Step 4 qualification; see `governance_g2_reset_failure_matrix.md`
for progress. On 2026-10-08 the user approved the host-only Patch 35 publisher
correction and affected create/reset requalification before remaining path/parity
checks; see `governance_g2_publisher_correction.md`. Frozen Patch 34 evidence is
preserved, and native Hermes source is unchanged by this correction.
Bounded source-level create is accepted; ordinary mandatory reset stays disabled.
This document specializes the existing ownership and consistency designs. It
does not reorder G0-G7 or authorize frontend composition, production activation,
runtime pin, wheel or installer changes.

References: `maya_governance_integration_plan.md`,
`governance_g2_session_ownership.md`, `governance_g2_session_consistency.md`,
`governance_g2_caller_acknowledgement.md` and the accepted
`governance_g2_create_acceptance_review.md`.

## Source Findings

Reviewed the effective frozen Patch 31 source, based on Hermes commit
`b13e2fd6948a59eeb59fe618914147d97a2ee90a`:

- `gateway/session.py`, `SessionStore.reset_session`: mandatory mode denies
  before effects. Ordinary mode changes the index before separately ending and
  creating SQLite sessions, with diagnostic catches. Do not enable this path
  by removing its guard.
- Maya `session_transitions.py`: create authority requires operation `create`
  and expected route version zero. It cannot be repurposed as reset authority.
- Staged `caller_preparation.py`: acknowledgement checks operation `create`,
  route versions zero/one and the exact create coordinator. Reset needs explicit
  operation-bound acknowledgement, not a wildcard or relaxed create check.
- Staged `session_readers.py`: the selected route requires an acknowledged
  receipt and a native session with no parent. Reset lineage must be recognized
  explicitly before a new fixed-session request can be issued.
- `authenticated_request` holds the cross-process projection lock through the
  request scope, while releasing SQLite/store locks before agent execution.
  Preserve that exclusion and G1 revocation; a process-local busy flag alone is
  not sufficient.

These observations identify changes to qualify, not runtime acceptance. The
original source checkout, frozen overlays and accepted create evidence remain
unchanged. New source candidates must reconstruct that baseline and verify hashes.

## Reset Contract

Only a fresh host-authenticated, same-owner request may propose a reset for one
host-selected route. Source IDs and versions are resolved from verified native
records, never trusted from prompt, JSON index or caller fields. Source must be
the current acknowledged, active, unarchived session at the exact expected route
and owner-binding versions. Missing, ended, legacy, pending or foreign sources
deny without allocation. No implicit create on a missing route.

The single-use descriptor binds operation `reset`, instance/database, actor and
classification, route slot, source and host-generated target IDs, expected route
and binding versions, request/correlation IDs and bounded execution authority.
Classification must match the approved profile and satisfy both ownership floors;
no downgrade, ownership transfer or inferred authentication. Target must not exist.

Independent permissions are required through the existing local gateway:

| Capability/operation | Exact target and meaning |
| --- | --- |
| `session.read/route_state` | Verify the owned source route; no transcript disclosure. |
| `session.transition/reset` | Replace this owned routing slot, not arbitrary routes. |
| `session.write/end` | Finalize this source with a fixed reset reason. |
| `session.write/create` | Allocate this exact host-generated target. |
| `session.transition/acknowledge_reset` | Acknowledge this reset only after guarded normal caller exit. |

Reset permission alone grants none of the other operations. It never grants
delete, clear, rewrite, reopen, compression, append, model or tool permission.
`session.write/end` is a proposed reset-specific gateway preflight permission,
not an already implemented request-scope operation. Existing native lifecycle
descriptors use `metadata`; Step 2 must map the exact source-end effect without
treating a general metadata grant as reset authority or widening append-only G1
scopes. The existing create preflight permission likewise is not a wildcard grant.
Source finalization is not transcript deletion or compaction. Preserve native
messages, FTS, counters, metadata and Maya SMB memory except the explicitly
authorized lifecycle fields. No MEMORY.md/USER.md migration or modification.

## Persistence And Visibility

Acquire the existing cross-process projection exclusion before inspecting or
mutating the source; preserve its lock ordering. An active request in another
host must make reset busy. A reset invoked inside an existing fixed-session
scope must deny rather than try to upgrade/reenter authority. No forced release
of another request's exclusion and no unqualified worker handoff.

In one native SQLite transaction, recheck source owner/lifecycle, descriptor,
route/binding versions, schema, expiry and revocation. Prepare target rows and
the complete next projection before mutation. End the source, update its owned
lifecycle state, insert the target and matching owner, compare-and-swap the
route to expected version plus one, and persist correlated pending receipt and
next projection generation/hash. Reuse commit/revocation synchronization; no
independently committing public end/create methods inside this transaction.

Proposed lineage uses existing native `sessions.parent_session_id` and owner
`parent_session_id`, both pointing to the retained source. The descriptor digest
binds source and expected versions; acknowledgement must verify that lineage,
source finalization, exact target, route version and current projection. Never
accept a reset receipt using create's zero/one checks. If existing record fields
cannot represent or verify these facts, report the exact schema delta for review
before implementation; no automatic migration or additional store is authorized.

Retain the established pending-publication, verified-projection, pending-caller,
acknowledged and quarantine semantics with operation-bound reset checks. Strict
temporary write/flush/fsync/replace and required outcome audit precede dispatch.
Unknown commit/publication/ack outcome stays blocked, without blind retry,
automatic source reopen, compensation or deleting the new session. Recovery
remains separately authorized maintenance, not conversation privilege.

Only after normal-exit acknowledgement may an independently authenticated reader
issue new fixed-target G1 authority. Validate exact acknowledged reset lineage,
owner/classification, versions and projection; a non-null parent is not itself
authorization. Clear caches/history/approvals and do not reuse the old agent or
lease. Late old executors must fail existing revoked-authority checks; qualify
this explicitly, including cancellation that outlives the initiating task.

## Ordered Implementation Steps

1. **Contract review (approved):** reconcile these reset-specific permissions,
   lineage, acknowledgement and exclusion rules against the existing design
   and actual pinned source. Record unresolved representation/caller dependencies
   before coding. Gate: explicit review of this sequence and contract.
2. **Authority and atomic native sink (scoped gate passed):** add a separate hashed source candidate
   with a reset-specific descriptor, exact native entry and synchronized SQLite
   finalization/allocation/route CAS. Keep ordinary reset and unbound mandatory
   reset unchanged. Gate: actual native allowed/denied and rollback tests;
   reset permission without end/create must have zero effects.
3. **Publication, caller and reader composition (accepted 2026-10-07):** qualify operation-bound
   acknowledgement/quarantine, strict publication and exact lineage selection,
   fresh request scope and actual empty-history new-agent conversation. Gate:
   caller failure cannot dispatch; old transcript preserved; independent model
   denial still stops transport; no old history/cache/approvals transfer.
4. **Failure matrix and acceptance review (current):** qualify the final combined source
   profile, not just historical overlays. Gate: actual process crash/restart,
   contention/competing resets, busy old request, late executor, revoke/expiry/
   cancellation, unknown commits, stale/replayed/foreign descriptors, failed
   write/fsync/replace/ack/audit, unsafe paths and ordinary-mode parity. Review
   exclusions and obtain bounded reset acceptance before the next transition.

Do not split new dependencies into unapproved milestones or implement steps
out of order. A defect requiring a different sequence must be reported with
the specific revised order for approval.

## Required Observations And Limits

For precommit denial/failure compare full SQLite state and projection bytes:
no source finalization, target allocation, route/cache change or agent dispatch.
For successful commit inspect source transcript/FTS/counters, target emptiness,
same-owner lineage, monotonically incremented versions, receipt state, projection
hash, safe audit events and actual dispatch/transport counts. For postcommit
failure inspect retained committed state and quarantine, not fictitious rollback.
Duplicate and stale requests cannot overwrite a newer route or rerun lifecycle
writes. Same-owner reset without delete permission must succeed once qualified;
foreign owner, revoked credentials and missing independent permissions must deny.

Use isolated explicit fixture provisioning, actual native SessionStore/SessionDB
and real SDK with synthetic transport. Production schema provisioning, live
frontend authentication, general workers/compression, durable audit reconciliation,
maintenance recovery, continuous hostile path races and power-loss/clean-install
qualification retain their later gates. Source-only reset evidence cannot qualify
the Standard installer or the entire G2 milestone.

## Step 1 Verification

The 47 required release/update/setup/closure regression tests pass on 2026-10-06.
Product-context validation, release-script syntax and whitespace checks pass.
These checks protected existing behavior; reset was unimplemented at Step 1.
No accepted input manifest or native source was edited.

## Step 2 Source Candidate

Patch 32 adds `SessionStore.reset_owned_session_candidate` and the separately
staged Maya `session_reset` module. Its input contract is
`governance-g2-reset.json`; `scripts/prepare_governance_g2_reset.py` reconstructs
only the two declared effective paths over the verified prepared Patch 31 source.
The original checkout, accepted baseline and installed artifacts are untouched.

The synchronous, single-use reset descriptor is host-selected, task/thread bound,
expiring and revocable. It is not create authority or a fixed-session agent lease.
Independent route-read, reset, source-end and target-create permissions pass through
the existing local gateway with safe audit events. Native finalization, allocation,
owner lineage, route CAS and pending receipt/generation commit in one transaction.
Each lifecycle update must affect exactly one row. Revocation is checked again
under the authority lock immediately before commit; already committed outcomes
are not claimed rolled back.

This initial sink accepts the acknowledged parent-free **create** source profile
only. Recognizing an acknowledged reset target for a subsequent reset requires
Step 3's exact receipt/lineage composition; a non-null parent or forged operation
is not adopted. No general metadata, append, model, tool or worker permission is
granted. Existing cross-process exclusion and native store/database locks are
reused; there is no parallel session engine or new schema.

A successful sink returns `committed_pending_projection` with
`dispatch_allowed=false`. The old projection bytes remain untouched and the
existing reader denies routing. Publication, caller acknowledgement/quarantine,
new-agent conversation and the combined failure matrix are deliberately absent
from this Step 2 candidate. Unknown commit outcomes retain blocked native records
for separately authorized recovery, not blind retry or source reopening.

Native tests use actual SessionStore/SessionDB and explicitly provisioned isolated
fixtures, not transports or customer credentials. Their scope is atomic sink
allow/deny/rollback and pending-reader exclusion, not full reset qualification.
Step 3 and Step 4 remain in order; G2 and production remain unaccepted.

### Step 2 Verification

2026-10-06: 22 native reset cases pass against the exact Patch 32 candidate.
They cover allowed atomic reset/transcript retention/pending-reader denial, each
independent permission, SQL rollback, ignored lifecycle updates, foreign/revoked/
expired/stale/replayed/out-of-scope authority, invalid source state, precommit
revocation and unknown postcommit outcome. No model, tool or connector transport
is used. Five preparation-contract tests and 47 required product regressions pass.
The native ordinary-mode gateway session suite passes all 88 cases against the
same effective native bytes. Context validation, syntax and whitespace checks pass.

The isolated native run reports one pytest `cache_dir` configuration warning
because its cache provider is disabled; no cases are skipped. Input hashes and
full source inventories are verified before execution. This meets Step 2's
scoped atomic-sink test gate, not bounded reset acceptance or G2 acceptance.
The next approved step is Step 3 publication, caller and reader composition;
no implementation of that step or downstream installer change is included here.

## Step 3 Source Composition

The 2026-10-07 criterion review is recorded in
`governance_g2_reset_composition_review.md`. Step 3 remains pending acceptance;
approval isolation and uncertain acknowledgement/failed quarantine require
explicit resolution before advancement. No implementation sequence is changed
by that review.

The user subsequently approved the bounded host-confirmation restriction and
exact approval cleanup on 2026-10-07. Patch 34 is a separate source candidate;
its evidence and acceptance review belong to the linked review document. Reset
restart routing now denies without fresh host confirmation; durable acknowledged
rows alone are insufficient and conversation authority cannot reconcile them.

Patch 33 reconstructs four declared paths over the frozen Patch 32 candidate:
the native SessionStore entry, staged reset authority, existing published reader,
and a staged `reset_publication` module. `governance-g2-reset-composition.json`
binds parent/patch/test hashes and effective source hashes; the preparation script
verifies the entire source/host inventory. Earlier manifests, source checkouts,
runtime pin and installed artifacts are unchanged.

`prepare_owned_reset_candidate` exposes explicit reset preparation, not an
ordinary reset fallback. It uses the existing strict temporary-file publication
primitive and native receipt states: committed pending projection, verified
projection, published pending caller, then guarded normal-exit acknowledgement.
Publication outcome audit must succeed before the pending caller state advances.
Acknowledgement independently requires `session.transition/acknowledge_reset`;
create/reset permission alone is insufficient. The caller receives immutable
correlation data, not a conversation lease, and holds no storage locks or SQLite
transaction. Typed failures/cancellation retain their scope; cleanup can reduce
only the exact failed receipt and cannot repair a newer route.

The reader checks the acknowledged reset operation, expected/result versions,
generation/hash, route correlation, both parent fields and the retained source's
owner/create receipt/finalization. It then uses the existing freshly authenticated
G1 append-only scope. Old agents and stored prompt snapshots are not reused; the
fixed no-snapshot profile remains. No model/tool permission is granted by reset.

This composition deliberately covers one initial acknowledged create-to-reset
lineage. Subsequent reset of a reset target remains denied, not implicitly adopted.
The actual conversation uses native AIAgent/SDK/SQLite with synthetic HTTP, an
inert tool catalogue and excluded title/background execution. It does not qualify
live credentials/transports, general tools or tool-approval transfer.

### Verification And Remaining Gate

2026-10-06: all 37 combined native cases pass (15 composition plus the unchanged
22 atomic tests, re-executed against the combined source). The composition covers
normal exit, exception/cancellation, missing acknowledgement permission,
revocation/expiry, publication/audit failure, corrupted lineage, fresh actual-agent
execution and independent model denial with zero SDK transport calls. A second
actual conversation after an old-agent turn proves distinct agent instances and
absence of old history, agent cache and stored snapshot in its synthetic request.
The native ordinary session suite passes 88 cases; nine preparation tests and
47 required product regressions pass. Context, syntax and whitespace checks pass.
The native matrix has one cache-provider configuration warning and no skips.

These results are scoped source evidence, not full Step 3 acceptance, bounded
reset acceptance or G2 acceptance. Step 3's criterion review still needs to
reconcile the excluded approval/tool profile. Uncertain acknowledgement commits
combined with failed quarantine are not qualified: this candidate must not be
claimed to block every failure combination or restart outcome. Crash/restart,
process contention, late executors, combined commit/publication/acknowledgement
faults and recovery remain the planned Step 4 matrix; durable audit reconciliation
and production provisioning remain G3. Consult this gate before proceeding; do
not activate production or rebuild a ready installer from these results.

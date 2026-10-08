# G2 Session Switch Transition

## Current Step

2026-10-08: the user approved the switch contract and ordered steps and authorized
G2 work package 3 switch Step 2, following bounded initial-reset acceptance.
Patch 36 is a separate source-only authority/atomic-sink candidate; publication,
caller acknowledgement and switch-specific reader remain Step 3, not enabled.
The agreed order remains switch, rotation, then work package 4 frontend
composition and work package 5 API/CLI/setup/maintenance identities.

References: `maya_governance_integration_plan.md`,
`governance_g2_session_ownership.md`, `governance_g2_session_consistency.md`,
`governance_g2_reset_acceptance_review.md` and
`governance_g2_reset_transition.md`. The accepted Patch 35 candidate and earlier
frozen evidence remain unchanged. No production activation, schema provisioning,
runtime-pin change, wheel or installer rebuild follows this document.

## Effective Source Findings

Inspected `.codex-build/governance-g2-publisher-20261008-a`, based on Hermes
`b13e2fd6948a59eeb59fe618914147d97a2ee90a`:

- `source/gateway/session.py`, `SessionStore.switch_session`: mandatory mode
  denies before effects. Ordinary mode replaces the cached entry and projection,
  then separately calls native end and reopen methods with diagnostic catches.
  Removing the mandatory guard would not satisfy the consistency protocol.
- `source/hermes_state.py`, `end_session` and `reopen_session`: independently
  committing metadata operations. They do not supply the combined owner/route
  transaction, source/target checks or distinct transition permission.
- `source/gateway/slash_commands.py`, resume handling: resolves titles, IDs and
  compression continuations, releases running state, switches, clears security
  state, evicts the agent, then reads title/history. These lookup, cleanup and
  disclosure paths require their own qualification; they are not authenticated
  simply because the underlying switch was authorized.
- `host/src/project_maya/hermes_plugins/session_readers.py`: accepts exact
  create/reset receipts only. Create routing requires version one. Reset routing
  requires retained ended-parent lineage plus live host confirmation.
- `host/src/project_maya/hermes_plugins/reset_publication.py`,
  `validate_reset_lineage`: reopening the retained parent invalidates the existing
  reset profile's active-child/ended-parent predicates. Its target-session receipt
  query also assumes one matching receipt. A later switch cannot reuse those
  assumptions or weaken the accepted checks to accept any same-owner row.

The new switch-specific path must correlate the current route to its exact
receipt, separately verify historical create/reset provenance, and recognize
authorized lifecycle changes without treating stored provenance as authentication.
Any additional schema or caller dependency discovered during implementation
requires a specific review before changing the approved sequence.

## Proposed Bounded Profile

One switch back within the already accepted lineage: acknowledged create A,
acknowledged initial reset A-to-B, then switch the current active B back to its
retained ended parent A. Both sessions belong to the same freshly authenticated
principal, instance, database and routing slot. Require valid live reset-host
confirmation at preparation; a restarted host cannot adopt reset state.

This exercises real end/reopen and target-history restoration without adding
unqualified title enumeration, cross-slot routing or compression-chain resolution.
General same-owner selection, repeated/back-and-forth switching, same-target
requests, legacy rows, foreign owners and compression descendants remain denied
in this initial profile. Those are limitations, not a claim of complete switch
or G2 acceptance. A caller-supplied ID is only a selector: the host resolves it
against the exact permitted lineage before preparing authority.

## Authority And Effects

A separately versioned, single-use host descriptor binds operation `switch`,
principal/classification, instance/database/slot, source B and target A, expected
route and both owner-binding versions, prior reset correlation, request and new
correlation IDs, task/thread, expiry and revocation authority. It cannot mutate
or upgrade an existing fixed-session G1 lease.

Independent gateway permissions are required:

| Permission | Exact effect |
| --- | --- |
| `session.read/route_state` | Read this verified owned slot. |
| `session.read/transition_state` | Validate source and target lifecycle/provenance without disclosing transcripts. |
| `session.transition/switch` | Replace this slot with this existing target only. |
| `session.write/end` | End the active source B with the fixed switch reason. |
| `session.write/reopen` | Reopen the verified retained target A. |
| `session.transition/acknowledge_switch` | Confirm this switch after guarded normal caller exit and security-state cleanup. |

These operation names are proposed contract additions, not existing grants.
History access needs independent `session.read/history` authorization before
disclosure or model context assembly. Switching grants no create/delete/clear/
rewrite/append, model/tool permission, ownership transfer or classification
downgrade. Reopening preserves A's identity, parent field, transcript, FTS,
accounting and unrelated metadata. B's transcript also remains intact. Hermes
MEMORY.md/USER.md, Maya SMB memory and Metabase stores are unaffected.

## Transaction, Publication And Caller

1. Acquire the existing database/projection cross-process exclusion. An active
   conversation makes the switch busy; do not forcibly release its lease or use
   the ordinary resume handler's early running-state cleanup as authority.
2. Verify the acknowledged current reset route and exact historical parent,
   identities, classification floors, schema and complete projection. Authorize
   the independent effects and require available authorization audit.
3. In one native SQLite transaction recheck exact state, versions, expiry and
   revocation. End B, reopen A, update their owner lifecycle fields, compare-and-
   swap the route, increment projection generation and persist a switch-specific
   pending receipt. Prepare complete projection bytes before mutation; every
   expected lifecycle/route update must affect exactly one row. Reuse synchronized
   revocation/commit semantics, not independently committing public methods.
4. Publish using the accepted Patch 35 strict complete-byte helper. Verify the
   file/generation/hash, require outcome audit and advance only the exact receipt.
   Failure or unknown commit remains committed-but-blocked where applicable;
   no blind retry, automatic compensation or claim of rollback after commit.
5. A switch-specific native caller performs exact security/approval/cache cleanup
   before normal-exit acknowledgement and live host confirmation. Cleanup failure,
   cancellation or acknowledgement uncertainty prevents selection. Old reset-host
   confirmation cannot authorize the switched route.
6. A switch-specific reader validates the current switch correlation, prior
   lineage, both owner states, versions and complete projection. It creates fresh
   target-bound G1 authority only after fresh authentication and confirmation.
   Construct a new AIAgent and load only A's independently authorized history.
   Never carry B's history, prompt snapshots, approvals or agent/provider state.

Historical receipts remain immutable evidence. Do not replay their projection
bytes or require their old lifecycle snapshot to be the current route state.
New-host/restart routing stays blocked pending separately authorized recovery.
Do not loosen create/reset readers or broaden reset permissions to support switch.

## Ordered Steps And Gates

1. **Contract review (approved 2026-10-08):** review the bounded A-to-B-to-A profile,
   independent end/reopen/read permissions, current versus historical receipt
   validation and normal-exit confirmation. Gate: explicit user approval before
   implementing Step 2; unresolved representation dependencies must be reported.
2. **Authority and atomic native sink (current):** create a separate hashed source candidate
   over accepted Patch 35. Gate: actual SessionStore/SQLite allowed switch and
   per-permission denial, foreign/forged/stale/replayed/expired/revoked descriptor,
   busy request, invalid target and complete transaction rollback tests. Ordinary
   mandatory switch stays denied; successful commit alone cannot dispatch.
3. **Publication, caller and reader composition:** qualify exact switch receipt
   acknowledgement, cleanup and fresh actual native AIAgent with controlled real
   SDK transport. Gate: restored A history only, preserved A/B records, no B cache
   or approval transfer, independently denied model egress with zero transport,
   missing confirmation/caller failure/uncertainty blocked. Review before Step 4.
4. **Failure matrix and acceptance:** exercise the combined candidate with real
   process crash/restart, contention, late old executors/cancellation, revocation,
   combined commit/publication/ack/audit failures, incomplete writes, unsafe paths,
   stale projection/receipts and exact ordinary-native compatibility controls.
   Gate: review observed native records/file bytes/dispatch/audit outcomes and
   explicit bounded switch acceptance before rotation or another scope extension.

No step is closed by an implementation patch, mock-only result or green CI alone.
New findings cannot silently introduce an extra capability or reorder milestones.

## Preserved Exclusions

Live authentication/provider/connectors, general tools/workers, normal resume/
branch/title listing, automatic continuation lookup, repeat reset, general switch
and rotation, production provisioning, maintenance recovery and durable audit
reconciliation retain their remaining gates. Actual file-symlink escapes,
continuous hostile filesystem/ACL races and power-loss guarantees remain outside
the bounded evidence, not implicitly qualified by a crash test. The known nine
ordinary Windows shell-path failures must remain visible. No installed-product
or Windows support claim follows source-level acceptance.

## Step 1 Verification

2026-10-08: all 47 required release/update/setup/closure regression tests pass.
The initial sandbox run encountered temporary-directory permission errors; the
authorized outside-sandbox rerun passed without changing tests. Product-context
validation, release-script syntax and whitespace checks pass. This verifies
documentation consistency and existing product behavior, not switch operation.
No native switch tests were added or claimed at Step 1. The user subsequently
approved the contract and authorized Step 2.

## Step 2 Source Candidate

Patch 36 adds only `SessionStore.switch_owned_session_candidate` and the staged
Maya `session_switch` authority/coordinator. `governance-g2-switch.json` pins the
accepted Patch 35 parent, patch bytes, both effective files, the 43-case native
matrix and the 27 unchanged inherited fixtures. Full native/host inventories
are verified; the original checkout and accepted source candidates are untouched.

The synchronous single-use descriptor selects exactly reset child B and retained
parent A, prior reset correlation, route version two and both owner bindings.
Preparation requires fresh host identity and the existing live reset confirmation.
Independent read/switch/end/reopen permissions and available authorization audit
precede mutation. Classification and native ownership remain exact; stored parent
fields alone cannot authorize switching or history access.

The native SQLite transaction ends B, reopens A, updates their owner lifecycle
states, compares-and-swaps the route to version three, inserts a new pending
switch receipt and advances the complete projection generation/hash. Every
expected write must affect one row. Existing transcripts and unrelated metadata
are retained; historical create/reset receipts are not rewritten. Permissions,
revocation, gate registration, store binding and effective projection are checked
again before commit under the synchronized authority lock.

The sink neither publishes the projection nor acknowledges a caller, cleans
approvals, changes a conversation lease or constructs an agent. Its result is
`committed_pending_projection` with `dispatch_allowed=false`; the old complete
projection remains on disk and existing readers deny. Unknown commit outcomes
remain blocked, not blind-retried or reported as rolled back. Native ordinary
mandatory switch remains denied. Publication, switch-specific receipt/reader
validation, fresh-agent history restoration and caller cleanup remain Step 3.

Reconstruction and qualification commands (repository root, prepared parent and
native dependency environment required):

```text
python scripts/prepare_governance_g2_switch.py --output .codex-build/governance-g2-switch-20261008-b
python scripts/qualify_governance_g2_switch.py --stage .codex-build/governance-g2-switch-20261008-b --python .codex-build/governance-g1-native-env/Scripts/python.exe --output .codex-build/governance-g2-switch-qualification-20261008-b
```

Use fresh output directories for a rerun; the tools never overwrite an existing
stage/report. Generated copies, homes, SQLite fixtures and reports stay ignored
under `.codex-build`, not in release artifacts. The initial development stage
was rejected when its captured manifest no longer matched the finalized test
inputs; the final candidate was reconstructed separately, not adopted as valid.

### Step 2 Verification And Remaining Gate

2026-10-08: all 43 native atomic-switch cases pass on
`.codex-build/governance-g2-switch-20261008-b`, with zero skips. The final
qualification report is
`.codex-build/governance-g2-switch-qualification-20261008-b/qualification.json`;
its exact-count JUnit evidence is beside it. Full frozen-parent ancestry and
candidate native/host inventories pass before and after the matrix.

The allowed case proves retained A/B transcripts and unrelated native metadata,
unchanged historical receipts, exactly two native sessions, the correct end/
reopen/owner/route states, complete pending receipt and zero agent/model dispatch.
Five independent permission cases deny without storage effects. Ten authority
cases cover revocation, expiry, forged/stale descriptors, foreign identity,
out-of-context use, replay, wrong thread and invalid/same target selectors.
Ten lineage/storage cases reject foreign/classification/lifecycle/parent/receipt/
version/projection/confirmation damage. Seven ignored/failed native write cases
roll back every effect. Ordinary mandatory switch, conversation/projection busy
states, precommit revocation, broken gates and unavailable policy/audit deny.
A commit-then-error case retains the correlated pending native state and old
projection, with no fabricated rollback, dispatch or raw exception marker.

All 88 unchanged ordinary native session tests pass on this candidate, with
inventory checks before and after their separate run. This is scoped compatibility,
not remediation of the previously recorded nine Windows shell-path failures.
All 47 required release/update/setup/closure regressions, six final switch
provenance/report-parser checks and two line-ending checks pass. Context,
release/new-script syntax and whitespace checks pass. The native matrix retains
the known disabled-cache-provider configuration warning; no warning is called
runtime qualification or suppressed by changing native tests.

Step 2's scoped authority/atomic-sink gate is satisfied. Next is Step 3 in the
approved sequence: strict publication, operation-bound caller acknowledgement,
security/cache cleanup, switch-specific reader and independently governed fresh
native agent loading A's history. Full bounded switch acceptance requires Step 4
and explicit review; work package 3, G2 and production remain unaccepted. Runtime
pin, product host, wheels, installers and production capability markers are
unchanged. No unsupported route is enabled by these source tests.

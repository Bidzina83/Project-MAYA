# G2 Session Switch Transition

## Current Step

2026-10-08: the user approved the switch contract and ordered steps and authorized
G2 work package 3 switch Step 2, following bounded initial-reset acceptance.
Patch 36's scoped authority/atomic-sink gate passed. The subsequent instruction
to proceed authorizes Step 3: separate source-only Patch 37 publication, guarded
caller acknowledgement and switch-specific reader composition. Native verification
and Step 3 review are recorded below; Step 4 and bounded switch acceptance are not
implied by implementation or a green CI run.
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
2. **Authority and atomic native sink (scoped gate passed):** create a separate hashed source candidate
   over accepted Patch 35. Gate: actual SessionStore/SQLite allowed switch and
   per-permission denial, foreign/forged/stale/replayed/expired/revoked descriptor,
   busy request, invalid target and complete transaction rollback tests. Ordinary
   mandatory switch stays denied; successful commit alone cannot dispatch.
3. **Publication, caller and reader composition (current):** qualify exact switch receipt
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

## Step 3 Source Candidate

Patch 37 changes the isolated native `gateway/session.py` and `gateway/run.py`,
adds staged Maya `switch_publication.py`, and adds an explicit switch branch in
the staged published reader. Frozen Patch 36 and every earlier input remain
unchanged; the normal product host is not activated. The new preparation wrapper
is explicit, not an unguarded replacement for native resume or switch commands.

The caller captures the independently approved historical create/reset receipts
before the atomic switch, then publishes the complete current projection with
Patch 35's strict helper. Current validation joins through the routing correlation;
historical validation explicitly selects create A and reset B. Their historical
projection bytes and old lifecycle states are not replayed or demanded as current
state. Complete receipt tuples remain immutable and part of live confirmation.
The original create/reset reader checks are preserved without relaxation.

Publication advances only the exact correlated receipt. Normal caller exit needs
separate `acknowledge_switch` authorization, fixed outcome audit and exact native
security/cache cleanup before acknowledgement. Approval waits are denied and
route-specific confirmations, provider/model/reasoning overrides, queued messages,
voice state and last-model recovery state are removed. Agent-cache detachment is
synchronous and verified; it neither borrows the ordinary best-effort eviction
helper nor launches its background thread. An active running-agent entry, invalid
cache/dictionary or incomplete cleanup blocks. Unrelated route state is retained;
the shared last-model fallback is cleared to prevent source-model transfer.

Only after authority and caller cleanup fully exit does the host issue confirmation.
Caller failure/cancellation, denied acknowledgement, uncertain commit, failed
cleanup and a fresh host with only durable receipts remain undispatchable. Pending
or failed outcomes are blocked, never implicitly compensated or falsely reported
as rolled back. Best-effort quarantine only reduces eligibility of the exact
failed receipt; failure to quarantine cannot create live confirmation.

After fresh authentication and independent history permission, the reader creates
new target-bound G1 append authority. The actual native caller constructs a fresh
AIAgent, recognizes existing A without recreation, rebuilds context without stored
snapshots, and sends only A's authorized history through independent model gates.
B's transcript and both stored snapshots remain intact. Neither switching nor
acknowledgement grants model/tool/append or administrative authority by itself.

### Qualification Boundaries

The controlled real-SDK transport is synthetic: no live provider or connector is
qualified. The native gateway's post-success automatic-title callback is observed
as an inert fixture call. Its worker, title persistence and provider selection are
not qualified or changed here; a source assertion claiming the callback was not
called failed diagnostically and was corrected to record what actually happened.
No background/title denial claim follows these results. This retains the prior
explicit title-worker exclusion rather than silently expanding the patch scope.

Cache detachment proves fresh-agent/state isolation, not general teardown of
native clients, browsers, terminal sandboxes, providers, children or worker jobs.
Those resource lifecycles remain outside this bounded caller profile. Process
restart/crash, contention and combined fault/path matrices remain Step 4. New-host
confirmation refusal in the same process is not process-restart qualification.
Known ordinary Windows shell-path failures remain visible and unchanged.

`governance-g2-switch-composition.json` pins all four effective files, the patch,
parent input, new native matrix and unchanged fixture/replay bodies. Reconstruction
and qualification verify complete native/host inventories and frozen ancestry;
JUnit validation rejects skips, duplicate names, partial counts and failed cases.
All source copies, homes and reports stay ignored under `.codex-build`.

```text
python scripts/prepare_governance_g2_switch_composition.py --output .codex-build/governance-g2-switch-composition-20261008-a
python scripts/qualify_governance_g2_switch_composition.py --stage .codex-build/governance-g2-switch-composition-20261008-a --python .codex-build/governance-g1-native-env/Scripts/python.exe --output .codex-build/governance-g2-switch-composition-qualification-20261008-a
```

Use fresh directories for reruns. The authoring diagnostic tree is not an accepted
artifact and does not substitute for the reconstructed candidate's qualification.

### Step 3 Verification And Gate Review

2026-10-09: final verification of committed candidate `7a91930` uses the unchanged
reconstructed `.codex-build/governance-g2-switch-composition-20261008-a`.
All 199 native cases pass, with zero skips: 42 switch composition cases, 43 frozen
atomic-switch cases, 80 frozen final-create cases and 34 frozen reset composition
cases. The supervisor verified full frozen ancestry and native/host inventories
before and after the matrices. Exact-count JUnit files and `qualification.json`
are under `.codex-build/governance-g2-switch-composition-qualification-20261008-a`.
Earlier native test bodies, source candidates and qualification inputs are intact.

| Step 3 criterion | Observed bounded evidence |
| --- | --- |
| Exact publication and caller receipt | Actual SessionStore/SQLite follows pending commit, verified complete projection, pending caller and guarded acknowledgement; current correlation selects the switch receipt rather than the older create receipt for A. |
| Retained records and provenance | Both native transcripts and historical create/reset receipt tuples survive. Parent A is reopened, child B is ended with the switch reason; damaged historical receipts, lifecycle/owner/route state and projections deny selection. |
| Fresh agent restores only A | The actual native caller constructs a new AIAgent over target-bound G1 authority; the real SDK's synthetic wire contains A history, not B history or either stored snapshot. A prior actual B agent is not reused; B messages remain unchanged. |
| Independent model and history decisions | Allowed inference reaches exactly one fixture request with zero SDK retries; denied model egress reaches zero requests. Missing history permission denies before conversation/agent dispatch. Switching itself grants neither permission. |
| No approval or cache transfer | Native session allowances, YOLO, pending waits/callbacks and slash confirmations are cleared; waits receive denial. Source-route agent/model/reasoning/queue/voice recovery state is detached, while unrelated route state is retained. |
| Incomplete cleanup denies | Raised/no-op native cleanup, malformed route/cache state, missing cache lock, active-agent state and a no-op whole cleanup entry issue no confirmation and cannot dispatch. |
| Guarded normal exit only | Caller exception, cancellation, generator close, denied acknowledgement, revocation and expiry quarantine the correlated caller outcome and deny selection. |
| Reported uncertainty cannot confer eligibility | Commit-then-error plus failed quarantine can leave SQLite honestly acknowledged, but live confirmation is absent and routing denies. Reported final lock-release failure also denies after committed acknowledgement. |
| Durable state is not authentication | Missing/forged confirmation, wrong process identity, altered runner/registration/phase and a newly registered host deny; prior reset confirmation cannot authenticate the switched route. This is not process-restart qualification. |
| Accepted readers remain strict | All unchanged create/reset/atomic-switch replays pass on the combined candidate; no old reader predicate or transition permission was relaxed. |

All 47 required release/update/setup/closure tests pass after the interruption was
resolved by an explicit rerun. All 14 switch/composition provenance, strict report
parser and real Windows line-ending checkout checks pass. Context, release/new
script syntax and whitespace checks pass. The retained pytest `cache_dir` warning
is the known disabled-cache-provider warning, not a qualified runtime capability.

The native evidence and final ordinary-mode comparison satisfy the listed bounded
Step 3 criteria; explicit acceptance remains the next decision. This does not
close switch Step 4, work package 3, G2 or production. The
frozen input and reports retain `pending_review`. Keep the actual title callback
observation, inert worker exclusion and cache-detachment/resource-lifecycle limits
above in any acceptance decision; do not relabel them as tested worker denial or
clean-install behavior. No source contract, runtime pin, wheel, installer or
production capability marker is changed by this gate review.

Ordinary-mode comparison command (prepared local Hermes Git objects, no downloads):

```text
python scripts/qualify_governance_g2_switch_composition.py --stage .codex-build/governance-g2-switch-composition-20261008-a --python .codex-build/governance-g1-native-env/Scripts/python.exe --ordinary-source-repo ../hermes-agent --output .codex-build/governance-g2-switch-composition-parity-20261009-a
```

The comparison runs unchanged native session/approval/slash-confirmation tests and
the two unchanged ordinary cache controls, in isolated homes against both the
candidate and pinned unpatched Git-object export. Full inventories and native
test/conftest bytes are checked; case-for-case outcomes, exact counts and the
known Windows failure set are enforced. Nine failures are not skipped, repaired
or renamed as passes. Generated exports, homes and reports remain ignored.

2026-10-09: the final comparison passes bounded parity. Each profile executes all
331 cases: 88 session, 225 approval, 16 slash-confirmation and two ordinary cache
controls. Each records 322 passes, nine identical known Windows shell-path
failures, zero skips and zero collection errors. Case identities/outcomes match,
native test bytes match pinned Git objects, and complete inventories and frozen
candidate ancestry pass before/after verification. This is compatibility evidence,
not an all-passing native suite or shell/platform qualification. The final report
is `.codex-build/governance-g2-switch-composition-parity-20261009-a/parity-report.json`.

### Next Decision

Approve or reject bounded switch Step 3 using this evidence and the explicit
title-worker/resource-lifecycle exclusions above. A commit, green CI or generic
instruction to continue before this criterion review is not recorded as acceptance.
After acceptance, Step 4 uses unchanged Patch 37 for process crash/restart,
contention, late old/new caller and cancellation, descriptor/revocation, combined
commit/publication/ack/audit, storage/path and compatibility qualification. No new
runtime overlay, general switch/rotation permission or installer rebuild is
authorized by this review. If a failure requires changing the contract or order,
report it and seek the specific approval before deviating.

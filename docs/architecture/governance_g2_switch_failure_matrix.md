# G2 Switch Failure Matrix

## Current Step

2026-10-09: the user explicitly accepted bounded switch Step 3 and authorized
Step 4 on unchanged Patch 37. The accepted profile remains one acknowledged
create A, initial reset A-to-B, then same-owner switch B-to-A. This document
organizes the existing failure requirements; it adds no runtime authority.

Batches 1-6 are executed on that unchanged profile. Final ordinary parity and
criterion review pass; explicit acceptance of the results is next. Step 4 and
bounded switch acceptance stay open pending that decision.

Consult `maya_governance_integration_plan.md`,
`governance_g2_switch_transition.md`, `governance_g2_session_consistency.md`
and `governance_g2_reset_failure_matrix.md`. Earlier inputs, patches and reports
stay frozen. Production activation, runtime pin, wheel and installer stay unchanged.

## Ordered Batches

1. Actual process termination at native commit, projection publication, pending
   caller, native cleanup, acknowledgement commit and live confirmation; fresh
   independent hosts must refuse adoption without changing durable records.
2. Independent-process contention for this route/database and publication lock;
   busy or stale losers must not overwrite another transition or acquire dispatch.
3. Late source/target callers, cancellation and descriptor identity/version,
   expiry/revocation/reuse faults, with independent per-action authorization.
4. Combined commit/publication/acknowledgement/audit uncertainty, including failed
   quarantine. Reported uncertainty must not grant dispatch or imply rollback.
5. Separate short-write, flush/fsync/replace and storage/audit faults; unsafe
   paths and malformed projections. Require old-or-new complete projection bytes.
6. Final ordinary-mode parity and criterion review, retaining known Windows
   failures and every bounded-profile exclusion before explicit switch acceptance.

Complete each batch before advancing. If a failure requires a source correction
or contract/order change, preserve its evidence and request specific approval.
Passing an individual batch is not Step 4 or G2 acceptance. Rotation and frontend
composition remain later work in the agreed integration plan.

## First Batch Contract

`governance-g2-switch-crash.json` separately hashes the ten new native process
cases, unchanged fixture bodies, frozen Patch 37 parent input and complete native
and host inventories. The supervisor verifies frozen ancestry before and after;
each worker verifies its effective sources. Exact-count JUnit validation rejects
failed, skipped, duplicate or incomplete cases.

Each case prepares actual native SQLite and an acknowledged create/reset lineage
in an isolated home. A switch worker terminates with `os._exit(73)` at one of:

| Boundary | Required durable switch state |
| --- | --- |
| Before native commit | Full prior database and projection unchanged. |
| After native commit / before publication | Pending projection; prior complete file retained. |
| After publication | Pending projection; new complete file retained. |
| Pending caller / before cleanup / after cleanup | Published pending caller, not eligible. |
| Before acknowledgement commit | Uncommitted acknowledgement rolls back to pending caller. |
| After acknowledgement commit / live confirmation | Acknowledged durable receipt, but no transferable live confirmation. |

Every case verifies integrity/foreign keys, both retained transcripts and unrelated
session metadata, immutable historical receipts, exact owner lifecycle/route/
generation state and kernel release of the projection lock. No agent, model or
tool request is dispatched in this batch; socket transport is explicitly blocked.

A second actual process constructs a fresh native reader and authenticated scope
against those records. It must deny both route selection and caller entry and
leave SQLite records and projection bytes unchanged. Even a pre-commit crash
stays blocked:
the old route is reset child B and the prior reset host's live confirmation died
with that host. This is the accepted restriction, not a new recovery policy.

Termination occurs immediately before/after the whole strict publication helper,
not inside write/fsync/replace. It is process-crash evidence, not power-loss,
storage-fault, live connector or clean-install lifecycle qualification. Inert
title-worker and general resource teardown exclusions from Step 3 still apply.

```text
python scripts/verify_governance_g2_switch_crash.py --stage .codex-build/governance-g2-switch-composition-20261008-a --python .codex-build/governance-g1-native-env/Scripts/python.exe --output .codex-build/governance-g2-switch-crash-qualification-20261009-a
```

Use fresh output directories. Generated homes, sources and reports remain ignored
under `.codex-build`; no production capability marker is added.

## First Batch Evidence

2026-10-09: all ten native cases pass, with zero failures, errors or skips. They
use twenty independent worker processes: ten abrupt terminations and ten fresh
native reader/authenticated-scope probes. Both transcripts, unrelated session
metadata and historical receipts survive. Each projection is the expected old
or new complete file. Pre-commit rollback, post-commit lifecycle/route/receipt
states and lock release match the boundary table. Every fresh host denies route
selection and caller entry without changing SQLite records or projection bytes.

The fresh process reconstructs the native store, fresh fixture identity and
published reader without adopting reset/switch confirmation or creating recovery
authority. It does not qualify a restarted full gateway/agent lifecycle; the
registered-host confirmation checks remain separately evidenced by Step 3.

Frozen ancestry and full native/host inventories pass before and after the run;
every worker verifies the exact candidate. Reports are under
`.codex-build/governance-g2-switch-crash-qualification-20261009-a` as `native.xml`
and `qualification.json`. The report remains `source_switch_process_crash_only`,
`production_qualified=false`, `acceptance=pending_review`. The known disabled-cache
provider `cache_dir` warning is retained, not relabeled as a runtime failure.

All 64 portable regressions pass: the 47 required release/update/setup/closure
tests, three new crash-input contract tests and 14 existing switch/composition/
Windows checkout checks, now including the new LF-protected files. Product-context
validation, release/new-script syntax and whitespace checks pass. Generated
sources, homes and reports are not committed.

Batch 1 is complete. Next is batch 2, independent-process contention. Remaining
caller/descriptor, combined uncertainty, storage/path and final compatibility/
acceptance batches stay open. This result does not close Step 4, bounded switch,
work package 3 or G2, and authorizes no new runtime overlay or installer rebuild.

## Second Batch Contract

The next instruction to proceed authorizes batch 2 on unchanged Patch 37.
`governance-g2-switch-contention.json` independently hashes the new eight-case
matrix, frozen composition input, unchanged fixtures and complete inventories.
The supervisor verifies frozen ancestry/inventories before and after; native
workers verify their sources. Exact-count reports cannot accept skips or failures.

| Case | Required observation |
| --- | --- |
| Foreign process holds projection lock | Owning host preparation denies with all records/file bytes unchanged; fresh preparation succeeds only after release. |
| Projection lock acquired after descriptor preparation | Actual native sink denies before effects; descriptor is revoked on scope exit and cannot be reused. Fresh preparation succeeds after release. |
| Foreign process holds SQLite BEGIN IMMEDIATE | Prepared native sink denies without commit, partial lifecycle writes or projection change; consumed attempt is not retried. Native busy timeout is unchanged. |
| Active B conversation | Real request lease/projection exclusion blocks a fully registered foreign host; owner lease/cache/records remain intact until normal exit. |
| Owner native commit / projection publication | Competing host observes actual cross-process busy denial before authority or caller entry; it cannot overwrite the in-flight owner's records or projection. |
| Pending caller, then acknowledged switch | A registered competing host denies pending recovery state, then denies the no-longer-valid initial-switch source after owner acknowledgement; no second receipt or write. |
| Two independent unconfirmed hosts | Both fail the live reset-confirmation gate before any descriptor is issued. Their uncontended attempts are deliberately sequenced to distinguish this denial from lock contention. |

The parent fixture performs the real initial reset and keeps its live confirmation.
Competing hosts reopen existing native records and register native runner/executor,
reset/switch coordinator, preparations, policy and reader, but do not copy or
forge `_confirmed`. Observational wrappers record only allowlisted fixed denial
codes and rethrow unchanged errors; they do not authorize actions or bypass gates.
Separate storage workers hold a real portalocker 3.2.0 lock or a SQLite transaction
without DDL/DML. Process barriers prove readiness and held locks, not timing guesses.

Each completed owner transition has one exact switch receipt, route/generation
three, preserved A/B histories, historical receipts and unrelated metadata,
complete verified projection and the expected publication/acknowledgement audit.
Blocked attempts leave authoritative records and projection bytes unchanged.
No agent/model/tool dispatch or external socket is allowed; fixture output and
audit are checked for synthetic history/key sentinels. Homes and reports are isolated.

This does not qualify two independently authorized switch hosts, automatic failover
or maintenance adoption. The accepted process-bound reset confirmation forbids
that profile; fabricating a second confirmation would invalidate this evidence.
General multi-host switching needs its own reviewed authority/recovery contract,
not an exception added to a test. Late callers, descriptor faults and other
remaining Step 4 batches are unchanged. No new runtime patch is introduced.

```text
python scripts/verify_governance_g2_switch_contention.py --stage .codex-build/governance-g2-switch-composition-20261008-a --python .codex-build/governance-g1-native-env/Scripts/python.exe --output .codex-build/governance-g2-switch-contention-qualification-20261009-a
```

Use fresh output directories; generated workers, homes and reports stay ignored.

## Second Batch Evidence

2026-10-09: all eight native contention cases pass, with zero failures, errors or
skips, using nine independent workers. Actual foreign-process projection locks
block both preparation and the prepared native sink with zero effects. A real
SQLite writer blocks the consumed sink attempt without any lifecycle/projection
mutation; native busy timeout is unchanged, the revoked scope cannot be reused,
and no automatic retry occurs. Fresh authorized owner preparations succeed only
after lock release.

An active B conversation retains its original live lease/cache while a registered
competing host receives actual busy denial. The same cross-process exclusion
protects native commit and strict publication. At pending caller state a competing
host is recovery-blocked; after owner acknowledgement it cannot replay the initial
switch against route version three. Independently registered unconfirmed hosts
both fail live reset confirmation before any descriptor/caller entry, without
copying or forging authority. Their two uncontended attempts are not a race of
two authorized writers, and do not qualify multi-host switching or failover.

Every owner completion has one exact switch receipt, expected lifecycle state,
route/generation three and complete verified projection. A/B transcripts,
historical receipts and unrelated native session metadata are preserved. Integrity,
foreign keys, expected publication/acknowledgement audit, zero agent/model/tool
dispatch and synthetic secret/history-safe output checks pass. Fresh-host fixture
registration does not qualify general gateway startup or resource teardown.

Full frozen ancestry and native/host inventories pass before and after; workers
verify their inputs. Reports are `native.xml` and `qualification.json` under
`.codex-build/governance-g2-switch-contention-qualification-20261009-a`. They retain
`source_switch_process_contention_only`, `production_qualified=false` and
`acceptance=pending_review`; the disabled-cache `cache_dir` warning is retained.
All 68 portable tests pass: 47 required product regressions, four new contention
contract/inventory tests, three crash contract tests and 14 switch/composition/
Windows checkout checks. Context validation, release/new-script syntax and
whitespace checks pass. Earlier frozen inputs, patches and test bodies are intact.

Batch 2 is complete only for this bounded lock/unconfirmed-host profile. Next is
batch 3 in the existing order; combined uncertainty, storage/path and final parity/
acceptance batches remain open. No new source overlay, production activation,
runtime pin, wheel or installer is authorized by these results.

## Third Batch Contract

2026-10-13: the next instruction to proceed starts batch 3 on unchanged Patch 37.
`governance-g2-switch-callers.json` hashes 29 new descriptor/authority cases and
six real native cancellation cases, their unchanged fixtures, frozen composition
input and complete source inventories. The supervisor verifies frozen ancestry
before/after and exact-count reports; each native suite verifies its candidate.

Descriptor cases exercise revoked/forced-expired authority before the atomic
sink, during final in-transaction authorization, before publication and at pending
caller acknowledgement. Pre-commit loss must preserve the complete prior database
and projection. Post-commit loss retains the honest pending/quarantined receipt
and both histories, with no confirmation or dispatch; no rollback after commit is
claimed. Fifteen sealed descriptor fields are independently replaced; these test
descriptor-object tampering denial, not independent semantic field branch coverage.
Consumed/exited authority, foreign thread/task, reuse under fresh target conversation
and policy withdrawal after preparation must not transfer permission or mutate state.

Cancellation tests use the actual native caller, AIAgent, native SQLite and real
SDK with synthetic HTTP, zero retries and no external sockets. Three races (normal,
repeated cancellation and a selected child swallowing cancellation) cover both:

- Cancelled B executor remains pending across the real B-to-A switch while a fresh
  independently authorized A request runs.
- After an ordinary approved B turn and the switch, a cancelled A executor remains
  pending while a different fresh A request runs. Matching session IDs cannot
  replace the unique request/lease binding.

Late model/tool/output, old/fresh writes, legacy routing and switch preparation
must deny with zero additional transport/handler calls, no record/projection/cache/
running-slot mutation and no borrowing of the active reader/root. New A context
must include A history, not B history. Fresh authorized completion must retain B
records, historical receipts and route version three. Synthetic private markers
must not appear in output/audit. Already authorized in-flight model requests are
not undone; cancellation revokes future use, not past egress.

Transport/async barriers observe actual boundaries; fixture cleanup releases and
awaits every selected thread/task. Title callbacks stay inert exclusions, not
qualified workers. General workers, live providers, frontend identity, failover,
production lifecycle and durable audit reconciliation are unchanged. No second
authorized switch host or copied confirmation is fabricated. The broader stale
multi-host descriptor race remains outside the accepted process-bound profile.

```text
python scripts/verify_governance_g2_switch_callers.py --stage .codex-build/governance-g2-switch-composition-20261008-a --python .codex-build/governance-g1-native-env/Scripts/python.exe --output .codex-build/governance-g2-switch-callers-qualification-20261013-a
```

Preserve failed evidence and seek specific approval if a failure needs a runtime/
contract correction. Batch 4 is not started by this diagnostic.

## Third Batch Evidence

2026-10-13: all 35 native cases pass, with zero failures, errors or skips: 29
descriptor/authority cases and six complete selected-caller cancellation cases.
Frozen ancestry and complete native/host inventories pass before and after; both
native suites verify their effective candidate. Patch 37 and earlier inputs,
source overlays and fixture bodies are unchanged. Reports are `suite-0.xml`,
`suite-1.xml` and `qualification.json` under
`.codex-build/governance-g2-switch-callers-qualification-20261013-a`. The report
retains `source_switch_callers_descriptors_only`, `production_qualified=false` and
`acceptance=pending_review`; the disabled-cache `cache_dir` warnings are retained.

Revocation/forced expiry before commit preserves the complete prior records and
projection, including loss during the final in-transaction authorization checks.
Loss before publication retains one `committed_pending_projection` receipt and
the old complete file; pending-caller loss leaves `caller_quarantined` and a
complete new projection. Both histories and historical create/reset receipts
survive; no confirmation or dispatch is granted. Sealed descriptor replacements,
consumed/exited reuse, thread/task transfer, old authority under fresh A conversation
and post-preparation policy withdrawal all deny without unauthorized writes.

The six caller cases use 15 actual native AIAgent constructions and 15 authorized
real-SDK requests through synthetic HTTP: two per source case, three per target
case including the prior B turn. Thirty SDK clients comprise 15 idle initialization
clients and 15 single-attempt request clients, all with zero retries. This is not
live provider, socket or allowed-tool qualification. Cancellation does not undo
the already authorized in-flight request.

Normal/repeated cancellation and a selected child swallowing cancellation cannot
restore either B or A authority. While independently authenticated fresh A runs,
late model/tool/output, both write targets, legacy routing and switch preparation
deny. The same-session A case keeps distinct request IDs and lease roots. No
additional SDK attempt or probe transport/handler call occurs; native records,
projection, reader/root and fixture cache/running-map state are unchanged during
the late probes. The fresh caller remains active and completes successfully,
with A-only history, retained B messages/receipts and route/generation three.
Supporting delivery/title workers remain disabled/inert profile exclusions;
unchanged running-map observation is not general active-worker qualification.
Synthetic private markers are absent from captured output and audit.

All 72 portable tests pass: 47 required product regressions, four new caller-input/
inventory tests and 21 existing contention/crash/switch/composition/checkout checks.
Context validation, release/new-script syntax and whitespace checks pass. New
hashed files preserve LF through actual Windows-style Git checkout. Generated
homes, sources and reports remain ignored, not committed.

Batch 3 is complete for this bounded profile. Next is batch 4 in the agreed order;
storage/path and final compatibility/acceptance batches remain open. Broader
workers, two-authorized-host switching, provider/error paths, provisioning and
production lifecycle remain unqualified. Step 4, bounded switch, work package 3
and G2 are not accepted by these results. No runtime pin, wheel, installer or
production activation change follows.

## Fourth Batch Contract

2026-10-14: the next instruction to proceed starts batch 4 on unchanged Patch 37.
`governance-g2-switch-uncertainty.json` separately pins 18 native cases and six
fresh-process probes, unchanged fixtures, the frozen composition input and full
native/host inventories. The supervisor checks frozen ancestry/inventories before
and after and rejects partial, skipped or failed reports. Each suite/worker checks
its effective candidate. No runtime overlay is authored.

| Combined failure | Expected durable result, always blocked |
| --- | --- |
| Native atomic commit succeeds then reports error | One pending projection receipt and old complete file; no publication or replay. |
| Strict publication completes then reports error | One pending projection receipt and complete new file, not false rollback. |
| Publication receipt commit reports uncertainty | Actual `projection_verified` or `published_pending_caller` row survives, without confirmation. |
| Acknowledgement fails before/after commit, quarantine available | Exact receipt becomes `caller_quarantined`; histories and lifecycle records survive. |
| Same acknowledgement faults, quarantine unavailable | Actual pending/acknowledged row remains, never live confirmation. |
| Same acknowledgement faults, quarantine audit unavailable | Native quarantine can succeed despite unavailable diagnostic audit; no reconciliation claim. |
| Required publication/acknowledgement audit and quarantine audit fail | Projection-verified or quarantined state remains blocked. |
| Caller exception/typed cancellation and quarantine failure | Preserve the original caller failure and pending receipt. This is synchronous caller-body injection, not the full-loop cancellation evidence of batch 3. |
| Quarantine transaction fails before/after its commit | Pending or quarantined row reflects the real SQLite outcome; the original acknowledgement failure remains authoritative. |
| Final caller-lock release error plus audit outage | Durable acknowledgement cannot dispatch; even restoring audit availability cannot recreate missing confirmation. |
| Native security cleanup completes then errors, quarantine unavailable | Prior cleanup is not falsely rolled back; pending caller remains blocked. |

Quarantine commit injection wraps the actual native connection and delegates
every operation except the selected failing commit; no alternate database or
schema is created. Whole-publisher completion/error injection does not qualify
lower-level write/flush/fsync/replace behavior; that remains batch 5.

Each case verifies actual A/B lifecycle state, one correlated switch receipt,
route/generation three, both retained transcripts, historical create/reset
receipts, unrelated metadata and the complete expected projection. Same-host
route selection, authenticated caller entry and switch replay must deny without
further writes or agent/model/tool dispatch. Synthetic private error/history/key
sentinels must not appear in output or audit. No automatic compensation occurs.

Six fresh processes reopen existing fixture records and register native runner/
executor, reset/switch coordinators, preparations and reader, with fresh fixture
identity but no copied confirmation. They must deny reads, caller entry and replay,
preserving records/projection bytes. Fixture registration is not general product
startup or maintenance recovery qualification. Broker/connectors and external
transport remain disabled; customer data and installed artifacts are untouched.

```text
python scripts/verify_governance_g2_switch_uncertainty.py --stage .codex-build/governance-g2-switch-composition-20261008-a --python .codex-build/governance-g1-native-env/Scripts/python.exe --output .codex-build/governance-g2-switch-uncertainty-qualification-20261014-a
```

Preserve failing evidence and request specific approval before a runtime/contract
correction. Step 4/G2 and production remain open.

## Fourth Batch Evidence

2026-10-14: all 18 native cases pass, with zero failures, errors or skips and six
actual fresh-process refusal probes. Full frozen ancestry and native/host inventories
pass before and after; suite/worker verification confirms unchanged Patch 37.
Reports are `native.xml` and `qualification.json` under
`.codex-build/governance-g2-switch-uncertainty-qualification-20261014-a`. They retain
`source_switch_combined_uncertainty_only`, `production_qualified=false` and
`acceptance=pending_review`; the disabled-cache `cache_dir` warning is retained.
Earlier source overlays, test bodies and qualification inputs remain frozen.

Commit-then-error retains one pending projection receipt and the prior complete
file, without attempting publication. Whole-publisher completion-then-error retains
the complete new file, not false rollback. Uncertain receipt commits retain their
actual projection-verified or pending-caller state. Acknowledgement/quarantine faults
produce the expected pending, quarantined or acknowledged durable row, with both
histories, historical receipts and unrelated session metadata preserved.

Every uncertain outcome denies same-host route selection, authenticated caller
entry and replay without further authoritative writes or dispatch. A committed
acknowledgement with failed quarantine or final lock release still has no live
confirmation. Audit restoration alone cannot make it eligible. Required outcome
and quarantine audit failures do not fabricate reconciliation or successful operation.
Native cleanup before an error is not reported as undone. Original caller exception/
typed cancellation survives quarantine failure. Real SQLite quarantine failure
before/after commit leaves the honest pending/quarantined state.

Six independently registered fresh native fixture hosts refuse selection, caller
entry and replay without inheriting reset/switch confirmation or changing records/
projection bytes. No agent, model, tool or external socket executes in this batch.
Synthetic private failure/history/key output and parent audit sentinel checks pass.
These are bounded fault/refusal observations, not general startup, maintenance
repair, durable audit reconciliation, power-loss or worker lifecycle qualification.

All 76 portable tests pass: 47 required product regressions, four new uncertainty
input/inventory tests and 25 existing caller/contention/crash/switch/composition/
Windows checkout checks. Context validation, release/new-script syntax and whitespace
checks pass; hashed inputs retain LF under actual Windows-style checkout. Generated
homes, source trees and reports remain ignored, not committed.

Batch 4 is complete for this bounded profile. Next is batch 5, separate short-write,
flush/fsync/replace, storage/audit and unsafe-path cases, then batch 6's final parity
and acceptance review. Step 4, bounded switch, work package 3/G2 and production remain
open. No new runtime overlay, pin, wheel, installer or activation change follows.

## Fifth Batch Contract

2026-10-14: the instruction to proceed starts batch 5 on unchanged Patch 37.
`governance-g2-switch-storage-paths.json` pins two native suites (17 storage/audit
and 42 path/projection cases), their unchanged fixture dependencies, frozen parent
input and full native/host inventories. The supervisor verifies ancestry before
and after, and rejects failed, skipped, duplicate or partial JUnit reports. Each
suite independently verifies the effective source. No runtime overlay is added.

The publisher cases separately inject temporary-file creation, partial write with
error, flush, fsync, EXDEV/EBUSY replacement failure, reported short write and
falsely reported full write with truncated completed bytes. The prior complete
projection must remain byte-identical, temporary files must be cleaned, and no
replacement/copy fallback may occur for incomplete bytes. The committed native
switch receipt remains pending and cannot authorize selection, caller entry or
replay. Required authorization audit failures cover route read, end, reopen,
switch and acknowledgement; real SQLite authorizer faults cover both publication
receipt updates, acknowledgement and quarantine. This is not durable external
audit reconciliation or power-loss durability qualification.

Five actual fixture directory junction/symlink cases cover before switch, after
commit, completed temporary file, acknowledgement and published reader. Sixteen
exact-path attribute injections exercise symlink/reparse guards on directory,
database, index and lock before/after commit; these are simulated file attributes,
not actual individual-file symlink evidence. Four missing/nonfile cases and one
UNC-before-access case must refuse dispatch and preserve authoritative records.
Fixture link moves/deletion stay within verified temporary roots; only the
verified link is removed, never its target tree or customer files.

Sixteen projection cases alter JSON syntax, contract, instance/database identity,
generation, route presence, target or route version before switch or at an
acknowledged reader. The complete canonical-byte/hash comparison must reject
every altered projection without repair, fallback or SQLite mutation. This is
byte-integrity rejection, not independent coverage of every JSON parser branch.
Both histories, historical receipts and unrelated metadata must survive each
committed failure. Output/audit synthetic-private sentinels and zero agent/model/
tool/socket dispatch are checked. Continuous hostile filesystem/ACL races,
individual-file escape behavior and general lifecycle recovery remain excluded.

```text
python scripts/verify_governance_g2_switch_storage_paths.py --stage .codex-build/governance-g2-switch-composition-20261008-a --python .codex-build/governance-g1-native-env/Scripts/python.exe --output .codex-build/governance-g2-switch-storage-paths-qualification-20261014-a
```

Retain failing evidence and request approval before any source/contract correction.
Batch 6 and explicit bounded switch acceptance remain subsequent work.

## Fifth Batch Evidence

2026-10-14: all 59 native cases pass (17 storage/audit, 42 path/projection), with
zero failures, errors or skips. Full frozen ancestry and native/host inventories
pass before and after; both suites independently verify unchanged Patch 37.
Reports are `suite-0.xml`, `suite-1.xml` and `qualification.json` under
`.codex-build/governance-g2-switch-storage-paths-qualification-20261014-a`.
They retain `source_switch_storage_audit_paths_only`,
`production_qualified=false`, `acceptance=pending_review` and the known disabled-
cache `cache_dir` warning. Input hash is
`06d9b5e61d896be3c331c6480839106a46e4ce8f3e0d586aa29217edc3f3563e`.
Earlier tests, inputs, patches and effective source inventories remain unchanged.

All eight independent publisher faults preserve the prior complete projection
and clean temporary files. Truncated writes, including a false full-length
report, never reach replacement. EXDEV/EBUSY each attempt one strict replacement
without copy fallback. The actual switch remains committed pending projection;
same-host read, caller entry and replay deny without further records or dispatch.
Authorization audit failures before mutation leave SQLite/projection unchanged;
acknowledgement audit failure quarantines the caller. SQLite receipt update
failures retain the exact pending-projection, projection-verified, quarantined or
pending-caller state. Both transcripts, historical receipts, unrelated metadata,
route/generation three and integrity/foreign-key checks survive committed faults.

Actual directory junctions deny at all five selected boundaries. Old or new
complete bytes and a fixture sentinel remain intact; missing/nonfile and UNC
cases never adopt fallback storage. Simulated individual-file symlink/reparse
attributes exercise the named guards without being presented as actual file-
escape qualification. All sixteen malformed-envelope cases deny by canonical
byte/hash comparison before mutation or disclosure, preserving SQLite and the
altered bytes without automatic repair. Reader refusals do not mint authority.
No agent/model/tool/socket dispatch occurs. Captured output remains synthetic-
secret safe, and committed-fault audit sentinel checks pass.

All 80 portable tests pass: 47 required product regressions, four new input/
inventory checks and 29 existing switch/failure/Windows checkout checks. Context
validation, release/new-script syntax and whitespace checks pass. Hash-pinned
files preserve LF through actual Windows-style checkout. Generated sources,
homes, junction fixtures and reports remain ignored, not committed.

Batch 5 is complete for this bounded source profile; no runtime correction was
needed. Next is batch 6's final ordinary-mode parity and criterion review,
retaining known Windows failures and exclusions before explicit switch acceptance.
Power-loss durability, continuous hostile filesystem/ACL races, actual individual-
file escapes, durable audit reconciliation, recovery and general workers remain
unqualified. Step 4, bounded switch, work package 3/G2 and production remain open.
Runtime pin, wheel, installer and plugin activation are unchanged.

## Sixth Batch Contract

2026-10-14: the user approved the batch 6 acceptance criteria and subsequently
explicitly instructed execution. This approves the criteria and execution, not
the unobserved results or bounded switch acceptance. Work remains on unchanged
Patch 37; rotation and frontend composition are not started.

Use the existing ordinary-mode qualifier with fresh output and isolated homes.
Export pinned unpatched Hermes from local Git objects without downloading or
modifying the user's checkout. Verify frozen candidate ancestry, complete source/
host inventories and unchanged native test/conftest bytes before/after. Run the
same 331 cases on both profiles; compare case identities and individual outcomes,
not only totals. Reject collection errors, missing/duplicate/skipped cases,
outcome differences or an unexpected failure set. Expected bounded Windows parity
is 322 passes and the same nine known shell-path failures per profile, not 331
passes. Retain those failures and their JUnit diagnostics.

```text
python scripts/qualify_governance_g2_switch_composition.py --stage .codex-build/governance-g2-switch-composition-20261008-a --python .codex-build/governance-g1-native-env/Scripts/python.exe --ordinary-source-repo ../hermes-agent --output .codex-build/governance-g2-switch-final-parity-20261014-a
```

Review retained exact-count Step 3/batch 1-5 XML and qualification reports against
current frozen contracts, report/input hashes and matching inventories. Distinguish
the 199 composition/replay and 130 failure-matrix case records from fresh executions
in this batch. Reconcile permissions, source/target isolation, normal-exit cleanup,
confirmation, cancellation, crash/restart, contention, uncertainty and complete
projection outcomes against the approved switch contract. Preserve denied broader
paths and every stated exclusion; do not create new grants to close a review row.

Rerun the required product regressions and existing report-parser, provenance and
Windows checkout checks, context validation and release-script syntax checks.
Record exact counts, report locations, hashes, warnings/known failures and any
uncovered criterion in `governance_g2_switch_acceptance_review.md`. Generated
sources/homes/reports stay ignored; earlier inputs keep their pending-review labels.
Recommend bounded acceptance only after the evidence passes. Explicit user
acceptance of the results remains necessary before closing Step 4 or moving to
rotation. Runtime changes, scope changes or reordered work require specific approval.

## Sixth Batch Evidence And Recommendation

2026-10-14: fresh ordinary comparison executes all 331 cases per profile. Patch 37
matches pinned unpatched Hermes case-for-case: 322 passes and the same nine known
Windows absolute shell-path failures on each profile, zero skips/collection errors
and no missing/duplicate cases. Full frozen ancestry, native/host inventories and
unchanged native test/conftest bytes verify before and after. Reports are under
`.codex-build/governance-g2-switch-final-parity-20261014-a`; this is bounded parity,
not an all-passing Windows suite. Known failures remain visible and relevant.

The retained 199 composition/replay plus 130 failure-matrix records verify against
their exact-count XML, current frozen test/fixture contracts and input/inventory
hashes. `.codex-build/governance-g2-switch-final-evidence-20261014-a.json` records
XML/report checksums and explicitly labels these as historical evidence, not 329
fresh executions. All 80 portable regressions pass again; context, release-script
syntax and whitespace checks pass. Final Windows checkout checks include the
new acceptance-review document. Generated exports/homes/reports remain ignored.

`governance_g2_switch_acceptance_review.md` maps the approved criteria to native
records, file bytes, transport/handler observations and audit outcomes; it records
report hashes, the exact nine failures, prior warnings and every bounded exclusion.
No new runtime correction, authority grant or reordered milestone was needed.
Batch 6 execution and review are complete. Recommend bounded switch Step 4
acceptance with those exclusions; explicit user result acceptance is pending.
Rotation/frontends have not begun. WP3/G2, installed artifacts and production
remain unaccepted; runtime pin, wheels and activation gates remain unchanged.

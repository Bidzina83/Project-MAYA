# G2 Switch Failure Matrix

## Current Step

2026-10-09: the user explicitly accepted bounded switch Step 3 and authorized
Step 4 on unchanged Patch 37. The accepted profile remains one acknowledged
create A, initial reset A-to-B, then same-owner switch B-to-A. This document
organizes the existing failure requirements; it adds no runtime authority.

Batches 1-2 now pass on that unchanged profile. Next is batch 3, late callers,
cancellation and descriptor faults; Step 4 and bounded switch acceptance stay open.

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

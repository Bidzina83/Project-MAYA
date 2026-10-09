# G2 Switch Failure Matrix

## Current Step

2026-10-09: the user explicitly accepted bounded switch Step 3 and authorized
Step 4 on unchanged Patch 37. The accepted profile remains one acknowledged
create A, initial reset A-to-B, then same-owner switch B-to-A. This document
organizes the existing failure requirements; it adds no runtime authority.

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

# G2 Switch Acceptance Review

Review date: 2026-10-14. Decision: explicitly accepted by the user on 2026-10-14,
bounded source-level switch Step 4 on unchanged Patch 37 with all exclusions
below. The later "I accept" approved the results, not merely the batch 6 criteria.

## Scope And Candidate

G2 work package 3, switch Step 4 batch 6, on unchanged Patch 37 over its frozen
Patch 36/35 ancestry. The only reviewed transition is acknowledged create A,
one initial reset A-to-B, then one same-owner switch B-to-retained-parent A.
Fresh authentication, independent permissions, normal-exit acknowledgement and
live process-bound host confirmation remain required. No general switch, recovery
or administrative authority is added. Hermes conversation stores remain separate
from Maya SMB memory; MEMORY.md/USER.md and Metabase stores are not redirected.

This review follows `governance_g2_switch_transition.md`, the ordered batches in
`governance_g2_switch_failure_matrix.md`, the ownership/consistency contracts and
the approved G0-G7 integration plan. No runtime fix or scope/order change was
needed. Runtime pin, wheels, installers and production activation are unchanged.

## Approved Criteria

| Criterion | Observed outcome and assessment |
| --- | --- |
| Frozen source integrity | Full frozen ancestry and native/host inventories verified before and after the fresh comparison. Native test/conftest bytes match pinned Git objects; candidate sources and earlier inputs remain unchanged. Passed. |
| Ordinary Hermes compatibility | Fresh runs execute the same 331 cases against Patch 37 and pinned unpatched Hermes; exact identities and individual outcomes match. No collection errors, missing/duplicate cases or skips. Passed bounded parity, not a failure-free suite. |
| Visible known Windows failures | Each profile has 322 passes and exactly the same nine known absolute shell-path failures listed below. No new or different failures. Their JUnit diagnostics are retained, not skipped or renamed as passes. Passed bounded criterion; shell/platform qualification remains open. |
| Complete criterion-to-evidence review | Retained 199 composition/replay and 130 failure-matrix case records are validated against exact-count XML, frozen test/fixture contracts, input hashes and matching native/host inventory hashes. These are historical evidence records, not 329 fresh executions today. The reconciliation below identifies their coverage and explicit limits. Passed within the approved profile. |
| Integrity and denial guarantees | Reviewed native records, file bytes, transport/handler counts and audit assertions cover retained A/B history and receipts, complete old-or-new projection, independent per-action authority and denial without live confirmation. Missing or uncertain confirmation never becomes authority through a durable receipt, audit restoration or replay. Passed within the approved profile. |
| Product/provenance/reporting checks | All 80 portable tests pass, including 47 required product regressions and 33 existing report/provenance/Windows checkout checks. Context, release-script syntax and whitespace checks pass. Earlier disabled-cache-provider warning remains documented; known failure diagnostics and hashes are retained. Passed. |
| Scope and acceptance decision | All exclusions below remain explicit and denied/unqualified as applicable. The user explicitly accepted bounded switch Step 4 results on 2026-10-14. Rotation and frontend composition have not begun; WP3/G2 and production remain unaccepted. |

## Native Evidence Reconciliation

| Switch requirement | Evidence and bounded conclusion |
| --- | --- |
| Independent permissions and atomic effects | The 43-case frozen atomic replay on Patch 37 covers route/source/target reads, switch/end/reopen permissions, owner/classification/lineage rejection, invalid/replayed authority, busy state and actual native SQLite effect-count/rollback failures. Commit alone grants no dispatch. |
| Publication, acknowledgement and fresh A agent | The 42-case composition suite verifies the exact current switch correlation, historical create/reset receipts, fresh actual AIAgent, independently authorized A-only history, real SDK with synthetic HTTP and zero retries, denied model egress with zero transport, and no B agent/snapshot/approval/cache transfer. The 80 create and 34 reset replays preserve the accepted shared paths. |
| Normal-exit cleanup and host confirmation | Composition cases deny raised/no-op/incomplete cleanup, caller failure/cancellation/close, denied acknowledgement, revocation/expiry, uncertain commits, final lock-release failure, missing/forged/process-mismatched confirmation and fresh registration. Native approval waits are denied; unrelated route state is retained. Cache detachment is not general resource teardown. |
| Process crash/restart | Batch 1 has ten actual crash/fresh-host cases and twenty workers. Native pre/post-commit state, both transcripts, receipts and complete files match the boundary; new-host reader/scope refuses adoption without mutations or dispatch. This is not a restarted full product lifecycle or power-loss guarantee. |
| Contention and busy requests | Batch 2 has eight cases and nine independent workers covering actual projection/SQLite locks, active B scope, commit/publication and pending/acknowledged routing. Competing hosts cannot overwrite or inherit confirmation. The unconfirmed-host cases do not qualify two authorized switch hosts or automatic failover. |
| Late callers, cancellation and descriptor faults | Batch 3 has 29 descriptor/authority faults and six actual source/target caller cancellation races. Fifteen authorized synthetic SDK requests exercise the native caller. Late B/A executors cannot borrow fresh A authority, even with the same session ID; repeated/swallowed cancellation does not restore authority or add transport/writes. |
| Combined uncertain outcomes and quarantine | Batch 4 has eighteen cases and six fresh-process refusal probes. Real commit/publication/ack/quarantine outcomes remain honestly pending, quarantined or acknowledged-but-blocked, without fabricated rollback, blind retry or compensation. Audit restoration alone cannot recreate live confirmation. Original caller failures survive failed quarantine. |
| Separate storage, audit and receipt faults | Batch 5 has seventeen cases. Creation/write/flush/fsync/EXDEV/EBUSY faults, short writes and falsely reported complete writes preserve the old complete file and clean temporary files. Real SQLite receipt update failures and required authorization-audit failures retain the exact blocked state without dispatch. |
| Unsafe paths and malformed projection | Batch 5 has forty-two cases: five actual directory-junction boundaries, sixteen scoped simulated file-attribute guards, four missing/nonfile cases, one UNC-before-access guard and sixteen altered-envelope cases. Projection rejection is canonical-byte/hash evidence, not every parser branch; individual-file escape/race behavior is not qualified. |

The 329 retained native case records contain no failed, errored or skipped cases.
This reconciles the observed bounded switch contract; it is not exhaustive
full-fork, worker, ingress, model-provider or installed-product coverage.
Synthetic-private output/audit assertions are retained as recorded in each batch;
they do not qualify general provider-error redaction, which remains later work.

## Fresh Ordinary Comparison

The existing qualifier exports unpatched commit
`b13e2fd6948a59eeb59fe618914147d97a2ee90a` from prepared local Git objects,
without network downloads or changing the user's Hermes checkout. Both profiles
use isolated homes and credential-filtered environments. Native inventories and
test/conftest bytes are verified; the same ordinary cases run without mandatory
candidate activation. Full frozen ancestry/inventories are rechecked afterward.

Per profile: 88 session, 225 approval, 16 slash-confirmation and two ordinary
cache controls, totaling 331. Each records 322 passes, nine failures, zero skips
and zero collection errors. The same test identities have the same outcomes.

The exact unchanged Windows failure set is:

```text
TestHermesConfigWriteProtection::test_perl_in_place_absolute_hermes_home_config
TestHermesConfigWriteProtection::test_ruby_in_place_absolute_hermes_home_env
TestHermesConfigWriteProtection::test_sed_in_place_absolute_hermes_home_config
TestHermesConfigWriteProtection::test_sed_in_place_absolute_hermes_home_env
TestSensitiveInPlaceEditPattern::test_ruby_in_place_absolute_home_zshrc
TestSensitiveRedirectPattern::test_append_to_absolute_home_ssh_authorized_keys
TestSensitiveRedirectPattern::test_redirect_to_absolute_home_bashrc
TestSensitiveRedirectPattern::test_redirect_to_home_set_after_import
TestTeePattern::test_tee_absolute_home_bashrc
```

These are retained failures, not nine successful tests. Bounded ordinary parity
does not establish managed shell/tool safety or Windows product support. Earlier
native suites retain the known pytest `cache_dir` warning caused by disabling
the cache provider; no warning is treated as a runtime capability or silently fixed.

## Evidence Locations

Fresh comparison: `.codex-build/governance-g2-switch-final-parity-20261014-a/`.
`parity-report.json` and both profiles' four `suite-*.xml` reports preserve
case counts/outcomes and failure diagnostics. The command is in the failure matrix.
Parity-report SHA256:
`ec4ed8f78e1366fa50c1de9cfa327c6b6fd6bf0b56170ca2f1fdcfa7bf028233`.

Retained-evidence audit:
`.codex-build/governance-g2-switch-final-evidence-20261014-a.json`.
It records every reviewed XML/report checksum, current input hash and count,
with `fresh_native_execution=false`, `production_qualified=false` and
`acceptance=pending_review`. Audit SHA256:
`b42adab3e77077b358a76fdab19a21d1b55155b6dded99d7dff48fe92ca19cfe`.

Frozen native inventory SHA256:
`1267339ad34d7f50dc49c6e2aa6409465331b86cdc8db6af718d9a7f993dbba7`.
Frozen host inventory SHA256:
`b20d0faa71b72daed6802753fd2a5dc4bd95982c75e49ac81769e987af01d20d`.
Composition input SHA256:
`13d0f0be580f176946e9901798d8bb5617aeda8e1c975fcdcd3e6860a55fe304`.

Earlier exact-count reports remain in the six qualification directories cited by
the switch runbook/failure matrix. Their original pending-review labels, frozen
inputs, fixtures, source overlays and earlier warnings are not rewritten. Today's
329-case audit reviews those reports; only the ordinary comparison and portable
regressions were freshly executed for batch 6. Generated exports, homes and
reports remain ignored, not committed or packaged.

## Exclusions And Decision

Preserve these boundaries in any acceptance decision:

- Live provider/connector authentication, normal Telegram/API/CLI frontend composition and setup/maintenance identity remain later work.
- General tools, terminal/shell qualification, arbitrary workers, title workers, nested delegation and general resource teardown are not qualified.
- General/repeated/back-and-forth switch, title/branch listing, automatic continuation lookup, repeat reset and rotation remain denied/unqualified.
- Two independently authorized switch hosts, transferable confirmation, automatic failover and maintenance adoption are not qualified.
- Schema provisioning/repair, full compression, governed SMB memory coverage and durable audit reconciliation retain G3 and later gates.
- Actual individual-file symlink escapes, continuous hostile filesystem/ACL races and power-loss durability remain outside the bounded path evidence.
- The nine ordinary Windows failures remain relevant before shell/platform qualification; no Windows desktop or clean-install lifecycle claim follows.
- Production activation, model routing, capability markers, runtime pins, Hermes wheels and installers remain unchanged and unqualified by this review.

The bounded execution/evidence criteria pass. No new runtime defect or contract
dependency was identified in this final batch. On 2026-10-14 the user replied
"I accept" to the completed batch 6 results and explicit acceptance recommendation.
Bounded switch Step 4 is closed on unchanged Patch 37 with all stated exclusions;
switch Steps 1-4 are complete for this one same-owner switch-back profile only.
This is not completion of work package 3/G2, full-fork or production governance.
Frozen evidence, original pending-review labels, known failures and warnings remain
unchanged; this document records the decision rather than rewriting test inputs.

Next is source-informed rotation contract review within WP3, followed by approval
of that specific contract before implementation. Rotation is still denied/
unqualified; it is not automatically enabled by switch acceptance. No installer
rebuild, production activation or broader transition grant is authorized here.

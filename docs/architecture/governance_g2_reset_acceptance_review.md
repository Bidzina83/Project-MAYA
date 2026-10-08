# G2 Reset Acceptance Review

Review date: 2026-10-08. Decision: pending explicit user acceptance.

## Scope

This reconciles G2 work package 3 reset Step 4 against the ordered reset contract
and consistency protocol. Step 3 was explicitly accepted on 2026-10-07. Its
frozen Patch 34 evidence is retained; the user-approved host-only Patch 35
publisher correction is the current bounded candidate. Native Hermes source is
unchanged by Patch 35. No installer or production activation is authorized.

The supported source profile is one initial, same-owner acknowledged create to
reset, with a fresh host-bound caller, retained source history and an empty new
target. A reset target cannot itself be reset in this profile. Durable reset
acknowledgement is insufficient for restart routing without live host confirmation;
maintenance reconciliation is not implemented or silently granted.

## Criterion Reconciliation

| Step 4 criterion | Evidence and bounded assessment |
| --- | --- |
| Process crash/restart | Eight corrected-profile replay cases terminate real workers and inspect independent SQLite state. Precommit state remains original; postcommit effects remain blocked on a new host. |
| Contention/competing reset/busy old request | Four corrected-profile process cases enforce exclusion and allocate one reset target, without forced lock takeover. |
| Late executor/cancellation | Three corrected-profile actual native caller cases prevent cancelled old executors from borrowing fresh reset authority, including repeated/swallowed cancellation. |
| Revocation/expiry/stale/replay/foreign authority | Eighteen corrected-profile descriptor cases deny at the stated boundaries without unauthorized allocation or authority transfer. |
| Unknown commit and combined publication/acknowledgement/audit failures | Thirteen corrected-profile cases retain committed/uncertain state honestly, deny readiness without confirmation and never blind-retry or fabricate rollback. |
| Separate write/flush/fsync/replace/receipt/audit failure | Twelve unchanged storage cases pass after Patch 35. Six additional create/reset publisher checks reject incomplete/corrupted temporary bytes before replacement. The original failed Patch 34 regression remains preserved. |
| Actual caller/reader composition and atomic reset | Thirty-four corrected-profile composition and twenty-two atomic cases preserve source data, exact lineage and independently governed fresh-agent execution. The 80-case create replay checks the shared publisher against its accepted parent behavior. |
| Unsafe paths | Twenty-six new native cases cover five real directory junction boundaries, sixteen explicit attribute probes, four missing/non-file storage cases and one UNC guard. Actual file-link races/ACL attacks remain excluded; see the detailed path runbook. |
| Ordinary-mode compatibility | All 331 exact-count outcomes match pinned unpatched Hermes: 322 passed, nine known Windows absolute shell-path assertions failed on each profile, zero skips/errors. Native tests remain unchanged; failures are not suppressed or called passes. |
| Product/provenance regressions | All 77 required product and provenance/report-parser cases pass. Context, syntax, whitespace and final inventory checks are recorded in the path runbook. |

Evidence references: `governance_g2_reset_failure_matrix.md`,
`governance_g2_publisher_correction.md`, `governance_g2_reset_paths_parity.md`,
`governance-g2-publisher.json`, `governance-g2-publisher-replay.json` and
`governance-g2-reset-paths.json`. Earlier accepted inputs and labels are not
rewritten to manufacture current acceptance.

## Limits And Decision

Live providers/connectors, repeat reset, switch/rotation, general tools/workers,
frontend authentication, production schema provisioning, maintenance recovery,
durable audit reconciliation, actual file-symlink escapes, continuous hostile
filesystem races, ACL attacks and power-loss durability remain outside this
profile. The existing Windows shell-path failures remain relevant before managed
shell/tool and product platform qualification. Synthetic transport/native source
tests do not qualify installed artifacts or claim Windows desktop support.

The bounded criterion evidence is complete on the unchanged corrected profile.
Recommendation: accept bounded source-level initial reset with the stated
exclusions. No new runtime defect was identified by the final path/parity batch.
This is a recommendation, not an acceptance decision or a full-fork qualification.
Step 4 is not closed merely because CI is green. Explicit user acceptance is
still required before another transition; work package 3, G2 and production
remain unaccepted. No installed artifact or capability marker is changed.

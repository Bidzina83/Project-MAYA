# G2 Create Acceptance Review

Review date: 2026-10-05. Decision: bounded source-level create accepted by the user
on 2026-10-05. Work package 3 and G2 remain unaccepted.

## Plan Location

This is G2 work package 3, create transition Step 4, and caller refinement
Step 4 (acceptance review). It does not authorize reset, switch, rotation,
frontend composition, a new runtime patch, or an installer rebuild.

The acceptance requirements are in `governance_g2_create_transition.md`,
`governance_g2_session_consistency.md`, and
`governance_g2_caller_acknowledgement.md`. The effective source candidate is
the frozen Patch 31 no-snapshot profile. Evidence on earlier overlays remains
historical evidence, not automatically qualification of that final profile.

## Requirement Reconciliation

| Requirement | Evidence | Assessment |
| --- | --- | --- |
| Exact owner/store authority; denied allocation has no effects | Final-profile create and acknowledged reader replay | Bounded final-profile pass. |
| SQL rollback, unknown commit and no blind replay | Final-profile create replay and actual process crashes/restart | Bounded final-profile pass. |
| Cross-process exclusion and competing allocation | Independent-process reader contention and two prepared allocation workers | Bounded final-profile pass; one allocation, pending caller is not dispatch authority. |
| Cancellation, expiry and revocation at commit/publication/ack boundaries | Final-profile authority-loss and caller replay | Bounded final-profile pass. |
| Strict replacement, acknowledgement/audit failure and unsafe paths | Final-profile failures and actual Windows junction replacement | Bounded final-profile pass; continuous hostile races remain excluded. |
| Temporary-file write and fsync failure | Separate partial-write and fsync injections at actual projection sink | Pass: old complete index, retained blocked commit, removed temporary file, no blind retry. |
| Caller normal-exit acknowledgement; failure quarantine; pending/legacy reader denial | Final-profile caller replay and real process exit before acknowledgement | Bounded final-profile pass. |
| Existing-session recognition without recreation or metadata grant | Patch 30 native recognition cases | Scoped parent evidence plus final-profile conversation coverage. |
| Governed no-snapshot first/resumed conversation; independent model denial | Patch 31 native cache/loop matrix | Bounded final-profile pass. |
| Independent process continuation and denied owner/mode/stale projection | Four two-process cases in `governance_g2_restart_loop.md` | Bounded final-profile pass. |
| Ordinary-mode compatibility | Ninety session/cache controls each on disposable patched and unpatched copies | Scoped parity pass; not full-fork compatibility. |
| Full product, frontend authentication, maintenance recovery and durable audit reconciliation | Explicitly excluded from these fixtures | Deferred to the agreed downstream gates, not passed. |

Frozen evidence inputs are `governance-g2-prompt-cache.json` and
`governance-g2-restart-loop.json`; caller case mapping is in
`governance_g2_caller_qualification.md`. This review does not rewrite any frozen
input, test, source inventory, or acceptance label.

## Limits And Verdict

The native caller uses actual AIAgent, SDK and SQLite with synthetic transport.
It does not qualify live providers, real connectors/tools, background workers,
production schema provisioning, continuous hostile path races, ACL attacks,
power-loss durability, or clean-install lifecycle. The outer handoff preserves
a typed stop but does not qualify exact denial-code preservation. These limits
remain exclusions of the accepted bounded source-level create profile.

The two evidence gaps identified in the initial review are now closed within
the approved bounded profile. No runtime defect was identified and no runtime
repair was applied. The user's explicit acceptance grants bounded source-level
create acceptance, retaining the exclusions above. Acceptance is not inferred
from CI or approval to execute qualification. Work package 3 still has other transitions;
G2 additionally requires authenticated frontend composition and identity lifecycle.

## Approved Closure Evidence

The user approved this closure on 2026-10-05. The separate frozen input is
`governance-g2-final-create.json`, checked by
`scripts/verify_governance_g2_final_create.py`. Its test SHA256 is
`798b199bfb4b0381e5367f55412acf8f52b44f92b37e9d440946f4bf2620361b`.
It retains the complete Patch 31/parent inventory verification and hashes seven
unchanged parent fixture files. Each independent worker checks the same contract.

- Final native matrix: 80 passed, no skips (329.80 seconds).
- Ordinary controls: 90 patched and 90 unpatched passed, no skips.
- Required product regressions: 47 passed.
- Provenance and actual Windows checkout controls: 8 passed.
- Context validation, syntax and whitespace checks passed.

The native runs emit the known unknown `cache_dir` warning because the pytest
cache provider is disabled. This is not a skipped qualification case.

Parent tests and verifiers are unchanged. The new harness reuses unchanged
case functions under its own full-tree verification. It replaces obsolete
`published` expectations with `published_pending_caller`, and replaces the
historical caller-failure limitation assertion with the existing quarantine
contract cases. New process workers use staged host paths and isolated homes.
The allowed cross-process reader enters/exits its request scope before asserting
cache cleanup. Initial harness-only failures are not final acceptance evidence.

No production activation, runtime pin, native patch, wheel, installer or installed
data changes. The create acceptance decision is now recorded. Next is reset
within work package 3, following the existing owner-scoped design and consistency
protocol. Reset remains disabled until its own implementation and native allowed,
denied and failure-path acceptance criteria pass. This decision does not accept
general resume, switch, rotation, frontend composition, G2 or production.
Frozen input manifests retain their original pending-review labels; this document
records the decision without rewriting evidence.

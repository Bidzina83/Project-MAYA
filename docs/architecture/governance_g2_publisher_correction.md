# G2 Step 4 Publisher Correction

## Approved Scope

On 2026-10-08 the user approved a bounded correction over frozen Patch 34, then
affected create/reset requalification, then the existing unsafe-path and
ordinary-mode parity matrix. This stays within G2 work package 3 reset Step 4;
it does not authorize another transition or production activation.

Patch 35 changes only the staged Maya host's shared `session_creation._publish`:
require an integer write count equal to the full serialized projection length,
flush/fsync/close the temporary file, and verify its complete bytes before strict
replacement. Boolean/zero/short counts and corrupted full-length files fail before
replacement. Existing path checks, locking, typed errors, cleanup, no-copy
replacement and post-replacement verification remain. No automatic recovery or
cross-store atomicity is introduced.

The entire native Hermes source inventory remains identical to frozen Patch 34.
The host inventory differs at exactly one file. The corrected stage is
`.codex-build/governance-g2-publisher-20261008-a`; generated stages are not release
artifacts and must not be committed. The patch is not applied to production code,
the runtime pin, installed wheels or installers.

## Frozen Evidence Contracts

`governance-g2-publisher.json` pins the parent, correction, effective host file,
six qualification entry points and 27 unchanged test fixtures. Preparation
verifies parent ancestry and checks the entire resulting source/host inventories.
The six suites comprise 80 create, 34 reset-composition, 22 atomic-reset, 12
storage, 13 combined-fault and six additional publisher-integrity cases (167).

`governance-g2-publisher-replay.json` separately pins four replay entry points:
eight process-crash/restart, four process-contention, eighteen descriptor and
three late-executor/cancellation cases (33). Supervisors check frozen ancestry;
worker entries check corrected inventories and fixture hashes before native use.
Only test entry/worker provenance is rebound; native authority and test assertions
are not replaced. Original manifests, source candidates and regression bodies
are preserved, including the failing Patch 34 short-write regression.

## Qualification Status

2026-10-08: all 167 corrected-publisher create/reset cases pass, with no skips.
The original twelve-case storage suite now passes unchanged, including the
previously failing short-write regression. Six additional create/reset cases
check zero/boolean counts and full-length corrupted temporary bytes before
replacement. The native run retains the existing disabled-cache-provider warning.
All 33 separate process/descriptor/cancellation replay cases also pass, with no
skips and the same configuration warning. The total is 200 bounded native cases.
Actual worker crash/restart and contention preserve their previous outcomes;
stale/revoked/expired authority and late cancelled executors remain denied.
These replay results qualify the corrected host profile, not a rewrite of the
earlier Patch 34 evidence or a general worker/recovery guarantee.

All 71 product/provenance regressions pass (68 in the combined product/manifest
run plus three replay-manifest checks). Context, syntax and whitespace checks
pass. Both contracts retain `pending_review` and `production_qualified=false`;
no acceptance is inferred from portable manifest tests or source diagnostics.
The next authorized item after affected requalification was the remaining
unsafe-path and ordinary-mode parity matrix. Its final evidence and the bounded
reset acceptance recommendation are now in `governance_g2_reset_paths_parity.md`
and `governance_g2_reset_acceptance_review.md`. Explicit user acceptance is still
pending; the correction does not itself close reset Step 4.

Live providers/connectors, general tools/workers, repeat reset, maintenance
reconciliation, production provisioning, power-loss durability and G3 durable
audit reconciliation remain excluded. Reset Step 4, G2 and production remain
unaccepted.

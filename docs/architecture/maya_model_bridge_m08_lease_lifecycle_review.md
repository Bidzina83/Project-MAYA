# M08 Lease Lifecycle Review

Read-only product review2026-11-04 after Final2 scoped cleanup. Approval covers
review/documentation only, not product/test implementation, assembly or native run.

## Findings

1. Final2's original guard observed expiry at2230ms against a2000ms lease,
   phase runtime_delivered, with no closed/audit/revoked condition. Correct
   fail-closed behavior; text mismatch was never tested in this run.
2. One lifetime spans multiple stages. model_service.py:issue samples its clock
   once and sets expiry+2; _live checks it at request/dispatch/release and
   prepare_operator before final-text comparison. Coordinator ModelBridgeRuntime
   waits for model_child_complete, positive report, SDK shutdown/config/origin
   checks before RunFinalText. These consume the same lifetime. The report does
   not allocate2230ms between those stages or prove a particular stage is slow.
3. model_worker.py imports model_final_text only after receiving model_prepare_final,
   before calling prepare_operator. That module imports other fixed bridge modules.
   This is avoidable fixed setup inside a live authorization interval, including
   whatever transitive import work is not cached. Neither import cost nor its
   contribution to the230ms overrun was measured. No native performance claim.
4. The two-second fixture lifetime is not a demonstrated production lifetime
   suitable for real inference, network latency, or arbitrary Hermes work.
   Synthetic success cannot establish that. WFP/AppContainer changes do not
   correct this application authorization-lifecycle issue.

## Recommended Next Source Scope

Prepare ONLY an M08-specific eager import of the same fixed final-text helpers
before service construction/readiness/issue. Retain the same module/functions,
final message parsing, lock/guard/decision ordering and diagnostic fields.
No authorization/lease/clock/dependency/security change; no lazy fallback after
issue and no ignored import failure. An import failure must prevent readiness.
Do not initialize a new grant, reset expiry, skip checks, or pre-authorize final
publication. Moving setup earlier can reduce avoidable lease consumption, but
does NOT guarantee native success or fix the observed timing deficit.

Preserve positive child conversation and all postconditions before final command;
do not submit the trusted fixture's expected output early and call it Hermes's
native final. Preserve original26-field effects/five-record operator-destination
audit, gateway2/effects(1,1,0), zero operator publication and uncertaintytrue.
Expiry must remain blocked. Keep Final2 diagnostics to observe the next attempt.

This is the smallest source-preparation candidate worth testing before changing
authorization semantics. If it still expires, stop; do not keep tuning sleeps,
TTL, retries or moving correctness checks merely to force an M08 pass.

## Alternatives And Product Design

Increasing TTL may change the frequency of expiry but enlarges the authorization
window and does not fix conflated lifetimes. A measured/product-approved bound
would need explicit design approval plus expiry/revoke/replay regression tests.
No arbitrary replacement duration is recommended by this evidence.

For real model traffic, recommend a separate future design for phase-specific
authorization: short-lived dispatch admission, truthful durable dispatch/delivery
receipts, then independently authorized bounded output release when an actual
candidate is ready. This must be a NEW explicit action, not automatic renewal of
an expired grant. Bind operator/attempt/request/response/candidate hash/destination,
policy version and one-use identity; recheck current policy/revocation and any
required consent; distinguish receipt recording from authority to disclose.
Retain crash/replay/fail-closed audit handling and final publication checks.
No child may mint or refresh authority. An earlier dispatch permission cannot
implicitly authorize later disclosure. Policy/consent/revocation semantics and
the exact security contract need separate review before implementation.
This future product design is NOT an M08 correction approved here and would
require revised schemas, audit admission and earlier-case regression coverage.

## Proposed Inert Acceptance Contract

- M08 imports the exact helpers before readiness and issue; non-M08 flow unchanged.
- Import failure sends no ready/grant, dispatch, runtime write or publication.
- Differential original _live/issue outcomes, operand order and clock counts match.
- Before/exact/after deadline retain text rejection/expiry boundary behavior.
- Earlier closed/audit/revoked/phase failures do not read the clock.
- Positive child postconditions still precede the trusted final mutation/command.
- Original effects/audit validators and denial diagnostics unchanged; no new grant.
- Wrong text with live lease yields original operator_text evidence; expiry,
  missing evidence and unavailable diagnostics stay blocked with truthful effects.
- Verify all reviewed product deltas and frozen Final2/predecessor identities.

These are proposed tests, NOT newly executed tests or source compatibility proof.

## Approval Gates And Verification

Request M08-only SOURCE preparation/inert tests for the eager-import change next.
No assembly/omissions/native retry authorized. Later source review, separate offline
assembly, full actual-profile inventory/resources/freeze, matching guest hash,
separate exact-artifact one-run approval and fresh consent remain mandatory.
Preserve Final2 and every predecessor. No TTL/deadline/permissions/WFP/token/job/
dependency/grant change, inference/recovery/M09/M2/qualification. Gate A open.

Review rehashed Final2 ZIP/EXE,391 frozen files and167 current product files against
sealed manifest. Read original service/worker/child/coordinator sequencing and
prior M08 contract. No product/test source edit, compile, product/bundled-runtime/
native/VM execution or new runtime experiment. This review is not a security scan.

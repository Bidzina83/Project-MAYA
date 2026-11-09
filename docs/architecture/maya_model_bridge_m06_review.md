# M06 Runtime Output Denial Review

Subsequent decision: user approved M06-only source preparation and inert tests.
See maya_model_bridge_m06_source_review.md for implementation and evidence.
Original review-only language below is historical, not package/run approval.

2026-11-01. Review/test-contract preparation only after bounded M05b success.
No product/test source edit, compilation, package, native/bundled-runtime run,
VM/security change, credential access or inference. Preserve frozen predecessors.
See maya_offline_model_recreate_1_outcome.md and maya_model_bridge_m06_tests.json.

## Purpose And Findings

Allow model.egress but omit ONLY model.output from fixed host-owned policy.
The original service must validate the unchanged native request, dispatch one
synthetic response, validate its exact bytes, then deny release to Hermes.
Expected effects(1,0,0), total gateway calls2, no runtime/model-response write or
operator publication. This is application authorization, not changed WFP rules.

OfflineModelBridge.prepare_runtime currently executes:
request admission -> original egress authorize -> durable egress_intent ->
synthetic dispatch/response validation -> durable dispatch_outcome ->
runtime destination -> original output authorize -> runtime_release_intent ->
runtime preparation. Thus a genuine output DENY must stop before release intent/
preparation, preserve dispatch_attempted and validated response metadata, and
produce a third denied event at runtime:<actual attempt>.

The original _authorize records named no-matching-rule evidence ONLY for egress.
Output failures currently become ModelDenied and a generic denied event through
_fail; that event alone cannot distinguish the intended gateway outcome from
another failure. Recommend an additional bounded read-only observation alongside
the existing egress flag: capture actual AuthorizationResult DENY with
governance.no_matching_rule/no constraints/no redactions for model.output at
runtime:<actual attempt>. It must not change the original authorization result,
policy matching, service guards, counters or exception/uncertainty behavior.
This new product-source observation requires explicit source-preparation approval.

ModelHostFiles.Prepare currently emits both rules except the fixed M02 egress
omission. Worker validates that exact policy; both need a separate M06-only policy
selection, preserving all other modes. Existing ModelDenialAdmission expects
M02/zero dispatch/one audit record and CANNOT admit M06 by relabeling it.
Ordinary positive coordinator expects a model_response; it cannot continue that
path when output is denied. Existing child denial adapters provide a compatible
pattern for a separate exact M06 control, not a fake positive conversation.

## Proposed Fixed Native Schedule

1. Fresh product-owned setup/consent and M06-only fixed profile. Policy contains
   exactly the existing egress allow for actual operator/target/infer; output allow
   absent. No user OS preconfiguration, rule mutation mid-test or second policy
   engine. Same grant, TTL2000ms and all channel/child deadlines and byte bounds.
2. Real pinned Hermes constructs and sends its original valid request once.
   Preserve pinned class/factory/config/distribution/origin checks. No M05
   recreation/probe, retry, fallback or second conversation.
3. Trusted worker invokes ORIGINAL prepare_runtime. Require actual egress allow,
   valid exact response, one dispatch, two gateway calls and named runtime output
   no-matching-rule denial. The service closes through original failure handling.
   Original ModelDenied.uncertain must remain TRUE because dispatch occurred.
   This is not a fabricated provider failure or a zero-effect denial.
4. A bounded M06 worker control reports named boundary/effects/hashes/counts,
   never raw synthetic response body or provider output. Specific frame/schema/
   key counts are to be source-reviewed before assembly. No model_dispatch_reply
   or model_response is forwarded; no runtime confirmation command is issued.
5. Coordinator independently binds trusted attempt/operator/request/route/digest,
   preserved dispatch and zero releases; sends the child an exact case-bound
   denial control on the existing private pipe. It is control, not model output.
   Candidate child control may reuse model_denied shape with case=M06 and
   reason=gateway_runtime_output_denied, but existing M02 controls stay unchanged.
6. Child must observe that exact control, then close normally. Report genuine
   constructor and one native request; native_conversation=false because no
   model response was delivered. An expected SDK connection error is acceptable
   ONLY alongside exact denial observation. No fabricated final text/positive
   conversation. Generic error, timeout or crashed process cannot pass.
7. Require child/worker EOF and natural exit0, bounded empty stderr, exact fresh
   beacon and protected files. Reread/admit exactly THREE records independently.
   No model_prepare_final, operator preparation, completion-to-output recovery,
   worker reopening or additional protected action.

## Exact Proposed Audit Admission

Ordered records, existing schema and original generic reason codes preserved:
- egress_intent: allow, provider destination, model.egress/infer,
  dispatches0, response hash empty/bytes0.
- dispatch_outcome: allow, provider destination, model.egress/infer,
  dispatches1, validated fixed response hash/byte count.
- denied: deny, runtime:<actual attempt>, model.output/disclose,
  dispatches1, SAME validated response hash/byte count.

All three bind actual operator, service request ID, attempt, route/model/endpoint,
original request hash/byte count and expected synthetic output hash; timestamps
valid UTC/nondecreasing. No runtime_release_intent/delivery or operator event.
Do not truncate the existing positive ledger verifier or rewrite earlier records.

For independent response binding, the trusted coordinator should derive the
expected fixed synthetic wire bytes/digest/length from its own fixture text using
a reviewed deterministic oracle. Do NOT obtain raw denied response bytes from
the child or expose them in the worker control. Inert fixtures must compare that
oracle with current SyntheticModel.wire_reply bytes; no SDK/provider execution.
Freeze this exact oracle, three-record C# verifier and evidence shape during
source preparation, keeping prior audit predicates unchanged.

## Required Inert Controls

Positive reference with both policy rules must still deliver normally.
M06 must retain one dispatch, response validation and exact two original gateway
decisions; no prepared/confirmed runtime/operator releases. Cover egress absent,
both rules present, wrong actor/target/operation, malformed request, response
validation fault, generic gateway exception/denial reason/constraints/redactions,
wrong destination, audit failures at all three write/flush locations, extra/
missing/reordered/mutated records, wrong hashes/counts and forged worker/child
controls. A failure before dispatch or unobserved output decision cannot pass.
Expiry cannot substitute for the named denial; do not assert an unexpired service
lease at this later point or extend/reissue it to make the case pass.

Test write/EOF/deadline/cleanup faults, unexpected response/receipt/publication
frames, nonzero child/worker exits, malformed final reports and all previous
profiles. Preserve truthful attempted dispatch/uncertainty/effects if audit or
delivery of the DENIAL CONTROL fails. Sending that control is not a runtime
model-response delivery; report control and output counters separately.

## Recommendation And Gates

Recommend M06-only source preparation INCLUDING the narrow read-only output
gateway observation, fixed egress-only host/worker policy, case-specific control/
child admission, trusted response oracle and exact three-record audit verifier.
Freeze protocol/evidence schemas and impacts before a separate package decision.
No implementation is performed by this review.

Future packaging must enumerate actual replacements/additions and inspect all
members under the actual profile. Any omission of inactive Recreate1 root entries
requires separate explicit approval for the new successor only; do not preapprove
or delete frozen artifacts/canonical helpers. Then exact artifact hash/path,
separate one-run VM approval and fresh product consent.

M06 does NOT test operator-only output denial: PolicyRule matches capability/
target/operation/actor, not destination; removing model.output denies runtime
first. Destination-specific policy/changes remain separately deferred. M07 invalid
response, M08 final-text substitution, M09 bypass probes and M2 real-provider
traffic remain pending. No network permit, dependency/security/TTL/deadline change,
inference/credentials/spending, retry/recovery or qualification. Gate A remains
open and every production/containment/independent-cleanup flag stays false.

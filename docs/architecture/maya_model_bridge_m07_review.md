# M07 Invalid Response Review

Subsequent decision: user approved M07a-only source preparation and inert tests.
See maya_model_bridge_m07a_source_review.md and maya_model_bridge_m07a_tests.json.
M07b/c remain unimplemented; original review-only statements below are historical.

2026-11-02. Review/test-contract preparation only after bounded M06 success.
No product/test source change, compile, package, product/native/bundled-runtime
run, security/VM change or inference. Preserve M06/all frozen predecessors.
Companions: maya_model_bridge_m07_tests.json and M06 outcome.

## Findings And Required Distinctions

Original prepare_runtime checks service/request/liveness and egress authorization,
durably writes egress_intent, sets dispatch_attempted=true, calls the fixed
synthetic provider, then checks:
1. bytes and length1..4096;
2. protocol.decode: strict UTF-8/JSON object, duplicates/constants/depth/type;
3. exact comparison against the original expected response bytes.
Only AFTER all checks does it assign _response, enter dispatched phase and write
dispatch_outcome. Output authorization and runtime release occur later.

Each M07 response fault therefore has effects(1,0,0), gateway calls1, original
uncertain=true, no validated dispatch_outcome and no model.output decision.
Do NOT reuse M06's output gateway denial, validated-response hash or three-record
audit. A provider-destination denied event records service failure; its
model.egress/infer label does NOT mean that the egress gateway denied the request.

## Separate Proposed Variants

M07a, recommended first: a fixed one-byte ASCII opening brace response.
It is within size bounds but protocol.decode must reject malformed JSON.
Require exact named JSON validation failure, observed-byte count1/digest,
dispatch1, _response remains None and no output authorization.

M07b, later separately approved: a fixed valid JSON object totaling4097 ASCII
bytes (six-byte object/string prefix,4089 ASCII filler bytes,two-byte suffix).
Size rejection must occur BEFORE decode/allowlist comparison. No bound increase,
truncation, chunking-to-accept or sending a4097-byte response across the pipe.

M07c, later separately approved: same normal valid synthetic completion envelope
with exactly the final host-owned fixture text hex digit changed by a fixed rule.
Preserve shape/model/length; pass size/decode, then fail exact-byte allowlisting.
Do not authorize arbitrary child/provider-selected response content.
Keep expected ORIGINAL response bytes unchanged; never derive the allowlist from
the fault bytes. Positive control must continue to accept original fixture bytes.

Each requires its own fixed product entry/profile, artifact, attempt and approval.
Do not combine them into a run loop or a customer-selectable fault switch.

## Proposed Source Seam Requiring Approval

Current constructor directly creates SyntheticModel and derives expected bytes
from its wire_reply. No approved native fault provider exists.
Recommend a narrow construction-time provider factory method: ordinary default
still returns SyntheticModel; a dedicated M07a host service subclass selects only
a fixed malformed-response provider BEFORE service publication/issue.
The fault provider inherits normal text/wire_reply/dispatch counter behavior,
calls original dispatch exactly once to consume the real synthetic allowance,
then returns its fixed malformed bytes. It must NOT override the expected-response
generator. Preserve exact canonical normal wire bytes as the allowlist and verify
this independently against a trusted host oracle before any native package.

No runtime replacement of _provider, monkeypatch, patched wheel, caller-supplied
provider/class/body, global SDK patch, arbitrary URL or external networking.
No copy of prepare_runtime's validation/authorization guard into a parallel engine.
Construction factory and fixed fault classes are product source seams needing
explicit source-preparation approval, not instructions to modify the VM.

Current generic failure handling also lacks exact response-validation origin.
Recommend narrow read-only failure-stage/returned-byte length+digest observation
at the ORIGINAL rejection sites. For M07a record JSON rejection only when the
original protocol.decode raises ProtocolError after passing original bytes/size
checks. Reraise into existing _fail; preserve uncertainty/dispatch count and
poisoned-audit behavior. Record no raw bytes or exception text. Wrong-type/
oversize/hash failure/clock/audit/provider exception cannot impersonate M07a.
Bound diagnostic hashing/readback to the reviewed fixed response size; no new
unbounded inspection. M07b/c observation details remain separately gated.

## Proposed M07a Native Sequence And Evidence

1. Fresh product-owned consent/setup and unchanged fixed BOTH-rule policy.
   Same native Hermes/SDK request, source pins/origins/distributions/config,
   same actual operator/attempt/channel/grant, TTL/deadlines/byte limits.
2. Worker uses construction-time fixed M07a service/provider and ORIGINAL
   prepare_runtime. Require request validated, egress allow, gateway1,
   dispatch_attempted=true, dispatch count1, exactly one returned byte and
   named JSON rejection. No response assignment or successful dispatch outcome.
   Original ModelDenied.uncertain=true, closed service/non-failed required audit,
   no prepared/confirmed runtime/operator release and no gateway-denial flags.
3. Send a bounded case/command/attempt-bound worker response-rejection control
   with stage and observed digest/count only. No invalid raw bytes, canonical
   model output, lease or model_response. Coordinator independently compares
   exact fixed-byte digest/count and all service effects.
4. Child receives an exact M07a denial/rejection control on the existing private
   pipe, NOT invalid provider bytes. Ordinary pinned native construction/request,
   exact observation and normal SDK closure; native_conversation=false.
   Expected SDK error only with exact observation, never a generic error pass.
5. Require child/worker EOF and natural exit0, fresh beacon/bounded empty stderr/
   protected files. No runtime receipt/confirmation, final preparation/publication,
   service reopening, retry or recovery. Denial-control writes counted separately
   from runtime model-response writes, which must remain0.
6. Trusted coordinator rereads EXACT TWO-record ledger after natural closure.
   Bind actual operator/attempt/service request/route/request digest/output oracle.
   New protocol/evidence/key counts, response oracle and case-specific independent
   audit verifier must be frozen in a SOURCE REVIEW before any assembly.

## Exact Proposed Audit

Record1 egress_intent: allow, provider destination, model.egress/infer,
dispatches0, validated response hash empty/bytes0.
Record2 denied: deny, SAME provider destination/capability/operation,
dispatches1, validated response hash STILL empty/bytes0.
Both use original request hash/byte count and canonical expected output hash,
not faulty response digest in validated-response metadata. Failed-response
digest/count belongs in separate bounded diagnostic evidence, not a forged
validated dispatch_outcome or output-release event. Keep existing event schema/
reason codes and prior verifiers unchanged; add exact two-record admission.
UTC timestamps valid/nondecreasing. Reject extra/missing/reordered/mutated records.
No dispatch_outcome/runtime_release_intent/delivery/operator event.

## Required Inert Coverage

Positive default factory/normal response remains unchanged; compare fixed normal
wire/oracle byte-for-byte and prove fault class does not poison expected bytes.
Test intended JSON rejection after exactly one real synthetic dispatch; wrong
fault bytes/stage/digest/count, provider throw/no return, zero/second dispatch,
generic request/policy/liveness/audit failure and output-policy denial must fail
M07a admission. Cover malformed worker/child controls, wrong case/attempt/IDs,
response assignment or release, forged counters/evidence, nonzero exit/EOF/
timeout and control write faults, without claiming inert admission tests are
native process/containment proof.

Mutate every audit/metadata field; missing/extra/reordered/unclosed ledger; both
write/flush locations and preserved prior effects/uncertainty on failures.
A partial control send is uncertain control delivery, not a successful negative
case or a model-response release. Maintain all earlier compile profiles/reader/
security/admission regressions. Native clocks must not be faked.

## Recommendation And Gates

Recommend M07a-only SOURCE PREPARATION next, INCLUDING the narrow construction-
time fixed provider factory and read-only original JSON-rejection observation,
trusted one-byte digest oracle, exact two-record audit and bounded denial controls.
M07b/c remain proposals, not approved implementation or execution.
Review actual source/protocol/payload impacts before separate assembly/any exact
inactive-root omissions approval, then matching-artifact one-run approval and
fresh product consent. No root omission is authorized here.

Do not modify existing M06/frozen packages, dependency/native pins, configuration,
grants/security/permissions/WFP/capabilities/jobs, TTL/deadlines/bounds. No inference,
customer content/credentials/spend, retry/fallback/recovery, M08/M09/M2 or
qualification. M07 is synthetic response-validation evidence, not real-provider
robustness or hostile-child bypass proof. Gate A/all false flags remain open.

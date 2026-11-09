# M07b Oversized Response Review

2026-11-02. Review/test-contract preparation only after bounded M07a success.
No product/test source change, compile, package, product/native/bundled-runtime
run, security/VM change, dependency acquisition or inference.
Preserve Malformed1/M06/all predecessors. See M07a outcome and
maya_model_bridge_m07b_tests.json.

## Boundary And Current Source

Original prepare_runtime checks returned bytes/length1..4096 BEFORE protocol.decode,
exact allowlist comparison, _response assignment, dispatch_outcome or output
authorization. M07b must exercise THAT original size rejection, not JSON failure,
request/frame limits, truncation or a downstream closed-channel error.

The existing response_failure_* observation is set only in the JSON decoder's
ProtocolError handler, AFTER the size guard. A4097-byte return currently raises
original ModelDenied(True) without named size evidence. Existing M07a evidence
requires exact service/provider types, stage=response_json and one-byte digest;
its schema/validator cannot pass M07b by relabeling it.

## Fixed Proposed Fault

Use one ASCII JSON object: six-byte object/string prefix for key x, exactly4089
lowercase ASCII filler bytes, then two-byte closing-string/object suffix.
Total4097 bytes. No caller-selected fields/body, file input or network endpoint.
This is valid JSON syntax/object, NOT an authorized normal completion envelope.
Independent inert parsing/length/digest checks will freeze its exact bytes.
Do not claim that any4096-byte JSON object is necessarily an allowed response.

Dedicated M07b provider uses the existing construction-time factory seam. Inherit
original SyntheticModel.text/wire_reply, call original dispatch exactly once, then
return the fixed4097-byte object. Default factory, canonical expected normal
response and original guard stay unchanged. No live _provider reassignment,
monkeypatch, wheel change, shared fault selector or modifications to M07a provider.
A separate fixed worker/root/profile selects ONLY this case before issue.

## Narrow Diagnostic Extension Requiring Source Approval

Inside the EXISTING size-failure branch, add read-only stage=response_size,
observed length/digest ONLY when the returned value is bytes of EXACT length4097.
Then raise the original ModelDenied(True) unchanged. Do not alter the original
bytes/length acceptance predicate or inspect/hash arbitrary larger returns.
This is an explicit bounded4097-byte diagnostic allowance, not a4097-byte
response acceptance allowance or a new pipe/frame/body limit.

No JSON decode should run for the oversized fault. Keep M07a's existing parser
observation unchanged, keep _response None and phase admitted/provider destination.
Specific evidence must require fixed fault digest/count, exact construction-time
provider/service, original attempted dispatch1, gateway1/egress allow, original
uncertain=true, nonfailed required audit, closed service, no gateway-denial flags
and all prepared/confirmed releases0. Generic size failures/types/counts,
JSON faults, provider throw, liveness or audit errors cannot pass M07b.

The canonical normal response remains independently derived/checked from host
fixture text. No oversized bytes may appear in worker/child controls, public
reports or validated-response metadata. Report only bounded hashes/counts/stage.

## Proposed Native Schedule And Contract

Fresh attempt, original BOTH-rule policy and original native request/grant;
same identity/channel/TTL/deadlines/bounds. No deliberate wait, second dispatch,
new agent/client/grant, SDK retry/fallback or second conversation.
Original size guard rejects the fixed return BEFORE response parsing.
Worker sends an exact case/attempt/original-dispatch-command-bound size-rejection
control with bounded evidence, then exits normally. Case-specific child rejection
control is NOT model output; ordinary native constructor/one request/SDK closure,
native_conversation=false and exact observation required. No raw response,
runtime receipt/confirmation or final preparation/publication.

Coordinator independently compares fixed4097-byte fault digest/count and canonical
normal-response oracle; requires no validated response/dispatch_outcome and records
dispatch1/uncertainty BEFORE control write. Keep model-response writes0 separate
from a denial-control write. Require child/worker EOF and natural exit0, fresh
beacon, bounded empty stderr, protected files and independent audit admission.
Freeze exact schemas/key counts/control names during source preparation, BEFORE
separate assembly. Do not reuse an M07a case label or weaken its validator.

Expected effects(1,0,0), gateway calls1, no output authorization, uncertain=true.
Audit is the SAME exact TWO-record semantics as M07a:
egress_intent allow/provider/model.egress/infer/dispatches0;
denied deny/provider/model.egress/infer/dispatches1.
Validated response hash stays empty/bytes0 in both; bind original request/output
hashes and actual actor/attempt/service request/route/model/endpoint/timestamps.
No dispatch_outcome or output-release/operator event. This is response validation,
NOT gateway egress denial. Reusing the unchanged pure two-record ledger verifier
is acceptable if independent case-specific evidence remains strict; no validator
change or fabricated audit record. Observation of4097 bytes belongs only in the
separate fault diagnostic, not validated-response metadata.

## Required Inert Controls

- Default normal fixture still passes response admission; exact expected bytes
  unchanged and inherited wire_reply pinned by source tests.
- Fixed fault is bytes/valid JSON object/exact4097/digest as specified.
- Spy/delegating decode fixture proves no call for the oversized return; do not
  substitute the original size guard. Native parser/SDK not executed.
-4095/4096-byte valid JSON neighbors pass SIZE admission then fail exact response
  allowlisting, not response_size. They are not positive full-response controls.
-4098, zero bytes, nonbytes and malformed4097-byte substitutes cannot satisfy
  exact M07b evidence; no hashing unbounded data or truncation-to-pass.
- One real synthetic allowance consumed; second dispatch denied. Provider exception,
  no return, request/policy/liveness failure, wrong stage/length/digest/type,
  changed expected bytes/response assignment/releases and forged controls fail.
- Mutate every ledger/evidence field; missing/extra/reordered/unterminated records,
  both audit write/flush points, EOF/timeout/nonzero exits/control send failures
  must block acceptance and preserve actual prior effects/uncertainty.
- Preserve earlier profiles, M07a/M06 evidence predicates, reader/deadline/cleanup
  behavior and disabled retry/recovery. Inert schema/source-order tests are NOT
  native process/containment proof.

## Recommendation And Gates

Recommend M07b-only SOURCE PREPARATION next, INCLUDING the exact4097-byte fixed
construction-time provider, narrowly bounded original size-rejection observation,
strict independent case evidence and controls, and unchanged two-record semantics.
No implementation follows this review. M07c remains unimplemented/unapproved.

After source review, separately approve actual payload assembly/any exact inactive
Malformed1 root omissions FROM NEW successor only. No omission approved here.
Keep canonical malformed/output-denial helpers and all frozen artifacts; inspect
every actual-profile member instead of widening admission. Later matching artifact
one-run VM approval/fresh consent remain mandatory.

No change to4096 response limit,8192 frame/131072 channel bounds, TTL2000ms,
ready/RPC/partial5000/2000/1000ms, child22/30s, configuration/dependencies/native
pins/security/WFP/capabilities/jobs/grants/permissions. No inference, customer data/
credentials/spending, retry/fallback/recovery, M07c/M08/M09/M2 or qualification.
Gate A remains open and all production/containment/independent-cleanup flags false.

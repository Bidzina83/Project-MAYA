# M03d Exact-Body Source Review

Subsequent decision: the user approved separate M03d offline assembly INCLUDING
the two named successor-only omissions. See maya_model_bridge_m03d_package.md.
Source-milestone statements below remain historical; exact-artifact one-run VM
approval and fresh consent are still required before native execution.

2026-10-31: the user requested proceeding after M03c's bounded result and scoped
manual cleanup. Source/inert preparation only. Candidate 0.2.1-offline-body.1,
scope offline-hermes-body-validation-v1. No product payload, launcher package or
ZIP assembled; no native Hermes/SDK, security/VM setup, inference or networking.
Frozen Attempt 1 and predecessors remain intact. M03c evidence/provenance is in
maya_offline_model_attempt_1_outcome.md; its allowance is consumed, flags unchanged.

## Fixed Mutation And Host Binding

HERMES_MODEL_BODY requires HERMES_MODEL_VALIDATION and excludes MODEL_ROUTE and
MODEL_ATTEMPT; existing guards also exclude MODEL_DENY/STATE/MEMORY and require
MODEL/BRIDGE/CONSTRUCTION/IMPORT. Fixed model_body_child_entry.py and
model_body_worker_entry.py select M03d; future model-contract.json must bind
cases=[M03d]. No selector from child, CLI, environment or editable policy.
Existing gateway and both positive M01 rules remain; M02 policy is rejected.

Real Hermes/SDK emits the original valid request with unchanged adapter/factory
checks. Coordinator compares body bytes with the protected host oracle and the
entire original envelope against the actual issued grant. v/type/attempt/route/
lease/seq/method/path/body and grant TTL/request digest must match host state.
Actual token/SID, attempt/directory, outer command, private channel, grant, model,
route, sequence/method/path and host expected request file never change.

Only a COPY of body.messages[1].content is altered: the final hex digit of the
fixed MAYA_OFFLINE_MODEL_REQUEST:<64 lowercase hex> canary becomes 1 if originally
0, otherwise 0. The other 63 digits and every other field remain identical.
Require canonical pinned field order messages/model/max_tokens/stream, two
system/user messages, max_tokens=32 and stream=false. Model stays
maya-offline-wire-v1. Mutation preserves request shape, JSON validity and byte
length, changing exactly one ASCII byte. Both body hashes are retained separately;
the original grant digest is NOT rebound to the mutant.

Python strictly decodes, changes only the named structured field and serializes
with the pinned compact UTF-8 convention; checks original canonical bytes and
validates the mutant again. C# strictly parses structure/model/roles/canary,
locates the pinned final user-message/top-level serializer suffix, changes only
that digit and reparses, restoring the field to compare complete structure. It
preserves all other original bytes, including Unicode/escapes. This is anchored
to the final user field, not global text replacement. Cross-language fixtures
include the SAME canary in Unicode system content and leave it untouched.

This is a trusted-coordinator WORKER diagnostic, not hostile-child adapter bypass,
actual Windows identity spoofing, socket bypass or full containment proof.

## Named Rejection And Exact Evidence

OfflineModelBridge adds request_shape_validated only after checked_request passes
all syntax/message/stream/token/model checks. The existing constant-time exact
body comparison still rejects any difference; it now raises RequestBodyDenied and
records request_body. Its accepted set is unchanged. M03a model/M03b route/M03c
attempt stage predicates retain their existing behavior. No gateway call occurs
before full body admission; request_validated remains false on mismatch.

WrongBodyBridge accepts only the exact fixed mutant derived independently from
its original oracle. It requires actual envelope/identity validation, valid
request shape, request_body stage, no completed request admission, zero gateway
calls, no gateway-policy denial, zero attempted/actual dispatch and zero prepared/
confirmed runtime/operator releases. Admission must still be live/unrevoked,
the coordinator command ID bound once and required audit healthy. Missing/extra/
second mutations, bad route/attempt/lease/channel, invalid model/shape, unmodified
body, generic exception, expiry/revocation or unknown stage cannot be a pass.
Audit short/write/flush/fsync failure poisons the ledger; never reopen or continue.

The worker durably writes exactly one event, closes and returns
model_body_rejected with exactly v=1, ACTUAL attempt, actual coordinator request_id
and exact evidence map. No second operation, model response or fallback follows.

## Audit Schema

One existing newline-terminated AuditRecord, integer schema_version=1, valid UTC
timestamp, event_type=model_bridge.body_rejected, decision=deny,
reason_code=model_bridge.wrong_body, actual windows:<operator SID>,
capability=model.egress, target=model:maya-offline-fixture, operation=infer,
data_classification=internal-synthetic, idempotency_key=null. Exact metadata:

- attempt/request_id/coordinator_request_id: actual host/service/dispatch IDs.
- route=maya.offline.model.v1, endpoint=https://maya-offline-model.invalid/v1/chat/completions,
  model=maya-offline-wire-v1, destination=provider.
- request_sha256/request_bytes: ORIGINAL oracle; mutated_sha256/mutated_bytes:
  exact independently reconstructed changed body, same length, different digest.
- response_sha256="", response_bytes="0", output_sha256 binds synthetic fixture.
- dispatches="0", real_inference="false", validation_schema=maya.model.body_validation.v1.
- case=M03d, stage=request_body, observed_model=maya-offline-wire-v1.
- mutation_field=messages[1].content.canary.last_hex,
  mutation_rule=last_digit_0_to_1_otherwise_to_0.
- gateway_calls="0", dispatch_attempted="false", runtime_prepared/runtime_released/
  operator_prepared/operator_released all "0".

Lowercase SHA256; decimal counters/sizes are exact strings. No raw request,
canary, lease, output or exception text. Missing/extra/rebound fields, boolean
schema, duplicate/truncated audit or invalid/non-UTC timestamp are rejected.
Python verify_body_audit and C# ModelValidationAdmission.Audit with explicit trusted
body=true independently admit the predicate. Case-selector combinations throw;
all older audit defaults stay intact. C# expected metadata is derived before
forwarding; protected audit is independently reread after normal closure.

## Child Control And Completion

Send only v=1,type=model_denied, actual attempt, seq=1,case=M03d,
reason=request_body_rejected. WrongBodyChannelClient recognizes only that fixed
case/reason and raises instead of returning model content; earlier controls
cannot satisfy it. The real lifecycle remains normal: only expected SDK connection
error after that exact denial, or Hermes' own error result, is handled as a
negative. Explicitly untrusted child report schema
maya.offline.model.body_validation.child.v1 requires completed/constructor/SDK
closure/origins/distributions/config/denial true, native_conversation and
real_inference false, request count 1, clients 2-8, empty reason_type.

Require EOF both ways, natural child/worker exit 0, bounded empty stderr,
protected-file recheck, exact audit, fresh beacon and worker stop. Only then set
model_body_evidence_matches and existing validation/model evidence flags. Product
cleanup must also succeed for offline_model_body_rejected_pending_independent_cleanup.
Shared startup_status remains offline_model_validation_child_completed. No model
response write or operator publication callback. Unknown failure, setup/token
error, missing audit, timeout or uncertain effect stays blocked, never a pass.

## Scope And Packaging Gates

New model_body_validation.py and ModelBodyAdmission.cs implement derivation/
service/audit and independent host mutation respectively. Shared model_service
adds shape observation/named mismatch; model_worker adds one exclusive trusted
mode/reply; model_bridge and native child add the fixed negative adapter/report.
The fixed worker reuses import-safe failure-only startup reporting. Coordinator,
profile selectors/allowlists, consent/version/case/status are extended without
new policy authority, transport or exception-based success fallback.

Future package approval must EXPLICITLY include omitting the two inactive M03c
root bootstraps model_attempt_child_entry.py and model_attempt_worker_entry.py
from the NEW M03d payload only. ReadIndex checks every member and M03d intentionally
excludes MODEL_ATTEMPT; source fixtures verify their rejection. Keep all canonical
modules and M03a shared worker support, plus every unrelated dependency/config
member. Prior frozen artifacts and workstation/guest files are never deleted.
Do not broaden admission or enable inactive modes. Enumerate exact old/new member
and launcher hashes, verify full actual-profile ReadIndex before assembly, then
freeze payload/index/resources/source and report exact executable/archive hashes.
Those preparation actions need separate approval; none was performed here.

Same Python 3.13.14, pinned Hermes/64 distributions/native guards/private config;
no acquisition. Same AppContainer, zero capabilities, six WFP denies, reduced
tokens, one-process jobs, child-process block, pipes, four host files/ACLs/labels.
Trusted worker remains OUTSIDE child containment; shared All Application Packages
access and profile removal remain gaps. No listener, service, account, registry/
loopback grant, credentials, customer data, inference or charge. Ready/RPC/partial
frame 5000/2000/1000 ms, child 22/30 seconds; frame 8192, cumulative channel/audit
131072, request/response/stderr 4096, report 65536, output 1024, diagnostic parser
256. No timeout extension, fallback, retry/recovery or VM test automation.

## Inert Verification

304 Python tests/629 subtests pass: 23 new body tests and two mocked startup-main
body checks plus the prior suite. Normal host temporary-folder access; existing
unknown-cache_dir warning remains. C# M03d: 136 assertions, six paired profiles
127 each. Earlier M03c 195/paired 186, M03b 177/168, M03a 108/101, M02 117/113,
startup reporting 874, earlier components 711, document bridge 154, model audit
178 pass. Counts overlap and are not native-run counts. Only fixture mains run.

Coverage: native-oracle and all-hex Unicode/duplicate-text cross-language bytes;
fresh positive dispatch; fixed negative/no gateway; malformed original/canary;
unmutated/second mutation; wrong envelope; missing/rebound IDs/metadata; forged
denial; expiry/revocation; audit faults; generic exception; wrong shape/stage or
nonzero effects; fixed entry guards and inactive bootstraps. Existing channel
fixtures cover EOF/partial framing, not native timing/pipe delivery. An initial
managed fixture assumed Object[] rather than the serializer's ArrayList; only
the fixture iterator was corrected before passing. No product fix resulted.

Next: review this source/impact and separately approve assembly INCLUDING the two
explicit successor-only omissions; later require matching-artifact one-run VM
approval/fresh consent. No M03d native behavior, later case, inference, containment,
Gate A or production is approved/qualified. Original false flags remain unchanged.

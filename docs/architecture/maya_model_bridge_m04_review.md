# M04 Lease-Liveness Contract Review

Subsequent decision: the user approved M04a-only source preparation. Its exact
candidate/impact/inert results are in maya_model_bridge_m04a_source_review.md and
maya_model_bridge_m04a_tests.json. Review-milestone statements below are historical;
M04b/c, assembly and native execution remain separately gated.

2026-10-31: document/source review after reported M03d result and scoped cleanup.
No product-code/test-fixture edits, package, native run, security setup or inference.
The existing denial roadmap remains intact. This successor resolves its M04
ambiguities for review; source preparation still needs separate approval.
Companion: maya_model_bridge_m04_tests.json. M03d: maya_offline_model_body_1_outcome.md.

## Findings And Decision

1. M04 is THREE cases, not one zero-effect test. Original v1_tests.json describes
   a combined expired/replayed/revoked entry with zero effects. The later denial
   proposal correctly requires a positive dispatch/runtime-delivery prefix for
   replay. Preserve those effects: M04a expiry (0,0,0), M04b revoke (0,0,0),
   M04c consumed-grant replay (1,1,0). Separate attempts/artifacts/ledgers; no suite.
2. The existing guard does not distinguish the reason. model_service.py:148 _live
   collapses closed/audit/revoked/wrong phase/expired into ModelDenied. Its call at
   :219 precedes envelope/body validation. A generic denied event or timeout
   cannot prove expiry, revocation or consumption; M03 validators reject those
   states deliberately. New case-bound observations/audit admission are required,
   not relabelling a frozen M03d executable or weakening its predicates.
3. Intentional expiry inside an RPC would conflict with its deadline.
   ModelBridgeRuntime.cs:101 limits worker RPC to 2000 ms; model_service.py:157
   gives the grant 2000 ms. Waiting beyond expiry inside that RPC risks a transport
   timeout rather than tested rejection. Proposed M04a delay belongs AFTER grant
   reply but BEFORE model_begin, outside any in-flight worker RPC, within unchanged
   22/30-second child budgets. No deadline/TTL extension or native fake clock.
4. Revocation/replay are not exposed native schedules. model_worker.py:100-146
   accepts issue, one dispatch, delivery/final/shutdown; no revoke or replay
   command exists. Its request-ID seen set (:82-88) must remain enabled.
   model_bridge.py:59-65 consumes a child's grant and request budget on first
   exchange; a second child call normally fails locally. A future M04c must use a
   separately reviewed trusted-coordinator replay, with a NEW command ID, rather
   than disabling child guards or mistaking duplicate-command rejection for
   consumed-service-grant evidence. M05 adapter-budget coverage remains separate.

Recommendation: approve ONLY M04a real-time expiry source preparation next.
M04b/M04c need later dedicated protocol/exit/audit reviews. No new policy engine,
network fault, increased timeouts, runtime wheel patch or retry is needed for M04a.
The findings concern test observability/scheduling, not proof of a new escape or
a claim that expiry currently authorizes a forbidden operation.

## Proposed M04a Schedule

1. Normal product setup/readiness and genuine pinned Hermes/SDK construction.
   Existing gateway has both positive M01 rules. Worker issues one ordinary
   2000-ms grant on actual host binding; coordinator verifies reply identity,
   request hash, TTL/route/sequence and saves a monotonic receipt timestamp.
2. Child is waiting for model_begin, NOT in a model exchange. Coordinator waits
   at least 2100 REAL monotonic ms after receiving the grant reply. Do not wait
   while a worker RPC/partial frame is active. No native injected clock, expiry
   field edit, token replacement, grant reissue, retry or unbounded sleep.
   All waits consume existing child budgets; insufficient budget/overrun blocks
   the attempt, never extends a deadline or counts as expiry acceptance.
3. Send the original grant in normal model_begin. Real Hermes/SDK emits its
   original valid request. Coordinator verifies full native envelope/body against
   the saved host grant/oracle; no M03-style mutation. Child keeps all guards.
4. Dispatch the unchanged request in a fresh ordinary bounded 2000-ms worker RPC.
   Worker independently preflights exact request/envelope/channel/body/lease
   binding without admitting an operation or calling gateway. Its actual liveness
   guard must reject specifically because this unused, unrevoked, issued grant
   expired. An expired malformed request is not sufficient proof.
5. Record the exact rejection once through healthy RequiredAudit, close service
   and return case-bound evidence/control. Require child denial observation,
   native SDK closure/config/origins/distributions, EOF, natural child/worker exit 0,
   protected-host audit readback, fresh beacon and normal product cleanup.
   No synthetic dispatch/model response/operator publication. Output stays blank.

PrivateChannel is blocking and relies on coordinator native deadlines; httpx's
timeout value is not a separate interrupt of its blocking custom pipe receive.
This design therefore does not rely on bypassing a child transport deadline.
Child remains within its existing cooperative/host budget; timeout is failure.

## Required Expiry Classification

Source preparation must preserve the liveness guard's accepted set and failure
ordering. Record a coherent guarded rejection snapshot, not an exception-string
guess or a caller assertion. Admission identity/envelope/body preflight is a
read-only diagnostic, distinct from request_validated/completed admission.
No fake gateway, replayed cached report, mutable raw clock field or new authority.

Mandatory at the actual rejection: phase_before=issued; closed_before=false;
revoked_before=false; required-audit healthy; one actual issued grant/lease;
exact preflight matched; worker monotonic now >= its actual expiry; no completed
request admission/gateway call/attempted dispatch/effects. No state resetting.
If any other reason applies, return generic blocked failure, not expected expiry.
M03's requirement that rejection audit occur BEFORE expiry must NOT be reused or
weakened globally: expiry needs its own predicate permitting diagnostic audit
after expiry, never authorizing a protected operation after expiry.

Worker reports bounded elapsed age, not absolute clock values. Proposed
worker_elapsed_ms is a decimal-string integer in [2000,30000]; native acceptance
requires the actual expiry guard AND that age bound. Coordinator independently
records its measured wait >=2100 ms. Never subtract timestamps from different
process clocks. Dynamic worker elapsed value must match between reply and protected
ledger, be range-checked by independent C# admission, and not become a wildcard
for other metadata. Boundary fixtures must test exact expiry, just-before expiry,
expiry/revoke/closed/audit precedence and no false zero counters.

## Proposed Exact M04a Protocol And Audit

Future fixed profile HERMES_MODEL_EXPIRY; mutual exclusion with M02/M03 fault
modes; exact parent defines/entry names and candidate version to be frozen during
source preparation. No child/environment/CLI-selected faults. Existing positive
gateway policy, private inherited pipes, real operator SID and original oracle.

Proposed worker reply: v=1,type=model_lease_expired, ACTUAL attempt,
actual coordinator request_id,evidence. Child control: v=1,type=model_denied,
actual attempt,seq=1,case=M04a,reason=lease_expired. Only exact denial control is
recognized; never a model-response substitute. Explicitly untrusted child report
schema maya.offline.model.expiry.child.v1, same negative constructor/closure/
config/origin/distribution/denial flags, one request, 2-8 clients,
native_conversation/real_inference=false, empty reason_type. No raw exceptions.

Exactly one existing newline-terminated AuditRecord envelope, integer schema_version
1, valid UTC timestamp, event_type=model_bridge.lease_expired, decision=deny,
reason_code=model_bridge.lease_expired, actual windows:<operator SID>,
capability=model.egress,target=model:maya-offline-fixture,operation=infer,
data_classification=internal-synthetic,idempotency_key=null. Proposed metadata:

- validation_schema=maya.model.lease_expiry.v1,case=M04a,stage=lease_expired.
- Actual attempt,service request_id,coordinator_request_id; fixed original
  route/endpoint/model,destination=provider.
- Original request_sha256/request_bytes and observed_request_sha256/observed_request_bytes
  equal; lease_sha256 binds issued lease, never raw token.
- grant_ttl_ms="2000", worker_elapsed_ms as bounded above,
  phase_before="issued",closed_before="false",revoked_before="false",
  expiry_observed="true",request_preflight_verified="true",
  request_validated="false",gateway_calls="0",dispatch_attempted="false".
- response_sha256="",response_bytes="0", output_sha256 of fixed synthetic fixture,
  dispatches/runtime_prepared/runtime_released/operator_prepared/operator_released
  all "0", real_inference="false".

All metadata strings, hashes lowercase SHA256, sizes/counters decimal; no missing,
extra, duplicate/rebound fields or malformed timestamp. Source review must freeze
the exact map and independently matching Python/C# validators before assembly.
Any schema change comes back for review, not silently accepted as this design.
Audit write/short/flush/fsync failure is terminal; never reopen or fabricate success.

Proposed final status offline_model_lease_expired_pending_independent_cleanup.
Require all prior positive native baseline/expiry/control/audit/natural-exit/cleanup
predicates. Qualification flags stay false. Generic timeout, EOF, crash, missing
audit, wrong grant/body, existing revoked/closed state or unavailable timer
evidence cannot be counted as a passed expiry test.

## Deferred M04b And M04c

M04b: trusted fixed revoke command after issue, actual unique command ID/ack; same
live unexpired grant at attempted request, revoked=true and no other rejection
reason. If TTL also expired, block/confounded, not isolated revocation proof.
No new revoke command or event schema is approved here. Normal zero effects.

M04c: first verify one synthetic dispatch and one runtime delivery, including
receipt plus worker confirmation. Hold operator publication. Trusted coordinator
replays exact saved original request/lease under NEW dispatch command ID while
the grant is still unexpired/unrevoked and worker phase is runtime_delivered.
That isolates consumption rather than time or duplicate-command failure. If expired,
blocked/confounded. No service reopen/reissue/reset and no child adapter bypass.
The child already completed one positive SDK exchange: a fabricated second child
denial or negative child report would be WRONG. Review its genuine positive final
report/closure without publication as a distinct native schedule.

Audit must retain the four-event positive prefix (egress_intent,dispatch_outcome,
runtime_release_intent,runtime_delivery) plus a separately reviewed consumed-grant
rejection, not one zero-effect record. Preserve two prior gateway calls, one dispatch,
one runtime preparation/delivery and zero operator publications. No second effect.
Exact commands, counter/audit schema and lifecycle need later dedicated review.
The broad old v1 zero-effect M04 wording is not authority to erase prior effects.

## Impacts, Faults And Approval Gates

Proposed M04a source changes: explicit service expiry observation/predicate,
exclusive worker profile/reply, fixed negative child adapter/report/entries,
bounded coordinator pre-begin wait and exact evidence/audit/status/consent.
No changes made by this review. Future assembly must review actual-profile
ReadIndex and inactive root omissions against frozen Body 1 before approval;
do not broaden allowlists merely to inherit bootstraps. No package edits now.

Required inert controls: fresh valid positive; fake clock only in fixtures for
before/at/after expiry; native path cannot inject clock; wrong grant/channel/body/
attempt/route; revoked/closed/wrong phase/audit failure not expiry; same-length
forged hashes/IDs; bad dynamic elapsed/wait claims; exact child controls;
missing/extra/duplicate/truncated audit; write/flush/sync/partial I/O; unexpected
exit/EOF; mis-scheduled wait inside RPC; budget exhaustion; no false effects.
Native expiry later uses ONLY real monotonic clocks and no timeout extension.

All frozen packages, Python/Hermes/64 pins/config, AppContainer/zero capabilities,
six WFP denies/reduced tokens/jobs/child-process block/pipes/host ACLs and limits
unchanged. Ready/RPC/partial frame 5000/2000/1000 ms; child 22/30 seconds; frame
8192, direction/audit 131072, request/response/stderr 4096, report 65536, output
1024, diagnostic parser 256. Trusted worker remains outside child containment;
shared All Application Packages exposure/profile removal remain limitations.
No new grant, dependency, registry/loopback exception, service/account/listener,
credential, customer data, model inference, spending or extra VM test automation.

Next decision: M04a-only SOURCE preparation, including the fixed pre-begin
real-time expiry schedule and versioned evidence above. Then review source/impact,
separate assembly approval, exact-artifact one-run VM approval/fresh consent,
result/scoped cleanup. M04b/c/M05-M09/M2/Gate A remain pending; all qualification
flags false. This document authorizes none of those implementation/run stages.

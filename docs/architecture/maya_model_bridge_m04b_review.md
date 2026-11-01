# M04b Revocation Source And Test-Contract Review

Subsequent decision: the user approved M04b-only source preparation. Candidate,
inert results and remaining assembly gates are in maya_model_bridge_m04b_source_review.md.
Review-stage statements below are historical, not a package/native-run allowance.

2026-10-31, document/source inspection only after M04a's reported bounded pass
and scoped cleanup. See maya_offline_model_expiry_1_outcome.md. No product/test
source edits, compilation, package, product/Hermes/SDK execution or security changes.
This proposal is not an implemented revoke path or a new execution allowance.
Companion: maya_model_bridge_m04b_tests.json. Historical M04a contracts stay frozen.

## Findings

1. OfflineModelBridge.revoke() currently sets _revoked under its existing RLock.
   _live() rejects revoked state, but combines closed/audit/phase/expiry failures
   into ModelDenied. Generic rejection cannot prove isolated revocation.
2. serve_model currently moves directly from model_issue to model_dispatch.
   No native revoke command, acknowledgement or revocation audit exists.
   A caller's flag or child testimony cannot substitute for invoking the real method.
3. ModelValidationAdmission.Audit admits ONE record. M04b must not reuse that
   count or M04a's expiry metadata. Require TWO ordered records: durable revoke
   acknowledgement evidence, then original-guard rejection of the same request.
4. M04a deliberately waited past TTL. M04b must NOT wait. Revoke and reject while
   the original two-second grant is still unexpired. If either observation/audit
   confirmation crosses expiry, stop as blocked/confounded, not passed revocation.
   The extra RPC/fsync has a real timing cost; no claim it fits natively yet.

These are missing schedule/observability components, not evidence that the
existing guard allows a revoked operation. Recommend M04b-only SOURCE preparation
next, with the exact two-event contract below, before separate assembly approval.

## Fixed Native Schedule Proposed

Future version 0.2.1-offline-revocation.1, scope
offline-hermes-lease-revocation-v1. HERMES_MODEL_REVOKE requires VALIDATION/MODEL/
BRIDGE/CONSTRUCTION/IMPORT and excludes EXPIRY/BODY/ROUTE/ATTEMPT/DENY/STATE/MEMORY.
Fixed model_revoke_child_entry.py / model_revoke_worker_entry.py only; no mode
selected by child input/environment/CLI/config. M04c replay remains deferred.

1. Product-owned consent/setup and genuine pinned child constructor/readiness,
   same positive M01 gateway rules. Issue one ordinary 2000-ms grant and validate
   its exact fields/attempt/route/sequence/TTL/original request hash/lease.
2. BEFORE model_begin, coordinator sends one fresh-ID model_revoke with the
   actual lease over its existing private worker pipe. No intentional delay and
   no in-flight child model request. Revoke is not a child protocol operation.
3. Worker validates exact command/attempt/lease/unique ID, one issued/open/unrevoked
   grant, healthy audit, no effects, unchanged captured expiry and finite actual
   monotonic time before expiry. Under the existing lock call the ORIGINAL
   OfflineModelBridge.revoke(), not a direct assignment or replacement service.
   Require phase still issued, open, same lease/expiry, _revoked=true, zero effects.
   Write/flush/fsync the exact grant_revoked event. Recheck real time/context after
   audit completion before replying; failure is terminal, never acknowledged as success.
4. Coordinator validates exact revoke acknowledgement, binds its command ID,
   lease hash, service ID, original request hash, TTL, zero counters and bounded
   worker age. Only then send ordinary model_begin with ORIGINAL grant/canary.
   No reissue, renewal, reset, substitute token or change to grant/body/envelope.
5. Real Hermes/SDK emits one original request with all existing child guards.
   Coordinator checks exact body AND full envelope. Send normal model_dispatch
   with a NEW command ID, different from issue and revoke. Worker preflights
   request/envelope/channel read-only; this is not completed request admission.
6. At original _live("issued") rejection, require exact ModelDenied with
   uncertain=false, phase issued/open, healthy audit, unchanged issued lease/
   expiry, acknowledged revocation=true and real time still strictly before expiry.
   Check finite, nonbackward real times before and after calling the original
   guard so a simultaneous expiry cannot masquerade as revocation. Preflight and
   every zero-effect predicate must match. If base guard returns, block BEFORE
   any gateway/dispatch. Never authorize through the diagnostic wrapper.
7. Persist one exact lease_revoked rejection event, checking context/time before
   and after required audit commit. Then close normally; only case-bound evidence
   may produce the exact negative child control. SDK denial handling/closure and
   config/origins/distributions, natural child/worker exit0, EOF, bounded empty
   stderr, protected-host readback, both audit records and fresh beacon required.
   Product cleanup followed by scoped operator checks remains separate.

The 2000-ms lease is NOT the 2000-ms per-RPC deadline: each normal RPC keeps its
deadline, and elapsed time across both RPCs still counts against the one lease.
Ready5000/RPC2000/partial1000ms, child22/30s and all byte ceilings stay unchanged.
Host receipt time is later than worker issue; host elapsed alone cannot prove
unexpired worker time. Use original guard/state plus worker-local observations,
not subtraction of cross-process absolute timestamps. No native clock injection.
Slow disk/scheduling crossing expiry is blocked; no automatic retry or TTL increase.

## Exact Proposed Protocol

All frames retain v=1, actual attempt and fresh 32-lowercase-hex coordinator
request_id. Existing seen-command-ID rejection remains active in every profile.

- Revoke command EXACT keys: v,type=model_revoke,attempt,request_id,lease.
  lease is the actual 64-lowercase-hex issued secret on the private pipe only.
- Ack EXACT keys: v,type=model_revoke_ack,attempt,request_id,evidence.
  evidence is the complete first-record metadata map below. No generic boolean
  or empty acknowledgement. Validate before model_begin; save it immutably.
- Dispatch stays the existing v,type=model_dispatch,attempt,request_id,request;
  original request, new outer ID. M04b accepts only issue/revoke/dispatch in order;
  duplicate revoke/dispatch, missing ack or other commands terminate the attempt.
  Prior profiles still reject model_revoke and retain their existing schedules.
- Rejection reply EXACT keys: v,type=model_lease_revoked,attempt,request_id,evidence.
  evidence is the complete second-record map. It binds the previously accepted
  revoke ID/age/lease and actual current dispatch ID. No model response.
- Child control EXACT: v=1,type=model_denied,attempt,seq=1,case=M04b,
  reason=lease_revoked. A dedicated adapter accepts only that case/reason;
  no child revoke command, second SDK call, budget reset or guard bypass.
- Untrusted child report schema maya.offline.model.revocation.child.v1.
  completed/native_constructor/denial_observed/sdk_closed/origins_verified/
  distributions_verified/config_unchanged=true; native_conversation/
  real_inference=false; model_requests=1; client_objects integer2..8; reason_type="".
  Retain genuine constructor/client shutdown behavior; generic crash does not pass.

Future status offline_model_lease_revoked_pending_independent_cleanup,
model_case=M04b, model_validation_stage=lease_revoked. Shared startup_status may
remain offline_model_validation_child_completed. Store actual revoke/dispatch
command IDs and both worker ages, model_revocation_evidence_matches and
model_evidence_matches only after independent host audit/closure checks.
No qualification flag becomes true.

## Exact Two-Record Audit Proposal

Exactly two newline-terminated existing AuditRecord envelopes, in order:
1. event_type/reason_code=model_bridge.grant_revoked.
2. event_type/reason_code=model_bridge.lease_revoked.

Both: integer schema_version=1, valid UTC timestamp, decision=deny, actual
windows:<operator SID>, capability=model.egress, target=model:maya-offline-fixture,
operation=infer, data_classification=internal-synthetic, idempotency_key=null.
The first deny is a grant-invalidation diagnostic, NOT a gateway decision or
protected inference admission. No new policy engine or policy permission.

Both metadata maps have EXACTLY these string keys:
validation_schema,case,stage,attempt,request_id,coordinator_request_id,
revoke_command_id,dispatch_command_id,route,endpoint,model,destination,
request_sha256,request_bytes,observed_request_sha256,observed_request_bytes,
lease_sha256,grant_ttl_ms,worker_elapsed_ms,revoke_elapsed_ms,phase_before,
closed_before,revoked_before,revoked_after,grant_unexpired,original_guard_rejected,
request_preflight_verified,request_validated,gateway_calls,dispatch_attempted,
response_sha256,response_bytes,output_sha256,dispatches,runtime_prepared,
runtime_released,operator_prepared,operator_released,real_inference.

Common fixed/bound values:
- validation_schema=maya.model.lease_revocation.v1,case=M04b; actual attempt,
  service request_id, revoke command ID, original request hash/byte count and
  issued lease SHA256; lowercase hashes, canonical decimal string counts.
- route=maya.offline.model.v1,endpoint=https://maya-offline-model.invalid/v1/chat/completions,
  model=maya-offline-wire-v1,destination=provider; grant_ttl_ms="2000".
- phase_before="issued",closed_before="false",revoked_after="true",
  grant_unexpired="true",request_validated="false",gateway_calls="0",
  dispatch_attempted="false",response_sha256="",response_bytes="0",
  output_sha256=fixed fixture hash,dispatches/runtime_prepared/runtime_released/
  operator_prepared/operator_released="0",real_inference="false".

First-record values:
- stage=revoke_applied,coordinator_request_id=actual revoke ID,dispatch_command_id="".
- revoked_before="false",original_guard_rejected="false",
  request_preflight_verified="false",observed_request_sha256="",
  observed_request_bytes="0" (no child request exists yet).
- worker_elapsed_ms=revoke_elapsed_ms, each the same actual worker age at
  successful revocation observation.

Second-record values:
- stage=lease_revoked,coordinator_request_id=actual dispatch ID,
  dispatch_command_id=same actual dispatch ID, distinct from revoke/issue IDs.
- revoked_before="true",original_guard_rejected="true",
  request_preflight_verified="true"; observed hash/bytes equal ORIGINAL request.
- revoke_elapsed_ms EXACTLY the first acknowledged age; worker_elapsed_ms actual
  rejection age, >= revoke age. Both canonical strings in [0,1999], not floats,
  booleans, leading-zero strings or absolute timestamps. Actual worker time MUST
  separately be strictly before captured expiry; integer rounding is not proof.

Only these two age values are dynamic: range/order checked, bound to their exact
reply/ack and required to match protected ledger records. Other metadata is
independently reconstructed by C# from trusted saved host binding/grant/request/
IDs and checked exactly; no wildcard, caller-controlled actor or raw lease/body/
canary/output/exception text in ledger. Dedicated Python and C# TWO-record
admission must reject missing/extra/swapped/duplicate/truncated/wrong-kind records,
invalid UTC/schema/types and rebound IDs/ages. Do not loosen earlier single-record
ModelValidationAdmission.Audit defaults. Audit failure/short write/flush/fsync
poisons the attempt; no reopening/replacement sink. A committed revocation record
alone, or two records followed by a timing failure, is not completed acceptance.

Evidence() runs after normal service close; it must use the previously captured
ack/rejection snapshots and healthy complete ledger, not infer earlier revocation
from close() setting both flags true. Revocation must have been acknowledged
BEFORE request handling, and not reconstructed from cleanup.

## Required Source Impacts And Inert Controls

Proposed new model_lease_revocation.py service observer/metadata/two-record verifier,
ModelRevocationAdmission.cs independent host admission, fixed revoke entry points
and exact negative adapter/report. Extend exclusive worker/bootstrap modes,
coordinator order/replies, compile selectors, payload allowlists and
version/consent/status only for this case. Original base model_service.py/revoke/
_live accepted set, ordinary TTL/gateway rules and frozen expiry sources/payload
remain unchanged. No refactoring of expiry to make this work.

Future successor assembly may need to omit ONLY model_expiry_child_entry.py and
model_expiry_worker_entry.py from its NEW payload. Those omissions are NOT
approved now: require exact byte inventory/source impact review and explicit
assembly/omission approval after implementation. Preserve canonical expiry
helper, M03a shared support, all dependencies/notices and every prior artifact.
Actual-profile ReadIndex must admit full successor inventory and reject inactive
entries before seal. No removal of workstation/guest/source/predecessor files.

Required inert controls before source acceptance:
- Separate fresh ordinary-service positive control; revoke calls original method
  exactly once, changes only revocation, no reset/new grant; original guard MUST
  reject before gateway/effects. Fake clocks only in inert fixtures.
- Missing/wrong/duplicate/reordered revoke/ack; command-ID reuse across issue/
  revoke/dispatch; wrong lease/attempt/channel/route/body/model/service identity.
- Revoke before issue, already revoked, closed, audit poisoned, wrong phase,
  changed lease/expiry or preexisting effects; every confound blocks.
- Live unrevoked request in fixed negative profile blocks BEFORE dispatch; revoked
  at just-before/at/after expiry, backward/nonfinite clocks, and crossing expiry
  during guard or audit. At/after expiry is NOT isolated revocation success.
- Distinct ack/rejection ages: [0,1999] bounds/order/canonical strings, mismatched
  reply/ledger age/command IDs, forged unexpired/guard flags, ack without audit.
- Exact two-record schema/order/types, missing/extra/duplicate lines and required
  audit write/short/flush/fsync faults. Terminal failures never reopen a ledger.
- Exact child denial control, one native SDK request, genuine closure reports;
  arbitrary child errors/EOF/unexpected exit/no report cannot pass.
- Cross-language Python/C# record vectors and paired old profile fixtures,
  old worker rejection of revoke, guarded imports/no eager dependency/native
  entry execution, compile mutual exclusion and actual-profile payload admission.
- Source-bound absence of native fake clock, expiry wait, TTL/deadline changes,
  environment fault selection, second request, guard bypass or live-provider path.

Same Python3.13.14/Hermes/64 distributions/config/native guards; ordinary
AppContainer/zero capabilities/six denies/reduced tokens/jobs/child-process block/
pipes/protected host files and labels. Frame8192/direction131072/audit131072/
request-response-stderr4096/report65536/output1024/diagnostic256 bounds.
Trusted worker remains outside child network containment. Shared All Application
Packages and profile-removal limitations stay open. No new dependency, grant,
registry/loopback exception, listener/service/account, credentials, customer data,
inference/spending, VM automation, retry, recovery or qualification.

## Next Decision

Review validation: companion JSON parses; each exact audit map contains all 39
unique string-valued metadata keys, with no missing/extra/overlapping keys.
Referenced review/outcome documents exist. All 166 product/test source files in
the frozen Expiry 1 source manifest still match; current product/test source was
not edited. Frozen Expiry 1 ZIP/EXE hashes match the outcome record. Coupled
context validator and whitespace checks pass (existing LF/CRLF notices only).
No product regression/fixture execution was needed for this document-only review.

Review/approve M04b-only SOURCE preparation INCLUDING the one fixed revoke/ack
operation and two-record audit contract. Then source/inert evidence review;
separate exact assembly/omission approval; guest path/hash; separate one-run VM
approval and fresh consent; result/scoped cleanup. No package or M04b implementation
exists yet. M04c/M05-M09/M2/Gate A and all qualification flags remain pending/false.

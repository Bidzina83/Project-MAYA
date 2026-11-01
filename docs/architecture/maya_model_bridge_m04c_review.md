# M04c Consumed-Grant Replay Review

Subsequent decision: user approved M04c-only source preparation. Implemented
candidate/inert results and remaining gates are in maya_model_bridge_m04c_source_review.md.
Review-stage statements below are historical, not package/native-run approval.

2026-10-31. Source/test-contract REVIEW only after the reported M04b pass and
scoped cleanup in maya_offline_model_revocation_1_outcome.md. No product/test
source edits, build, native execution, security setup or inference. Companion:
maya_model_bridge_m04c_tests.json. Original M04/denial contracts remain historical.

## Findings And Decision

1. Replay is NOT a zero-effect negative. Preserve two prior gateway calls, one
   synthetic dispatch, one runtime preparation and confirmed delivery. The child
   has completed a genuine positive SDK exchange; no second SDK call or invented
   negative child report. M05 adapter-budget tests remain separate.
2. ModelChannelClient already consumes the grant/request budget on first exchange.
   A second child call would normally fail locally. To test the service's consumed
   grant, replay the exact saved request from the TRUSTED coordinator using a NEW
   model_dispatch command ID. Existing worker seen-ID checks must stay active.
3. Original _live("issued") rejects the phase runtime_delivered before envelope
   validation, but combines phase/closed/audit/revoked/expiry in ModelDenied.
   Read-only preflight plus coherent unexpired/unrevoked state is needed to isolate
   consumption. Original dispatch_attempted=true means ModelDenied.uncertain=true;
   preserve that flag and the known prior effect. Do NOT require/reset false like
   M04a/b. A true flag alone is not proof of replay rejection.
4. confirm_runtime_delivery deliberately records a prior write even after expiry/
   revocation. Do not add an early expiry check that suppresses this truth. Record
   the original delivery first; only afterward require unexpired/unrevoked state
   for M04c replay admission. A late confirmation is blocked/confounded for M04c,
   not zero-effect, and its committed prefix remains.
5. Current worker expects model_prepare_final after runtime ack and host proceeds
   to operator publication. Add a fixed M04c-only terminal replay branch BEFORE
   operator preparation, not a generic reopen/retry or a suite. Both existing
   positive audit validators require six events: a NEW five-record verifier is
   needed; do not relax the old six-event/single-event/two-event checks.
6. Runtime_delivery's current service destination remains runtime:<attempt>.
   During replay failure the original _fail uses this destination. New case-bound
   observation must explicitly verify that retained context and emit a provider-
   destination lease_consumed diagnostic for the attempted replay; do not silently
   overwrite _destination or reinterpret it as another output-denial test.

Recommendation: approve M04c-only SOURCE preparation with the exact schedule,
positive-prefix preservation and five-record contract below. No current bypass
is established: these are missing native schedule/observability components.

## Proposed Fixed Schedule

Candidate 0.2.1-offline-replay.1, scope offline-hermes-consumed-lease-v1.
HERMES_MODEL_REPLAY requires VALIDATION/MODEL/BRIDGE/CONSTRUCTION/IMPORT for
existing bounded startup reporting, excludes REVOKE/EXPIRY/BODY/ROUTE/ATTEMPT/
DENY/STATE/MEMORY. It is an explicitly POSITIVE child path despite inherited
VALIDATION support: coordinator must select it rather than RunValidation; other
profiles retain their prior selection. Fixed model_replay_child_entry.py and
model_replay_worker_entry.py; no caller/environment/config-selected fault.

1. Normal product setup/consent, real pinned child construction/readiness. Issue
   one ordinary 2000-ms grant and validate exact identity/route/seq/TTL/request
   hash/lease. No delay or reissue. Same positive M01 policy and actual operator.
2. Send ordinary model_begin. Child uses the UNCHANGED ModelChannelClient,
   factory/SDK and all guards to emit one valid original request. Host validates
   full envelope/body, saves an immutable exact copy and first command ID, then
   sends ordinary model_dispatch. Service follows its ORIGINAL positive path:
   real existing gateway, fixed synthetic dispatch, output authorization to runtime,
   and original three audit records. Verify exact synthetic response/digest/shape/
   fixture text and counters; any first-exchange failure blocks the case.
3. Host writes the one verified response to child and verifies its exact existing
   receipt (actual attempt, hash and byte count). Send model_runtime_delivered
   with fresh command ID and actual response hash. Original service confirmation
   MUST record committed delivery and its fourth audit event truthfully, even if
   time ran out. After that, M04c observer verifies runtime_delivered/open/
   healthy/unrevoked/same grant state, exact first effects and real finite
   nonbackward worker time strictly before expiry. Capture delivery age.
4. M04c-only model_runtime_ack adds exact delivery_elapsed_ms evidence described
   below. Host requires acknowledgement of count1, exact ID and canonical age.
   Immediately replay SAVED original request under NEW model_dispatch ID, before
   waiting for the final SDK report. Do not mutate any request field/channel/lease,
   call the child adapter a second time or send a child denial control.
5. Under the existing service lock, immutable first envelope/body/channel/lease/
   response and first/delivery command bindings must match the replay, with
   exact v/seq integer types. Preflight is diagnostic, NOT new admission.
   Verify phase runtime_delivered, open, healthy audit, unrevoked, unchanged
   captured lease/expiry, real time before expiry and known first counters.
   Call original _live("issued") via original prepare_runtime. Require exact
   ModelDenied with uncertain=true, actual wrong-phase guard rejection, unchanged
   context/counters and finite nonbackward time before AND after the guard.
   If guard returns, block BEFORE any further gateway/effect. Generic exception,
   uncertain outcome without this proof, closed/revoked/expired/wrong phase,
   malformed replay or duplicate-command rejection is not consumed-grant proof.
6. Persist exact fifth lease_consumed rejection, check time/context before/after
   required audit commit, close normally and return one bound terminal evidence
   reply. No second model response, delivery, operator preparation or publication.
   A clock/audit failure after a committed prefix keeps its effects but blocks
   acceptance; never reopen, reset counters or replace a failed sink.
7. Host validates terminal replay evidence and then consumes the child's genuine
   positive final text/report, verifies fixture text and normal constructor/
   conversation/SDK closure/config/origins/distributions. This report can already
   be buffered while replay RPC runs; it grants no permission and is not published.
   No model_prepare_final/model_operator_delivered commands and no publish call.
8. Require child/worker normal exit0, EOF, bounded empty stderr, fresh beacon,
   protected-host readback and independent exact five-record audit admission
   before success flags. Product cleanup and scoped operator checks follow
   separately. Final counters remain (1,1,0), not (0,0,0).

Every command ID (issue, first dispatch, runtime confirmation, replay) is distinct.
No waiting for child final before the time-sensitive replay; existing bounded
private-pipe framing/budgets remain. No new listener or transport. Child may
finish its ordinary positive closure while host replays; it need not falsely
claim to have observed the host-only replay. Native interleaving/timing is unproven.

The original 2000-ms grant covers the complete positive prefix plus replay.
Existing Ready5000/RPC2000/partial1000ms and child22/30s limits stay intact. No
expiry wait/TTL extension/fake native clock/renewal/retry. If real disk or scheduling
cannot fit the schedule, report blocked/confounded and stop for review. A new
attempt or strategic change is not automatically authorized.

## Exact Proposed Worker And Child Protocol

Use existing command shapes for issue/first dispatch/runtime-delivered and replay.
Replay is model_dispatch with identical saved request, NEW request_id, same
actual attempt/channel/lease, not a new opcode rejected before liveness.

M04c-only runtime acknowledgement EXACT keys:
v,type,attempt,request_id,confirmed_runtime_releases,delivery_elapsed_ms.
v=1,type=model_runtime_ack,actual attempt/confirmation request_id, integer count1,
canonical string worker delivery age [0,1999]. Return only after the fourth
required audit commit and strict actual unexpired/context check. Other profiles
keep the current acknowledgement shape. This is no extra audit event.

Terminal worker reply EXACT keys:
v,type,attempt,request_id,evidence.
v=1,type=model_lease_consumed,actual attempt/replay request_id, complete exact
fifth-record metadata below. Then normal return/close, no extra command. Lost/
malformed ack or replay reply, EOF/timeout/crash is blocked, not passed negative.

Child retains genuine POSITIVE model_child_complete frame with v/type/attempt/
text/report and existing maya.offline.model.child.v1 report schema. Required:
completed/native_constructor/native_conversation/sdk_closed/origins_verified/
distributions_verified/config_unchanged=true; model_requests=1,client_objects
integer2..8,real_inference=false,reason_type="". No denial_observed claim or
model_child_denied frame. Validate text privately against original fixture; no
operator release. Future bootstrap accepts cases=[M04c] exclusively but leaves
the real positive factory/client/request/lifecycle unchanged.

Proposed startup_status=offline_model_replay_child_completed, final status=
offline_model_lease_replay_rejected_pending_independent_cleanup,
model_case=M04c, model_validation_stage=lease_consumed.
model_replay_evidence_matches/model_evidence_matches only after host validation.
Report totals gateway_calls2,synthetic_dispatches1,runtime_pipe_writes1,
operator_publications0 plus replay-specific zero deltas. Do not infer counters
from a generic exception or copy M04a/b zero totals. All qualification flags false.

## Exact Five-Record Audit

Exactly five newline-terminated existing AuditRecord envelopes, schema_version
integer1, valid UTC timestamps nondecreasing across all five, exact key/type
checks and no extra/duplicate/rebound fields. Common actual windows:<operator
SID>, target=model:maya-offline-fixture, classification=internal-synthetic,
idempotency_key=null. No raw body/lease/canary/output/exception text.

Records1-4 retain the actual original committed prefix without rewriting it,
using the existing event/reason/schema semantics:
1. model_bridge.egress_intent: allow, model.egress/infer,destination provider.
   response hash="",bytes="0",dispatches="0".
2. model_bridge.dispatch_outcome: allow, model.egress/infer,destination provider.
   Actual response hash/bytes,dispatches="1".
3. model_bridge.runtime_release_intent: allow, model.output/disclose,
   destination runtime:<attempt>, actual response hash/bytes,dispatches="1".
4. model_bridge.runtime_delivery: allow, model.output/disclose,
   destination runtime:<attempt>, actual response hash/bytes,dispatches="1";
   coordinator_request_id binds actual runtime-confirmation command.

Each prefix metadata map has EXACT keys attempt,request_id,route,endpoint,model,
destination,request_sha256,response_sha256,request_bytes,response_bytes,
output_sha256,dispatches,real_inference; only record4 also coordinator_request_id.
Same actual service ID, original request hash/bytes, route=maya.offline.model.v1,
endpoint=https://maya-offline-model.invalid/v1/chat/completions,
model=maya-offline-wire-v1, fixed output hash, real_inference="false".
No new age fields added to prefix. Do NOT pass a truncated prefix to the original
six-record verifier or invent two operator events. New Python/C# five-record
admission must reconstruct these prefix maps independently.

Record5 has exactly 50 string metadata fields. Its
event_type/reason_code=model_bridge.lease_consumed,decision=deny,
capability=model.egress,operation=infer,destination provider. That destination
names the rejected replay, not a new authorization or previous runtime release.
Its EXACT string metadata keys/values are frozen in the companion JSON:
- validation_schema=maya.model.lease_replay.v1,case=M04c,stage=lease_consumed;
  actual attempt/service request_id; coordinator_request_id=replay_command_id,
  first_dispatch_command_id/runtime_delivery_command_id/replay_command_id actual
  and distinct. Same original route/endpoint/model, destination provider.
- Original request_sha256/request_bytes and observed_request_sha256/
  observed_request_bytes identical; lease_sha256 actual issued lease; exact
  saved-envelope/channel preflight required, no new actor/lease/projected fault.
- Actual response_sha256/response_bytes and output_sha256 of first verified
  response/fixture, grant_ttl_ms="2000".
- delivery_elapsed_ms EXACT prior runtime ack age; worker_elapsed_ms actual
  consumed-guard rejection age, both canonical strings [0,1999], rejection>=
  delivery. Strict actual worker expiry/monotonic checks are separate; never
  subtract absolute clocks from different processes or trust rounded age alone.
- phase_before="runtime_delivered",closed_before="false",revoked_before="false",
  grant_unexpired="true",original_guard_rejected="true",
  original_denial_uncertain="true",request_validated="true" (FIRST admission),
  replay_request_preflight_verified="true",replay_request_validated="false".
- gateway_calls/gateway_calls_before/gateway_calls_after="2",replay_gateway_delta="0".
  dispatch_attempted="true" (FIRST dispatch),replay_dispatch_attempted="false";
  dispatches/dispatches_before/dispatches_after="1",replay_dispatch_delta="0".
- runtime_prepared/runtime_released="1",replay_runtime_delta="0",
  operator_prepared/operator_released/replay_operator_delta="0",real_inference="false".

Only delivery/rejection ages are dynamic; bounded, ordered and exactly equal
between ack/reply and fifth protected record. All other fields are reconstructed
from trusted saved host binding/request/response/IDs and checked exactly.
Prefix4 binds the runtime command independently. Counter snapshots before/
after guard/event must match first committed effects, never be zeroed.
uncertain=true preserves original service semantics after a prior dispatch;
it does not mean the replay is permitted or prove no second effect by itself.

Original _fail sees retained runtime:<attempt> destination and calls close().
Observer must verify that prior context, record the provider replay diagnostic
without mutating it, and retain immutable before-close rejection/effect snapshots.
Evidence after close cannot infer earlier unrevoked/open/phase state from current
flags. No automatic ledger reset, cleanup-derived negative or audit reopening.
Any unknown/premature failure remains blocked with accurate prior effects.

## Source Impacts And Required Inert Controls

Proposed new model_lease_replay.py observer/five-record verifier,
ModelReplayAdmission.cs host admission and two fixed model_replay root entries.
Extend exclusive worker/bootstrap mode and positive-child contract selection,
runtime-ack shape for M04c, terminal replay schedule, host preservation of
saved request/response/effects, compile selectors, consent/status and entry
allowlists. ModelValidationAdmission.Enabled currently selects RunValidation:
add an explicit exclusive M04c positive branch, not a relaxed old negative.
Reuse current bounded startup reporting. Preserve base model_service.py/revoke/
_live/TTL/confirmation semantics, ModelChannelClient/factory and all old audit
validators exactly; no Hermes/SDK wheel patch or runtime monkeypatch.

Future package may need omission of ONLY model_revoke_child_entry.py and
model_revoke_worker_entry.py from NEW successor inventory. Not approved now.
Keep canonical revocation/expiry helpers/shared support and all prior artifacts.
Source impact/inventory must be reviewed after implementation, before explicit
assembly/omission approval and full actual-profile ReadIndex/byte/pin verification.

Mandatory inert source-acceptance controls:
- Fresh ordinary positive control and genuine four-event effect prefix; preserve
  two gateway calls, one dispatch/preparation/delivery, zero operator preparation.
  No acceptance when first dispatch/receipt/confirmation/prefix is missing.
- Original guard must reject actual consumed phase. Returning guard, generic
  errors or an uncertain flag alone cannot qualify; no further gateway/dispatch.
- Duplicate command ID rejected BEFORE observer is not consumed replay; fresh-ID
  exact same request succeeds as the negative control only at intended guard.
- Wrong body/model/route/attempt/lease/channel/seq/v/service/response/IDs, malformed
  or reordered issue/dispatch/confirmation/replay, early/second replay all block.
- Expired/revoked/closed/poisoned/wrong phase or altered captured grant cannot pass.
  Before/at/after expiry and clock crossing guard/audit, nonfinite/backward clocks;
  only real native clock, fake times confined to inert fixtures.
- Late delivery confirmation STILL records its prior effect before M04c blocks.
  No rollback/zeroing/reissue or suppression of truthful committed prefix.
- Positive child stays one SDK call with normal report/closure; no second adapter
  request, budget reset, negative child control or fabricated denial observation.
- Missing/bad/forged receipt/runtime ack, response digest, dynamic ages/order/
  ledger mismatch; incomplete SDK closure/report, EOF/unexpected exit block.
- Every prefix/fifth key/type/order, wrong timestamps, truncated/missing/extra/
  duplicate operator/rejection events; required-audit write/short/flush/fsync
  failures before/after first effects. Counts stay accurate on blocked outcomes.
- Exact Python/C# cross-language five-record vectors, prefix isolated from old
  six-event verifier, paired old profiles, compile-mode exclusion, import/native
  entry guards, no eager dependency/clock injection/operator publish path.
- Actual full payload admission is an assembly gate; inert entry-name probes
  cannot substitute for the real successor inventory/resource verification.

Same Python3.13.14/Hermes/64 pins/config/native guards, AppContainer/zero
capabilities/six denies/reduced tokens/jobs/child-process block/pipes/host files/
ACLs/labels. Frame8192/direction-audit131072/request-response-stderr4096/
report65536/output1024/diagnostic256. Trusted worker remains outside child network
containment; shared All Application Packages/profile deletion remain limitations.
No new grant/dependency/registry/loopback/listener/account/service, customer data,
credential, real provider/inference/spending, VM runner, retry or recovery.

## Next Decision

Review validation: companion JSON parses with four exact positive-prefix maps
(13/13/13/14 string fields) and 50 unique string fields in fifth metadata.
Effects remain (1,1,0), gateway calls2, original denial uncertainty true and
positive child conversation/one-request guard. Referenced documents exist.
All 174 product/test files in frozen Revocation 1's source manifest still match;
ZIP/EXE hashes match its build record. No product/test source edits, regression
fixture execution or native run performed by this document-only review. Coupled
context validator and whitespace checks pass; existing LF/CRLF notices only.
Source/assembly/omission/native-run approval flags remain false.

Approve M04c-only SOURCE preparation INCLUDING the positive child path, one
additional trusted new-ID replay dispatch after delivery acknowledgement, M04c
runtime-ack age field and exact four-positive-plus-one-denied audit contract.
Then review implementation/inert evidence before separate assembly/omission
approval, matching-artifact VM-run approval/fresh consent and result/cleanup.
No code/package/run approval follows this review. M05-M09/M2, Gate A and all
qualification flags remain pending/false; native two-second timing is unproven.

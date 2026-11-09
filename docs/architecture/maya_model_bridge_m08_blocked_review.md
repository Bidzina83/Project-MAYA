# M08 Blocked Source Review

2026-11-04. User approved SOURCE REVIEW only after blocked Final1 and scoped
manual cleanup. No product/test source edits, compile, fixture/product/bundled
runtime/native execution, package, VM retry, security/grant/dependency/deadline
change or qualification authorized.
See maya_offline_model_final_1_outcome.md for evidence/provenance/limitations.

## Findings

1. The two-second lifetime spans more than response transport.
   model_service.py:158-168 checks aggregate closed/audit/revoked/phase/clock
   and issues _expires=monotonic+2. prepare_operator:337 checks original
   _live(runtime_delivered) BEFORE changing destination to operator.
   The retained runtime-destination denied record does not satisfy M08.
   Expiry is plausible, not established: the failing predicate and original
   monotonic sample were not captured.

2. A runtime-delivery ack does not prove an unexpired authorization.
   confirm_runtime_delivery:317 intentionally records an actual prior write
   without checking expiry. Its purpose is truthful effect accounting.
   Do NOT change it to discard a delivery that occurred after expiry.
   Four positive audit event names/ack cannot establish time remaining at final
   preparation; the original liveness check is still required.

3. Native completion work occurs after the early response receipt.
   ModelChannelClient.request sends model_runtime_receipt before returning
   response bytes to the SDK (hermes_plugins/model_bridge.py:84).
   Child subsequently finishes run_conversation, closes memory/agent/SDK clients,
   rereads config and checks imported module origins, then sends the positive
   final report (model_child_entry.py:120-165).
   Coordinator confirms runtime delivery, waits for that final report and
   performs original positive final/report checks before fixed mutation
   (ModelBridgeRuntime.cs:223-282). All this remains inside the ORIGINAL lease
   lifetime. The actual cost of these phases on the VM is unmeasured.

4. Some cold diagnostic work is also after issue.
   M08 worker imports model_final_text only after model_prepare_final arrives
   (model_worker.py:224), before calling original prepare_operator.
   Coordinator's mutation helper/oracle also runs after final admission.
   These are possible contributors, not measured bottlenecks. Static source
   does not establish that imports, SDK cleanup, module-origin traversal, JIT,
   reader scheduling or any single operation caused expiry.
   Blind preloading/reordering is not a demonstrated native fix.

5. Generic channel failure is compatible with fail-closed evidence rejection.
   Original prepare_operator failure calls _fail and writes denied using the
   current destination. M08 catches ModelDenied, but final_text_evidence requires
   named operator_text observation, runtime_delivered phase and operator
   destination. A pre-comparison failure cannot satisfy it; ProtocolError
   prevents model_operator_text_rejected from being sent.
   Hence the retained denial plus missing specific reply is consistent with
   safe rejection of a wrong-stage failure, not proof the text guard passed.
   Existing diagnostics lose its specific liveness cause.

## What Remains Unknown

_live combines closed state, poisoned audit, revocation, phase mismatch and
clock expiry, and may also propagate an exception evaluating a dependency.
In the ordinary serialized successful-ack path source sets runtime_delivered
and contains no intervening revoke/close call; expiry is the leading hypothesis
under those assumptions. Runtime observations do not isolate the predicate,
clock value, guard phase/flags or worker exit/exception.
Do not elevate a source inference to an observed root cause.

Second-resolution UTC event timestamps do not expose the grant issue point
or its monotonic deadline. Created-to-finished duration includes setup/cleanup
and must not be treated as conversation duration or grant age.
Full positive audit bodies, final file hash and natural-exit evidence were not
admitted. No retroactive M08 pass or native retry follows review.

## Recommendation

Request separate M08-only SOURCE preparation for bounded product diagnostics,
not a TTL increase or scheduling fix.
Capture original issue/guard timing and the original guard's state/predicate
without changing its decision, short-circuit behavior or clock-call count.
Use only the original clock sample when the original condition actually
evaluates it; mark timing unsampled for earlier state failures. Do not add a
second clock read and describe it as the failing sample, substitute a fake
native clock, override the decision, reset _expires, reissue or extend a grant.

Before implementation, freeze exact bounded fields and diagnostic failure
admission in source review. No raw text/body/lease/secrets, exception messages
or traces. Diagnostics must identify original phase/flags, clock-sampled state,
bounded age/deadline relation when observed, and trusted command/attempt binding.
If timing cannot be captured faithfully without altering original behavior,
stop for design review rather than weaken the predicate.

Add inert compositions for actual delivery followed by both before-deadline
text mismatch and after-deadline rejection, state failures with NO clock call,
clock exception and audit failure; prove exact original clock-call counts,
truthful prior effects/uncertainty and no publication. Existing constant-clock
positive service fixtures and immediate local worker fixture do not reproduce
native SDK shutdown/origin-check timing.
Guard diagnostics are not M08 success evidence. Expiry/other wrong-stage failures
must remain blocked and must NOT satisfy the exact operator-text contract.

Only after diagnostic source review may separate assembly and exact-artifact
ONE-run approval/fresh consent be sought. No omissions approved here.
Preserve Final1/379 frozen sources, all predecessors and existing audit/guard/
permissions/WFP/grant/dependency/bound/deadline rules. No new native run now.
If measured scheduling cannot fit original lifetime, a lifecycle/authorization
design decision would require separate explicit approval; this review grants
none. No inference/retry/recovery/M09/M2/qualification. Gate A remains open.

## Verification Performed

Read-only rehash matched Final1 ZIP/EXE, all379 frozen source entries and seven
current reviewed runtime files against sealed source pins. Reviewed original
guard/order, child post-response work, coordinator path and inert test fixtures.
No product/test source edit or test/compile/native execution performed.

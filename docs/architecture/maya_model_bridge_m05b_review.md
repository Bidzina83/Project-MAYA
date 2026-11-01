# M05b Recreated Client Review

Subsequent decision: user approved M05b-only source preparation and inert tests.
See maya_model_bridge_m05b_source_review.md for implementation and evidence.
Original review-only statements below are historical, not package/run approval.

2026-11-01. Review/test-contract preparation only after bounded M05a success.
No product/test source change, compilation, assembly, product/native run,
dependency acquisition or VM/security change. Preserve Budget3 and predecessors.

## Findings

ModelChannelClient.exchange consumes _grant before first send, increments
requests once, and rejects another exchange through the original guard before
pipe send. bind_grant cannot rebind. PipeModelTransport.close closes only its
transport; close_model_clients poisons the shared adapter and must NOT run
before this diagnostic. A closed adapter makes the existing factory reject
creation, which would test shutdown rather than budget persistence.

OfflineModelClientMixin._maya_create_client delegates to the native factory
with copied fixed kwargs, creates separate SDK/HTTP/transport ownership and
retains one shared _maya_model_channel. It refuses closed channel or eight
existing client triples. A new client does not imply a fresh adapter budget.

Budget3's SameClientBudgetMixin probes BEFORE native request-client close.
The packaged pinned Hermes chat_completion_helpers.py invokes that close on
the request-owning thread before conversation returns. Therefore propose a
SEPARATE case-bound recreated-client mixin: at that eligible close hook, verify
the actual used triple and save its validated snapshot, delegate original close
exactly once FIRST, verify closure, then recreate/probe on the SAME owner thread
before the hook returns. Positive native conversation must still return normally.
Do not run the existing M05a hook and then try recreation: its rejection poisons
the adapter, making that schedule invalid.

BudgetPipeTransport._validated_request currently rejects a first observation
when adapter.requests is already one; it also insists on BudgetChannelClient
type. Reusing it unchanged for a new transport cannot test M05b. Future source
preparation needs a separately reviewed observer that validates the recreated
transport's FIRST request against the original snapshot while retaining the
original PipeModelTransport request validation and ModelChannelClient guard.
Never relax those original guards or replace live runtime methods.

## Proposed Fixed Sequence

1. Fresh attempt, unchanged grant/request, genuine native Hermes first exchange,
   gateway2/effects(1,1,0), actual runtime confirmation and positive audit prefix.
2. Existing bounded probe-control scheduling frame is case/profile bound by the
   reviewed child entry. It is not a new grant. Validate attempt and unique ID.
3. On eligible request_complete/owner thread, identify the actually used triple
   and exact original method/URL/headers/body. Assert adapter open, bound,
   grant absent, requests1, completed first exchange1, no prior rejection.
4. Delegate original native close exactly once even if preflight fails. Verify
   old SDK/HTTP/transport all closed but shared adapter remains open/consumed.
   No close_model_clients, agent recreation or state mutation.
5. Invoke the existing parent-delegating factory once with original validated
   copied kwargs and reviewed reason/shared values. Resolve exact native request
   factory semantics during source preparation. Require one new owned triple,
   distinct SDK/HTTP/transport objects, same adapter by object identity, no bind,
   zero SDK retries, original timeout/origin/model and existing ownership cap.
   Creating another client must not silently replace another reference or client.
6. Send exactly one explicit httpx request through the NEW HTTP client, copying
   original validated bytes/headers, never an SDK retry or second conversation.
   Require ordinary transport validation then original consumed-budget rejection,
   requests still1, second transport completed exchanges0 and no extra pipe send.
   Closed-client/malformed-request/generic error cannot pass.
7. Close new owned triple directly and verify closure without recursively entering
   the request-close diagnostic. Always delegate/complete original close on errors;
   never suppress/defer close to gain compatibility. Any abort poisons admission.
   Do not raise diagnostic failures into Hermes retry/fallback machinery.
8. Genuine positive conversation returns; collect strict case-bound lifecycle/
   identity observations, then normal agent/client shutdown, child EOF/exit0.
   Trusted coordinator independently rejects extra model frames/effects; worker
   terminates normally with case-specific terminal evidence and exit0.
9. Admit EXACTLY the four original positive audit records. No synthetic fifth
   denial event exists because the second request must never reach the worker.
   No model_prepare_final or operator publication. First effects remain truthful
   on any later failure; retain blocked/uncertain evidence, never zero them.

## Evidence And Source Gates

Use a separate compile/profile and fixed bootstrap, proposed version
0.2.1-offline-recreate.1 (not yet implemented/frozen). Existing M05a profile,
schemas, audit admission and frozen packages remain unchanged. New strict
child/lifecycle schema must identify M05b, original closure BEFORE recreation,
owner thread, new distinct triple, same consumed adapter, no rebind, two total
transport attempts, original completed exchange1 and exactly one budget rejection.
Avoid raw object IDs/addresses/kwargs/payload/secrets in public evidence.
Bounded identity booleans are untrusted child observations, not OS provenance.

Independent terminal evidence must still bind original attempt/operator/request/
response/delivery and show total gateway2/dispatch1/runtime1/publication0,
additional pipe/gateway/dispatch/runtime0, four verified audit records and natural
closure. Do not reuse M05a case labels or weaken its exact admission validator.
Freeze new exact protocol/schema/key counts during source review BEFORE assembly.

Required inert controls: wrong owner/used triple/reason, failed or duplicate old
close, adapter poisoned by shared shutdown, new or rebound adapter/grant, factory
failure/client-cap overflow, identical objects/reused transport, changed headers/
body, closed new client, premature probe, extra pipe request, wrong case/attempt/
command/counters, forgery, native/new-client close failures, abort, EOF/timeout,
audit missing/extra/reordered/mutated and preservation of first effects. Preserve
old profile regressions and reader/deadline/cleanup behavior. Generic failures
cannot become passing negative cases.

## Limits And Recommendation

Recommend M05b-only source preparation next, including explicit post-native-close
owner-thread hook, separate observer, bounded lifecycle/identity schema and
independent case-bound admission. These are product components, not a VM runner.
This document does NOT implement them or authorize execution.

No new agent/adapter/grant/dependency, TTL/deadline/security change, service
unexpired-lease assertion, inference, credential use, retry/fallback success or
M06-M09/M2. M05b tests cooperative factory behavior and no-extra-effect evidence;
it does not prove protection against arbitrary hostile Python state mutation.
Source preparation approval -> source review -> separate assembly/any exact
successor-only root omissions approval -> full inventory/freeze checks -> guest
hash/path -> separate one-run approval/fresh consent. Do not preauthorize omissions.
All qualification flags remain false; Gate A remains open.

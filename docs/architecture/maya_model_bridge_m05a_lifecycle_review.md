# M05a Request-Client Lifecycle Review

Subsequent decision: user approved M05a-only source correction and lifecycle
tests. Candidate/inert results are in maya_model_bridge_m05a_lifecycle_source_review.md
and maya_model_bridge_m05a_lifecycle_tests.json. Historical review gates below do
not authorize successor package assembly or native execution.

2026-11-01. Review only after Budget1 attempt903761cb996541fc8b9dc9acc077daa7
blocked and scoped manual cleanup. No product/test source changes, package,
product/Hermes/SDK execution or VM/security change. Source-preparation approval
for a successor has NOT been requested or granted by this review.

## Findings

P1: The current M05a schedule requires an open client AFTER native Hermes has
already closed it. windows_runtime/model_child_entry.py:115 calls
agent.run_conversation; lines140-150 wait for probe control and call
probe_same_client afterward. hermes_plugins/model_budget.py:60-62 explicitly
rejects a closed SDK/HTTP client or transport. This is a correct local fail-closed
precondition placed in an incompatible native schedule, not an AppContainer or
WFP finding and not evidence of a consumed-budget bypass.

Inspected inert bytes from the sealed Budget1 model-payload.zip, not an upstream
checkout or a different Hermes version. Pinned run_agent.py:3703-3727 creates a
separate request client with shared=False;3729-3730 delegates closure to
_close_openai_client;3609-3616 closes the SDK. Pinned
hermes/agent/chat_completion_helpers.py:233-239 uses that request-scoped client
for nonstreaming chat.completions.create. Its _call finally at253-254 calls
_close_request_client_once("request_complete"); that helper at174-191 delegates
to _close_request_openai_client on the owning thread after releasing its holder
lock. The primary client is a different unused client, so selecting it instead
would abandon the SAME-used-client claim. Native two-client construction in
the guest report is consistent with this source behavior.

Inspected helper SHA256:
ff17762913d3e38aefa57fa22b56048f99d09fc18d189ab6441bf9c69433a76c.
Pinned run_agent.py SHA256 remains
7a36be48ffdc0fe62b855263683d55c1c7138cc65acf597175920fcf86b45bd5.
Dependency bytes are covered by the frozen payload/index; no wheel was changed.

P2: Inert success fixtures leave the request client open. In
tests/test_model_adapter_budget_inert.py:63-75, response.close does not close its
httpx.Client before probe_same_client. The test at93-101 correctly rejects a
closed client, but calls it premature closure. Native Hermes performs that
closure as NORMAL request completion. Missing lifecycle composition, rather
than a missing closed-client guard, allowed the incompatible schedule to pass
the earlier inert suite. Those results are not native compatibility evidence.

## Bounded Reproduction And Guest Attribution

Read-only local diagnostic using existing in-memory fixture and local httpx:
perform first synthetic exchange, close its HTTP client as native cleanup does,
then call unchanged probe_same_client. SDK/HTTP/transport closed=true;
shared adapter closed=false,requests1,validated_attempts1,completed_exchanges1.
Probe raises ProtocolError, adds zero pipe bytes and budget_guard_rejections0.
No bundled runtime, native Hermes, socket, product entry or security setup ran.
No fixture/source file was edited for this reproduction.

Guest child report records native_constructor/native_conversation true, one
request/two clients, probe_command_id a3b8d9c5db2e4746b83ee8353ce548ef,
schema maya.offline.model.budget.child.v1, reason_type ProtocolError and NO probe
result. Four audit event NAMES match the positive runtime-delivery prefix; full
ledger fields/hash were not supplied/admitted. The source conflict is sufficient
to explain this failure. Exact guest line/subcheck remains unobserved because
all these preconditions report the same ProtocolError. Do not claim a guest
traceback, observed client-closed state or validated second-budget rejection.

## Recommended Narrow Successor

Recommend M05a-only lifecycle SOURCE preparation, subject to explicit approval:

1. Keep Hermes/dependency bytes, ordinary mixin profiles, original budget guard,
   transport request validation, single grant and all limits unchanged. Do NOT
   reopen/replace the used client, suppress its close, switch to primary/new
   client, rebind grants or merge this case with M05b.
2. Add one case-specific override around _close_request_openai_client in the
   existing M05a mixin. At the normal owning-thread cleanup boundary, BEFORE
   delegating original close, identify exactly the passed USED SDK/HTTP/transport
   tuple and require the first validated successful exchange and open consumed
   shared adapter. Freeze exact eligible close reason and single-use/thread
   binding in source review. Unexpected/abort/duplicate cleanup cannot pass.
3. Coordinator still confirms actual first runtime delivery and sends its fixed
   probe control without waiting for native conversation completion. Consume that
   control once in the owning-thread hook after the first exchange has returned,
   using the existing private channel/budgets. No concurrent child pipe reader.
   Explicit second HTTP request stays on this SAME still-open used client and
   must reach the original budget guard before any pipe send.
4. Always delegate to original native close in finally, whether probe succeeds
   or fails. Preserve exact first response and effects; do not turn a diagnostic
   failure into model output or an exception that enables automatic retry/fallback.
   Retain bounded outcome/failure state and require it after run_conversation
   returns. A successful first call is not proof the probe passed. Do not emit
   final completion early or omit genuine positive conversation/all-SDK closure.
5. Add bounded named probe stage/failure observations to distinguish client
   selection, close-boundary admission, original guard and postcondition failures.
   Child diagnostics remain untrusted and disclose no raw exception/body/lease.
   Freeze exact new report fields and independently review C# admission before
   assembly; a generic ProtocolError/TransportError remains failure, not success.
6. Require lifecycle-composed INERT tests: native-style request factory/call/finally
   ordering, close exactly once on success/failure, correct owner/used client,
   abort/duplicate/closed-client rejection, no additional pipe/effects, SDK closure
   failures, no retry/rebind/recreation and unchanged earlier profiles. Include
   pinned-source AST/byte checks for the actual helper's factory/close schedule,
   not only a hand-written positive fixture that leaves clients open.

The owning-thread hook changes WHERE the fixed probe runs, not authorization.
Its precise bounded protocol/thread/exception behavior still needs implementation
review; native interleaving remains unverified. Preserve exact four-record audit,
gateway2/effects(1,1,0), genuine positive child report and zero publication. No
grant/TTL/deadline/dependency/security change, new attempt, retry/recovery,
M05b/later case or inference. Source approval, source review, separate successor
assembly and exact-artifact one-run VM approval/fresh consent remain separate.
Keep Budget1/all predecessors intact, all qualification flags false/Gate A open.

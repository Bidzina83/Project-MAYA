# M05a Same-Client Budget Source Review

2026-11-01. User approved M05a source preparation including bounded diagnostic
reporting after the M05 review. Candidate0.2.1-offline-budget.1, assembly file
version0.2.1.11, scope offline-hermes-same-client-budget-v1. No M05b implementation,
payload/EXE/ZIP assembly, native product/bundled-runtime execution or VM/security
changes. Inert fixture executables are not product packages or native evidence.

## Implemented Source

- hermes_plugins/model_bridge.py: no-op observation hooks inside the EXISTING
  consumed-budget branch and after existing transport request validation/response
  exchange. The original rejection predicate, grant consumption, pipe send,
  response checks and exception-to-closure behavior remain. Default transport
  factory still constructs PipeModelTransport. offline_agent_class selects the
  case-specific mixin only through an exact boolean argument; ordinary calls
  retain the original class behavior. Hermes source pins unchanged.
- New hermes_plugins/model_budget.py: BudgetChannelClient observes only an open,
  bound adapter with consumed grant and requests1 at the original rejecting guard.
  BudgetPipeTransport snapshots the FIRST validated method/URL/header tuple/body
  in child memory, records successful first exchange, and requires an identical
  second validated request. No bytes are changed or written to a new file. The
  case mixin delegates SDK construction to the same native parent factory and
  retains separate SDK/HTTP ownership over one shared adapter.
- probe_same_client selects the UNIQUE actually-used transport tuple, not simply
  agent.client. It requires open SDK/HTTP/transport/shared adapter, one completed
  exchange, bound consumed grant and no prior rejection. It creates one explicit
  httpx.Request from the immutable first snapshot and calls the SAME HTTP client's
  send with redirects disabled. No SDK retry, conversation, factory recreation,
  monkeypatch, new adapter or grant. Exact bounded TransportError alone is NOT
  sufficient: validated_attempts2/completed_exchanges1/budget_rejections1/requests1
  and original fail-closed state must match. Generic/closed/malformed paths fail.
- model_child_entry.py: fixed exclusive positive M05a mode. Genuine native
  conversation first, await trusted probe control, perform explicit probe, then
  unchanged memory-provider/agent/all-client closure. Report retains genuine
  native_conversation=true; adds bounded probe evidence and command binding.
  Final fixture text remains private; no publication. New fixed budget root
  entries use existing pre-import non-execution guards and file-bound importlib
  loading compatible with isolated Python. Shared validation bootstrap gains
  exclusive same_client_budget mode and preserves startup reporting.
- model_worker.py: same positive service, policy, grant, original dispatch and
  confirmation. After runtime acknowledgement the case accepts ONLY a fresh
  model_adapter_finish bound to actual prior delivery ID. New
  bridge/model_adapter_budget.py snapshots existing healthy runtime_delivered
  state/counters, then closes without new authorization or audit event. It makes
  no unexpired-grant claim and never calls _live or changes service TTL. The base
  model_service.py and all original audit verifiers receive no M05a changes.
- ModelBridgeRuntime.cs: positive branch bypasses wrong-model diagnostic for
  BUDGET only. Validates native original grant/full envelope/body and synthetic
  response, writes one response, verifies receipt and original runtime ack.
  RunBudget sends one probe control, accepts ONLY genuine completion shape, then
  requires child EOF/exit0 BEFORE terminal worker command. Extra model_request or
  trailing frame blocks. Worker EOF/exit0, host readback and dedicated audit
  admission precede evidence flags. No publish/model_prepare_final call.
- New ModelBudgetAdmission.cs independently checks exact child/terminal shapes
  and four positive ledger records, each envelope/metadata field, UTC order,
  attempt/operator/service/delivery bindings and actual request/response/output
  hashes. It does not truncate the old six-event validator. ProductFiles adds
  only two fixed M05a root names; canonical helpers remain under existing
  project_maya admission. Windows child/worker selection, consent, case/status
  reporting select HERMES_MODEL_BUDGET only.

HERMES_MODEL_BUDGET requires VALIDATION/MODEL/BRIDGE/CONSTRUCTION/IMPORT and excludes
REPLAY/REVOKE/EXPIRY/BODY/ROUTE/ATTEMPT/DENY/STATE/MEMORY. VALIDATION is inherited
for bounded startup capture, NOT permission to run wrong-model injection. Both
positive source schedule and compile exclusions are explicit.

## Exact Protocol

All frames retain integer v1, actual attempt and existing strict field/type bounds.
Worker command IDs remain unique via the original seen-ID set; coordinator checks
issue/dispatch/delivery/probe/finish IDs pairwise distinct. No caller-selected
operation, request content, path or fault switch is introduced.

1. Existing worker issue/grant, child begin, native request, dispatch/reply,
   runtime response/receipt, runtime confirmation/ack unchanged.
2. Coordinator to child: {v,type=model_adapter_probe,attempt,request_id}.
3. Child to coordinator: original {v,type=model_child_complete,attempt,text,report}.
   report schema maya.offline.model.budget.child.v1 retains original13 fields
   and adds probe_command_id and probe. Probe exact9 fields: case=M05a,
   boundary=adapter_consumed_budget, transport_attempts=2, model_requests=1,
   completed_exchanges=1, budget_rejections=1, same_used_client=true,
   request_sha256 and integer request_bytes. Original completed/construction/
   conversation/SDK closure/origins/distributions/config flags true, empty reason,
   real_inference=false, one request and two-to-eight client objects required.
4. Require child EOF/natural exit0. Coordinator to worker:
   {v,type=model_adapter_finish,attempt,request_id,delivery_command_id}.
5. Worker reply {v,type=model_adapter_complete,attempt,request_id,effects}.
   Effects exact9 fields: case=M05a,gateway_calls=2,dispatches=1,
   confirmed_runtime_releases=1,confirmed_operator_releases=0,real_inference=false,
   request_sha256,response_sha256,delivery_command_id. No denial fifth record.
6. Worker EOF/exit0, protected-file readback and EXACT four-record audit. Original
   egress_intent,dispatch_outcome,runtime_release_intent,runtime_delivery metadata
   sizes13/13/13/14 retained. Last record uses actual original runtime command ID.
   Nothing is prepared/published to operator. Final product success status:
   offline_model_adapter_budget_rejected_pending_independent_cleanup.

Worker waits within existing bounded topology; coordinator retains 30-second
overall/2000-ms RPC and child22-second budgets. The second local call does not
need an unexpired grant; first confirmation always records truthful prior effects.
Any later fault blocks acceptance while retaining prior dispatch/delivery1.

## Evidence And Limits

324 focused Python tests/1163 subtests pass across model transport/worker,
M02/M03a-d/M04a-c, startup, document bridge and protected-Python fixtures. Includes
17 new M05a tests and two mocked startup-main integrations. All four targeted
audit write/flush faults assert the actual selected fault location was reached.
Same used-client selection, closure, rebind, altered request, wrong adapter,
generic failure, case conflicts and exact metadata mutations are covered.

C# new BudgetFixtures:197 active assertions, ten paired earlier profiles192 each.
Ten conflicting/missing profile combinations intentionally fail compilation.
Earlier replay fixtures rerun:409 active/nine paired400 each. Counts overlap;
these are pure fixtures with explicit fixture Main, never product Main/setup.
Fixtures compile the new native schedule and exercise report/audit/path admission,
not real Windows pipe/process interleaving or native Hermes client ownership.
Full actual-profile payload ReadIndex remains an assembly gate.

One old workspace replay test used a fixed future timestamp2026-11-01, now no
longer necessarily future. Its test-only mutation now derives last-record time
plus one second; no native clock/service/deadline change. Frozen source copies
and packages untouched. Replay1 ZIP/EXE hashes freshly match its build record.
Broad repository collection was attempted but is not a complete test result:
five unrelated memory-plugin collection errors report missing jsonschema. No
dependency was installed; focused tests above complete independently. Existing
unknown pytest cache_dir warning remains. Generated tracked cache changes from
that collection were restored only for the seven paths clean at turn start.

Child probe/closure testimony is explicitly UNTRUSTED. Inert observer tests
corroborate the intended local guard; host EOF/frame checks and worker/ledger
evidence support the narrower no-additional-pipe-request/effects observation.
This cannot qualify hostile-child bypass prevention, general retries/fallback,
M05b or full containment. Native same-client compatibility remains untested.

## Next Gate

Review these changes before separate M05a-only assembly approval. A successor
would need explicit permission to OMIT model_replay_child_entry.py and
model_replay_worker_entry.py from the NEW payload only: the inactive names are
intentionally rejected by the BUDGET profile. Keep canonical replay helper and
shared support. No omission/assembly is authorized by source approval. Enumerate
actual changed/additional members, verify ALL actual-profile index members and
freeze dependency/config/security/grant/deadline equality before a runnable
package. Preserve Replay1 and all predecessors. Matching guest artifact, separate
one-run VM approval/fresh consent remain mandatory. M05b/M06-M09/M2, recovery,
inference, Gate A and production/containment qualification remain pending/open;
all false qualification flags unchanged.

# M05b Source Preparation Review

2026-11-01. User approved M05b-only product source preparation and inert tests.
Candidate0.2.1-offline-recreate.1/file0.2.1.14, profile HERMES_MODEL_RECREATE,
scope offline-hermes-recreated-client-budget-v1. No package or VM run approved.

## Implemented Sequence

Separate RecreatedClientBudgetMixin and RecreatePipeTransport leave the existing
M05a hook/observer and original ModelChannelClient budget guard unchanged.
Before native request cleanup, identify the actual used triple and its owner
thread, exact validated method/URL/headers/body and original copied factory
kwargs/reason/shared flag. Only chat_completion_request/shared=False is eligible.
The helper pin remains ff17762913d3e38aefa57fa22b56048f99d09fc18d189ab6441bf9c69433a76c.

Always delegate original native close once, including when diagnostic preflight
fails. Require old SDK/HTTP/transport closed. Then receive the existing bounded
probe control, require same open/bound/consumed adapter, and delegate once to the
existing factory with copied original kwargs and reason, shared=False.
Require one appended triple, retained earlier ownership, distinct new objects,
same SDK class, real httpx.Client, case-specific transport, same adapter by object
identity and max_retries0. No adapter mutation, rebind, new grant or second agent.

The new transport independently observes its first validated request and compares
it against the exact old snapshot. Ordinary transport validation precedes the
unchanged original exchange guard. Require exactly one consumed-budget rejection,
adapter requests1 and zero completed exchanges on the new transport.
Close the new triple directly, not recursively through the request-close hook.
Abort or any diagnostic/closure fault poisons admission without injecting an
exception into native retry/fallback logic. Genuine positive conversation must
still return, followed by normal agent/client shutdown and verified child exit0.

## Shared Integration And Evidence

Four existing Python entry/support modules gain an exclusive recreated_client_budget
mode: model_bridge.py, model_worker.py, model_child_entry.py and
model_validation_worker_entry.py. Worker reuses original finish_adapter_budget
guards and copies only its terminal case label to M05b; original service/audit
implementation remains unchanged. New fixed child/worker root bootstraps select
only M05b and retain Windows/version/isolation preconditions.

Five existing C# files change: ProtectedPython.cs, ModelBridgeRuntime.cs,
ProductFiles.cs, WindowsBridgeProcess.cs and WindowsIsolation.cs. Changes select
the fixed profile, consent/version/status, roots and admission, not security setup.
New ModelRecreateAdmission strictly checks separate child/effects evidence and
delegates the identical four-record ledger to the unchanged M05a audit validator.
Existing RunBudget schedule is reused with explicit case-specific admission:
runtime confirmation -> probe -> positive child completion -> child EOF/exit0 ->
terminal worker finish/complete -> worker EOF/exit0 -> protected audit readback.
Any additional model_request is an invalid next child frame. No publication.
Compile guard requires VALIDATION/MODEL topology and excludes other fixed cases.

Child schema maya.offline.model.recreate.child.v1 has exactly16 outer keys:
schema, attempt, completed, native_constructor, native_conversation, sdk_closed,
origins_verified, distributions_verified, config_unchanged, model_requests,
client_objects, real_inference, reason_type, probe_command_id, probe, probe_lifecycle.
client_objects must be integer3..8, not2 (primary, used request, recreated triple).
Probe has exactly10 keys: case=M05b, boundary=adapter_consumed_budget,
transport_attempts2, model_requests1, completed_exchanges1, budget_rejections1,
distinct_new_clients=true, same_consumed_adapter=true, request_sha256, request_bytes.
Lifecycle has exactly13 keys: schema=maya.model.recreate.lifecycle.v1, stage=complete,
failure_stage='', armed=true, hook_calls1, close_delegations1, owner_thread_verified,
used_client_verified, native_close_verified, probe_after_native_close,
new_clients_distinct, same_adapter_verified, new_client_close_verified (all true).
No raw identities, settings, headers, body, lease or exception messages disclosed.

Effects retain gateway2/dispatch1/runtime1/publication0, additional pipe/gateway/
dispatch/runtime0. Audit EXACTLY egress_intent, dispatch_outcome,
runtime_release_intent, runtime_delivery, with existing bindings/hashes.
No fifth worker denial event or service-unexpired-lease assertion. Child
identity/local-guard observations remain untrusted; trusted host evidence supports
the narrower no-additional-pipe/effects claim, not hostile Python bypass prevention.

## Inert Results

359 focused Python tests/1303 subtests pass, including20 M05b tests/130 subtests.
Controls cover old/new close failures, owner/client identity, malformed control,
EOF, abort during control read without a held diagnostic lock, changed request,
replacement adapter/reused client, shared shutdown, factory failure/cap,
duplicate hook/rearm/rebind, exact audit mutation/order/write/flush faults and
terminal/compile-mode binding. Actual pinned Hermes/SDK was not executed.

C#:355 active M05b assertions and11 paired profiles346 each pass.
M05a regression219 plus ten older paired profiles214 each pass.
15 invalid M05b profile combinations are compile-rejected.
Shared bridge154, startup reporting874, protected Python231 and M01 audit178 pass.
Reader/deadline/cleanup fixture uses an explicit fixture Main, not product Main.
See local .codex-build/maya-model-recreate-source-20261101-1 recipes/evidence.
The existing pytest cache_dir warning remains; not a full-repository test claim.

## Delta, Limits And Next Gate

Frozen Budget3 ZIP/EXE and298 frozen sources remain intact. Source delta is nine
replacements (four Python/five C#) and four additions (Python observer, C# admission,
two roots); original M05a helper/admission, reader, service, grants and audits stay.
No runtime/dependency/config/native-pin/security/deadline changes.

Future payload plan: five replacements (model-contract.json, model_child_entry.py,
model_validation_worker_entry.py, project_maya/bridge/model_worker.py and
project_maya/hermes_plugins/model_bridge.py); three additions (model_recreate roots
and project_maya/hermes_plugins/model_recreate.py).
Actual M05b admission intentionally rejects the two inactive model_budget root
bootstraps still present in Budget3. A future successor would require explicit
assembly approval INCLUDING omission of exactly model_budget_child_entry.py and
model_budget_worker_entry.py FROM THE NEW PAYLOAD ONLY. No omissions approved here.
Preserve canonical model_budget.py (still required), canonical helpers, frozen
Budget3 and all predecessors. Do not widen admission to retain inactive roots.
Full actual-profile inventory/resource/freeze verification remains an assembly gate.

No product/native/bundled-runtime/security/VM execution, package, inference,
credentials/spending, retry/recovery, M06-M09/M2 or qualification occurred.
Native lifecycle timing/compatibility remains unverified. Obtain source review
acceptance and separate exact assembly/omission approval next; later matching
guest artifact one-run approval/fresh consent remain mandatory. Gate A stays open;
all production/containment/independent-cleanup flags remain false.

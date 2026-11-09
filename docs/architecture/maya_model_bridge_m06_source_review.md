# M06 Source Preparation Review

2026-11-01. Approved M06-only source preparation/inert tests complete.
Candidate0.2.1-offline-output-denial.1/file0.2.1.15; fixed
HERMES_MODEL_OUTPUT_DENY profile, scope offline-hermes-runtime-output-denial-v1.
No product/native/bundled-runtime/VM execution or package assembly.

## Implementation

Original OfflineModelBridge._authorize gains only the approved read-only
runtime_output_gateway_denied flag, initialized false. It is set only for actual
AuthorizationResult DENY/governance.no_matching_rule with no constraints/redactions,
model.output, exact runtime:<bound attempt> destination and dispatched phase.
The original gateway call, decision predicate, policy semantics, exception,
liveness, dispatch and release behavior remain unchanged. _fail still raises
ModelDenied(dispatch_attempted); M06 requires uncertain=true, never resets it.

New model_output_denial.py verifies closed/non-poisoned audit, named decision,
original request/dispatch/response validation, exact response oracle, gateway2,
dispatch1 and every prepared/confirmed release0. Returned evidence contains no
raw response: exactly18 fields as frozen in maya_model_bridge_m06_tests.json.
Generic exception, wrong deny reason, constraints/redactions, egress denial,
malformed request, invalid response or early expiry cannot pass.

Worker has an exclusive deny_runtime_output mode and exact fixed egress-only
policy. It calls original prepare_runtime and, only after exact evidence admission,
returns model_runtime_output_denied with effects. No model_dispatch_reply/
model_response, release intent or delivery confirmation follows. Service closes
normally through original failure handling. Existing worker modes are unchanged.
Fixed guarded child/worker roots choose only M06. Shared startup diagnostic and
child support accept the new exclusive boolean; no caller-selected production mode.

A dedicated RuntimeOutputDenialChannelClient recognizes only exact M06 denial
control. Real pinned Hermes still constructs and sends one native request. Child
reports native_conversation=false, observed denial, closure/origins/config/
distribution checks and one request. No fabricated model output or final response.
No M05 hook, recreation, retry/fallback or extra client behavior is enabled.

## C# Integration And Oracle

New ModelOutputDenialAdmission has separate 18-field effects admission, M06
14-field child schema admission and independent exact THREE-record audit check.
It derives deterministic synthetic response bytes from the trusted host fixture
text, strictly MAYA_OFFLINE_MODEL_OK:<32 lowercase hex>. The C# oracle matches
Python SyntheticModel.wire_reply via inert vectors; denied raw response bytes
never cross from worker to coordinator or child. Existing audit verifiers stay.

Six existing C# files select the fixed profile/version/consent, entries and
coordinator branch: ProtectedPython, ProductFiles, ModelBridgeRuntime,
ModelHostFiles, WindowsBridgeProcess and WindowsIsolation. ProductFiles admits
M06 roots only under its profile. Compile guard excludes every other fixed model
case and requires VALIDATION/MODEL/BRIDGE topology. No path predicate widening.

ModelHostFiles.Rules(actor) extracts the existing pure policy-array emission so
fixtures can verify actual compile-profile policy without invoking filesystem/
label/security setup. Prepare still supplies actual windows:<operator SID>.
M06 has only original egress rule, M02 only output rule, earlier profiles both;
all actor/target/operation fields remain identical.

Coordinator verifies original native body/envelope, M06 evidence and expected
response hash/count, then sends only a denial control. It records dispatch1/
uncertainty before any control write and tracks denial_control_pipe_writes
SEPARATELY from runtime model-response writes (always0). Failed/partial control
write does not fabricate a zero dispatch. Child completion, EOF/natural exit0,
worker EOF/natural exit0 and protected ledger readback precede success admission.
No model_prepare_final/publication path exists in this branch.

## Frozen Evidence Contract

Worker denial control: exactly v,type=model_runtime_output_denied,attempt,
request_id (original dispatch command),effects. No body/lease/response frame.
Effects: case=M06,boundary=gateway_runtime_output,request_validated=true,
response_validated=true,gateway_denied=true,gateway_calls2,dispatch_attempted=true,
dispatches1,prepared_runtime_releases0,confirmed_runtime_releases0,
prepared_operator_releases0,confirmed_operator_releases0,real_inference=false,
uncertain=true,request_sha256/request_bytes,response_sha256/response_bytes.

Child control: exactly v1,type=model_denied,attempt,seq1,case=M06,
reason=gateway_runtime_output_denied. Child completion: v1,
type=model_child_denied,attempt,report. Report schema
maya.offline.model.output_denial.child.v1 has14 keys, matching prior denial
shape but NOT M02 schema. native_conversation=false, real_inference=false,
reason_type='', model_requests1, integer client_objects2..8; all completed/
constructor/SDK/origin/distribution/config/denial_observed flags true.

Audit exactly egress_intent/dispatch_outcome/denied, existing record schemas and
reason codes. First two provider/model.egress/infer allowed; final runtime:
<actual attempt>/model.output/disclose denied. Response hash/bytes empty/0 first,
then exact validated oracle metadata for both subsequent records. Dispatches
0/1/1, request/output hashes unchanged, actual actor/attempt/service request ID
and valid nondecreasing UTC timestamps. No release intent/delivery/operator event.

## Inert Verification

376 focused Python tests/1440 subtests pass;17 M06 tests/137 subtests included.
M06 controls cover exact denial/positive reference, response oracle, wrong/
conflicting policies/modes, bad request/control, generic/incorrect gateway denial,
wrong destination/phase, early expiry/egress denial/invalid response, all audit
record/metadata mutations, count/order and three write/flush locations.
Additional faults preserve prior dispatch/uncertainty when auditing or denial
control send fails. Inert BytesIO initially lacked fileno and correctly failed
before dispatch; fixed the fixture, not production audit. A source-string
control initially matched the model_response_validated report key; tightened it
to exact quoted protocol literals, without changing acceptance code.

C#:341 active M06 assertions; twelve paired older profiles pass (eleven336 each,
M02 profile332 due its one-rule policy).16 invalid compile combinations rejected.
Prior M05b355/eleven paired346 and M05a219/ten paired214 regressions pass.
Shared bridge154/reporting874/protected-Python231/M01-audit178 pass.
Corrected reader163 assertions/13 cases pass under M06 profile.
All executables used explicit fixture Main only; no product Main or Windows
security provisioning executed. Native EOF/exit/cleanup behavior remains gated,
not experimentally proven by source-string or admission fixtures.
Existing pytest cache_dir warning only; not a full-repository test claim.

Local recipes/receipt: .codex-build/maya-model-output-denial-source-20261101-1.
Frozen Recreate1 ZIP/EXE and307 frozen source/recipe files verified intact.
Exact product delta:11 replacements (five Python/six C#), four additions
(output-denial helper, C# admission and two guarded roots), no source removals.
Source receipt pins current product files and two new fixtures.

## Assembly Gate And Limits

No runnable M06 package exists. Future payload plan: SIX replacements:
model-contract.json, model_child_entry.py, model_validation_worker_entry.py,
project_maya/bridge/model_service.py, project_maya/bridge/model_worker.py,
project_maya/hermes_plugins/model_bridge.py. THREE additions:
project_maya/bridge/model_output_denial.py, model_output_deny_child_entry.py,
model_output_deny_worker_entry.py. Existing inactive Recreate1 root entries
conflict with intentional actual-profile admission. Separate assembly approval
MUST explicitly include omitting only model_recreate_child_entry.py and
model_recreate_worker_entry.py FROM THE NEW SUCCESSOR PAYLOAD. No omission
approved by source preparation. Retain canonical model_recreate/model_budget
helpers and all frozen packages. Never widen admission to retain inactive roots.
Expected6783 members requires actual inventory/resource/freeze checks at assembly.

TTL2000ms, all deadlines/byte bounds, dependencies/config/native pins, WFP/
capabilities/permissions/jobs stay unchanged. No service-unexpired-lease claim.
M06 denies runtime output, NOT operator-only policy. No inference, customer data/
credentials/spending, retry/recovery, M07-M09/M2, qualification or Gate A closure.
Next: separate exact assembly/omission approval, then artifact-specific one-run
VM approval/fresh consent. All original qualification flags remain false.

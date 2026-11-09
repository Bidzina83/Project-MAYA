# M07a Source Preparation Review

2026-11-02. Approved M07a-only product source preparation/inert tests complete.
Candidate0.2.1-offline-malformed.1/file0.2.1.16, HERMES_MODEL_MALFORMED,
scope offline-hermes-response-json-rejection-v1. No package or native run.
M07b/M07c remain unimplemented.

## Fixed Fault And Original Authority

OfflineModelBridge now constructs its provider through _new_provider; ordinary
default still returns SyntheticModel(fixture_text). Dedicated MalformedJSONBridge
overrides only that construction factory. Its exact MalformedJSONProvider inherits
the original text/wire_reply behavior and calls original dispatch once before
returning the fixed one-byte opening brace. No live _provider reassignment, caller
body/class/URL, wheel change, arbitrary switch or replaced validation engine.
The original canonical expected bytes remain unchanged; fixtures verify inherited
wire_reply identity and exact oracle match before/after dispatch.

The original bytes/length1..4096 guard still runs first. Only when ORIGINAL
protocol.decode raises ProtocolError does the approved read-only observation set
response_failure_stage=response_json, bounded returned-byte count and SHA256.
Hashing occurs after the size guard, at most4096 bytes. Original exception reraises
to original _fail; no raw response retained in _response or diagnostic fields.
No M07b size-specific or M07c allowlist-specific acceptance path was implemented.
Authorization/allowlist/liveness/release predicates, original uncertainty and
dispatch counter remain authoritative. Fault does not poison the expected oracle.

New model_malformed_response.py provides exact case-bound evidence and independent
TWO-record audit admission. Require exact service/provider types, closed service,
nonfailed required audit, request validated/phase admitted/provider destination,
one gateway call, one original dispatch, original uncertain=true and matching
one-byte JSON failure observation. _response must remain None; canonical expected
response must match the independent host oracle. All releases0, no gateway-denial
flags. Wrong bytes/stage/count/digest/provider exception/policy/expiry/audit failure
cannot satisfy this negative case.

## Product Integration And Protocol

Five existing Python files change: model_service.py, model_worker.py,
hermes_plugins/model_bridge.py and two shared child/worker support entries.
Worker validates unchanged BOTH-rule policy, selects fixed service at construction
and invokes ORIGINAL prepare_runtime. Only exact evidence admits
model_response_json_rejected. It returns/closes naturally; no raw response frame
or further protected action. Fixed guarded M07a roots select one exclusive boolean.
A dedicated child channel recognizes only case=M07a/reason=response_json_rejected.
Real native constructor/one SDK request remains; expected rejection and ordinary
closure mean native_conversation=false, never a fabricated positive response.

Five existing C# files change: ProtectedPython.cs, ProductFiles.cs,
ModelBridgeRuntime.cs, WindowsBridgeProcess.cs and WindowsIsolation.cs; new
ModelMalformedAdmission.cs. Separate fixed compile profile/version/consent,
root paths, case/child/effects admission and status. Original model policies/
ModelHostFiles.Rules remain unchanged. Compile guard excludes other fixed cases
and requires VALIDATION/MODEL/BRIDGE topology. Inactive roots are not admitted.

Worker control has exactly v,type=model_response_json_rejected,attempt,
request_id=original dispatch command,effects. Effects has exactly25 fields:
case=M07a,boundary=response_json,request_validated=true,egress_allowed=true,
gateway_calls1,dispatch_attempted=true,dispatches1,response_validated=false,
validation_stage=response_json,observed_response_sha256=SHA256(opening brace),
observed_response_bytes1,response_sha256='',response_bytes0,
expected_response_sha256/expected_response_bytes (canonical host oracle),
prepared_runtime_releases0,confirmed_runtime_releases0,
prepared_operator_releases0,confirmed_operator_releases0,real_inference=false,
uncertain=true,request_sha256/request_bytes,egress_gateway_denied=false,
runtime_output_gateway_denied=false. Raw fault or normal response is not sent.

Child control: exactly v1,type=model_denied,attempt,seq1,case=M07a,
reason=response_json_rejected. Completion v1,type=model_child_denied,attempt,
report. Schema maya.offline.model.malformed_response.child.v1 has14 keys,
native_conversation/real_inference false, reason_type='', one request, integer
client_objects2..8, other constructor/completion/closure/origin/distribution/
config/denial-observed flags true. M02/M06 schema cannot substitute.

Coordinator verifies original body/envelope and effects against trusted request,
fixed fault digest/count and canonical normal-response oracle. It records truthful
dispatch1/uncertainty BEFORE denial-control write, separately counts that control
(not a model-response delivery) and never prepares/publishes final output.
Child/worker EOF/natural exits0, protected file checks and independent audit
readback precede success flags. Raw JSON failures or child testimony alone cannot
pass. No new response bytes are exposed to Hermes.

## Exact Audit And Evidence Limits

Exactly egress_intent/denied, allow then deny, both provider destination,
model.egress/infer, dispatches0/1. Validated response metadata stays empty hash/
bytes0 in BOTH records. Bind actual actor/attempt/service request/route/model/
endpoint, original request digest/count, canonical expected output hash and
nondecreasing valid UTC timestamps. No validated dispatch_outcome or release event.
Denied event is service response rejection, NOT gateway egress denial.
Separate observed-fault digest/count must not be relabeled validated response.

Retain original uncertain=true after attempted dispatch even if audit/control
delivery fails. No invented zero effects, successful delivery or recovery.
Child report remains untrusted; native process/containment/cleanup behavior is
not proven by inert schema/codec/source-order tests.

## Inert Results

388 focused Python tests/1529 subtests pass;12 M07a tests/89 subtests included.
Default factory/positive response unchanged, fixed fault consumes original dispatch,
canonical expected bytes preserved, exact named parser failure, wrong fault bytes/
types/provider throw, request/egress/expiry failures, forged observation/release
states, malformed denial controls, audit field/count/order/write/flush faults and
control send failure are covered. Native Hermes/SDK was not executed.
Inert fixtures deliberately inject negative provider faults only in memory; no
such monkeypatch is installed in product or bundled runtime.

C#:311 active M07a assertions and13 older profile pairs pass (eleven300 each,
M06/M02 profiles296 each due one-rule policies).17 invalid compile combinations
rejected. Earlier M06 fixtures341 active/older profile pairs still pass.
Shared bridge154/reporting874/protected Python231/M01 audit178 pass.
Reader163 assertions/13 cases pass under M07a. Explicit fixture Main only.

An earlier prior-regression recipe pointed to a missing local M06 vector; corrected
it to read the frozen M06 vector, without changing product predicates or frozen
evidence. Full-source edit preparation also hit a tool output truncation; the
patch was rejected, then reapplied from an untruncated read. Source delta checks
confirm only intended files changed. Existing pytest cache_dir warning remains;
this is not a full-repository test claim.

Local recipes/receipt: .codex-build/maya-model-malformed-source-20261102-1.
Frozen M06 ZIP/EXE and322 frozen source/recipe files verified intact.
Exact product delta:10 replacements (five Python/five C#), four additions
(new helper, C# admission, two fixed roots), no source removal. Receipt pins
current product sources and both new fixtures. No runnable product assembled.

## Next Gate

Future payload plan: SIX replacements (model-contract.json, model_child_entry.py,
model_validation_worker_entry.py, project_maya/bridge/model_service.py,
project_maya/bridge/model_worker.py, project_maya/hermes_plugins/model_bridge.py);
THREE additions (project_maya/bridge/model_malformed_response.py,
model_malformed_child_entry.py, model_malformed_worker_entry.py).
M06's inactive root entries conflict with actual M07a admission. Separate assembly
approval MUST explicitly include ONLY omitting model_output_deny_child_entry.py
and model_output_deny_worker_entry.py FROM NEW successor. No omissions approved
by source preparation. Retain canonical model_output_denial.py (oracle dependency),
all other canonical helpers, M06/all frozen predecessors. Never widen admission
to retain inactive roots. Expected6784-member full actual-profile/resource/
archive/source-freeze verification remains required during assembly.

No package, product/native/bundled-runtime/security/VM run, inference, credential/
customer-data/spending, dependency/grant/security/TTL/deadline/bound change,
retry/fallback/recovery, M07b/c/M08/M09/M2 or qualification. Native scheduling/
compatibility unverified. Review before separate exact assembly/omission approval,
then matching-artifact one-run VM approval and fresh consent. Gate A/all false
qualification flags remain unchanged.

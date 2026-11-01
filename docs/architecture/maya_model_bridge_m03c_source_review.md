# M03c Attempt-Binding Source Review

The user subsequently approved the exact two successor-only root-bootstrap
omissions in maya_model_bridge_m03c_package.md. That packaging hold is resolved;
source/security/dependency/deadline predicates remain unchanged. Separate native
artifact approval and fresh consent are still required. Earlier hold/source
statements below are historical, not permission to retain rejected entries.

Subsequent decision: separate M03c assembly was approved, but read-only packaging
preflight found that retaining the two inactive M03b root bootstraps contradicts
M03c's intentional payload allowlist. ReadIndex validates every member. See
maya_model_bridge_m03c_package.md for the HOLD and exact two successor-only
omissions proposed for separate approval. No payload/EXE/ZIP was built and no
product run occurred. The source-milestone record below remains intact; its
preserve-all-entry assembly assumption is not sufficient to produce a valid bundle.

2026-10-31: after the M03b result and scoped manual cleanup, the user requested
proceeding with M03c. This authorizes source/inert preparation only. Candidate
0.2.1-offline-attempt.1, scope offline-hermes-attempt-validation-v1. No product
payload/launcher/ZIP assembly, native Hermes/SDK run, security/VM provisioning,
network, credential access or inference. Preserve Route 1 and all predecessors.
See maya_offline_model_route_1_outcome.md for M03b provenance and remaining limits.

## Exact Mutation And Authority

Fixed HERMES_MODEL_ATTEMPT requires HERMES_MODEL_VALIDATION and excludes
HERMES_MODEL_ROUTE (and, through existing guards, MODEL_DENY/STATE/MEMORY).
MODEL/BRIDGE/CONSTRUCTION/IMPORT remain required. The fixed native entries are
model_attempt_child_entry.py and model_attempt_worker_entry.py. Future package
contract must select cases=[M03c]. No case selector from child, environment,
editable policy or free-form CLI. Existing positive gateway rules remain present.

Actual Windows token, operator SID, host binding, attempt directory, private
channel, outer coordinator command attempt, service/command IDs and issued grant
stay unchanged. Real Hermes/SDK child still sends its valid original envelope
and exact body, with all adapter/factory checks enabled. Coordinator checks its
body against the protected host oracle and complete envelope against the actual
host-issued grant. Grant v/type/attempt/route/sequence/TTL/body digest are checked.

Only a COPY of that verified request's attempt field changes. Deterministic rule:
if the first hex digit is 0, change it to 1; otherwise change it to 0. All other
31 lowercase hex digits are identical. The new value is valid 32-digit lowercase
hex and necessarily different, never a real host principal or replacement host
binding. Body bytes/model/route/lease/sequence/method/path remain identical. The
original host file and admission digest are never rebound to the mutant.

This tests worker rejection of a TRUSTED coordinator injection, not Windows
actor impersonation, stolen grants, hostile-child adapter bypass or containment.
Changing the outer command's actual attempt is a protocol error, not this test.

## Worker Boundary And Fail-Closed Evidence

OfflineModelBridge separates RequestAttemptDenied from generic envelope failure.
Its accepted input set is unchanged. The issued/live admission, exact keys,
v/type/sequence/method/path/channel/lease/body-string checks still precede it.
Only when a mismatched request attempt has the correct route does the service
record envelope_attempt_context_validated=true. Identity/full-envelope/request
admission remain false. The named stage is request_attempt, before body admission
or any gateway call. A simultaneous wrong route cannot satisfy this marker.
M03a model and M03b route predicates keep their existing semantics.

WrongAttemptBridge reconstructs the exact mutant from its trusted binding,
original body and issued lease, never child testimony. Requires one bound actual
coordinator command ID. Missing/extra fields, a different valid mutant, bool v/seq,
second mutation, invalid channel, wrong outer command, unissued/expired/revoked/
closed grant, unknown exception or wrong boundary cannot produce accepted evidence.
Named attempt context, no accepted identity/envelope/body, zero gateway calls,
no gateway-policy denial, zero attempted/actual dispatch and zero prepared/
confirmed runtime/operator releases are mandatory. Audit must be healthy and
admission live/unrevoked. RequiredAudit short/write/flush/fsync failure poisons
the ledger; it is never reopened or replaced. No generic failure is a pass.

After exactly one durable event the closed service returns model_attempt_rejected
with exactly v=1, actual outer attempt, actual coordinator request_id and exact
evidence metadata. The worker returns normally, accepting no second operation.

## Projection And Audit Contract

Body hashes and lengths deliberately remain equal. Both languages independently
construct this ASCII LF-delimited field projection, with a final LF:

1. maya.model.attempt_projection.v1
2. 1
3. model_request
4. Original actual attempt OR exact derived request attempt
5. maya.offline.model.v1
6. SHA256 of ASCII host-issued lease
7. 1
8. POST
9. /v1/chat/completions
10. SHA256 of original body bytes
11. Decimal body length

The hashes bind this explicitly VERSIONED FIELD PROJECTION, not serializer-specific
raw pipe JSON. Authority comes from actual host state, not the projection or the
untrusted request. Body/canary/lease are not emitted. M03b projection is not
relabelled or reused as M03c proof. Python/C# fixtures compare full native-oracle
projection bytes and complete metadata; both mutation branches/all hex digits
are checked without importing Hermes or the SDK.

Exactly one existing newline-terminated AuditRecord envelope: schema_version
integer 1, valid UTC timestamp, event_type=model_bridge.attempt_rejected,
reason_code=model_bridge.wrong_attempt, decision=deny, actual windows:<operator SID>,
capability=model.egress, target=model:maya-offline-fixture, operation=infer,
data_classification=internal-synthetic, idempotency_key=null. Exact metadata keys:

- attempt, request_id, coordinator_request_id: ACTUAL host attempt/service/command.
- route=maya.offline.model.v1, endpoint=https://maya-offline-model.invalid/v1/chat/completions,
  model=maya-offline-wire-v1, destination=provider.
- request_sha256/request_bytes, mutated_request_sha256/mutated_request_bytes:
  identical original body identity.
- response_sha256="", response_bytes="0", output_sha256 binds synthetic fixture.
- dispatches="0", real_inference="false".
- validation_schema=maya.model.attempt_validation.v1, case=M03c, stage=request_attempt.
- projection_schema=maya.model.attempt_projection.v1, original_projection_sha256,
  original_projection_bytes, mutated_projection_sha256, mutated_projection_bytes.
- observed_attempt: exact fixed different request attempt, not authority.
- gateway_calls="0", dispatch_attempted="false", runtime_prepared/runtime_released/
  operator_prepared/operator_released all "0".

Hashes are lowercase SHA256, counters/sizes exact decimal strings. Reject every
absent/extra/rebound field, duplicate/truncated record, boolean schema version,
invalid/non-UTC timestamp, altered actual actor/grant/ID. Python verify_attempt_audit
and C# ModelValidationAdmission.Audit(...,route:false,attempt:true) independently
admit the exact predicate; selecting both cases throws. Existing default/M03b
audit predicates remain unchanged. Public reports bind the mutated attempt as
model_observed_attempt, never replace top-level attempt_id or operator_sid.

## Child Closure And Acceptance

After exact evidence admission, send only v=1,type=model_denied, ACTUAL attempt,
seq=1,case=M03c,reason=request_attempt_rejected. WrongAttemptChannelClient recognizes
only this fixed case/reason; M02/M03a/M03b replies cannot satisfy it. It raises,
never returns model content. Native lifecycle accepts only the expected SDK
connection error after that exact control, or Hermes' own error result, not an
arbitrary exception. Explicitly untrusted report schema
maya.offline.model.attempt_validation.child.v1 requires completed/constructor/
SDK closure/origins/distributions/config/denial true, native_conversation and
real_inference false, request count 1, clients 2-8 and empty reason_type.

Require two-sided EOF, natural child/worker exit 0, bounded empty stderr,
protected-host recheck and independent exact ledger readback. Only then set
model_attempt_evidence_matches alongside the existing model/validation evidence
flags. Fresh beacon, worker stop and successful product cleanup remain required
for offline_model_attempt_rejected_pending_independent_cleanup. The shared
startup_status remains offline_model_validation_child_completed; the case/stage/
final status distinguish M03c. No publication callback or model-response write.
Generic failure, timeout, missing audit, diagnostic stderr, abnormal exit or
uncertain effects remains blocked. No qualification flag changes.

## Source Scope And Unchanged Boundaries

New model_attempt_validation.py implements fixed derivation/service/projection/
audit checks, reusing only the existing structured original route_request helper.
New ModelAttemptAdmission.cs independently reconstructs the native original and
mutant, body identity and metadata. model_service adds the attempt-stage observation;
model_worker adds one exclusive fixed mode and terminal reply; model_bridge adds
one fixed negative adapter. Shared child/worker entries add explicit trusted
wrong_attempt arguments; no CLI/environment selector or live runtime patch.
The fixed worker entry reuses the same import-safe startup reporter.

Windows coordinator reuses existing grant/envelope verification and validation
closure/audit flow; selectors and profile-only payload allowlists admit the two
new entries. ProtectedPython adds guarded version/case/consent/status. No new
policy engine, authority source, provider transport, recovery or test supervisor.
Future assembly must enumerate exact product replacements/additions against
frozen Route 1; do not change unrelated payload/config/runtime/dependency bytes.

Same pinned Python 3.13.14, Hermes and 64 distributions, no downloads. Same
ordinary AppContainer, zero capabilities, six WFP denies, reduced tokens, jobs,
child-process block, inherited pipes, four host files and ACLs/labels. Worker is
trusted OUTSIDE child containment; shared All Application Packages exposure and
profile deletion gap remain. No listener, loopback/registry grant, service,
account, credentials, customer data, inference or charge. Ready/RPC/partial frame
5000/2000/1000 ms; child 22/30 seconds; frame 8192, cumulative channel/audit
131072, request/response/stderr 4096, report 65536, output 1024, diagnostic parser
256 bytes. Failure-only diagnostics remain optional, not success evidence.

## Verification And Next Gate

279 Python tests/550 subtests pass: 19 new attempt-case tests and two mocked
startup-main tests, plus previous suite. Existing unknown-cache_dir warning remains.
Only ordinary-host fixtures, with normal temporary-directory access, ran.
New C# M03c profile: 195 managed assertions; five paired profiles 186 each.
Earlier M03b: 177/paired 168; M03a: 108/paired 101; M02: 117/paired 113;
startup diagnostics: 874. Prior component/bridge/model-audit checks remain part
of regression verification. Counts overlap and are not native runs.

Coverage includes fresh valid positive dispatch, exact negative/no gateway,
all hex digit mutation branches, wrong outer attempt, nonfixed mutant, second
mutation/missing fields, channel/grant failures, expiry/revocation, rebound audit
and command/lease/actor, forged denial, audit faults, generic exceptions, nonzero
effect/wrong-stage rejection and fixed-entry guards. Existing channel fixtures
cover EOF/partial framing; no native timing/pipe behavior is inferred.

Source/inert preparation is complete, not a runnable package. Review this exact
contract/impact before separate assembly approval; later require exact-artifact
one-run VM approval and fresh consent. No M03c native run, later case, retry,
recovery or inference is approved. M03d/M04-M09/M2, Gate A, containment, profile
deletion and production remain pending/unqualified; all qualification flags false.

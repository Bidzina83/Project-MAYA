# M03b Wrong-Route Source Review

Subsequent decision: the user approved separate offline M03b assembly. See
maya_model_bridge_m03b_package.md. Source-milestone statements below remain
historical; product/VM execution still needs separate exact-artifact approval.

2026-10-31: the user requested proceeding with M03b after Validation 2 and its
scoped cleanup. This record covers source preparation and inert verification
only. Candidate 0.2.1-offline-route.1, scope offline-hermes-route-validation-v1.
No product payload/launcher package or ZIP assembled, no product/native Hermes/
SDK run, guest access, security provisioning, network or inference performed.
Frozen predecessors remain intact. See maya_offline_model_validation_2_outcome.md
for the completed M03a attempt, its provenance and unresolved limitations.

## Fixed Contract

HERMES_MODEL_ROUTE requires HERMES_MODEL_VALIDATION, which still requires
MODEL/BRIDGE/CONSTRUCTION/IMPORT and excludes MODEL_DENY, STATE and MEMORY.
Fixed model_route_child_entry.py and model_route_worker_entry.py are selected
before M03a selectors. Future model-contract.json must bind cases=[M03b]. No
mutation selector comes from the child, environment, CLI or editable policy.
Existing gateway and both positive M01 rules remain; the M02 policy is rejected.

The real child keeps all body/route/grant checks enabled and sends its original
valid synthetic request. Coordinator compares native body with the protected
host oracle, then independently checks the complete envelope against the actual
host-issued grant: v/type/attempt/route/lease/seq/method/path/body. The grant itself
must have the expected type/attempt/route/sequence/TTL/request hash. Only a copied
envelope's route changes from maya.offline.model.v1 to maya.offline.model.v0.
Model, body bytes, actual SID, attempt, lease, channel, method/path and sequence
are unchanged. Host request.json and child admission digest stay original.

This proves only worker rejection of the fixed TRUSTED coordinator injection,
not that a hostile child bypassed its adapter, changed a trusted actor, or escaped
Windows containment. No positive gateway denial can substitute for validation.

## Worker Boundary

OfflineModelBridge separates RequestRouteDenied from its generic envelope failure
without changing its accepted request set. Live admission and every other
envelope binding are checked first; envelope_identity_validated becomes true.
Only the route mismatch sets validation_stage=request_route. Full
envelope_validated and request_validated remain false; body admission and gateway
authorization have not happened. Existing M03a request_model semantics remain.

WrongRouteBridge independently reconstructs every field from its host binding,
issued lease and original expected body, accepting only the exact fixed mutant.
Missing/extra fields, bool v/seq, second mutation, wrong channel, unissued/closed/
expired/revoked admission, generic error or missing coordinator command binding
cannot produce accepted evidence. The event requires the named route stage,
other-envelope validation, zero gateway calls, no attempted/actual dispatch,
no gateway-policy denial and zero prepared/confirmed releases. RequiredAudit
must be healthy; write/short-write/flush/fsync failures poison it permanently.

After durable audit the worker closes and sends exactly v=1,
type=model_route_rejected, actual attempt, actual coordinator request_id and
evidence. No model response, second command, retry or reopened ledger follows.

## Evidence And Audit

The original and mutant body digests are deliberately IDENTICAL. To bind the
changed envelope without publishing a raw lease or body, both languages construct
the same bounded ASCII projection with LF separators and trailing LF, in order:

1. maya.model.route_projection.v1
2. 1 (protocol version)
3. model_request
4. Actual attempt
5. Original or mutated route
6. SHA256 of the ASCII host-issued lease
7. 1 (sequence)
8. POST
9. /v1/chat/completions
10. SHA256 of original body bytes
11. Decimal body byte length

This is explicitly a versioned FIELD PROJECTION, not a hash of serializer-dependent
raw pipe JSON. Both sides independently reconstruct it from host state, not a
child-supplied digest. Fixture comparisons verify full projection bytes and the
complete evidence map across Python/C# on the full pure native-request oracle.

Exactly one newline-terminated existing AuditRecord envelope, schema_version
integer 1, valid UTC timestamp, event_type=model_bridge.route_rejected,
decision=deny, reason_code=model_bridge.wrong_route, actual windows:<operator SID>,
capability=model.egress, target=model:maya-offline-fixture, operation=infer,
classification internal-synthetic, idempotency_key=null. Exact metadata keys:

- attempt, request_id, coordinator_request_id: actual attempt/service/command IDs.
- route=maya.offline.model.v1, endpoint=https://maya-offline-model.invalid/v1/chat/completions,
  model=maya-offline-wire-v1, destination=provider.
- request_sha256/request_bytes and mutated_request_sha256/mutated_request_bytes:
  same original body hash/length.
- response_sha256="", response_bytes="0", output_sha256 binds synthetic fixture.
- dispatches="0", real_inference="false".
- validation_schema=maya.model.route_validation.v1, case=M03b, stage=request_route.
- projection_schema=maya.model.route_projection.v1, original_projection_sha256,
  original_projection_bytes, mutated_projection_sha256, mutated_projection_bytes.
- observed_route=maya.offline.model.v0, gateway_calls="0", dispatch_attempted="false".
- runtime_prepared/runtime_released/operator_prepared/operator_released all "0".

Hashes are lowercase SHA256; sizes/counters are exact decimal strings. No absent,
extra or rebound fields, malformed timestamp, duplicate/truncated record or boolean
schema version is accepted. Python verify_route_audit and C# ModelValidationAdmission
with its explicit trusted route argument independently validate the predicate.
M03a's default event predicate remains unchanged. Raw body, canary, lease, paths
and exception text are not emitted in this metadata or public diagnostics.

## Closure And Acceptance

Coordinator validates exact evidence before sending the bounded denial control:
v=1, type=model_denied, actual attempt, seq=1, case=M03b,
reason=request_route_rejected. WrongRouteChannelClient accepts only that control
and raises, never returning model content. M02/M03a controls cannot satisfy it.
The shared real-Hermes lifecycle remains normal: only an SDK connection error
after the exact control, or Hermes' own returned error result, is expected;
arbitrary exceptions are not success. The untrusted child report uses
maya.offline.model.route_validation.child.v1 and requires completed/constructor/
SDK closure/origins/distributions/config/denial true, native_conversation and
real_inference false, one request, 2-8 clients and empty reason_type.

Require EOF both sides, natural child/worker exit 0, empty bounded stderr,
protected-host recheck, independent exact audit readback and fresh beacon before
the existing worker-stop/cleanup predicates. Only then may
model_route_evidence_matches and model_validation_evidence_matches become true.
Final status offline_model_route_rejected_pending_independent_cleanup also
requires successful product cleanup. No operator publication callback is used.
Timeout, token/setup/channel error, wrong stage, failed audit, uncertain effects,
abnormal exit or missing evidence stays blocked, not an expected-negative pass.

## Changes And Unchanged Boundaries

New canonical model_route_validation.py implements fixed reconstruction/projection/
service/audit checks; new ModelRouteAdmission.cs implements independent host
reconstruction. model_service.py adds the named route observation; model_worker.py
adds one fixed exclusive mode and terminal reply. model_bridge.py adds the fixed
negative adapter. Shared model_child_entry.py adds the case-bound schema/adapter.
Two fixed route bootstraps and profile-only ProductFiles entries are added.

model_validation_worker_entry.py is now import-safe under a standard main guard;
default direct execution still selects M03a. Its launch(wrong_route=True) is used
only by the fixed M03b wrapper, not a runtime CLI selector. StartupDiagnostic,
its allowlists and failure-only reporting are reused unchanged. The wrapper's
early runtime guard can exit 2 before that reporter is loaded; unavailable
diagnostics never convert failure into success. C# startup snapshots remain the
same optional, non-authoritative observations. Child/worker selectors, coordinator
dispatch/evidence admission, profile version/case/consent/status are updated.

No Hermes/runtime/dependency/config change or acquisition. Future assembly must
enumerate reviewed product-member replacements/additions against Validation 2;
preserve every unrelated member and frozen artifact, including existing M03a
bootstrap members used as support. No M02 bootstrap admission is broadened.

Ordinary AppContainer, zero capabilities, six denies, reduced tokens, jobs,
child-process block, inherited pipes and four protected host files/ACLs/labels
stay unchanged. Worker remains trusted OUTSIDE child WFP containment. Shared
All Application Packages access and product-reported profile removal remain gaps.
Bounds: ready 5000 ms, RPC 2000 ms, partial frame 1000 ms, child 22/30 seconds;
frame 8192, cumulative channel/audit 131072, request/response/stderr 4096,
report 65536, output 1024 bytes. No new grant, socket/listener, loopback/registry
exception, credential, inference, spending, VM test automation or recovery.

## Inert Verification And Next Gate

- 258 Python tests and 447 subtests pass, including 15 new route tests and two
  mocked startup-main route checks. Real host files/handles/native runtime are
  not used by these startup fixtures.
- New C# route profile: 177 managed assertions; M03a/M02/M01/legacy builds each
  pass 168 overlapping route assertions. Compilation selects ModelRouteFixtures,
  never the product Main; no native security calls are exercised.
- Prior M03a checks: 108 active, paired profiles 101 each; M02: 117 active,
  paired 113; startup diagnostics: 874; earlier components: 711; bridge: 154;
  model audit: 178. Counts overlap and are not native test counts.
- The first cross-language fixture read exceeded the product frame size because
  its trusted vector bundles multiple messages. Only the fixture-file parser was
  corrected. Product framing and StrictJson bounds were not changed.
- Full Python's restricted run could not access temporary fixture folders.
  Rerunning with normal temporary-folder access passed. The existing pytest
  unknown-cache_dir warning remains; no product fix was made for it.

Coverage includes fresh positive dispatch, exact negative/no gateway, missing and
second-field mutations, wrong channel, grant expiry/revocation, missing binding,
audit write/short/flush/sync faults, rebound ledger/grant/IDs, fake denial control,
generic exception, profile payload gating and import-safe support. Existing
channel regression fixtures cover EOF/partial framing; no native timing or pipe
delivery behavior is inferred from those fixtures.

Source preparation is complete. Next: review this exact impact/contract, then
separate offline package-assembly approval. Later review exact artifact hashes
before separate one-run VM approval and fresh product consent. No package or
native M03b test exists yet. M03c/d, M04-M09, M2, Gate A, containment and production
remain pending/open; all qualification flags remain false.

# M03a Source Preparation Review

Subsequent decision: the user approved separate M03a offline assembly. See
maya_model_bridge_m03a_package.md. Source-milestone statements below remain
historical; product execution still needs separate exact-artifact approval.

2026-10-31: user approved M03a-only source preparation after the proposal.
Source/inert candidate version 0.2.1-offline-validation.1, scope
offline-hermes-model-validation-v1. No product payload, EXE or ZIP was assembled;
no native product, bundled Hermes/SDK, guest security setup or inference ran.
Frozen M01/M02/Document 2 artifacts remain unchanged. Review this record before
separate package approval; exact-artifact native approval/consent comes later.

## Fixed Native Diagnostic Contract

HERMES_MODEL_VALIDATION requires HERMES_MODEL and excludes HERMES_MODEL_DENY;
the existing bridge/construction/import requirements still apply. The profile
selects fixed model_validation_child_entry.py and model_validation_worker_entry.py.
No child, CLI, environment or editable policy selects a mutation. The future
model-contract.json must bind cases=[M03a]. Existing M01/M02 modes stay separate.
The positive M01 policy retains both exact gateway rules and real operator SID;
the worker rejects the M02 policy. No second policy engine or fake gateway.

Real Hermes/SDK child emits the original valid request through unchanged factory/
transport guards. Coordinator compares its body to the original protected oracle
before deriving a distinct worker request. Python strict decoding plus canonical
serialization changes only top-level model maya-offline-wire-v1 to
maya-offline-wire-v0. C# uses StrictJson and the pinned serializer's top-level
suffix, preserving all other bytes; reparsing verifies the single logical change.
This is not text-wide replacement. The expected host file and child grant digest
are never rebound to the mutant. A copy of the envelope preserves route, actual
attempt, lease, sequence, method/path and private channel identity.

The pure Python native-request oracle and independent C# mutation agree byte for
byte on a full synthetic native request vector. Separate Unicode/content-literal
fixtures check that a model-looking string inside message content is unchanged.
No Hermes or SDK was executed to create those source-fixture vectors.

This diagnostic proves WORKER rejection of a host-derived malformed request,
not that a hostile child bypassed its adapter, escaped isolation or changed a
trusted actor. Public report explicitly labels the trusted diagnostic origin.

## Worker Validation And Required Evidence

checked_request now distinguishes RequestModelDenied only after all other shape,
message, stream and token bounds pass. Its allowed request set is unchanged.
prepare_runtime checks live admission and envelope before this parser, records
the request_model stage on that specific rejection and fails closed as before.
gateway_calls increments immediately before each actual gateway invocation;
it is an observation, not a substitute authorization decision.

WrongModelBridge accepts only the exact fixed mutant reconstructed from its
original trusted oracle. Its terminal event requires a valid envelope, named
request_model rejection, no completed request admission, no gateway denial/call,
no attempted/actual dispatch, zero prepared/confirmed releases, live/unrevoked
admission and healthy RequiredAudit. Invalid route/attempt/lease, expiry, revoked
grant, second body change, generic exception or unknown stage cannot satisfy it.
Required audit failure poisons the sink; no reopening or continuation occurs.

The worker requires a single bound coordinator command ID, writes the rejection
durably, then returns model_validation_rejected with exactly v/type/attempt/
request_id/evidence. request_id echoes the actual coordinator dispatch command.
evidence exactly equals the audit metadata below. The service is closed, the
worker returns naturally with exit 0, and no further worker command is accepted.
There is no positive model_dispatch_reply or real model response.

## Exact Audit Schema

One newline-terminated existing AuditRecord envelope, schema_version integer 1:
event_type=model_bridge.validation_rejected, decision=deny,
reason_code=model_bridge.wrong_model, actual windows:<operator SID>,
capability=model.egress, target=model:maya-offline-fixture, operation=infer,
data_classification=internal-synthetic, idempotency_key=null, valid UTC timestamp.
Its separate metadata version is maya.model.validation.v1. Exact keys:

- attempt, request_id: actual attempt and worker service request IDs.
- route, endpoint, model: original fixed M01 route/.invalid endpoint/allowed model.
- destination=provider; request_sha256/request_bytes bind the ORIGINAL oracle.
- response_sha256="", response_bytes="0", output_sha256 binds the fixed fixture.
- dispatches="0", real_inference="false".
- validation_schema="maya.model.validation.v1", case="M03a", stage="request_model".
- coordinator_request_id: actual dispatch command ID, not a child-selected ID.
- mutated_sha256/mutated_bytes: independently reconstructed mutant identity.
- observed_model="maya-offline-wire-v0", gateway_calls="0", dispatch_attempted="false".
- runtime_prepared/runtime_released/operator_prepared/operator_released all "0".

Hashes are lowercase SHA256, sizes/counters use exact decimal strings in metadata.
IDs are fixed-length lowercase hex; no missing/extra/rebound keys, boolean schema
version, duplicate records, truncation or non-UTC/invalid timestamp is admitted.
No raw body, canary or exception text appears in public report/audit. Python
verify_validation_audit and C# ModelValidationAdmission independently implement
the predicate. C# constructs expected metadata before forwarding and rereads the
protected ledger after natural exits. M01/M02 event formats remain unchanged.

## Child Control, Closure And Final Status

After evidence validation the coordinator sends only this bounded control:
v=1, type=model_denied, actual attempt, seq=1, case=M03a,
reason=request_model_rejected. WrongModelChannelClient recognizes only that exact
case/reason and raises rather than returning model content. M02 controls cannot
satisfy it. The original child request remained valid; the mutation did not
disable or alter child-side checks.

The shared native lifecycle handles only APIConnectionError after exact denial
observation, or Hermes' own returned error result; no arbitrary exception is
converted to success. Child report schema maya.offline.model.validation.child.v1
requires completed/native_constructor/denial_observed/sdk_closed/origins_verified/
distributions_verified/config_unchanged true, native_conversation/real_inference
false, one request, 2-8 clients and empty reason_type. No child final text is
published. Report remains untrusted and is admitted only with host evidence.

Coordinator requires two-sided EOF, normal child/worker exit 0, bounded/empty
stderr and protected-file checks; then exact ledger readback. Only then sets
model_validation_evidence_matches. Final status is
offline_model_validation_rejected_pending_independent_cleanup and also requires
fresh Python entry/beacon, both process stops and product cleanup. Missing
evidence, timeout, abnormal exit, token/setup failure or audit error stays blocked.
The operator-publication callback is not called; only a denial control crosses
the child pipe, never a model-response release. All qualification flags stay false.

## Scope Of Source Changes

New canonical model_validation.py contains the fixed derivation, service subclass,
evidence schema and audit predicate. model_service.py gains bounded observations
and specific parser-stage reporting; model_worker.py selects the explicit profile
and terminal reply. model_bridge.py adds the fixed negative child endpoint; shared
child entry selects the case-bound lifecycle/report without weakening its guards.
New fixed bootstraps have early non-Windows/runtime guards.

Windows changes: ModelValidationAdmission derivation/evidence/audit predicates;
ModelBridgeRuntime M03a-only path and diagnostics; fixed worker/child selectors;
ProductFiles admits the two new entry names only in this profile. The common
denial child-report checker accepts an explicit trusted schema argument (M02
default unchanged). ProtectedPython adds profile guards, disclosed consent,
version/case/status. No new general mutation/HTTP/IPC API or policy authority.

Future assembly must explicitly omit the inactive M02 root bootstraps
model_deny_child_entry.py and model_deny_worker_entry.py from the successor
payload: M03a intentionally rejects those names. Do not broaden ProductFiles
admission merely to copy the whole M02 payload. This removes no frozen artifact
or existing VM evidence; it is a two-member successor-bundle exclusion. Runtime/
dependency bytes remain unchanged, with all product changes/additions/removals
enumerated and reviewed in the future package manifest.

Dependencies, Hermes wheel/pins, config, host file inventory/ACLs, ordinary
AppContainer, zero capabilities, six denies, both jobs, reduced tokens and child
process block are unchanged. Keep 22/30-second deadlines, 8192-byte frames,
131072-byte cumulative channel/audit bounds, 4096-byte request/response/stderr,
65536-byte report, 1024-byte model-output bounds and disabled recovery/retry.
No new grant, registry/loopback exception, service, account, listener, provider
credential, networking or real inference. Worker remains outside child WFP scope.

## Inert Verification And Remaining Gate

232 Python tests/352 subtests pass, including 19 new M03a tests. One harmless
unknown cache_dir configuration warning follows disabling the pytest cache plugin.
108 M03a C# checks pass; paired M02/M01/legacy runs pass 101 each (overlapping).
The earlier M02 checker still passes 117 (paired 113); prior 711 component,
154 document-bridge and 178 M01 model checks pass. Compilations use optimized x64
and warnings as errors, with selected fixture mains, never product Main.

Fixtures cover fresh valid-request dispatch through the real gateway, exact
wrong-model rejection with no gateway call, second-field and envelope changes,
expiry/revocation, bad policy/profile, missing command binding, forged denial,
late unrelated exception, audit write/flush/fsync/short-write failure and ledger
field/hash/ID/type/count/time mutations. Existing protocol/Windows suites retain
partial-write, EOF, token/setup and byte-bound controls. Native bootstrap tests
exit on forced non-Windows guards. No bundled Hermes/SDK or security API ran.

Source/inert success does not prove native timing, SDK error unwinding, child
closure or full containment. Review this exact contract/impact before approving
separate M03a package assembly. A future package must bind changed-source and
dependency inventories, exact payload/index/resources/source/artifact hashes;
separate matching-artifact one-run approval and fresh consent remain mandatory.
No package/run is ready. M03b-M03d, M04-M09, M2, Gate A and qualification remain open.

# M04c Consumed-Grant Source Candidate

2026-10-31: user approved M04c-only source preparation including the positive
child path, new-ID trusted replay, delivery-ack age and five-record audit contract.
See maya_model_bridge_m04c_review.md and maya_model_bridge_m04c_tests.json.
Candidate 0.2.1-offline-replay.1, scope offline-hermes-consumed-lease-v1.
No Maya Main/setup, bundled Python/Hermes/SDK, native timing test, VM/security
change, credentials, network or inference. No product payload/package assembled.

## Implemented Path

ConsumedGrantBridge preserves the original first prepare_runtime, authorization,
synthetic dispatch and audit flow. It captures issued lease/expiry, first command
ID, exact immutable request envelope and verified response. Original base
model_service.py, including revoke/_live/TTL/confirmation behavior, is unchanged.
First SDK request/body/identity/model/route remain unchanged; both original
positive M01 policy rules and the existing gateway are used.

Original confirm_runtime_delivery runs before M04c timing admission. A prior
write remains counted/logged even when the grant has expired or been revoked.
Only after that committed fourth event does the observer require open/healthy/
unrevoked/runtime_delivered/same binding and exact known effects, capture a
finite nonbackward real worker age strictly before expiry and return the M04c
acknowledgement age. Late confirmation closes/blocks M04c but retains delivery.

Exclusive replay_grant worker mode uses ordinary issue/first model_dispatch/
model_runtime_delivered, then a SECOND model_dispatch under a NEW command ID.
Original seen-ID/shape/attempt guards remain. Fixed guarded replay wrappers
select this mode; no child/config/environment/CLI-selected fault. No worker
clock parameter is supplied natively. Runtime ack adds delivery_elapsed_ms only
for M04c; older profiles retain their exact acknowledgement shape.

Coordinator verifies original grant/body/full envelope, saves an exact separate
dictionary of primitive request values, verifies the first synthetic response,
writes it ONCE to the child, validates receipt hash/byte count, and receives
the worker's runtime acknowledgement. Immediately (before waiting for child
final) it sends the exact saved request under a distinct replay command ID.
Issue/first dispatch/delivery/replay IDs must all be distinct. No reissue, delay,
changed lease/channel/body/model, counter reset or child adapter bypass.

The service locks/preflights the replay against the saved first envelope, exact
integer v/seq and channel, with unchanged token/expiry/response. This read-only
diagnostic is NOT a second admission. It calls the ORIGINAL _live("issued")
from the ORIGINAL prepare_runtime while actual phase is runtime_delivered.
Real finite nonbackward clocks bracket that guard. Only exact ModelDenied with
uncertain=true, open/healthy/unrevoked/unexpired context, exact first effects
and no deltas establishes consumption. If the guard returns, generic/uncertain
failure applies without this state proof, or time reaches expiry, the attempt
blocks before another gateway/dispatch. No authority is introduced.

Original dispatch_attempted/request_validated stay TRUE from first admission,
gateway_calls2/dispatches1/runtime_prepared1/runtime_released1 remain, operator
preparation/release0. Observer verifies retained _destination runtime:<attempt>
but writes the provider-destination replay diagnostic without mutating that
state. It checks context/time before and after required fifth audit commit,
then original failure handling closes normally. Immutable before-close metadata
snapshot, not cleanup flags, drives terminal evidence.

## Genuine Positive Child And Host Admission

Child replay_grant participates in exclusive contract/profile selection but is
NOT included in negative mode. It uses the unchanged ModelChannelClient, real
pinned factory/SDK, one-request guard and original positive lifecycle. Existing
maya.offline.model.child.v1 report and model_child_complete frame retain
native_conversation=true and genuine SDK closure. No second SDK request,
model_denied control, model_child_denied frame or denial_observed field.

HERMES_MODEL_REPLAY inherits VALIDATION only for existing bounded startup capture;
its explicit positive coordinator branch skips RunValidation's fixed wrong-model
schedule, not a security check. Earlier profiles keep their selection/semantics.
After the consumed reply, host checks the privately held final fixture text,
positive constructor/conversation/closure/config/origins/distributions report,
natural child/worker exit0, EOF, empty bounded stderr and protected host files.
It never sends model_prepare_final/operator-delivered or calls publish.

New ModelReplayAdmission independently reconstructs all fifth metadata and the
original positive prefix. Exact five-record protected ledger readback precedes
model_replay_evidence_matches/model_evidence_matches. Original single-record,
two-record and six-record audit verifiers are byte-identical; they are not
relaxed to admit a prefix. Python verify_replay_audit separately enforces the
same five envelopes, exact keys/types/values, valid nondecreasing UTC timestamps
and zero additional effects. Prefix maps13/13/13/14 fields; fifth50 string fields.
Every field follows the approved JSON contract, including original uncertainty.

Two dynamic ages (delivery/rejection) are canonical strings0..1999, ordered,
bound to exact ack/reply and fifth record. All other fields are independently
host-derived from original request/response/grant/actual command IDs. Actual
unexpired worker clock checks remain separate from integer age or UTC stamps.
No raw lease/body/canary/output/exception text in report/audit. Required-audit
write/short/flush/fsync failures poison acceptance; no sink reopen/replacement.

Final startup_status=offline_model_replay_child_completed;
status=offline_model_lease_replay_rejected_pending_independent_cleanup. Totals
remain two gateway calls/one dispatch/one runtime pipe write/zero operator
publications, with explicit zero replay deltas. Fresh beacon/worker stop/product
cleanup still required. All qualification flags remain false.

## Scope And Remaining Gates

New canonical model_lease_replay.py, ModelReplayAdmission.cs and two fixed
model_replay root entries. Changed existing payload sources: model_worker.py,
model_child_entry.py and model_validation_worker_entry.py. Existing child-client/
factory module is unchanged. Launcher changes: ModelBridgeRuntime.cs,
ProtectedPython.cs, ProductFiles.cs, WindowsBridgeProcess.cs, WindowsIsolation.cs.
No dependency, Hermes/SDK wheel, gateway engine, OS grant or earlier helper refactor.

Read-only frozen Revocation 1 comparison: three Python replacements plus future
model-contract.json (four total), three additions; future successor only needs
two inactive model_revoke_child_entry.py/model_revoke_worker_entry.py omissions.
Those omissions and package assembly are NOT approved now. If later approved,
expected inventory6779 and6772 unchanged predecessor members. Keep canonical
revocation/expiry helpers, M03a shared support, all Python/Hermes/64 distribution/
config/native guards/notices and every predecessor. Full actual-profile ReadIndex
of an assembled payload remains an assembly gate; name probes alone are not it.

Same AppContainer/zero capabilities/six denies/reduced tokens/jobs/child-process
block/private pipes/four protected host files and labels. Worker remains outside
child network containment; shared All Application Packages/profile deletion gaps
stay open. Ready/RPC/partial5000/2000/1000ms, child22/30s; frame8192, direction/
audit131072, request-response-stderr4096, report65536, output1024, diagnostic256.
Original TTL2000ms must cover positive prefix AND replay; native timing may fail.
No timer/TTL extension, fake native clock, delay, renewal, fallback, automatic
retry/recovery or VM automation. No real provider, secrets, customer data or spend.

## Inert Evidence

375 Python tests/1058 subtests pass, including20 new replay cases and two mocked
startup-main integrations. Existing unknown pytest cache_dir warning remains.
C# replay fixture409 active assertions, nine paired profiles400 each; nine
intentional invalid profile combinations rejected at compilation. Counts overlap,
not native cases. Fake clocks/streams/pure protocol and fixture mains only,
not product Main/security or bundled runtime execution.
Earlier C# regressions also pass: revocation268/259, expiry225/216, body136/127,
attempt195/186, route177/168, validation108/101, denial117/113, startup874,
prior components711/document154/model-audit178. Counts overlap. Final focused
replay/startup retest41 tests/213 subtests passes after the added schedule guard.

New coverage verifies the truthful positive prefix and genuine first response,
original guard and uncertainty required, no second gateway/dispatch, actual
new-ID replay vs duplicate command rejection, wrong envelope/channel/grant/
response/phase, missing first/delivery, late/expired/revoked truthful confirmation,
before/at/after expiry and crossing guard/fifth commit, poisoned audit, malformed
ages/IDs, every prefix/fifth metadata binding, timestamp order, missing/extra/
duplicate/truncated/forged operator records, one-request client guard and guarded
entry paths. All20 required-audit fault injections assert the exact targeted record,
including fsync's descriptor argument; prior effects remain counted. Shared
transport/EOF/deadline/closure fixtures stay in regression coverage, not native
timing/containment proof.

Local fixture development corrected a fake-clock issue-time sample and a commit
stub's fsync signature. These were in inert tests, not a native startup experiment;
no base service/TTL/deadline correction was made. New record-target assertions
avoid treating an earlier generic failure as the intended later-record fault.

Inert reproduction .codex-build/maya-model-replay-source-20261031-1 contains
check.ps1, vector.py, negative-profiles.ps1, source_scope.py and generated
replay-vector.json/source-inspection.json. Source comparison validates every
frozen predecessor payload member and exact source changes without assembling
a successor. Frozen Revocation 1 ZIP/EXE hashes still match:
53B92F27D0079201F617AE6CD2693E47D5DFEE89161CB6C56784730565A15739 /
2370BCA535EB33A4876C8CE4A348BEC92E3D2A4380D2BC5B4ADA48E3A02352F3.
Coupled product-context, whitespace and JSON/vector fixed-value/key/type checks
pass. Existing LF/CRLF notices are informational. Source-preparation approval
is true; assembly/omission/native-run approvals remain false. No unrelated
worktree cleanup or code commit performed.

## Next Decision

Source preparation is complete for review. Obtain separate assembly approval
INCLUDING exactly two inactive Revocation 1 root omissions from NEW successor
only; then full payload/pin/resource/freeze review, matching guest path/hash,
separate one-run VM approval and fresh product consent. No runnable M04c package
or native qualification exists. M05-M09/M2/Gate A and production remain open.

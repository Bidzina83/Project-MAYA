# M04b Revocation Source Candidate

2026-10-31: user approved M04b-only source preparation, including the fixed
revoke/ack protocol and two-record audit contract in maya_model_bridge_m04b_review.md
and maya_model_bridge_m04b_tests.json. Version 0.2.1-offline-revocation.1, scope
offline-hermes-lease-revocation-v1. Preparation is not package or native-run approval.
No Maya Main/setup, bundled Python/Hermes/SDK, real native wait, VM/security change,
network, credentials or inference ran. M04c and later cases remain unimplemented.

## Implemented Source Path

RevokedGrantBridge captures the original issued lease/expiry under the existing
RLock. revoke_issued checks exact lease/command binding, issued/open/unrevoked/
healthy-audit/zero-effect state and finite nonbackward worker time before expiry.
It calls super().revoke() exactly once, preserving token/expiry/phase, verifies
revoked=true, writes/flushes/fsyncs grant_revoked, and rechecks time/context before
returning an immutable-snapshot-derived acknowledgement. Any failure closes and
blocks; no acknowledgement from cleanup's close() or a caller's assertion.

Exclusive revoke_grant worker mode adds exactly one model_revoke command between
issue and dispatch. Existing exact command shape/attempt/seen-ID checks remain.
Old profiles reject that command. Fixed guarded child/worker wrappers select M04b;
no config/environment/CLI-selected mode or native clock injection. Policy still
has both original positive M01 rules. Real worker construction supplies no clock.

Coordinator verifies original grant and complete model_revoke_ack evidence BEFORE
ordinary model_begin; no delay, renewal or TTL/deadline change. It saves host-
constructed acknowledgement metadata and rejects issue/revoke/dispatch ID
collisions. Real pinned Hermes/SDK construction/request/closure path remains,
with one original request and all child guards enabled. Body and full envelope
must match the original protected host oracle/grant.

Worker read-only exact request/channel preflight is NOT completed admission.
The observer calls the ORIGINAL _live("issued"), with worker clock checks before
and after. Only exact ModelDenied with uncertain=false plus acknowledged
revocation, issued/open/healthy state, same lease/expiry, exact preflight,
strictly unexpired finite monotonic time and zero effects establishes M04b.
If the original guard returns, or any other failure applies, it blocks before
gateway/effects. No fallback dispatch. The observer writes the distinct
lease_revoked event, rechecks time/context after required audit commit, then
allows the original failure path to close normally. Captured tuple snapshots,
not close() changing flags, bind acknowledgement and rejection evidence.

Existing base model_service.py (including revoke, _live, TTL and accepted set)
and ModelValidationAdmission.cs's single-record audit verifier are byte-identical
to frozen Expiry 1. Expiry's canonical helper/root wrappers are unchanged.
No parallel gateway/policy engine or refactoring of earlier denial semantics.

## Exact Protocol And Host Evidence

The approved review's exact keys and 39-string metadata maps are implemented.
model_revoke includes only v/type/actual attempt/fresh command ID/actual lease.
Ack model_revoke_ack and terminal reply model_lease_revoked carry complete
case-bound evidence. All command IDs stay unique; raw lease travels only over
the existing private pipe, never in report/audit.

First metadata stage=revoke_applied: no child request/preflight/guard rejection
claimed, no dispatch ID; age is actual revocation observation. Second stage=
lease_revoked: actual new dispatch ID, original observed request hash/bytes,
preflight/guard rejection true, revoked_before=true. Both ages are canonical
strings [0,1999], second >= first, original TTL2000ms. Python and C# reconstruct
all other fields and bind each dynamic age exactly between reply/ack and ledger.
Actual worker time must separately be strictly before the captured expiry:
integer age rounding or host elapsed time is not proof.

Exactly two newline-terminated AuditRecord envelopes, in order grant_revoked,
lease_revoked, both decision=deny, exact reasons/actual Windows actor and fixed
model.egress/target/infer/internal-synthetic metadata. The first is an invalidation
diagnostic, not an authorized inference/gateway call. Dedicated
verify_revocation_audit and ModelRevocationAdmission.Audit enforce two records,
exact fields/types/UTC times/IDs/hashes/ages and zero effects. Earlier one-record
admission remains unchanged. Missing/extra/swapped/duplicate/truncated ledger,
required-audit failure or expiry across guard/audit commit cannot pass. No sink
reopen, replacement, retry, reset or inferred success.

Exact child control case=M04b, reason=lease_revoked; report schema
maya.offline.model.revocation.child.v1. Genuine constructor/one request/2..8
clients/SDK closure/config/origins/distributions and denial observation required,
but report remains explicitly untrusted. No model response write/publication.
Coordinator independently verifies ledger, normal exit0/EOF/empty bounded stderr
and protected host readback before setting model_revocation_evidence_matches and
model_evidence_matches. Fresh beacon/product cleanup remain mandatory for
offline_model_lease_revoked_pending_independent_cleanup. Shared startup_status
remains offline_model_validation_child_completed; all qualification flags false.

## Scope And Future Assembly Gate

New canonical model_lease_revocation.py, ModelRevocationAdmission.cs and two fixed
model_revoke root entries. Changed payload sources: model_worker.py, model_bridge.py,
model_child_entry.py and shared model_validation_worker_entry.py.
Launcher changes: ModelBridgeRuntime.cs, ProtectedPython.cs, ProductFiles.cs,
WindowsBridgeProcess.cs and WindowsIsolation.cs. Consent discloses native
revocation/two audit events, timing/confounding, protections and cleanup limits.

Read-only inventory comparison against frozen Expiry 1: four Python replacements
plus future model-contract.json replacement (five total), three additions and
two proposed NEW-successor-only omissions: model_expiry_child_entry.py and
model_expiry_worker_entry.py. Omissions/assembly are NOT approved. With those
approved later, expected inventory 6778 and 6770 unchanged predecessor members.
Keep canonical expiry helper, old case modules, M03a shared support, config,
native literals, Python/Hermes/64 distribution pins, notices and all predecessors.
No existing workstation/guest/source/artifact deletion. Full actual-profile
ReadIndex of a real assembled inventory remains an assembly gate; source fixtures
only establish the new entry-name controls, not a packaged payload.

Same AppContainer/zero capabilities/six denies/reduced tokens/jobs/child-process
block/private pipes/four protected host files and labels. Trusted worker remains
outside child network containment; shared All Application Packages and profile
removal limitations remain. Ready/RPC/partial5000/2000/1000ms, child22/30s,
frame8192, direction/audit131072, request-response-stderr4096, report65536,
output1024 and diagnostic256 bounds unchanged. Native ability to fit both
required audits and the original request inside TTL2000ms is UNVERIFIED; slow
disk/scheduling blocks rather than changing timeouts or retrying.

## Inert Evidence

353 Python tests/855 subtests pass, including 26 new revocation cases and two
mocked startup-main integrations. Only ordinary-host fixture classes/clocks/
streams ran, not bundled SDK/Hermes or native product setup. Existing unknown
pytest cache_dir warning remains. New C# fixture main: 268 active assertions,
eight paired profiles 259 each; eight intentionally invalid define combinations
rejected by compile guards, with no execution of those outputs.

Earlier regressions: expiry225/216, body136/127, attempt195/186, route177/168,
validation108/101, denial117/113, startup874, prior components711/document154/
model-audit178 pass. Counts overlap and are not native cases/qualification.
Cross-language exact first/second maps, every metadata binding, missing/forged/
reordered audit, ages, child controls and paired payload-name controls pass.
Real revoke invoked once; original guard required; expiry before/at/after and
crossing guard/audit, generic/uncertain failure, poisoned audit, wrong state/
request/channel/IDs, preexisting effects, required-audit short/write/flush/fsync
faults and preserved child request budget covered. Shared transport/exit fixtures
remain in regression coverage; native timing/process/cleanup is not qualified.

Reproduction recipes are inert .codex-build/maya-model-revocation-source-20261031-1:
check.ps1, vector.py, negative-profiles.ps1 and source_scope.py, with generated
revocation-vector.json and source-inspection.json. One local helper initially
named inspect.py shadowed Python's standard library during a final fixture-script
run; it was renamed source_scope.py, after which the entire check passed.
This was a local verification-helper issue, not a product/VM startup correction.

Frozen Expiry 1 ZIP/EXE rehashed unchanged:
13D8CDC92B6BDA67B1DF3EC25A21D029CE7A031D34CE439523A08495B476EAE7 /
BB4FB259CCF09C519D5A5F50BAFD2C1AFB86303805B217639C426FCB12ACBC21.
Current read-only inspection validates every frozen payload member and exact
source changes; no successor runtime/dependency acquisition or payload assembly.
Coupled product-context validation, whitespace check and companion JSON/vector
key/type/fixed-value consistency checks pass. Source-only approval is true;
assembly/omission/native-run approval remains false. Existing LF/CRLF notices
are informational. No code commits or unrelated worktree cleanup performed.

## Next Decision

Source preparation is complete for review. Obtain separate M04b assembly approval
INCLUDING exactly the two inactive Expiry 1 root omissions from the new successor
only, verify actual full payload membership/pins/PE/resources/freeze, then obtain
guest path/hash, separate matching-artifact one-run VM approval and fresh consent.
No M04b runnable package/run, M04c/later implementation, inference, broader grant,
retry/recovery, Gate A acceptance or qualification follows source preparation.

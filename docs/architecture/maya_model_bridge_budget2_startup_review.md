# Budget2 Startup Channel Review

Subsequent decision: user approved local inert-only reproduction. Completed
evidence is in maya_channel_scheduling_inert_result.md. It establishes the
scheduling/category ambiguity, not the actual guest cause. No product correction,
successor assembly or native retry is approved by that experiment.

2026-11-01. Focused read-only source review after Budget2's blocked native report
and scoped cleanup. No product/test source change, compilation, fixture execution,
new package, product/bundled runtime execution or VM/security change. This review
does NOT authorize a retry or successor. Outcome: maya_offline_model_budget_2_outcome.md.

## Findings

P1 reliability risk: BridgeChannel.cs:68-82 reads the FIRST byte on one task,
then starts ANOTHER Task.Factory.StartNew for remaining header/payload/JSON work.
It synchronously waits1000ms for that nested task. The timeout includes task
scheduling delay, remaining stream I/O AND parsing. Consequently
bridge_incomplete_frame_timeout can occur when the nested task was not scheduled
in time, not just when the producer withheld frame bytes. A complete prebuffered
frame can be subject to that scheduling path. This is a source-established
ambiguity/risk, NOT a reproduced guest root cause. Queue/start/progress/available
byte observations were not captured. Do not declare ThreadPool starvation proven.

The outer Bound method also starts a task and waits. Readiness uses Read(5000),
while this inner first-byte-to-completion wait is1000ms. Extending ONLY general
readiness would not remove the inner limit; no extension is recommended here.
Task.Factory calls specify neither an explicit scheduler nor a dedicated reader
thread. A controlled inert scheduling experiment is warranted before selecting
a source correction. Actual default-scheduler behavior on the VM is unmeasured.

P2 observability gap: StartupDiagnostic.mark stores a stage in process memory;
it emits a bounded stage/type only through fail after a caught exception. It
does not transmit ordinary progress. A live stall at request fsync/close, service
construction, send/flush or wait produces no exception diagnostic. Also ready_sent
suppresses subsequent startup failure messages even if the coordinator never
accepted readiness. Empty stderr therefore establishes neither successful setup
nor a particular failing stage. WorkerStartupCapture correctly calls the pending
and empty states diagnostic-only; do not reinterpret them as readiness.

Existing windows_bridge_fixtures.cs checks full MemoryStream frames, truncation,
invalid sizes/JSON and blocked I/O. windows_worker_startup_reporting_fixtures.cs
checks failure categories and captured error lines. No controlled nested-reader
scheduler-delay/full-frame comparison is present in these inspected fixtures.
Earlier passing tests do not disprove this risk or localize this native attempt.

## What The Evidence Narrows

The reported category is generated only after input.ReadByte returned a
nonnegative byte and the nested task did not complete within1000ms. Thus worker
stdout supplied at least ONE byte to the host reader; total stdout silence or a
simple wait-for-first-byte timeout is inconsistent with this particular path.
No captured prefix or decoded frame proves that byte belonged to the intended
model_worker_ready message. Unexpected stdout is not ruled out.

Worker source order: open audit handle; build expected request; write request;
flush; fsync; close; verify write count; construct ordinary OfflineModelBridge;
encode/write/flush model_worker_ready; mark ready_sent; await model_issue.
same_client_budget selects no special startup service: its distinct worker
branch occurs only AFTER original runtime delivery. Lifecycle model_budget.py
is child code and has not run: child_resumed=false. These reviewed Budget2
changes do not execute at the observed pre-child failure boundary.

request.json length2617 proves file bytes existed at later readback, not exact
body identity, completed fsync/close or readiness transmission. audit.jsonl0 is
consistent with no admitted model operation; the worker writes no audit record
before its first model dispatch. It does not locate startup. If the observed
stdout byte IS from the intended ready frame, then the preceding flush/fsync/
close/service-construction steps necessarily returned in this source path.
Without prefix/frame provenance, keep that inference conditional.

PrivateChannel.send_frame constructs the complete length-prefixed frame, checks
one destination.write count and flushes. Successful write/flush would support a
complete producer send, but this run contains no producer completion evidence.
No product networking or model inference is implicated or qualified.

## Proposed Next Step: Inert Reproduction Only

Request approval for a narrowly scoped LOCAL fixture, not a product correction:

1. Compile existing BridgeChannel/strict parser with a separate fixture Main,
   never product Main/setup or an assembly-loading harness.
2. Verify an already-complete valid frame under ordinary scheduling, then under
   a private constrained/delayed task scheduler. Record whether the nested reader
   actually started before timeout and whether any frame bytes were missing.
   Do not change global machine/VM settings or infer that a private scheduler
   was used by the actual launcher.
3. Compare true delayed/truncated-header/payload/EOF/invalid-frame cases, preserve
   existing5000/1000-ms readiness/partial limits, channel budgets and terminal
   failure. Release/drain fixture tasks and streams; no abandoned blocked reader.
4. Keep experiments source-bound to the frozen Budget2 channel code and clearly
   separate scheduling reproduction from native cause attribution. An inert
   positive/reproduction is not M05a/cleanup/containment qualification.
5. Only after evidence, review a targeted scheduling/progress correction with
   unchanged security/deadlines/audit/authorization. Do not expand worker fault
   policy, suppress timeouts, retry VM runs, run M05b or repackage speculatively.

No implementation or fixture build follows from this REVIEW alone. All Budget2/
Budget1/predecessor artifacts stay intact, run allowance consumed, false flags
and Gate A unchanged. The corrected M05a client lifecycle remains untested on VM.

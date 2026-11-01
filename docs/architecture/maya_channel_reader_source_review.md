# Channel Reader Source Review

Date: 2026-11-01. Approval: source correction and inert verification only.
Candidate: Budget3, 0.2.1-offline-budget.3, file version 0.2.1.13.
No package assembly, product execution or VM retry is authorized by this record.

## Change

BridgeChannel.cs now reads the first byte, remaining header, payload and strict
JSON inline in one explicitly LongRunning task on TaskScheduler.Default. A
completion continuation only wakes the caller; it is not another I/O reader.
The caller enforces the earlier original overall deadline and first-byte plus
1000 ms. Completion resamples the effective deadline and finished timestamp
under the progress lock, preventing stale samples from accepting late work.
No timing grace, retry, recovery or producer substitution is added.

Pending tasks remain owned and joined. Dispose latches terminal failure at entry.
A blocked reader still produces cleanup uncertainty until released and drained.
Overlapping reads are rejected without replacing the original read observation.
Write and EOF scheduling remain unchanged and are outside this correction.

ModelBridgeRuntime.cs includes channel_read_progress in existing bounded worker
snapshots. ProtectedPython.cs changes only the BUDGET version and consent text.
No Python, dependency, worker protocol, authorization, grant, audit admission,
security provisioning or payload admission change is intended.

## Diagnostic Contract

Schema maya.channel.read_progress.v1. A not-started observation has schema and
observation only. An observed read has exactly 18 primitive fields:
schema, observation, read_sequence, stage, reader_started, first_byte_observed,
header_bytes, first_byte_elapsed_ms, payload_bytes_expected, payload_bytes_read,
json_parsed, frame_accepted, reader_finished, elapsed_ms,
reader_finished_elapsed_ms, overall_limit_ms, partial_limit_ms, failure_category.

Stages: queued, first_byte, header, payload, parse, complete.
Failure snapshots are frozen and returned as defensive copies. Counts/timings
are bounded observations, not message content, identity, secret or raw exception.
Frame acceptance is not model readiness or authorization.

## Inert Verification

Latest source-bound fixture: 163 assertions across 13 cases pass. Full buffered
frame succeeds even with constrained caller scheduling; only one caller task is
queued on the private scheduler. Real header/payload stalls still fail at the
1000-ms partial deadline, no-first-byte at 5000 ms, and a 2000-ms RPC overall
deadline wins when earlier. EOF, malformed JSON, invalid/oversize length, byte
budget, successive reads, overlapping-read ownership, frozen diagnostics and
blocked-reader cleanup uncertainty are covered.

Shared C# checks pass: bridge154, startup reporting874, protected Python231,
M01 audit178. Budget profile checks: active219 and ten paired profiles214 each.
Ten invalid profile combinations compile-rejected. Focused Python regression:
339 tests/1173 subtests pass; this is not a full-repository test claim.
Two local runner profile-selection mistakes were corrected: document and M01
fixtures initially used the Budget profile and rejected its version as expected.
No acceptance predicate was changed to accommodate those runner mistakes.

Evidence: .codex-build/maya-channel-reader-source-20261101-1/
reader-results-bound.json and source-bindings.json pin the compiled source,
fixture, executable and result bytes. Fixture Main only; product Main not run.

## Limits And Next Gate

The earlier private-scheduler reproduction proved category ambiguity, not actual
VM ThreadPool starvation. This correction removes that demonstrated reader
dependency but cannot guarantee native scheduling or establish the VM root cause.
No successful M05a native test is claimed. Budget2 and earlier frozen artifacts
must remain intact; qualification flags remain false and Gate A remains open.

Next is separate Budget3 offline assembly approval. Expected payload change is
the versioned model-contract.json only, subject to full actual inventory checks;
no root entry omission, dependency change or runnable product execution follows
source approval. Exact artifact hash/path approval and fresh product consent
are still required before any one-run VM attempt.

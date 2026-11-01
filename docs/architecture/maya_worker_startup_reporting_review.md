# Worker Startup Reporting Source Review

Subsequent decision: the user approved separate offline successor assembly. See
maya_worker_startup_reporting_package.md. Source-milestone statements below are
historical; exact-artifact VM-run approval and fresh consent remain required.

2026-10-31. Approved scope: reporting-only source correction, focused inert tests
and source review after M03a Validation 1 failed before worker readiness. The
underlying native startup cause is still unknown. Frozen Validation 1, M02,
M01 and Document 2 remain untouched. No product package/build/run is authorized.

## Source Candidate And Impacts

The candidate M03a version is 0.2.1-offline-validation.2 (file version 0.2.1.4),
scope unchanged. Version/consent disclosure identifies the reporting-only successor;
the old contract/package is not rewritten. No model validation, policy, token,
ACL, WFP, payload/dependency, host-file inventory or deadline correction is made.

Changes: M03a worker bootstrap adds a small standalone StartupDiagnostic class;
shared model_worker.py marks fixed stages only when that M03a reporter is supplied.
Other native worker entries supply no reporter. BridgeChannel preserves the old
primary bridge_channel_failed error but exposes an allowlisted FailureCategory.
WindowsBridgeProcess attaches bounded stderr capture only to M03a and adds a
nonblocking process snapshot; ModelBridgeRuntime records snapshots on startup
failure before cleanup and after stop. WorkerStartupCapture is a managed-only
formatter/parser. No additional file, listener, process or provisioning path.

## Failure-Only Worker Diagnostic

Successful startup writes NO diagnostic stderr. A failure before ready_sent emits
at most one ASCII line on the existing stderr pipe:

```text
MAYA_WORKER_STARTUP_V1|<allowlisted-stage>|<allowlisted-error-type>
```

It is not a stdout protocol frame, ready message, audit event or authorization.
Error messages, tracebacks, paths, canaries, credentials and request text are never
included. Unknown exception class names become OtherError. Preflight rejection
uses PreflightRejected. Writer/flush failure is swallowed by this reporting helper
without retry or altering the original blocked outcome. Main still returns 3 on
caught failure, bootstrap preflight 2 and uncaught bootstrap exception 1.

Stages distinguish bootstrap preflight/imports/paths, worker import/preflight/root,
dependency/canonical readback, config/policy/literals reads, audit open, service
config, request build/open/write/flush/sync/close/check, validation-service import/
construction, ready_send and ready_sent. Python/C# allowlists match exactly.
Once the ready write returns, reporting closes its startup window; later runtime
errors are not mislabeled startup failures. Original normal stderr rejection stays:
any stderr still prevents a successful WaitBridge result. Diagnostics never pass
a failed M03a attempt or satisfy the existing one-record validation-audit predicate.

No continuous heartbeat/progress stream is added. A hung process may produce no
terminal line; the stage/type then remain unavailable. This correction improves
evidence but does not guarantee localization of every timeout or loader failure.

## Channel Category And Snapshots

BridgeChannel.Category unwraps bounded single-inner aggregate exceptions and
returns only known timeout/incomplete-frame/frame/JSON codes or eof, invalid_utf8,
stream_closed, io_error, multiple_failures or operation_failed. Raw messages and
unknown StartupFailure codes are not forwarded. The primary failure code and
failed-channel behavior stay unchanged; no retry or deadline extension is added.

Only a startup-failed M03a records model_worker_before_cleanup and
model_worker_after_stop. Fields:

- observation_phase: before_job_stop or after_job_stop_attempt_not_natural_exit_evidence.
- process_state: not_created, running, exited or unavailable.
- exit_code_hex: available exited-process status, otherwise null.
- stderr_bytes_observed: observed count, or null if capture never started.
- stderr_capture_complete: true only after completed, nonfailed reading.
- diagnostic_state: unavailable, pending, capture_failed, empty, invalid or
  reported_failure. Snapshot-query failure uses snapshot_unavailable.
- diagnostic_stage/diagnostic_error_type: populated only from a complete,
  exactly parsed allowlisted single line; otherwise null.
- channel_failure_category: retained bounded category, otherwise null.

The post-stop snapshot also runs if stop throws; its phase denotes an attempted
stop, not a new claim that termination succeeded. Existing cleanup gates still
require actual stop confirmation. Read existing process handles with
WaitForSingleObject(handle,0); do not wait for
a new exit or launch anything. Post-stop exit codes are NOT proof of the original
natural failure. A running pre-stop process has no fabricated exit 0. Counts
observed while pending are provisional, not complete zero-stderr attestations.
The capture retains at most 256 bytes for parsing; original 4096-byte stderr
enforcement stays unchanged. Extra/oversized/non-ASCII/multiline/unknown reports
are invalid and never release raw text. LF and Windows CRLF are both accepted.
Synchronization protects capture snapshots; diagnostics cannot suppress the
original startup exception or prevent the existing stop/cleanup sequence.

## Preserved Boundaries

Ready/RPC/frame predicates, exact M03a mutation, independent audit admission and
all success conditions are unchanged. Both jobs still stop before security
cleanup. Ordinary AppContainer, zero capabilities, six denies, reduced tokens,
child-process block, trusted medium worker topology, fixed host files and grants
remain. Keep 5-second worker readiness, 2-second RPC, 1-second partial-frame,
22/30-second child budgets and all original byte bounds. No longer wait, registry
or loopback exception, dependency, wheel patch, fallback, automatic retry/recovery,
model traffic or authoritative operation is introduced. A new nonblocking exit
query observes the already owned worker handle; it grants no new capability.

## Verification

241 Python tests/362 subtests pass. New fixtures execute the startup main function
only with mocked native preflight, metadata, private-file handles, fsync and pipe
peers using real serialized config/policy. They exercise normal readiness and
config/policy/audit/request open, request write/flush/sync/close, service construction
and ready-send failures; post-ready faults remain ordinary nonzero failures with
no startup line. No real Win32 file open, restricted worker, Hermes or SDK runs.
Standalone reporter tests cover redaction, one-shot behavior, reporting failure,
closed ready window and Python/C# allowlist parity.

874 managed reporting assertions pass, including the stage/type cross-product
(not 874 independent native scenarios), invalid/partial/multiline/CRLF handling,
unavailable/partial/complete counts, snapshot labels and real in-memory channel
EOF, truncated frame, invalid size/UTF-8/JSON, I/O failure and unchanged timeout
behavior. Tests use selected fixture Main, not product Main; no native process
snapshot call is exercised. M03a 108 and paired 101 assertions pass, as do the
prior 711 component, 154 document bridge and 178 M01 checks. Paired coverage
overlaps and is not additive. One harmless pytest cache_dir warning remains.

During preparation the positive mocked-main fixture initially omitted forwarding
its written request to its in-memory peer; that test fixture was corrected.
Cross-profile compilation then caught an inactive-profile field-initialization
warning; explicit null initialization fixed it without enabling those profiles.
Final tests pass. These were local preparation findings, not native product runs.

## Next Gate

Review these source changes before separate successor package approval. No
Validation 2 EXE/payload/ZIP or guest artifact exists; native reporting, process
snapshots and the original cause remain unverified. A future package must preserve
dependencies/security and bind exact changed sources/resources/hashes, followed
by separate exact-artifact one-run approval and fresh product consent. Stop on
failure. All qualification flags, Gate A and later case/M2 gates remain unchanged.

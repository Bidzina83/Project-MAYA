# Maya Offline Model Validation 2 Handoff

Preparation checks: 6771 payload files, 143990551 expanded bytes, 963796-byte
index. Exactly 6768 Validation 1 members unchanged and three reviewed replacements;
no member additions/removals. Runtime/dependency/configuration bytes are unchanged.
Fresh inert checks pass: 241 Python tests/362 subtests, 874 managed reporting
assertions, 108 M03a checks and paired profiles of 101 each (overlapping coverage).
One harmless pytest cache_dir warning remains. Optimized x64 GUI compilation
passes with warnings as errors. No product or bundled runtime was executed.

Version 0.2.1-offline-validation.2; scope offline-hermes-model-validation-v1;
M03a only. Approved 2026-10-31 for separate offline assembly after
maya_worker_startup_reporting_review.md. No native run follows this approval.

## Purpose And Unchanged Test

Validation 1 stopped before worker readiness; its underlying cause is UNKNOWN.
This successor only improves startup diagnostics. It is not a repair of that
cause, a permission workaround or a guarantee of a passed M03a test.

Real pinned Hermes/SDK child still sends its valid synthetic request. The trusted
coordinator verifies it, derives one separate worker request changing only the
fixed model to maya-offline-wire-v0, and requires worker rejection before any
gateway call/dispatch. Expected model responses/publications are zero; output
should stay blank. One exact validation audit record, natural child/worker exit 0,
SDK closure and host evidence remain mandatory. Expected success status remains
offline_model_validation_rejected_pending_independent_cleanup. Generic failure,
timeout, missing audit, wrong stage or diagnostic stderr is NOT a pass.

## Reporting Changes

Only a pre-readiness failure may emit one bounded allowlisted stage/error-type
line on existing worker stderr. No raw stderr, traceback, exception message,
path, prompt or canary is released in reports. Successful startup remains silent;
any stderr still rejects an otherwise successful process result.

Startup failure JSON may add model_worker_before_cleanup and model_worker_after_stop:
bounded channel category, process state, available exit code, observed stderr count,
capture completeness and parsed stage/type if a complete valid diagnostic exists.
Before-stop and after-stop-attempt observations are distinct. Post-stop exit codes
are NOT evidence of the original natural failure. Missing data stays unavailable,
not fabricated zero; an unfinished count is provisional. A hang or loader failure
may still lack a stage. Diagnostics never establish readiness or authorize effects.

## Preserved Setup And Limits

Actual product consent/setup/cleanup still own a fresh private ProgramData attempt,
ordinary AppContainer, zero capabilities, reduced tokens, one-process jobs,
child-process block and six child-scoped WFP deny-all filters. Trusted medium
worker remains outside child containment and implements no networking. No registry,
loopback, account, service, listener or new grant. Keep customer-like Windows 11 Pro
x64 build 26300.9711; do not manually preconfigure OS permissions to pass the test.

Embedded Python 3.13.14, pinned Hermes and 64 distribution versions are unchanged.
No Python installation, wheel modification or new dependency. Same four protected
host files remain evidence; private UTC does not change Windows timezone.
Worker ready 5 seconds, RPC 2 seconds, partial frame 1 second, child cooperative/
host 22/30 seconds. Frames 8192 bytes; cumulative channel/audit 131072; request/
response/stderr 4096; report 65536; model output 1024. Diagnostic parsing retains
at most 256 bytes; existing stderr enforcement is unchanged. Exit snapshot reads
use the already owned process handle with zero wait. Both jobs stop before security
cleanup. No retry, recovery, new inference, customer data access or charge.

## Artifact And Run Gates

Build directory: .codex-build/maya-offline-model-validation-20261031-2.
Archive: Maya-Offline-Model-Validation-2.zip, containing a same-named folder with
MayaProtectedPython.exe, this README, package-manifest.json and unchanged notices.
Manifest/source-freeze and local checksums/verification receipts bind exact source,
configuration, dependencies, payload/index/resources and output hashes. All prior
artifacts, especially failed Validation 1, remain untouched. Assembly never loads
or executes the product assembly or bundled Hermes/SDK.

Copy/extract into a SEPARATE VM folder; return the full guest EXE path and SHA256.
Do not launch before separate matching-artifact one-run approval and fresh product
consent. Then use RDP and the real launcher, not an extra VM automation wrapper.
Return complete result JSON even on failure and whether output stayed blank.
Stop on failure; do not retry, adjust OS permissions or extend timeouts.
Subsequent cleanup checks bind this attempt's PIDs/root/package SID/filter IDs.

All qualification flags remain false. Profile deletion remains product-reported
unless independently checked. Other M03 variants, later cases, M2, real inference,
Gate A, full containment and production remain pending/unapproved.

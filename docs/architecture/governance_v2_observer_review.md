# Python Comparison Observer - Preparation Review

## Scope And Decision

2026-10-17: the user authorized observer implementation within Step 1 of
[the Azure procedure](governance_v2_python_azure_procedure.md). The user also
explicitly approved a common outer Windows job for A-D: contain each launcher and
descendants, disallow breakaway and request tree termination on timeout/observer
exit. Both frozen launcher binaries remain unchanged. Adding the outer job is a
declared common launch-context change, including a nested job for Maya; compatibility
is not inferred from the Microsoft API documentation or successful compilation.

The first delivery supplied the evidence core and read/job primitives only.
The user subsequently authorized continuation: stage 2 now adds launcher adapters,
supervision and a native backend, with the joint source review recorded below.
It remains an unarmed x64 .NET Framework library with no executable entry point;
its native backend is compiled but never constructed/executed by local fixtures.
No native token, job, launcher or managed-Python operation was executed during
validation. No VM/security, upload or A-D permission follows from preparation.
Gate A and production remain blocked.

## Fixed Implementation Sequence Within Step 1

1. **Evidence core and cleanup primitives: implemented, fixture-tested.** Retain
   PID/creation-time/image identity; inspect documented token fields and selected
   descriptor controls; retain independent child exit status; provide the approved
   outer-job primitive and the 95/100-second deadline decision rules. Native
   behavior remains unqualified.
2. **Launcher supervision adapters and joint source review: source candidate
   implemented and fixture-reviewed, not native-qualified.**
   Attach an observer-owned suspended launcher to the outer job before resume;
   establish selected-child ancestry/identity without trusting stdout alone;
   distinguish Maya's ordinary suspended control; retain handles through exit;
   bind exact expected case capabilities and frozen artifacts. Integrate bounded
   admission/output handling, early-exit/missed-observation reporting, process-tree
   read-back, actual launch-context evidence and one shared case clock. Validate
   these adapter decisions with inert fixtures before declaring Step 1 complete.
   The implementation and limits are recorded in the stage 2 review below.
3. **Freeze the reviewed observer for later execution: partially prepared, not completed.** Record
   final source/binary hashes and exact invocation in the execution manifest.
   Move to the existing VM preparation/approval gates, not a workstation launch.
   Actual token/LPAC, discovery timing, nested-job compatibility and termination
   read-back are VM-only evidence in the separately authorized comparison; there
   is no additional startup matrix, automatic retry or ordinary-mode fallback.
   The unarmed candidate's hashes and proposed guest layout are now recorded in
   `governance-v2-observer-review-package.json`. This is not the final execution
   manifest: the trusted executable host, guest-specific bindings and approved
   invocation remain absent. Do not treat a DLL path as a launch command.

These are implementation dependencies inside the existing observer sub-item,
not new product gates or approval to move past Step 1. Do not insert helper/Hermes
patches, a driver, debugger, registry grant or new diagnostic experiment to make
an adapter work. Present any required contract change for permission first.

## Implemented Evidence Behavior

`scripts/native/governance_v2_observer.cs` is separate from the frozen Maya helper.
The process reader requests only query-limited-information/synchronize rights,
pins creation time and full image path on a retained handle, and rejects a reused
PID or changed identity. It does not accept a reported PID as sufficient ancestry
evidence; stage 2 adds ancestry/job membership and retained-handle correlation.

Token reads use size-negotiated, bounded buffers, x64-checked layouts and SID bounds.
They inspect user, AppContainer, package, Low IL and the complete capability list,
including attributes. Extra/missing/duplicate/disabled capabilities fail the
comparison. Expected identity/capability inputs must eventually come from the
reviewed host execution manifest, never child output. The core alone does not
bind cases; stage 2's immutable launch plan fixes A-D commands/capability names.
The final execution-manifest/host-permission binding remains stage 3/later VM gates.

DuplicateToken/AccessCheck operate on memory-only descriptors: explicit selected
package access must allow; AAP-only, wrong-package and no-grant checks must deny.
API failures are distinct from successful access denials. There is no class-46
LPAC assumption. These selected-token checks do not manufacture an independently
observed ordinary AppContainer control. Maya's frozen helper already creates its
suspended control; stage 2 now requires its independently observed ordinary-token
profile and retained-handle exit zero before admission. Missing observation fails
the case, rather than treating the helper's final JSON as that independent proof.

An exit before token read is partial evidence even for exit zero. Exit status is
read only after the retained process handle signals, so numeric code 259 is not
confused with an active process. The prior token observation can be retained for
a later exit read. Result reason codes are allowlisted, with no raw exception,
path, SID, command line, console output or environment included in the result.
Raw identity values remain private in-memory inputs, not sanitized report fields.
No startup/containment/production-success label is produced.

## Approved Outer Job - Implemented Primitive, Not Supervision Yet

The outer job requests only KILL_ON_JOB_CLOSE, with no breakaway, UI, process-count,
memory or token limit. `AttachOwnedSuspendedLauncher` remains a trusted-caller API,
not independent proof that a supplied handle is suspended/owned. Stage 2 now creates
and retains its own launcher handles, attaches that returned handle before resume,
and checks ordering/time on both sides of the backend interface. No arbitrary
process was attached during preparation; native ordering remains VM-unqualified.

The job exposes active-member read-back and bounded terminate/read-back using
the shared case stopwatch. Deadline rules reserve the final five seconds of the
existing 100-second case budget for cleanup. Stage 1 did not implement a watchdog;
stage 2 now checks that clock around dispatch/admission/collection and supplies an
independent deadline watcher plus bounded cleanup. Native timing is not proven.
If no time remains, cleanup cannot be declared confirmed.
Closing a job handle is a safety net, not observed proof of process termination.
It does not restore WFP, profiles, registry descriptors or NIC state. Those remain
separate procedure requirements; networking must stay disabled on uncertainty.

The common job changes launch context even though executable bytes do not change.
Its nested interaction with Maya's existing job may affect startup. Unsupported
nesting or member discovery is an invalid/blocked case, never permission to drop
the outer job, replace the launcher or extend the test budget. General descendant
or sandbox-escape qualification is not established by these APIs.

Primary API references reviewed:
[GetTokenInformation](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-gettokeninformation),
[AccessCheck](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-accesscheck),
[GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes),
[job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[nested jobs](https://learn.microsoft.com/en-us/windows/win32/procthread/nested-jobs).

## Validation And Artifacts

The C# fixture executable uses only inert interface implementations and managed
layout checks. It makes no native process/token/job calls and reports 57 passing
checks for profile/identity mismatches, capability sets/attributes, API-like faults,
early/late exit, exit 259, retained identity, sanitized errors and deadline edges.
These are evidence-policy tests, not tests of native APIs, PID discovery, outer-job
enforcement, cleanup or a real launcher. The Windows test wrapper compiles this
fixture and verifies its fixed report; non-Windows CI skips that executable test
explicitly and still runs portable source/input guards.

The initial command-sandbox fixture compilation failed at temporary Win32 resource
creation/cleanup with access denied. The permissioned unsandboxed fixture run
passes; no error was interpreted as a passing token denial. A separate artifact
compile first used an incompatible relative slash path; corrected absolute source
paths compiled the library/fixtures with warnings treated as errors. Neither
failure consumed an A-D attempt or prompted a security-permission correction.

Local artifacts are ignored under `.codex-build/governance-v2-observer-20261017`.
The library is not bundled into a frozen reproduction, wheel or installer.
Historical comparison contracts retain their frozen hashes. No generated C# or
test binaries are added to Git. The final armed supervisor/hash is not established
by this first library build.

Historical first-stage source SHA256 (not the current stage 2 source):
`8adb73f3fe2514c4af55bf5d61941c5eedd5a7fd76766eaeabf030e614f25d77`.
Library SHA256:
`1956096f4c160c878dd49690da1f3b1d5825017f3124fb840fd5d36497dd292c`.
The local `preparation-record.json` binds source, fixtures and artifact hashes;
all execution/qualification flags remain false. These first-stage values are not
the future complete observer execution-manifest binding.

Validation: 38 combined `tests.test_governance_v2_observer` and
`tests.test_governance_v2_python_repro` tests pass, including the 57 inert C# checks;
context validation, Python compilation and diff whitespace checks pass. The old
helper and both prepared-bundle manifest hashes remain unchanged. The existing
Plan V2 checkout LF-to-CRLF warning persists; no global Git setting was changed.

## Stage 2 Joint Source Review

The user requested continuation on 2026-10-17. Scope stayed within the existing
observer sub-item. No frozen launcher/helper, probe or comparison contract was
modified. The current source is split into the evidence core, the fixed-case
adapter/controller and the native lab backend:

- `scripts/native/governance_v2_observer.cs`
- `scripts/native/governance_v2_observer_supervision.cs`
- `scripts/native/governance_v2_observer_launch.cs`

| Obligation | Implemented Source Behavior | Qualification Limit |
| --- | --- | --- |
| Fixed inputs/cases | Immutable A-D plan, pinned base inventory/helper/reference hashes, bounded non-reparse runtime inventory walk | Future reviewed guest kit must contain the reference at the declared input path; original bundles remain unchanged |
| Owned launcher | CreateProcessW suspended, explicit three-handle inheritance, attach outer job, require ResumeThread previous count one | Native ownership/nesting/creation behavior has not run |
| Selected child | Job membership, parent PID, creation time, image path and retained handle; no stdout-PID authority | A process may exit before it can be opened; missing observation invalidates the case |
| Ordinary control | Separate ordinary-token AccessCheck result, same expected identity/capabilities and exit zero before Maya admission | The short-lived control may be missed; no source-attestation substitution or retry |
| Admission/output | One inert newline only after selected/control/context checks; bounded nonblocking stdout/stderr collection, no raw reporting | Pipe/console behavior and WMI timing remain VM-only evidence |
| Deadline | One monotonic case clock, 95-second watcher termination request, read-back/worker joining within 100 seconds | Windows scheduling/API timing is not fixture-proven or a hard real-time guarantee |
| Cleanup | Active-job population read-back; owned unassigned suspended launcher cleanup; no job-handle recycling while watcher lives | Failed/late cleanup or pending query yields uncertainty and no network permission |
| Outcomes | Fixed reason codes, independently captured exits, fresh exact beacon, immutable production/network/security-cleanup false flags | Evidence collection is not startup success, containment, security restoration or Gate A acceptance |

### Exact Commands And Context

The proposed guest root is fixed to `C:\MayaGateA`; the VM preparation decision
must still confirm it. A uses the frozen helper's `launch <stage> 18765` from
the workspace root. B-D use the same pinned Microsoft reference at
`.codex-build/governance-v2-reference-tools/LaunchAppContainer.exe`, with `-l -w`,
without `-r` or `-k`, from private state. The nested `-i` argument is the quoted
Python executable, `-I -S`, and the quoted frozen worker. No alternate executable,
shell, live provider or custom capability list is accepted by the plan.

The parent environment is rebuilt from the exact eight approved names, not
inherited wholesale. Native PATH uses the same Environment.SystemDirectory value
as the frozen x64 Maya helper, including its spelling, so B-D do not introduce a
different path value. Existing launcher console/job/creation differences remain
declared confounders; this is not a single-variable proof of a Maya helper defect.

A bounded asynchronous Windows WMI query checks the selected child's actual
command line against the fixed command. No process-memory read, debugger, registry
grant, service installation or diagnostic trace was added. WMI and .NET Framework
are guest diagnostic prerequisites to verify later, not customer installer additions.
The query may exceed its API timeout; the supervisor does not wait indefinitely.
Incomplete query work prevents confirmed cleanup. It retains the process handle
that pins a still-pending PID-based query; the guest must remain offline and follow
the existing stop/deallocate procedure on uncertainty, not continue or reconnect.

Child cwd/environment are controlled through verified creation arguments and the
frozen launchers' inheritance/explicit-environment behavior, not an independent
read of the child's environment block. A fresh exact beacon in private state also
witnesses cwd after Python entry. A pre-entry failure has no beacon-based cwd
witness; reports must retain that distinction rather than claim a memory/OS
read-back that did not occur. The final execution manifest must record these
creation inputs and their evidence basis explicitly.

### Missing Processes And Failure Semantics

Polling and job notifications are not guaranteed to capture short-lived tokens.
The implementation uses live member enumeration plus aggregate job accounting,
not notification delivery as proof that no process existed. A total/active count
showing an exited unobserved process stops the case early, before Maya admission
when applicable. Unclassified held-child exit codes may be retained as partial
evidence, never relabelled as the selected LPAC exit. API/open/token/command errors,
PID reuse, unexpected ancestry/image/capability or inconsistent counts invalidate
the case and trigger bounded tree cleanup. There is no automatic repeat.

The helper's exact fixed return frame is byte-compared against the independently
observed child exit. A duplicate-key, string/bool exit code, prefix diagnostic or
partial frame is rejected. This corroborates completion; it does not replace
ordinary-control or selected-token observation. The Python beacon is also checked
byte-for-byte; BOMs/alternate encodings/extra bytes are not silently normalized.

`CaseEvidenceComplete` means the bounded diagnostic evidence was collected,
including observed startup failure; it is not a successful-startup flag. Only
`observer.python_entry_observed`, exit zero and the fresh exact beacon describe
Python entry. Other observed outcomes stay `startup_not_established`, invalid,
deadline or cleanup-uncertain. Every result still refuses production qualification,
security-cleanup verification and permission to resume networking.

### Review Corrections And Remaining Gates

The source review corrected the initial cooperative-only timeout by adding the
independent watcher. It also corrected SID release to the documented FreeSid API,
checked native layouts, kept pipe handles tracked on close failure, guarded input
traversal before descent, rejected missing exit-code values, made fixed return
frames unambiguous and preserved pending-query process identity through cleanup.
These changes are in the diagnostic observer only, not another Hermes/helper patch.

The native backend requires a future trusted VM host's explicit execution-permission
callback and then checks the frozen OS build/edition, VM model, exact operator SID
and a named local elevated account. SYSTEM/service/remote-domain substitutions
are refused. The callback is an operational approval input, not cryptographic
authorization or proof of an Azure VM identity/NIC/WFP/ACL/snapshot read-back.
The final reviewed execution host must bind those prerequisite records and human
permissions before invoking it. No such host invocation or approval was created.

Stage 2 is complete only as a source/fixture candidate and joint review. Next is
the existing stage 3 observer freeze/manifest and exact invocation review. Do not
skip to VM provisioning or comparison. Native discovery/control timing, WMI, nested
jobs, deadline and termination read-back remain unqualified until the separately
approved VM execution. No additional startup experiment is authorized by a miss.

Additional primary references:
[process snapshots](https://learn.microsoft.com/en-us/windows/win32/api/tlhelp32/nf-tlhelp32-createtoolhelp32snapshot),
[job notification limitations](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_associate_completion_port),
[redirected process handles](https://learn.microsoft.com/en-us/windows/win32/procthread/creating-a-child-process-with-redirected-input-and-output),
[Win32_Process command line](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-process),
[profile SID ownership](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-deriveappcontainersidfromappcontainername).

Stage 2 builds are kept separately in the ignored directory
`.codex-build/governance-v2-observer-supervision-20261017`. The first-stage library
and preparation record are retained unchanged; their source hashes are historical,
not the current source binding. The new candidate record is not an execution manifest.

## Stage 3 Review Package - Unarmed Candidate Only

2026-10-17: the user's continuation authorizes finishing local validation and
preparing this review package, not deployment or native testing. The candidate
source and existing artifact bytes are bound in
[the review-package record](governance-v2-observer-review-package.json).
Rebuilding with this compiler need not reproduce the same binary hash; these
hashes identify the retained bytes. A changed build needs a new reviewed binding.
The original bundles, helper, reference and historical observer artifacts are
not rewritten or extended by this record. No transfer archive was created.

### Proposed VM Layout

```text
C:\MayaGateA\
  reproduction-manifest.json          unchanged base manifest
  observer\
    Maya.GateA.Supervision.dll        trusted administrator-side library
  .codex-build\
    governance-v2-native-tools\GateANative.exe
    governance-v2-reference-tools\LaunchAppContainer.exe
    governance-v2-lpac-stage\
      runtime\python\python.exe
      runtime\worker.py
      state\                         empty before each authorized case
```

This is a review layout, not an installed/deployed kit. The reference file would
be added to a new assembled kit, never inserted into the frozen base bundle.
Do not grant the restricted Python access to the observer directory or host
authorization records; review their exact ACLs during VM preparation. Fixture
executables, source checkouts, development tools and customer application packages
are not guest payload dependencies. The observer is not a Windows service, startup
task, driver, Hermes plugin or Maya installer component. Its runtime dependencies
are the guest's x64 .NET Framework and WMI; their presence remains a prerequisite,
not permission to install components or silently change the guest.

### Invocation Review And Explicit Remaining Gap

The current artifact is a library, not an executable supervisor. Its reviewed
call order is `LaunchPlan`, `NativeSupervisionBackend`, then `Supervision.Run`.
There is no approved shell command to run it. Direct helper/reference commands
or a script passing an unconditional true callback are not substitutes.

The final trusted host must bind the actual guest/operator/package identities,
frozen kit, console/offline evidence and per-case security preparations to the
explicit execution decision. It must maintain the one-attempt record across host
restarts; `LaunchPlan.Claim` prevents only reuse of one in-memory plan, not another
process recreating that plan. It must serialize only allowlisted result fields,
preserve failed attempts, stop the remaining matrix on invalid/uncertain evidence,
and never reconnect networking itself. Its source/hash and exact invocation must
be reviewed before execution. This is the remaining invocation obligation in
existing stage 3, not a completed host or authorization for another diagnostic.

Guest-specific values are deliberately unset rather than fabricated from old
screenshots. The JSON lists these remaining bindings without customer identifiers
or secrets. It is explicitly non-executable and grants no sharing, security or
execution permission. Stage 3 and Step 1 remain incomplete until the executable
host/invocation review is satisfied; subsequent Azure preparation, rehearsal and
execution approvals remain separate. Do not bypass the sequence by testing the
library directly on this workstation or the VM.

### Final Candidate Validation

The x64 library and inert fixture executable compile with warnings treated as
errors. The fixture reports **200 passing managed checks**, with `native_calls`
and `production_qualified` false. The combined observer, reproduction and
line-ending suite passed 42 tests before adding the three review-record guards.
One attempted suite invocation used a nonexistent line-ending module name; its
import failure was corrected to the existing module, not counted as a pass.
The review-record guards also verify source fingerprints, unarmed status and the
unchanged A-D budget. Final aggregate results are recorded after validation below.

Final result: **45 tests pass**, zero skips, including the 200 inert C# checks;
product-context validation, Python compilation and diff whitespace checks pass.
All 802 files in the 26H2 inventory and all 800 in the historical 25H2 inventory
were rehashed successfully. Both manifest hashes, the frozen helper/reference,
historical observer library and all four original comparison documents remain
unchanged. The ignored stage 2 `preparation-record.json` records these checks;
the test binaries remain ignored and are not committed or deployed.

The retained library SHA256 is
`1a07c156ddd55b5e18066d747344721b71100083c1e9a29ad0011d6344aafcdc`;
the inert fixture executable SHA256 is
`4d38ea3aa65bd1c7aac73bd58e9956e921a971d8afda85b078553e0fd5265047`.
The plan now has a targeted LF attribute; no global Git conversion setting or
unrelated line-ending policy changed. Native compatibility, deadlines, token/job
operations and process cleanup have not been exercised by these checks.

## Subsequent Stage 3 Entry-Point Candidate

The user requested continuation of the remaining host work on 2026-10-17.
The separate [host review](governance_v2_observer_host_review.md) and successor
`governance-v2-observer-host-review.json` record a compiled, fixture-tested entry
point and exact proposed command format against this unchanged library. The
earlier absence of an executable host is now historical; no ready-to-run manifest
or VM permission has been supplied. Review the candidate before the existing
VM preparation-impact gate. Local claims prevent process-restart reuse but do
not survive a baseline disk restore; the external ordered attempt reservation
remains a trusted procedural requirement, not a fabricated cross-snapshot guarantee.
No native host operation, launcher execution or product qualification occurred.

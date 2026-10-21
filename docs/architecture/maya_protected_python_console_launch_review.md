# Protected Python Console Launch Review

## Scope And Result

2026-10-21: the user requested a focused product-code review after the final
targeted capture localized a false ConsoleInitialize result. This is source
review and documentation, not approval to change code, prepare Package 6, run
Maya/Python/CDB, inspect deeper Windows helpers, or modify guest security.

**No confirmed pipe-inheritance or native-layout defect was found.** The strongest
bounded compatibility candidate is to replace CREATE_NO_WINDOW with
DETACHED_PROCESS while retaining explicit pipe redirection and every restriction.
This is a proposed launch-mode change, not a proven root cause or working fix.

The user subsequently approved preparation of Package 6 with this change only,
explicitly without running it. Implementation/build receipts belong in the
[startup package record](maya_protected_python_startup_package.md). The review
findings remain evidence, not a successful native result or renewed trace budget.

Subsequently, the operator confirmed the older session closed and the matching
Package 6 EXE hash, then explicitly approved one ordinary RDP run. Its
[reported result](maya_protected_python_startup_package.md#package-6-operator-result-received-2026-10-21)
is startup_failed with natural exit 0xC0000022, empty output, no beacons and
reported complete cleanup. The candidate failed acceptance. The changed exit
does not establish console success or the denied operation/resource. No further
grant, patch, native run or debugger investigation is authorized by that result.

The [final capture](maya_protected_python_final_diagnostic.md#captured-outcome-2026-10-20)
observed ConsoleInitialize return zero at RVA 0x4ebe6, stage 600, then outer base
return zero and natural exit 0xC0000142. Its child flag/full-image-path limitations
remain; the log does not establish the inner console failure or extended error.
Maya/debugger closure remains unconfirmed, despite reported complete cleanup.
No closure or ordinary-run result is inferred from this source review.

## Frozen Input Check

All seven source/test hashes still match the Package 5 manifest. Its executable,
payload and manifests were not changed. Reading python/python.exe directly from
the existing payload ZIP as data confirms PE machine 0x8664 and subsystem 3
(Windows CUI), SHA256
`ef8f51028ac5329641985112f8efb1c2d4c47c86b8011ddf7e6fae21e2b4e5a1`.
No extracted executable was launched and no replacement executable was downloaded.

## Findings

### Pipe Wiring Matches The Documented Pattern

WindowsIsolation.cs:358-366 creates three inheritable child pipe ends, clears
inheritance on the parent-only ends, and lists exactly the three child handles
in PROC_THREAD_ATTRIBUTE_HANDLE_LIST. Lines 373-378 set STARTF_USESTDHANDLES,
populate all three handles and pass bInheritHandles=true. The x64 Startup and
StartupEx field layout agrees with the existing 104/112-byte fixtures.

This agrees with Microsoft's
[pipe-redirection example](https://learn.microsoft.com/en-us/windows/win32/procthread/creating-a-child-process-with-redirected-input-and-output),
[STARTUPINFO requirements](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/ns-processthreadsapi-startupinfow)
and [explicit handle-list contract](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute).
It is a source-contract check, not proof of the actual child handle table,
native pipe access under LPAC, or successful console initialization.

The parent's copies of child pipe ends are closed only after successful process
creation or failure unwinding. That is not equivalent to closing the child's
inherited copies. Closing the parent stdin writer makes EOF intentional for this
noninteractive startup check; startup_check.py does not read stdin. Output/error
readers start before ResumeThread and drain bounded output concurrently. No
console handle is substituted for an anonymous pipe in this source.

### Console Mode Is The Focused Compatibility Lead

WindowsIsolation.cs:378 uses creation flags **0x08080404**: no-window,
extended startup information, Unicode environment and suspended creation.
No incompatible detached/new-console combination is currently set. The current
flag combination is not itself a documented invalid API use.

Microsoft distinguishes a console application's no-window launch from an
explicitly detached console launch. DETACHED_PROCESS starts without console
attachment; standard handles can separately refer to redirected pipes. These
contracts make detached operation a candidate for this pipe-only worker, but do
not promise that Windows' internal ConsoleInitialize is skipped or succeeds under
this exact reduced-token/LPAC/job context.
[Creation of a console](https://learn.microsoft.com/en-us/windows/console/creation-of-a-console),
[process creation flags](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags),
[console versus redirected handles](https://learn.microsoft.com/en-us/windows/console/console-handles).

The inference is limited: the observed failure is in console initialization, so
altering only the documented console-association mode is more targeted than
changing unrelated permissions or payload. No particular denied device, service,
desktop, handle, token property or flag has been proved responsible. The presence
of STARTF_USESTDHANDLES alone does not prove invalid child handles. Do not infer
that CREATE_NO_WINDOW always creates an extra console-host process or that the
one-process job limit caused this failure.

### Existing Checks Do Not Qualify This Launch Mode

The current 11 Python unit/static checks pass, but they use mocked Python state
and inspect source wiring. The assertion at tests/test_windows_protected_python.py:117
pins the existing creation-flags literal; it does not exercise native process
creation or validate the child standard handles. Existing C# fixture layout tests
also cannot establish that either console mode works on the VM. No native fixture
was executed in this review. This is a coverage gap, not proof that current source
has a specific pipe defect or that changing a flag fixes it.

## Proposed Candidate, Not Implemented

If separately approved, prepare a single product-owned compatibility candidate:

- Replace CREATE_NO_WINDOW (0x08000000) with DETACHED_PROCESS (0x00000008).
  The resulting creation flags are **0x0008040c**. Replace the mode rather than
  adding both; keep the other three creation bits unchanged.
- Keep the same python.exe, arguments, payload hashes, Unicode environment,
  private cwd, three explicit inherited pipes and STARTF_USESTDHANDLES.
- Keep the same reduced token, all child admission predicates, LPAC opt-out,
  zero capabilities, six package-specific WFP denies, file/integrity scopes,
  atomic job assignment, active-process limit, child-process policy and deadline.
- Retain product consent, exact stdout/state beacon criteria, failure reporting
  and cleanup. No retry with a console, ordinary token, pythonw.exe or broader
  grants. A failed candidate remains failure.
- Update only the affected launch-mode regression checks and version/provenance
  records when packaging. Explicit flag-mask checks should preserve suspension,
  Unicode and extended attributes and reject no-window/new-console/breakaway
  bits. Do not describe those inert checks as native qualification.

DETACHED_PROCESS is a console-association choice, not CREATE_BREAKAWAY_FROM_JOB.
The job attributes and token/WFP restrictions remain present in the proposed
source change; effective native enforcement would still require verification.
No new permission scope is proposed. Functional risks include another startup
failure, missing Python standard streams, changed console-control semantics or
unexpected native lifecycle behavior. Preserving source controls alone does not
qualify containment, future interactive console use or full Hermes behavior.

Any subsequent VM run is a separate ordinary product-candidate test through RDP,
after normal closure is confirmed, not a renewal of the consumed debugger budget.
Useful startup still requires zero exit plus both fresh matching beacons and
reported cleanup, with unchanged restriction verification. Success would qualify
only this bounded startup result, not containment/Gate A. Failure stops for review;
no automatic next mode or another tracing sequence is proposed.

## Verification And Decision

Review complete: seven frozen source/test hashes match; all 11 existing inert
Python checks pass. No product source/test was edited, no runtime rebuilt and no
guest command, native target launch, permission change or deeper disassembly was
performed. Context and whitespace checks are required for the review record.

Recommend the one-mode compatibility candidate for explicit preparation approval,
not a claim of a confirmed bug fix. If this hypothesis is not worth another
bounded product revision, stop this mechanism and assess another isolation
approach; do not continue broad Windows tracing. Gate A and production stay blocked.

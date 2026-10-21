# Package 5 Automatic Loader Capture And Outcome

## Authority And Status

Current status (2026-10-20): the one approved VM capture has returned a matching
child exit and localized the failing initializer to KERNELBASE.dll. Its internal
failure remains unexplained. The allowance is consumed; the sequence below is a
historical record, not authorization to repeat it. See the outcome section.

2026-10-20: after Package 5 again reported a natural 0xC0000142 exit, the user
approved preparing a corrected capture procedure for review before another run.
The initial document was preparation, not execution approval. No CDB, Maya,
Python, symbol checker or native security operation ran during preparation.
The operator subsequently supplied the Package 5 guest path:
`D:\Maya-Protected-Python-Startup-5\MayaProtectedPython.exe`.
Invocation binding is complete for that reported path, not independent file
verification. Providing the path did not authorize execution.

The user then explicitly approved **one debugger-controlled Package 5 run** under
this revised procedure, including its temporary child-memory loader tracing and
unchanged protections/deadline. VM hash/signature/cache/baseline and fresh-log
preflight remain pending. Guide that one attempt through the operator's RDP
session only after preflight; approval is not an actual launch or native result.
Launch consumes the allowance even if consent/configuration/capture later fails.

The operator subsequently confirmed the earlier Maya window closed and supplied
matching Package 5/CDB hashes, Valid CDB signature, Windows 10.0.26300.9711,
present cached PDB/capture directory, and absent `loader-02.log`/`ntsd.ini`.
These read-only preflight results match the fixed inputs. PDB presence is not a
fresh symbol-match check; the existing prior match is retained, and initial CDB
symbol/flag readback remains next. No CDB launch has yet been reported. Guide the
approved launch to its initial prompt only, then review readback before `g`.

The operator has now reported the initial CDB prompt from that approved launch;
the single launch allowance is consumed. `lmv m ntdll` shows the expected cached
PDB key and ntdll image/checksum/size, with NtGlobalFlag and NtGlobalFlag2 both
zero. This is the initial setup-host readback, not child tracing. The OS build
remains the separately reported 26300.9711; ntdll's 26100.9711 file-version field
does not replace that baseline. Continue only this session's pre-consent callback
configuration and review its `sx` listing before `g`. No child run, loader capture
or cleanup outcome is yet reported; do not start a second CDB/Maya session.

The operator subsequently supplied the initial `sx` listing: create/exit/load
and initial-break events are output/notify, with the proposed callback text;
the three selected failure codes are output and not handled, with first/second
chance logging. No configuration error was supplied. Other unexpected exceptions
retain their normal break settings. This supports proceeding with the planned
single `g` and product consent in this existing session, not another launch.
Actual child binding, flag changes, capture and outcome remain unreported.

The operator subsequently confirmed the earlier Maya window closed and supplied
matching Package 5/CDB hashes, Valid CDB signature, Windows 10.0.26300.9711,
present cached PDB/capture directory, and absent `loader-02.log`/`ntsd.ini`.
These read-only preflight results match the fixed inputs. PDB presence is not a
fresh symbol-match check; the existing prior match is retained, and initial CDB
symbol/flag readback remains next. No CDB launch has yet been reported. Guide the
approved launch to its initial prompt only, then review readback before `g`.

The [customer-like Windows testing contract](governance_v2_customer_windows_testing.md)
and [startup component contract](maya_protected_python_startup_package.md) remain
controlling. This is a proposed diagnostic exception using the already installed
Microsoft debugger, not a replacement for normal customer-path tests. Preserve
the [earlier loader procedure and consumed result](maya_protected_python_loader_diagnostic.md).
Neither that allowance nor the historical A-D matrix is renewed.

No command file, wrapper, supervisor, observer, new tool installation, download,
product correction or rebuilt package is included. The operator would perform
one now-approved attempt through RDP. Preparation supplies no approval
for a repeat after setup, configuration, capture or startup failure.

## Question And Fixed Inputs

Question: can loader output identify the DLL initialization operation associated
with Package 5's 0xC0000142 exit, without manual debugger interaction during its
protected startup? A last lookup failure is not itself an identified cause.

- Package 5 EXE SHA256:
  `6709bb7673c1eca2fecec006cf2c72dd7b3059278c3e7a92d59034c6bac92b66`.
- Operator-supplied guest EXE path:
  `D:\Maya-Protected-Python-Startup-5\MayaProtectedPython.exe`.
- Package 5 ZIP SHA256:
  `3523429149640869ef4237011e44d6ffb01dcb747ea14b95fa74a66c354457df`.
- Existing Windows 11 Pro x64 26300.9711, same operator/account and RDP session.
- Unchanged Python 3.13.14 payload, reduced-token and LPAC admission checks,
  zero capabilities, six WFP denies, file grants, process/job constraints,
  process-local critical-error handling and product-owned cleanup.
- Unchanged **30,000 ms** product wait. Debugging does not turn timeout into a
  pass or justify extending the deadline.
- Existing CDB x64 10.0.26100.1, SHA256:
  `37095ef02baf6bb87e7d0eb4b0fc466dbe2c87cabc60afd114394db6f62edfe9`.
- Existing diagnostic root: `%LOCALAPPDATA%\MayaLoaderTrace-20261019`.
- Existing exact ntdll PDB key:
  `ntdll.pdb/C031D45B0DA18A6E74D06ED6AB2DD9E11/ntdll.pdb`.
- Fresh proposed log: `capture\loader-02.log`. Do not overwrite or append to
  `loader-01.log` or reuse an existing `loader-02.log`.

The Package 5 report verifies empty output capture and no startup beacon, with
cleanup reported complete. It does not identify the DLL/resource, independently
qualify cleanup or prove why the earlier debugger attempt timed out.

## Correction To The Capture Procedure

The old sequence stopped at child creation and waited for a chat exchange before
continuing the child. The new sequence configures all callbacks at Maya's initial
debugger prompt, before its UI/consent and before its protected-child wait exists.
After continuation and product consent there is **no planned manual debugger stop**.

Use a process-name-filtered creation notification to bind the first `python.exe`
child's PID. An ntdll-load notification then enables loader snaps only when the
current PID equals that binding and differs from the recorded Maya host PID.
Repeated matching creation is logged as invalid, without replacing the binding.
The name filter is a diagnostic selector, not full-path authentication: validate
the final loader image path and PID against the fresh product report as well.

These are notify-mode (`sxn`) event callbacks. They run without an operator
continuation command; do not use nested `g` commands or manually resume the
product-created suspended thread. All configured exception handling statuses
remain unchanged; no exception is marked handled to bypass startup failure.
The selected failure events log context at both chances without waiting for input.

The only intended target-memory change is `!gflag +sls` in the PID-selected
child, after ntdll metadata is available. Parent flags, tokens, return values,
code, protection checks and persistent OS settings are not patched. Flag readback
must show only Show Loader Snaps (0x2) added. Callback text/markers alone do not
prove that the flag was set or that the right child was selected.

The debugger still pauses processes briefly while handling events and printing
output. Symbol lookup and stack generation also take time. Removing manual waits
reduces one confound; it does not eliminate timing interference or guarantee a
useful capture. Another timeout or incomplete trace is inconclusive and consumes
the proposed attempt, not permission to correct and retry.

## Operator Sequence (Historical; Allowance Consumed)

### 1. Bind And Check Before Launch

Use the operator-supplied Package 5 path above; require a current hash match before
launch. Do not infer it from the Package 4 path or use an old launcher. The user
explicitly approved this disclosed one-launch scope; use Maya's own consent once
after preflight and initial debugger configuration review. No renewed approval
is implied for a later correction or retry.

Before that approved launch, verify the product and CDB hashes above, Valid
Microsoft CDB signature, unchanged OS baseline, existing exact cached PDB and
closed previous Maya/CDB sessions with cleanup reported complete. Stop on missing
or changed inputs, pending cleanup, warning or unsupported build; no repair,
new symbols, additional download or repeated launch is authorized by this plan.

The existing private capture directory must contain no `ntsd.ini` and no proposed
log. The symbol path below names only the existing local store, with no upstream
URL; `-sins` excludes inherited symbol-path environment settings. No `.symfix`,
network debugger, postmortem registration or persistent GFlags setting is used.

Invocation template for the bound, approved VM run only:

```powershell
$trace = Join-Path $env:LOCALAPPDATA 'MayaLoaderTrace-20261019'
$maya = 'D:\Maya-Protected-Python-Startup-5\MayaProtectedPython.exe'
$log = Join-Path $trace 'capture\loader-02.log'
```

After the checks and native-run approval, from an elevated same-user PowerShell
window, with no alternate credentials:

```powershell
Set-Location -LiteralPath "$trace\capture"
& "$trace\debugger\cdb.exe" -o -hd -nosqm -noshell -noinh -sins -y "srv*$trace\symbols" -logo $log $maya
```

The path is now bound. Do not launch until checks pass and run approval is
recorded. Launch consumes that allowance even if Maya never reaches consent.
The elevated debugger is trusted and outside LPAC, with target-memory access;
this launch context is not normal-customer or containment qualification.

### 2. Configure Before Consent

At the initial CDB prompt, **before continuing Maya**, first enter the read-only
symbol/flag checks. Return their output for review if it differs from the cached
guest ntdll match; no live run is used to fix symbol problems.

```text
.reload /f ntdll.dll
lmv m ntdll
!gflag
```

While still paused at that initial prompt, enter this complete configuration.
`$t0` and `$t1` are debugger variables, not writes to Maya's registers or token.
Do not enter this in PowerShell and do not save it as a command script.

```text
.expr /s masm
r $t0 = @$tpid
r $t1 = 0
.childdbg 1
sxn ibp
sxn -c ".if ((@$t1 == 0) & (@$tpid != @$t0)) { r $t1 = @$tpid; .echo MAYA_AUTO_PYTHON_CREATE; |; .lastevent; } .else { .echo MAYA_AUTO_UNEXPECTED_PYTHON_CREATE; }" cpr:python.exe
sxn -c ".if ((@$t1 != 0) & (@$tpid == @$t1) & (@$tpid != @$t0)) { .echo MAYA_AUTO_CHILD_NTDLL; |; .reload /f ntdll.dll; !gflag; !gflag +sls; !gflag; }" ld:ntdll.dll
sxn -c ".echo MAYA_AUTO_PROCESS_EXIT; |; .lastevent" epr
sxn -c ".echo MAYA_AUTO_DLL_INIT_FIRST; .lastevent; .exr -1; kb" -c2 ".echo MAYA_AUTO_DLL_INIT_SECOND; .lastevent; .exr -1; kb" 0xc0000142
sxn -c ".echo MAYA_AUTO_ACCESS_FIRST; .lastevent; .exr -1; kb" -c2 ".echo MAYA_AUTO_ACCESS_SECOND; .lastevent; .exr -1; kb" 0xc0000022
sxn -c ".echo MAYA_AUTO_ACTIVATION_FIRST; .lastevent; .exr -1; kb" -c2 ".echo MAYA_AUTO_ACTIVATION_SECOND; .lastevent; .exr -1; kb" 0xc0150002
sx
```

Return the configuration listing for review **before** continuing. Require notify
status, correct process/module filters, and unchanged exception handling status.
The three diagnostic status codes may appear only as exits, so absence of their
exception callbacks is not evidence that those failures did not occur. Other
unexpected exceptions can still stop CDB; they are not silently handled here.

Only after initial configuration review, enter the one manual continuation:

```text
g
```

Maya then displays its normal disclosure. Read it, approve once and click Start
protected Python. Do not wait for a child-create prompt, paste another debugger
command, select a process, manually resume a thread or click Open results during
startup. The process-create and ntdll callbacks execute automatically.

### 3. Finish Or Report An Unexpected Stop

Let Maya finish the attempt and its cleanup. Preserve its displayed result and
fresh `attempt.json`. If cleanup is reported complete, close only the Maya window
normally, let CDB return to PowerShell, then copy the finished `loader-02.log` and
report privately. Do not close CDB first or kill the setup host to end capture.

An unexpected CDB stop, callback error, repeated Python creation, wrong PID/path,
flag mismatch, symbol mismatch, timeout or incomplete exit record invalidates the
intended capture/timing inference. Do not repair or add commands mid-startup.
If a stop blocks product cleanup, send the current screen for guidance; do not
blindly quit or kill a process. The existing reviewed child-only abort rule can
be considered only after positive identification of the current attempt's Python
child, leaving Maya alive to perform cleanup. Uncertain identity/cleanup stays
blocked, with no new cleanup helper or manual resource deletion.

## Evidence And Stop Conditions

Require the create binding, child ntdll event, actual before/after flag readback,
fresh product child PID/full image path and matching Package 5 hash. Distinguish
parent and child loader/exception output. Retain process-exit context and the
product report; a capture marker is not an authoritative process exit code.

Look for the first **terminal** child loader/init failure and its relevant DLL,
operation, status and stack. A preceding unsuccessful lookup or module mapping
does not identify a missing DLL, required grant or failing initializer. Even a
named DLL failure may not identify its underlying denied resource.

Keep logs private/ignored: they can contain paths, operator/attempt identifiers,
PIDs, module addresses and stacks. No memory dump, upload, live provider traffic,
credentials, customer documents or public sharing is proposed. No further run,
permission correction, capability expansion, runtime change or production/Gate A
claim follows the result. Stop for a separate decision, including if inconclusive.

## Captured Outcome (2026-10-20)

The operator supplied a pasted-text trace attachment and the fresh Package 5
report. The received text is 42,781 bytes, SHA256
`59e6e3107719d7c4c56c7163e61eb379206f7567f336ffa209359a15120ab785`.
This receipt identifies the pasted attachment, not a byte-verified original CDB
log. Raw account, path, attempt and process identifiers remain private.

The trace's host/child IDs, Package 5 image path and attempt-specific Python path
match the report. The report's launcher hash matches the fixed Package 5 hash.
One-based lines in that received text establish:

- Lines 252-267: actual Python-create and child-ntdll callbacks, with child
  NtGlobalFlag changing from zero to 0x2 and NtGlobalFlag2 remaining zero.
- Lines 269 and 290-297: the matching child begins Windows process initialization;
  KERNELBASE.dll is found through KnownDLL lookup and maps successfully.
- Lines 421-433: KERNELBASE.dll's initializer fails during DLL_PROCESS_ATTACH.
  Windows then unloads it and KERNEL32, propagating 0xC0000142 through
  LdrpInitializeKernel32Functions and process initialization.
- Lines 434-438: the matched child exits with code 0xC0000142. No python313.dll
  mapping appears in the supplied text. Failure precedes observed Python runtime
  loading or health-check output.

The matching product report says `startup_failed`, child resumed, both reduced
and child token checks verified, six network filters verified, payload verified,
and natural child exit observed before cleanup. Output capture is complete with
zero stdout/stderr bytes and no stdout/state beacon. Cleanup is reported complete;
Python startup, containment and production qualification remain false.

This is a natural-exit result, not another startup timeout. The capture localizes
the failing Windows initializer; it does not identify which operation inside it
failed, a denied resource, DLL corruption or a safe permission/code correction.
API-set redirection names containing registry/SideBySide are not observed access
denials. Selected exception callback strings occur in configuration, not as fired
failure callbacks; the exit event still directly records the failure. Subsequent
parent CLR/other first-chance events are not child initialization evidence.

The pasted tail does not show Maya's exit, debugger closure or a PowerShell return.
Reported cleanup is not independent resource-cleanup proof. If Maya/CDB are still
open and cleanup remains complete, close Maya normally and let CDB return to
PowerShell as already prescribed; do not blindly kill/quit the debugger.

The operator subsequently confirmed normal Maya/debugger session closure.
This resolves the session-state question, not independent security-cleanup proof.
The separately approved [launch-source review](maya_protected_python_launch_review.md)
found no confirmed correction for the initializer failure. Desktop/bootstrap
resource access remain leads, not established causes or permission to change them.

The single approved diagnostic allowance is consumed. No further capture,
permission expansion, Windows DLL replacement, runtime correction or qualification
is authorized by this result. Preserve the unchanged product and VM protections.

The subsequent user-approved preparation produced the separate
[initializer diagnostic proposal](maya_protected_python_initializer_diagnostic.md).
It does not reopen this consumed capture or authorize another native run.

## Preparation Checks And References

Preparation was documentation-only, checked against Microsoft references and
the source/Package 5 receipt without executing CDB. The subsequently approved
operator capture now demonstrates child binding, callbacks, flag readback and
exit correlation for this one attempt. It does not generally qualify debugger
timing, normal customer execution or containment. No new fixture, testing
application, source patch or additional native run is added by recording it.

References: [event filters and automatic commands](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/controlling-exceptions-and-events),
[SX command syntax](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/sx--sxd--sxe--sxi--sxn--sxr--sx---set-exceptions-),
[debugger variables](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/pseudo-register-syntax),
[MASM conditions](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/masm-numbers-and-operators),
[process flags](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-gflag),
[local symbol-store syntax](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/symbol-path),
[CDB options](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/cdb-command-line-options).

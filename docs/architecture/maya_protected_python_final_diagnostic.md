# Package 5 Final Targeted Failure Capture

## Authority And Hard Stop

2026-10-20: after the completed offline review, the user explicitly requested
the proposed final targeted diagnostic attempt. This authorizes one fresh CDB
session and at most one product-consented protected-child attempt on the existing
VM through RDP. The single protected-child attempt is now consumed. Its report
and trace localize a false ConsoleInitialize result in the instrumented child;
see the captured outcome below. The underlying cause/correction remains unproven.
Maya/debugger closure is not shown in the received log. All launch/configuration
commands below are historical, not instructions to repeat the test.

No product patch, Package 6, new test script/framework, download, installation,
workstation target execution, security grant, flag correction, OS/account change,
timeout increase, fallback or retry is included. Keep Package 5's product-owned
consent, reduced token, LPAC, zero extra capabilities, six WFP denies, file scope,
job/pipe restrictions and 30,000 ms child wait unchanged. The operator performs
VM commands; this chat has no direct guest session.

If this one attempt cannot identify a defensible failing operation/result, stop
this diagnostic route and evaluate another isolation approach. Even a localized
operation is not automatic permission to repair or broaden access. Gate A,
containment, Hermes and production remain unqualified.

## Fixed Inputs

Use the unchanged inputs from the
[initializer record](maya_protected_python_initializer_diagnostic.md#fixed-inputs-and-impact)
and [verified offline review](maya_protected_python_offline_review.md):

- Maya: `D:\Maya-Protected-Python-Startup-5\MayaProtectedPython.exe`, SHA256
  `6709bb7673c1eca2fecec006cf2c72dd7b3059278c3e7a92d59034c6bac92b66`.
- CDB under `%LOCALAPPDATA%\MayaLoaderTrace-20261019\debugger`, SHA256
  `37095ef02baf6bb87e7d0eb4b0fc466dbe2c87cabc60afd114394db6f62edfe9`,
  Valid Microsoft signature, same 64-bit tool. No replacement tooling.
- Guest System32/KERNELBASE.dll SHA256
  `5c29b73622ce0976e1ada566f31f2197ba0f8beaea89c3ec033366126172c3d0`.
  Public PDB GUID 79B50527-6F14-0450-EB83-DF0440BF06C6; image/DBI age 1,
  PDB Info age 2; received PDB SHA256
  `81658a0fe06f313f0370a4bd988e763bcf791da9a20124b24c3f2db4e3b36b43`.
- Existing exact ntdll PDB cache, Professional x64 build 26300.9711, same
  operator/RDP context and existing Windows settings. No Windows repair.
- Fresh private log `capture\base-failure-final-01.log`, no existing file and no
  `capture\ntsd.ini`. Preserve every earlier log; never overwrite or append.

## Four Points, No Rearming

The existing range output and exact DLL bytes support reading Windows' existing
two-byte `BasepInitializationStage` at KERNELBASE RVA **0x3adea2**. Five reviewed
RIP-relative stores at 0x4e94b, 0x4e9ab, 0x4eb9a, 0x4ebba and 0x4ebda all resolve
to this address. No new helper-body inspection was performed. This field is an
internal breadcrumb for this exact binary, not a supported Windows contract.

| Hardware execution point | RVA | Read-only observation |
| --- | --- | --- |
| Deeper base initializer entry | 0x4e6c0 | Attach reason, thread, initial stage, branch-selector scalar |
| Common attach false leaf, before AL is cleared | 0x4ec6b | EAX and stage at the actual false-return route |
| ConsoleInitialize result test | 0x4ebe6 | EAX/AL and stage before the Boolean test |
| Base-wrapper return in outer initializer | 0x506d | Final EAX/AL, stage and observation mask |

Each is a one-shot, child-process hardware execution breakpoint. At most four
hits, no rearming, stepping, instruction patching, return-value edits or automatic
repair. Commands end in automatic continuation to avoid an operator/chat pause
during the product deadline. Timing is still perturbed by debugging.

The selected branch scalar is a 32-bit read at the child PEB ProcessParameters
pointer +8, matching the verified signed test at RVA 0x4e96b. It is recorded on
entry and printed again at the false leaf. Do not assign general Windows field
semantics to this offset. No environment, heap, customer buffer or dump is read.
Module full paths, scalar metadata and at most eight stack frames per hit remain
private diagnostic data.

### Conditional Interpretation

Interpret only after matching PID, entry thread/reason, image paths/headers,
point bytes, initial zero stage, actual hardware-point installation, hit markers
and the fresh product report. Mere command text or an ARMING marker is not proof.

| Actual common-false hit stage | Candidate operation on the reviewed attach path |
| --- | --- |
| 0 | NtQuerySystemInformation; require negative EAX and initial stage zero |
| 0x64 / 100 | Server setup; nonnegative recorded selector selects CsrClientConnectToServer, negative selector selects CsrpLocalSetupForSecureProcess; require unchanged selector and negative EAX |
| 0x190 / 400 | BaseNlsDllInitialize; require AL zero |
| 0x1f4 / 500 | RtlInitializeCriticalSection; require negative EAX |

A Console result hit with AL zero and stage 0x258 / 600 takes the separate direct
false route, not the common leaf. Require the outer base-return observation and
matching natural failure/exit report to connect the observed result to startup.
Success at Console or an outer nonzero result is different evidence, not license
to investigate ARI or other branches during this attempt.

These mappings are conditional on the recorded stage remaining consistent with
the reviewed code. Helper bodies/other potential stage writers were not audited;
unexpected, missing or contradictory values make attribution inconclusive. A
BOOL/AL zero does not supply an extended error: do not invent one from EAX upper
bits or a stale last-error value. Negative scalar results can be preserved as
hexadecimal values without claiming the resource or access right behind them.

The earlier child had NtGlobalFlag 0x10 despite a zero parent. This attempt does
not write global flags, enable loader snaps or claim the flag was repaired. Log
the actual child `!gflag` output. Zero or the previously observed 0x10 permits
only interpretation of this instrumented run; 0x10 is a retained confounder, not
ordinary customer-mode qualification or a demonstrated cause. Other unexpected
flags further limit interpretation; never clear them or repeat the attempt.

## Operator Sequence

### 1. Read-Only Preflight

In VM 64-bit PowerShell, with the previous Maya/CDB session closed, return fresh
hashes for Maya, CDB, guest KERNELBASE and the existing cached KERNELBASE PDB;
CDB signature, OS build/UBR/edition, both PDB cache-presence checks, active
Maya/CDB process count, capture-directory presence, new-log absence and ntsd.ini
absence. A missing or changed input stops before launch; no downloads/repair.

The operator's returned preflight matches all four fixed SHA256 values (Maya,
CDB, guest KERNELBASE and cached KERNELBASE PDB), reports Valid CDB signature,
64-bit PowerShell, Professional 26300.9711, ntdll cache present, zero active
Maya/CDB processes, capture directory present, and both the proposed log and
ntsd.ini absent. No mismatch is reported. This clears the file/baseline preflight
for the one launch below; it does not prove loaded-module identity, installed
hardware points, a launched target, protected-child execution or cleanup.

### 2. One Launch To Initial Pause

Only after preflight matches, run the following in VM PowerShell. Launch consumes
this single session allowance even if configuration later fails before consent.

```powershell
$trace = Join-Path $env:LOCALAPPDATA 'MayaLoaderTrace-20261019'
$maya = 'D:\Maya-Protected-Python-Startup-5\MayaProtectedPython.exe'
$log = Join-Path $trace 'capture\base-failure-final-01.log'
if (Test-Path -LiteralPath $log) { throw 'Stop: log already exists.' }
if (Test-Path -LiteralPath "$trace\capture\ntsd.ini") { throw 'Stop: startup ini exists.' }
Set-Location -LiteralPath "$trace\capture"
& "$trace\debugger\cdb.exe" -o -hd -nosqm -noshell -noinh -sins -y "srv*$trace\symbols" -logo $log $maya
```

At the initial CDB prompt, do not continue or consent yet. Return:

```text
.reload /f ntdll.dll
.reload /f kernelbase.dll
lmv m ntdll
lmv m kernelbase
!gflag
|
bl
```

Require the expected setup-host path, known exact cached symbols/PE identity,
initially zero host flags and no existing breakpoints. Do not perform new live
disassembly, fetch symbols, force symbol matching or launch a second session.

The operator now reports the expected Package 5 setup host as the only listed
target, an empty breakpoint list, zero NtGlobalFlag/NtGlobalFlag2 and matching
cached ntdll/KERNELBASE PDBs. ntdll image size/checksum are 0x268000/0x27e340;
KERNELBASE timestamp/checksum/image size are 0xfb9071fb/0x411e21/0x401000, numeric
version 26100.9711. This consumes the one CDB launch allowance and supports
configuration in that same paused session. No protected-child start or hardware
point installation/hit has yet been reported. Return the configuration readback
below before the one continuation; do not restart or repeat module inspection.

### 3. Bound Commands After Initial Readback

The literal configuration below uses only debugger pseudo-registers: t0 host PID,
t1 child PID, t2 child KERNELBASE base, t3 PE header, t4 attach reason, t5 thread,
t6 entry branch selector, t7 hit mask, t8 entry stage, t9 invalid flag. Target
registers/memory are only read. Native debugger-engine behavior is not locally
tested; review `sx`/`bl` before the single continuation. No code runs locally to
simulate the product or debugger.

```text
.expr /s masm
r $t0 = @$tpid
r $t1 = 0
r $t2 = 0
r $t3 = 0
r $t4 = 0
r $t5 = 0
r $t6 = 0
r $t7 = 0
r $t8 = 0
r $t9 = 0
.childdbg 1
sxn ibp
sxn -c ".if ((@$t1 == 0) & (@$tpid != @$t0)) { r $t1 = @$tpid; .echo MAYA_FINAL_CHILD_CREATE; |; .lastevent; } .else { r $t9 = 1; .echo MAYA_FINAL_UNEXPECTED_CREATE; }" cpr:python.exe
sxn -c ".if ((@$t1 != 0) & (@$tpid == @$t1) & (@$tpid != @$t0) & (@$t2 == 0)) { r $t2 = kernelbase; r $t3 = @$t2+dwo(@$t2+0x3c); .if ((dwo(@$t3) == 0x4550) & (wo(@$t3+4) == 0x8664) & (wo(@$t3+0x18) == 0x20b) & (dwo(@$t3+8) == 0xfb9071fb) & (dwo(@$t3+0x28) == 0x5060) & (dwo(@$t3+0x50) == 0x401000) & (dwo(@$t3+0x58) == 0x411e21) & (dwo(@$t2+0x4e6c0) == 0x245c8948) & (dwo(@$t2+0x4ec6b) == 0x44e9c032) & (dwo(@$t2+0x4ebe6) == 0x840fc084) & (dwo(@$t2+0x506d) == 0x05100ff2) & (dwo(@$t2+0x4e94e) == 0x35f550) & (dwo(@$t2+0x4e9ae) == 0x35f4f0) & (dwo(@$t2+0x4eb9d) == 0x35f301) & (dwo(@$t2+0x4ebbd) == 0x35f2e1) & (dwo(@$t2+0x4ebdd) == 0x35f2c1)) { .echo MAYA_FINAL_ARMING; |; lmf m python; lmf m kernelbase; .reload /f kernelbase.dll; lmv m kernelbase; !gflag; ba0 e 1 /1 (@$t2+0x4e6c0) \".if ((@$tpid == @$t1) & (@edx == 1)) { r $t4 = @edx; r $t5 = @$tid; r $t6 = dwo(poi(@$peb+0x20)+8); r $t8 = wo(@$t2+0x3adea2); r $t7 = (@$t7 | 1); .echo MAYA_FINAL_ENTRY; |; r edx; r $t6; r $t8; kb 8; .if (@$t8 != 0) { r $t9 = 1; .echo MAYA_FINAL_INITIAL_STAGE_INVALID; } } .else { r $t9 = 1; .echo MAYA_FINAL_ENTRY_INVALID; }; gc\"; ba1 e 1 /1 (@$t2+0x4ec6b) \".if ((@$tpid == @$t1) & (@$tid == @$t5) & (@$t4 == 1)) { r $t7 = (@$t7 | 2); .echo MAYA_FINAL_COMMON_FALSE; |; r eax; dw (@$t2+0x3adea2) L1; r $t6; dd (poi(@$peb+0x20)+8) L1; kb 8; } .else { r $t9 = 1; .echo MAYA_FINAL_HIT_INVALID; }; gc\"; ba2 e 1 /1 (@$t2+0x4ebe6) \".if ((@$tpid == @$t1) & (@$tid == @$t5) & (@$t4 == 1)) { r $t7 = (@$t7 | 4); .echo MAYA_FINAL_CONSOLE_RESULT; |; r eax; dw (@$t2+0x3adea2) L1; kb 8; } .else { r $t9 = 1; .echo MAYA_FINAL_HIT_INVALID; }; gc\"; ba3 e 1 /1 (@$t2+0x506d) \".if ((@$tpid == @$t1) & (@$tid == @$t5) & (@$t4 == 1)) { r $t7 = (@$t7 | 8); .echo MAYA_FINAL_BASE_RETURN; |; r eax; dw (@$t2+0x3adea2) L1; r $t7; r $t9; kb 8; } .else { r $t9 = 1; .echo MAYA_FINAL_HIT_INVALID; }; gc\"; bl; .bpcmds; } .else { r $t9 = 1; .echo MAYA_FINAL_IMAGE_MISMATCH; } } .else { .if ((@$t1 != 0) & (@$tpid == @$t1)) { r $t9 = 1; .echo MAYA_FINAL_DUPLICATE_LOAD; } }" ld:kernelbase.dll
sxn -c ".echo MAYA_FINAL_PROCESS_EXIT; |; .lastevent; r $t7; r $t9" epr
sxn -c ".echo MAYA_FINAL_DLL_INIT_FIRST; .lastevent; .exr -1; kb 8" -c2 ".echo MAYA_FINAL_DLL_INIT_SECOND; .lastevent; .exr -1; kb 8" 0xc0000142
sxn -c ".echo MAYA_FINAL_ACCESS_FIRST; .lastevent; .exr -1; kb 8" -c2 ".echo MAYA_FINAL_ACCESS_SECOND; .lastevent; .exr -1; kb 8" 0xc0000022
sxn -c ".echo MAYA_FINAL_ACTIVATION_FIRST; .lastevent; .exr -1; kb 8" -c2 ".echo MAYA_FINAL_ACTIVATION_SECOND; .lastevent; .exr -1; kb 8" 0xc0150002
sx
bl
```

Enter each physical line once in CDB, not PowerShell; the module callback is one
long line. No saved debugger/test script is introduced. The five displacement
checks bind the breadcrumb address, alongside PE and four point-instruction
checks; they do not hash all live module bytes. Verify the expected cached PDB
and full child runtime path in the resulting log. Expected child image:
`C:\ProgramData\MayaProtectedPython-Startup1\<new-attempt>\runtime\python\python.exe`.
The attempt component must match the fresh product report, not an earlier run.

The pre-child `bl` should be empty. Return configuration readback before `g`.
During the run require four installed hardware execution points at the correct
child-relative addresses, not a software fallback. A zero t9 is only the
implemented binding/stage guards, not validation of symbols, paths, flags, all
callback parsing or security cleanup. Missing path/readback or command errors
can consume the attempt without yielding a usable result; no repair-and-retry.

The operator returned a 5,261-byte configuration transcript, SHA256
`dab9c7dcda57d1f33125fdc142f151c753184fd30c66ca38d1b9e80d9a383958`.
The create/module-load/exit callback text exactly matches the prepared commands;
the selected first/second failure notifications and initial-break notification
are present, with an empty final bl and no reported error. This verifies stored
configuration text, not runtime embedded-command parsing, hardware installation,
child/module binding, hit results or cleanup. The next action is the single
continuation in the same session and product consent/Start once, not relaunch.

### 4. One Continuation And Result

After configuration readback, one `g` and Maya's informed consent/Start once.
Do not manually pause/step or paste commands during the child wait. Unexpected
debugger stops require current-state guidance, not blind continue/quit. No
exceptions are swallowed to make startup pass; notify failure filters preserve
not-handled status.

Let Maya report exit/deadline and perform its own cleanup. Preserve the complete
fresh JSON and private log. After reported cleanup, close Maya normally and let
CDB return to PowerShell. Keep incomplete-cleanup evidence; no manual resource
deletion, forced host kill or additional recovery helper is included.

Analyze actual hit bodies (not strings echoed in command listings), child paths,
flags, thread/reason, stage/result consistency, natural exit, host closure and
reported cleanup. An instrumented result cannot by itself qualify an ordinary
customer launch or independently prove cleanup. If no specific defensible
operation/result emerges, stop this approach's diagnostic chain. No second log
name, automatic next capture or correction is authorized.

## Preparation Checks

Existing offline bytes independently confirm the four instruction DWORDs and
all five RIP-relative stage destinations against the approved DLL hash. These
are static checks only, not native command-engine or hardware-breakpoint tests.
No Maya/Python/CDB target was launched during preparation.

Command forms were checked against Microsoft's documentation for
[hardware breakpoints](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/ba--break-on-access-),
[automatic continuation](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/gc--go-from-conditional-breakpoint-),
[full module paths](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/lm--list-loaded-modules-)
and the prior reviewed notify-filter procedure. Existing cache only; no live
symbol download. Actual guest execution remains pending operator results.

## Captured Outcome: 2026-10-20

The operator supplied a fresh Package 5 JSON report and a 34,378-byte pasted
trace, SHA256 `e6695e4f0980f4cacba280cdcd0b29d91f95b8bbba4b9e1d6c2dba114d04b166`.
This hash identifies the received text, not an independently collected original
log. Raw account/attempt IDs, addresses and stack contents remain private.

The trace host/child IDs match the fresh report, and the setup-host path and
reported launcher hash match the frozen Package 5 input. One-based trace lines:

- 291-298: child-create event/PID binding and KERNELBASE load.
- 299-333: ARMING, child module/symbol/PE readback, and child NtGlobalFlag 0x10
  with NtGlobalFlag2 zero. The cached PDB/header match the reviewed DLL.
- 334-341: four actual child-process one-shot hardware execution breakpoints
  at the reviewed addresses, including their stored commands.
- 342-356: deeper initializer entry, EDX=1, initial stage zero, branch-selector
  scalar 0x6001, and the expected loader stack. Guarded subsequent hits use the
  same entry thread/reason; no invalid-hit marker is reported.
- 357-370: **ConsoleInitialize result observation at RVA 0x4ebe6, EAX=0/AL=0,
  stage 0x258 (600)**, in the same matched child.
- 371-386: outer base-wrapper return at RVA 0x506d, EAX=0/AL=0, same stage,
  observation mask 0xd (entry + Console result + outer return), invalid flag zero.
- 387-393: matched child exits naturally with 0xC0000142; mask/invalid flag
  remain 0xd/0. No standalone common-false-leaf hit appears.

The reviewed exact bytes show a call to ConsoleInitialize at RVA 0x4ebe1,
`test al,al` at 0x4ebe6, and a zero branch at 0x4ebe8 to the initializer epilogue
at 0x4e7b6. The live zero result is therefore on the direct false-return path,
and the outer-return hit confirms its propagation. This localizes the failed
operation in this instrumented child, rather than inferring it from a stage
value alone. The absent common-false hit is consistent with this separate route.
The earlier explicitly tested failures were passed on this observed path; no
negative result for those operations was captured. ARI was not reached after
the false base return. Do not generalize to all calls or earlier runs.

The JSON reports informed consent, verified payload/reduced and restricted
tokens, six verified network filters, child resume, natural exit observed before
cleanup, complete capture with zero stdout/stderr bytes, no startup beacon and
cleanup_complete=true. Python startup, containment and production remain false.
This is a startup failure, not a timeout or qualification success. Offline trace
analysis does not independently verify security-resource cleanup.

### Remaining Limits And Product Relevance

Even `lmf m python` prints only python.exe in the received log. Its full runtime
path is not independently established. Preserve PID/report correlation without
claiming complete path qualification. The retained child 0x10 flag/debug-register
and timing perturbations mean this is not a clean ordinary-customer comparison.
A zero invalid flag covers implemented guards, not these evidence limitations.

ConsoleInitialize returned a false Boolean. The trace contains no supported
extended error or inner failed resource; do not reinterpret zero as success
status, manufacture an NTSTATUS/last-error, or infer console/desktop permissions,
pipe access, account incompatibility, damaged Windows or a specific flag defect.

The existing Maya source uses python.exe, three inherited anonymous-pipe handles,
STARTF_USESTDHANDLES, and creation flags 0x08080404 (including no-window) under
the reviewed reduced-token/LPAC/job contract. That is now a focused product-code
review area, not evidence that a particular setting is wrong. No patch,
pythonw substitution, console-flag change, desktop grant, relaxed token or
Package 6 is justified or implemented by this result. No ConsoleInitialize
helper-body investigation or another live capture follows automatically.

### Closure And Stop

The pasted trace ends at line 415 with setup-host module loads, after the child
exit. It has no setup-host exit or debugger-unload tail. Do not claim both
targets have closed. Given the reported complete cleanup, the existing approved
normal closure step is to close Maya normally if it remains open and let CDB
return to PowerShell, then retain the final log tail. If already closed, report
that state; do not relaunch. No blind debugger quit/continue or forced host kill.

The attempt allowance is exhausted. The failed operation is localized, but a
safe correction remains a separate evidence/impact decision. Stop VM testing;
no retry, new broad trace, download, permission change or product rebuild.
Gate A, Hermes, containment and production remain unqualified.

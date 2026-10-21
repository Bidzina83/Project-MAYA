# Package 5 KERNELBASE Initializer Diagnostic Proposal

## Authority And Readiness

Current status: the approved attempt is complete and both targets have exited.
Its partial result and unexpected child heap-tail flag are recorded below.
The inspection/attempt allowances are consumed; all command blocks are historical,
not permission to run or repeat them.

The user later separately approved a
[final targeted attempt](maya_protected_python_final_diagnostic.md) after the
offline review. Its fresh preflight/session/results are pending. Use that new
four-point stage/result contract, not the historical commands in this document.

The user subsequently approved the separate
[two-file private transfer and offline review](maya_protected_python_offline_review.md).
That scope permits existing static tools only and does not reopen this live-read
or attempt allowance. File receipt/verification and that bounded offline review
are now complete. It mapped possible base-initializer failure routes but did not
justify a specific correction; see its completed outcome. No new run follows.

2026-10-20: after the launch-source review, the user requested continuation.
This authorizes preparation of this targeted procedure, not a new native run or
symbol retrieval. No debugger, Maya, Python, guest security operation or download
was executed during preparation.

The user subsequently explicitly approved the KERNELBASE symbol-setup step only.
Its VM results remain pending. Guide the operator using existing SymChk/cache;
no download or success is inferred from approval. CDB/Maya launch, protected-child
execution and breakpoint installation still require a separate decision.

The [launch review](maya_protected_python_launch_review.md) and
[completed loader capture](maya_protected_python_loader_capture_v2.md#captured-outcome-2026-10-20)
remain the evidence. The earlier capture allowance is consumed and its session
is closed. This proposal is a separate, bounded diagnostic exception to the
[customer-like testing contract](governance_v2_customer_windows_testing.md).

**Not ready for payload execution:** exact guest DLL metadata and matching
KERNELBASE symbols are now reported in the setup result below. Disassembly and
exact breakpoint commands remain unavailable. The old log does not contain the
initializer's instructions. Do not invent function names, calling conventions
for undocumented helpers or breakpoint offsets. Only the pre-consent inspection
session described below is approved, not protected-child execution.

The user then explicitly approved one pre-consent CDB/Maya inspection session.
Read-only VM preflight remains pending; approval is not a launch report. This
allows the setup host's initial debugger pause and bounded code readback only,
not product consent, protected Python, child breakpoints or a test continuation.
Launch consumes this session allowance even if readback later fails.

The operator now reports matching Package 5/CDB/KERNELBASE hashes, Valid CDB
signature, 64-bit PowerShell, both exact PDB cache files, existing capture
directory, absent kernelbase-01.log/ntsd.ini, and Professional 26300.9711.
Preflight matches the fixed inputs. Cache presence does not replace initial
loaded-module/symbol readback. Guide the approved launch to its initial pause
only; no launch is yet reported and no protected Python start is approved.

The operator subsequently supplied the initial CDB module/header readback. The
one inspection-session allowance is consumed. ntdll and KERNELBASE use the exact
expected cached PDB keys. ntdll image/checksum are 0x268000/0x27e340; KERNELBASE
image/checksum/timestamp are 0x401000/0x411e21/0xfb9071fb, with verified entry RVA
0x5060. NtGlobalFlag and NtGlobalFlag2 are zero. No child is reported.

The CDB KERNELBASE version fields show 26100.9711, unlike PowerShell's earlier
26100.9278. The PE/PDB fields agree, but that does not explain the version-field
difference or establish mapped-byte identity. Preserve it as unresolved before
any later capture; do not repair Windows or force mismatched symbols. Bounded
read-only code inspection in this existing paused session remains within scope.
The first proposed read is `u kernelbase+0x5060 L40` (64 instructions); it has
not yet been reported or counted as completed. No `g`, product consent or child
breakpoint/start is approved.

The first read has now returned 64 instructions, identifying the public symbol
KernelBaseDllInitialize at verified RVA 0x5060. The 5,297-byte pasted attachment
has SHA256 `d765bf0015d09833b5719a5cd685a05be68435e7e73c494a491d11f6cc986fc1`.
This is static readback from the paused setup host, not a child execution trace.

For attach reason 1, the shown path checks AL from the direct call to
KernelBaseBaseDllInitialize (RVA 0x51d0), branching to the return path at 0x50ba
when AL is not 1. A later call to ARI::Globals::Initialize (RVA 0x5ff0) has EAX
tested at 0x5138 and branches on sign to 0x51c0. The actual failure-return bytes
at 0x51c0 are not yet shown. These two candidate paths do not establish a
child-observed failure or an undocumented helper's return-type/resource semantics.

The next proposed reads, still in this paused session, are
`u kernelbase+0x51c0 L4`, `u kernelbase+0x51d0 L40` and
`u kernelbase+0x5ff0 L40`. If reported, cumulative instruction reads become
196 of the 256 limit, with both allowed direct helpers inspected. These reads
have not yet been reported. No further helper recursion, execution, breakpoint
or protected-child attempt is approved; version discrepancy remains unresolved.

The next pasted transcript is 14,251 bytes, SHA256
`a6aea7b00d88927cfd8d5f838d8cc097750e82bff7367e4cae5c8abe9011fe85`.
It includes the previously supplied entry read and all three newly requested
reads. The requested disassembly total is now 196 instructions; the repeated
transcript prefix is not itself proof of another execution of that command.
No runtime execution or native child observation is shown.

The 0x51c0 leaf clears AL and jumps to the common zero-extending return path.
KernelBaseBaseDllInitialize initializes a critical section on attach, then calls
DllMainCRTStartupForGS2 and tail-jumps to _KernelBaseBaseDllInitialize (RVA
0x4e6c0). That deeper helper is outside the two-direct-helper inspection scope;
do not follow it automatically or label its unobserved result a denial.

ARI::Globals::Initialize calls AppModelPolicy_GetPolicy_Internal at 0x60d9,
copies EAX to ESI, ORs ESI with 0x10000000, then branches on the sign flag to
0x6348. Another shown branch target is 0x61e6. This is code structure, not proof
of a failed call, a status type, a denied resource or a bad policy value.
Its return path and these targets still need bounded inspection before claiming
a propagated failure. No deeper AppModelPolicy helper inspection is approved.

The final proposed reads are `u kernelbase+0x6348 L10` (16 instructions) and
`u kernelbase+0x61e6 L2c` (44), both within the already selected ARI function's
branch targets. If returned, the requested total reaches the 256-instruction
limit. They are not yet reported; no further disassembly follows automatically.
Do not repeat earlier reads. The version discrepancy and child-run prohibition
remain unchanged; no breakpoint installation or execution is authorized.

Both final requested reads have now returned: the instruction inspection total
is 256 and both direct helpers were read. No further disassembly or deeper helper
inspection is authorized. This is static host code, not another payload attempt.

At 0x6348 the shown policy-error path loads EDX=0x5c and jumps to 0x61cb, whose
instructions are outside the received ranges. The other read shows
OpenProcessIfPackaged's EAX tested at 0x61fe, a nonzero branch to 0x6352,
positive low-word-to-0x80070000 transformation there, CheckBuiltInAccountUser's
sign check, and later BuildFilenameForPackage/sign-check paths. These establish
additional possible failure branches, not which ran or any denied resource.
In particular, the symbol CheckBuiltInAccountUser does not establish that the
operator's built-in Administrator account caused the failure. No account/UAC,
registry, policy or repository correction is justified by this static output.

The pre-consent session remains paused. Before any capture proposal is treated
as ready, clarify the outstanding numeric/text DLL-version readback with a
read-only query in a separate VM PowerShell window; do not type PowerShell into
CDB, resume Maya or close this session merely to collect metadata.
Use FileVersionInfo.GetVersionInfo on the same System32 DLL and report FileName,
FileVersion/ProductVersion and FileMajorPart/FileMinorPart/FileBuildPart/
FilePrivatePart, plus current SHA256. This check is proposed, not yet reported.
Windows [version resources](https://learn.microsoft.com/en-us/windows/win32/menurc/versioninfo-resource)
contain binary version values and string blocks; reading the
[numeric components](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.fileversioninfo.fileprivatepart?view=netframework-4.8.1)
can clarify the fields, but does not itself prove mapped-byte identity or explain
the discrepancy. No new native target, download or Windows setting is involved.

The operator's subsequent read-only metadata query reports FileMajorPart=10,
FileMinorPart=0, FileBuildPart=26100 and FilePrivatePart=9711. The text
FileVersion/ProductVersion remain 26100.9278 and the file SHA256 remains the
recorded 5c29...c3d0. Numeric file version therefore agrees with CDB; the observed
field-level discrepancy is resolved, without inferring why the text differs or
proving mapped-byte identity. No Windows repair/change is needed on this evidence.
The permitted pre-consent inspection is now complete. Keep the same session
paused; do not perform further disassembly, set breakpoints or start Python yet.

## Proposed Observation Binding (Not Execution Approval)

The received instructions support the following four-point set within the
proposed hardware-breakpoint budget. RVAs are relative to the matched child's
KERNELBASE module, never old absolute addresses or the setup-host context.

| Point | RVA | Readback purpose |
| --- | --- | --- |
| Initializer entry | 0x5060 | Record EDX attach reason before instructions execute. |
| Base helper return | 0x506d | Record AL immediately after the base initializer helper returns. |
| ARI helper return | 0x5138 | Record EAX before the caller's sign test. |
| Explicit failure leaf | 0x51c0 | Record EAX before AL is cleared and zero returned. |

These points can distinguish a base-helper result failure from a negative ARI
return and correlate the explicit failure leaf. They do not necessarily identify
a deeper failed call/resource. No AppModelPolicy or account cause is established
by selecting these points; an inconclusive deeper cause remains a stop result.

Literal process-bound automatic breakpoint commands/configuration still require
preparation and readback review before continuation. The existing CDB session
would be reused, with no second debugger launch and no new symbols. One proposed
protected-child attempt would use product consent/setup/cleanup and unchanged
deadline, tokens, LPAC, file grants, six WFP denies and payload. Hardware debug
register changes remain diagnostic perturbations, not normal-customer qualification.
The bound four-point capture below does not re-enable loader snaps or alter the
child's global flags. No permission broadening, product patch, new tool
or repeat is proposed. That configuration/one-attempt scope is not yet approved.

The user subsequently explicitly approved the four hardware-breakpoint
configuration and one protected-Python attempt in this existing paused session.
No second CDB launch or attempt is included. Actual target/breakpoint readback,
configuration review and execution outcomes remain pending. Approval is not a
capture result or permission for another correction.

The operator's subsequent current-process listing shows only the expected
Package 5 Maya setup host, and bl is empty. The bound automatic configuration
below is now the next action in this same paused session; return its sx/bl
readback before g. It uses one KERNELBASE-load callback and does not re-enable
loader snaps. No configuration, child execution or capture result is yet reported.

The operator's sx readback now contains the expected create/load/exit callback
text, all four one-shot hardware-point commands within the KERNELBASE callback,
initial-break notify and the selected failure-code notify/not-handled settings.
The final bl is empty, as expected before child creation. No configuration error
is reported. This supports the approved one g and product consent/Start once;
it does not prove that hardware points have been installed or fired. The load
filter's runtime child/image binding, flags, breakpoint installation, hits,
exit/report and cleanup are still unreported. No manual pause, command repair,
second attempt or further disassembly is authorized. An unexpected stop requires
current-state guidance while preserving the host's cleanup opportunity.

## Captured Outcome (2026-10-20)

The operator supplied a fresh Package 5 JSON report and a 53,179-byte pasted
trace attachment, SHA256
`2b3932e8f29991bbc9398b8572370c4adb9118562a563d694ea65f25acd47573`.
This identifies the received text, not an independently collected original log.
Raw SID, attempt/profile identifiers, PIDs, addresses and stack contents remain
private; they are omitted from this tracked record.

The host/child process IDs match the report, and the host path is the approved
Package 5 executable. Its reported launcher hash matches the frozen input.
The focused trace labels the child python.exe but does not independently print
its full image path; retain this missing path-binding evidence rather than
claiming complete native image-path confirmation.

One-based lines in the received text establish:

- 618-625: actual child-create binding and the corresponding Windows module loads.
- 626-653: image/point guards reached ARMING and the child's KERNELBASE PDB/header
  fields match the reviewed binding.
- 654-656: child NtGlobalFlag is **0x10**, NtGlobalFlag2 zero; htc is enabled.
- 657-664: bl/.bpcmds show all four expected addresses as child-process one-shot
  hardware execution points with their logging commands. ARMING is supported by
  actual installation readback, not taken as proof on its own.
- 665-677: the initializer-entry observation fires with EDX=1 and a loader stack.
- 678-690: the base-helper-return observation fires with EAX=0, therefore AL=0.
- 691-696: the matched child exits naturally with 0xC0000142; t9 remains zero.
- 719 onward: the setup host exits with code zero, followed by debugger visualizer
  unload messages. Both debug targets have exited; no further closure command is
  needed on this evidence.

No standalone ARI-return or explicit-failure-leaf hit appears. Combined with the
already inspected AL check and return instructions, the observed base-helper zero
explains the early initializer-failure path in this instrumented child. ARI's
later calls and CheckBuiltInAccountUser were not reached on that path. Their symbol
names are not evidence for an account, policy, registry or package-repository fix.
The underlying operation/resource inside the base initialization remains unknown.

The matching report says resumed child, verified payload/token/reduced-token and
six filters, natural exit observed before cleanup, complete empty output capture
and no stdout/state beacon. Cleanup is reported complete; Python startup,
containment and production qualification remain false. This is not a timeout or
a successful Python run, nor independent proof of security-resource cleanup.

### Qualification Failure And Causal Limits

The bound procedure explicitly required a zero child global-flag readback.
Instead the child has [heap tail checking, 0x10](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/enable-heap-tail-checking).
The setup-host flags were zero, and the new callback does not write global flags;
the child's 0x10 is already printed before hardware-point creation. Its provenance
and causal relevance to the failure are not established. The documented
[-hd option](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/cdb-command-line-options)
does not replace actual child-state verification.

This fails the intended zero-flag diagnostic profile. Preserve the recorded
entry/return observations as facts about this instrumented run, not a clean
comparison or a demonstrated cause for the ordinary launch failure. In particular,
t9 only covers the implemented binding/hit guards: it did not verify global flags
or the full image path. Its zero value cannot override these qualification gaps.
Do not clear the flag, alter registry/debugger settings or rerun automatically.

Parent-side profile-registration file/path-not-found messages occur before child
creation, and parent CLR/WFP first-chance messages occur after child exit. They
are not identified failing child operations or independent cleanup failures.
Do not treat them as a proven missing resource or a grant/repair justification.

The attempt and 256-instruction inspection budgets are consumed. No live session,
closure step or further VM command is pending. Stop for a separate decision; no
new capture, deeper helper disassembly, permission expansion, account/Windows
change, product patch or qualification is authorized by this partial result.

## Question

Which observed operation and result lead the matching KERNELBASE.dll initializer
to its failure return during DLL_PROCESS_ATTACH?

The existing trace proves successful mapping and the initializer failure, followed
by child exit 0xC0000142. It does not identify an access denial, desktop defect,
registry requirement or damaged DLL. This procedure seeks the failing call/branch,
not another general loader trace or a way to make startup pass.

## Fixed Inputs And Impact

- Unchanged Package 5 at the reported guest path
  `D:\Maya-Protected-Python-Startup-5\MayaProtectedPython.exe`.
  EXE SHA256:
  `6709bb7673c1eca2fecec006cf2c72dd7b3059278c3e7a92d59034c6bac92b66`.
- Same declared Windows 11 Pro x64 26300.9711, operator and RDP session context;
  no account, UAC, desktop, filesystem or registry permission preparation.
- Existing diagnostic root `%LOCALAPPDATA%\MayaLoaderTrace-20261019`.
  CDB SHA256:
  `37095ef02baf6bb87e7d0eb4b0fc466dbe2c87cabc60afd114394db6f62edfe9`.
  Require Valid Microsoft signatures for the existing CDB and SymChk.
- Existing ntdll match/cache is retained. KERNELBASE public symbols must match
  the guest's actual System32 DLL, not the workstation's file or a guessed PDB.
- Proposed fresh private log: `capture\kernelbase-01.log`.
  No overwrite/append to any earlier log; no capture-directory ntsd.ini.
- Identical payload, reduced-token and LPAC checks, zero extra capabilities,
  six package-scoped network denies, file grants, job and handle constraints,
  product-owned consent/cleanup and **30,000 ms** wait.

If separately approved, setup may use the existing SymChk to retrieve **only
KERNELBASE.dll's matching public symbols** from Microsoft's symbol server into
the existing private cache. This makes a network request containing symbol/image
identifiers; no customer data or memory dump is submitted. No tool installation,
recursive symbol sweep or download while the protected child is starting.
Record DLL hash, version, image size, checksum and matched PDB GUID/age/key.
Missing/unmatched symbols stop setup; do not force-load mismatched symbols.

The proposed capture uses at most four child-process hardware execution
breakpoints. These alter debug-register state, not target instruction bytes,
permissions, return values or protection predicates. They still suspend execution
briefly and perturb timing. No software-breakpoint fallback, manual stepping,
whole-process call trace, broad syscall instrumentation or deadline increase.
Native compatibility of this breakpoint/callback combination is unproven.

## Operator Symbol-Setup Result

The operator supplied a 5,029-byte pasted-text attachment, SHA256
`dc736760f039c98bcb84b7904cf85fc46a98a5cc1e2acd20d92d029b55ae076b`.
This identifies the received text, not an independently collected VM log.
The signature/cache guards returned without a reported error. SymChk copied the
matching Microsoft public PDB into the existing cache and returned to PowerShell.

| Item | Reported value |
| --- | --- |
| Guest file | System32/KERNELBASE.dll |
| SHA256 | `5c29b73622ce0976e1ada566f31f2197ba0f8beaea89c3ec033366126172c3d0` |
| File/product version | 10.0.26100.9278 |
| Image size | 4,198,400 bytes / 0x00401000 |
| PE checksum | 0x00411e21 |
| PE timestamp field | 0xfb9071fb; not interpreted as a calendar date |
| Public PDB GUID | 79B50527-6F14-0450-EB83-DF0440BF06C6 |
| PDB age | 1 |
| Cache key | kernelbase.pdb/79B505276F140450EB83DF0440BF06C61/kernelbase.pdb |
| Retrieved PDB size | 12,554,240 bytes |
| Validation | PDB Matched TRUE; DBG Matched TRUE; FAILED 0; PASSED + IGNORED 1 |

The preliminary index2.txt HTTP 404 did not prevent the subsequent exact PDB
download and match. Public symbols have no reported line/type information; do
not assume they provide undocumented helper signatures or private structures.

The image size agrees with the earlier child's observed KERNELBASE mapping.
That trace did not provide a KERNELBASE file hash or PDB match, so byte identity
with that earlier mapping is not established. This DLL's 26100.9278 file version
is not a fresh OS-build measurement or proof of a baseline change. Require the
separate OS baseline and current loaded-module identity before any native capture.

Symbol setup is complete for this scope only. No debugger/Maya/Python launch,
new breakpoint, native startup result or security correction follows. Exact
code inspection remains the next separately approved pre-consent stage.

## Proposed Budget And Stages

### A. File And Symbol Setup

This stage requires separate approval and operator-reported results before CDB
launch. Recheck frozen executable/tool identities, guest build and earlier normal
closure/cleanup report. Bind the exact KERNELBASE DLL hash and matching symbols.
The reported KERNELBASE PDB key is recorded above; the earlier ntdll PDB is not
its symbol file. Symbol setup has now returned a matching result, not a launch.

The now-approved symbol lookup uses the existing SymChk, after a Valid signature
and existing-cache check, against the guest's actual System32 KERNELBASE.dll:

```powershell
$trace = Join-Path $env:LOCALAPPDATA 'MayaLoaderTrace-20261019'
$symchk = Join-Path $trace 'debugger\symchk.exe'
$kb = Join-Path $env:WINDIR 'System32\KERNELBASE.dll'
if ((Get-AuthenticodeSignature -LiteralPath $symchk).Status -ne 'Valid') { throw 'Stop: SymChk signature is not Valid.' }
if (-not (Test-Path -LiteralPath "$trace\symbols" -PathType Container)) { throw 'Stop: existing symbol cache not found.' }
(Get-FileHash -Algorithm SHA256 -LiteralPath $kb).Hash
(Get-Item -LiteralPath $kb).VersionInfo | Format-List FileVersion, ProductVersion
& $symchk /v $kb /s "srv*$trace\symbols*https://msdl.microsoft.com/download/symbols"
```

These are manual VM PowerShell commands, not a saved setup/test script. Return
the full output and stop after this one lookup, including on failure. Recheck
the remaining CDB/product/baseline inputs before any separately approved launch.

No product run occurs here. Do not resolve a setup mismatch by changing Windows,
replacing a DLL, installing a newer debugger or selecting another product package.

### B. One Session, Before Product Consent

After explicit approval, the proposed maximum is **one CDB launch of Maya and
at most one consented protected-child attempt in that same session**. Launch
consumes the session allowance even if preparation stops before child creation.
No automatic restart or second child attempt.

The approved subset currently stops at pre-consent inspection. After fresh
preflight matches the fixed files/baseline and confirms a new log/no ntsd.ini,
the bound launch for that one session is:

```powershell
$trace = Join-Path $env:LOCALAPPDATA 'MayaLoaderTrace-20261019'
$maya = 'D:\Maya-Protected-Python-Startup-5\MayaProtectedPython.exe'
$log = Join-Path $trace 'capture\kernelbase-01.log'
Set-Location -LiteralPath "$trace\capture"
& "$trace\debugger\cdb.exe" -o -hd -nosqm -noshell -noinh -sins -y "srv*$trace\symbols" -logo $log $maya
```

No `g`, child breakpoint or product Start/consent command follows this initial
pause under the current approval. Return readback for review in the same session.

Use the previous reviewed CDB launch context: child debugging enabled, normal
debug heap, local-only symbol cache, no shell commands, no inherited symbol path
and a fresh private log. The actual invocation must be reviewed before launch;
this document does not renew the old loader-02 invocation.

At the initial setup-host prompt, before continuing Maya or starting Python, the
read-only module/header checks to be reviewed are:

```text
.reload /f ntdll.dll
.reload /f kernelbase.dll
lmv m ntdll
lmv m kernelbase
!dh -f kernelbase
!gflag
```

Require the known ntdll match, the new exact KERNELBASE PDB match, image/header
agreement and initially zero global flags. The setup host already maps the system
DLL; reading its code here does not require a protected child or start that
child's timeout. It is not evidence of the child's access or successful bootstrap.

The previous log's initializer offset was 0x5060 relative to its mapped KERNELBASE
base. This is only a historical lead. First compare the new DLL/header and entry
point; do not reuse the old absolute address under ASLR or assume this is a public
symbol. If consistent, inspect the verified entry and at most two directly
relevant helper routines with bounded disassembly, at most 64 instructions per
read and 256 instructions total. No guessed helper signature or unbounded
recursive disassembly.

**Return this pre-consent readback for review.** Only then can exact command text
be bound. If those bounded reads cannot identify a defensible failure path within
the four-breakpoint budget, stop without starting protected Python. Close the
unstarted Maya/debugger session through current-state guidance; no blind quit
while process state is uncertain.

### C. Bound Capture Contract

Before any product consent, record the reviewed DLL identity, RVAs, instruction
boundaries, call/result semantics and literal debugger commands. This binding is
currently pending; no executable breakpoint template with guessed offsets is
supplied. Retain the already exercised Python-name/PID binding and final full-path
correlation from the previous capture.

The fixed maximum is:

1. One initializer-entry observation, including the DLL attach reason.
2. Up to two verified post-call instructions on the selected failure path.
3. One verified failure-branch/return observation.

Use one-shot hardware execution breakpoints installed only in the PID-selected
child when its matching KERNELBASE module loads, before its initializer runs.
Rebase from that child's module, verify identity, and keep the setup host outside
the breakpoint set. Do not use kernel-mode /p or /t options as user-mode PID filters.
Unexpected module identity, process binding or breakpoint installation invalidates
capture; do not attempt alternative offsets or a software breakpoint.

Each hit records a fixed marker, process/thread identity, instruction location,
the reviewed scalar result register and at most eight stack frames, then resumes
automatically using the reviewed logging-breakpoint continuation. At most four
hit records. No raw buffers, object strings, heap inspection or dump. Registers
are read, never changed; debugger pseudo-registers hold diagnostic bindings only.
Retain child exit notification and correlate it with the fresh product report.
If loader snaps are retained, disclose the same child-only 0x2 change and verify
before/after readback; do not silently add parent or persistent GFlags settings.

Interpret results according to the specific call: a BOOL failure is not an
NTSTATUS, and an arbitrary last-error value is not evidence unless that call's
documented contract makes it valid. A low-level denial may be handled normally;
require a demonstrated control-flow connection to the initializer's failure.
The selected first one-shot observation can miss a later failing invocation.
That is an inconclusive capture, not permission to rearm, loop or retry.

After command/readback review, one continuation and Maya's own informed consent
start the attempt. No chat waits, command pasting or manual stepping during the
child's wait. Unexpected debugger stops require current-state guidance; no blind
continue/quit, child resume or host termination.

### D. Result And Closure

Let Maya observe exit/deadline and perform cleanup. Preserve its fresh report and
the private trace. Once cleanup is reported complete, close Maya normally and
let CDB return to PowerShell. Preserve any incomplete-cleanup report rather than
manually deleting resources. No extra closure helper.

Startup failure remains failure; instrumentation success is not Python startup
or containment proof. Timeout, missed path, symbol mismatch, breakpoint error,
ambiguous return or missing correlation ends this allowance without a retry.
Even an identified failing call is not approval for a permission/product change.

## Bound Commands For The Approved Attempt

Before entering configuration, require the current CDB process listing to show
only the existing Maya setup host at its pre-consent pause, with an empty `bl`
list. Return `|` and `bl` readback first. Do not clear existing breakpoints,
replace another target, resume or relaunch if this differs.

The following literal candidate is prepared, not yet executed or engine-tested.
It uses debugger pseudo-registers only: t0 host PID, t1 child PID, t2 child
KERNELBASE base, t3 PE header, t4 attach reason, t5 entry thread, t9 invalid flag.
No real result register, code byte, access control or product check is changed.
The prior disassembly budget is exhausted; the bounded instruction-byte/PE reads
here validate the four already reviewed binding points, not new disassembly.

```text
.expr /s masm
r $t0 = @$tpid
r $t1 = 0
r $t2 = 0
r $t3 = 0
r $t4 = 0
r $t5 = 0
r $t9 = 0
.childdbg 1
sxn ibp
sxn -c ".if ((@$t1 == 0) & (@$tpid != @$t0)) { r $t1 = @$tpid; .echo MAYA_INIT_PYTHON_CREATE; |; .lastevent; } .else { r $t9 = 1; .echo MAYA_INIT_UNEXPECTED_CREATE; }" cpr:python.exe
sxn -c ".if ((@$t1 != 0) & (@$tpid == @$t1) & (@$tpid != @$t0) & (@$t2 == 0)) { r $t2 = kernelbase; r $t3 = @$t2+dwo(@$t2+0x3c); .if ((dwo(@$t3) == 0x4550) & (wo(@$t3+4) == 0x8664) & (wo(@$t3+0x18) == 0x20b) & (dwo(@$t3+8) == 0xfb9071fb) & (dwo(@$t3+0x28) == 0x5060) & (dwo(@$t3+0x50) == 0x401000) & (dwo(@$t3+0x58) == 0x411e21) & (dwo(@$t2+0x5060) == 0x83485340) & (dwo(@$t2+0x506d) == 0x05100ff2) & (dwo(@$t2+0x5138) == 0x880fc085) & (dwo(@$t2+0x51c0) == 0xf3e9c032)) { .echo MAYA_INIT_ARMING; |; .reload /f kernelbase.dll; lmv m kernelbase; !gflag; ba0 e 1 /1 (@$t2+0x5060) \".if ((@$tpid == @$t1) & (@edx == 1)) { r $t4 = @edx; r $t5 = @$tid; .echo MAYA_INIT_ENTRY; |; r edx; kb 8; } .else { r $t9 = 1; .echo MAYA_INIT_ENTRY_INVALID; }; gc\"; ba1 e 1 /1 (@$t2+0x506d) \".if ((@$tpid == @$t1) & (@$tid == @$t5) & (@$t4 == 1)) { .echo MAYA_INIT_BASE_RETURN; |; r eax; kb 8; } .else { r $t9 = 1; .echo MAYA_INIT_HIT_INVALID; }; gc\"; ba2 e 1 /1 (@$t2+0x5138) \".if ((@$tpid == @$t1) & (@$tid == @$t5) & (@$t4 == 1)) { .echo MAYA_INIT_ARI_RETURN; |; r eax; kb 8; } .else { r $t9 = 1; .echo MAYA_INIT_HIT_INVALID; }; gc\"; ba3 e 1 /1 (@$t2+0x51c0) \".if ((@$tpid == @$t1) & (@$tid == @$t5) & (@$t4 == 1)) { .echo MAYA_INIT_FAILURE_LEAF; |; r eax; kb 8; } .else { r $t9 = 1; .echo MAYA_INIT_HIT_INVALID; }; gc\"; bl; .bpcmds; } .else { r $t9 = 1; .echo MAYA_INIT_IMAGE_MISMATCH; } } .else { .if ((@$t1 != 0) & (@$tpid == @$t1)) { r $t9 = 1; .echo MAYA_INIT_DUPLICATE_LOAD; } }" ld:kernelbase.dll
sxn -c ".echo MAYA_INIT_PROCESS_EXIT; |; .lastevent; r $t9" epr
sxn -c ".echo MAYA_INIT_DLL_INIT_FIRST; .lastevent; .exr -1; kb 8" -c2 ".echo MAYA_INIT_DLL_INIT_SECOND; .lastevent; .exr -1; kb 8" 0xc0000142
sxn -c ".echo MAYA_INIT_ACCESS_FIRST; .lastevent; .exr -1; kb 8" -c2 ".echo MAYA_INIT_ACCESS_SECOND; .lastevent; .exr -1; kb 8" 0xc0000022
sxn -c ".echo MAYA_INIT_ACTIVATION_FIRST; .lastevent; .exr -1; kb 8" -c2 ".echo MAYA_INIT_ACTIVATION_SECOND; .lastevent; .exr -1; kb 8" 0xc0150002
sx
bl
```

Enter each physical line once in CDB, not PowerShell or a saved command file.
The KERNELBASE callback is one long line; its inner breakpoint-command quotes
are escaped. Return `sx`/`bl` output for review before continuation. At that
point `bl` should still be empty: no child exists and hardware points are
installed only in the selected child's matching module-load callback.

The callback checks PE machine/magic, timestamp, entry RVA, image size/checksum
and four reviewed instruction DWORDs before attempting four one-shot hardware
execution breakpoints. It prints `bl` and `.bpcmds` after installation. ARMING
is not proof of four installed points: inspect the actual types/addresses,
one-shot state and callback text in the resulting log. No software fallback or
manual debug-register edit is provided. A command/install/context error can make
this single attempt inconclusive; do not repair and repeat it.

At each hit, PID/entry-thread/reason checks gate fixed register/stack logging;
unexpected hits mark t9 invalid. A one-shot hit is consumed even if invalid.
The logging callback ends in `gc`; this is a breakpoint continuation, not a
nested continuation inside notify event callbacks. The module callback installs
points before initializer execution without an operator wait. Parent events do
not install breakpoints. This focused capture uses one KERNELBASE-load filter,
not separate competing module-load filters. It does not add loader snaps;
the child global-flag readback must remain zero or interpretation is invalid.
This is a diagnostic logging choice, not a product/security fallback.
Exceptions retain not-handled
status; none is swallowed to force startup success.

After configuration readback review, guide one `g` and Maya's informed consent/
Start once. No command pasting or chat pause is planned while its child wait is
active. Unknown debugger stops require current-state guidance, not blind
continuation/quit. Native behavior remains unproven until this actual attempt.
Collect the product report and close Maya normally after reported cleanup.

The four hits reveal only selected helper results/branch evidence. Even a
negative ARI result may leave its internal operation/resource unknown. Preserve
that limitation and stop instead of adding deeper breakpoints or more attempts.

Microsoft references: [hardware breakpoint commands and escaped command strings](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/ba--break-on-access-),
[notify filters](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/sx--sxd--sxe--sxi--sxn--sxr--sx---set-exceptions-),
[logging continuation](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/gc--go-from-conditional-breakpoint-).

## Completion And Limits

Useful evidence requires the intended child/module, observed DLL_PROCESS_ATTACH,
verified call/result semantics, a traced connection to the failure branch and
matching natural exit/report. Distinguish a failed operation from identification
of its exact resource; do not infer desktop or registry grants from a generic
denial. Parent exceptions are not child failures.

This is a staged proposal, not a ready-to-run capture: symbol setup is reported
complete but exact breakpoint commands remain unbound. The approved operator
symbol fetch is recorded above; no new script, wrapper, supervisor, test
application, package build, VM setting or native product/debugger launch was added.
Raw paths, attempt/account IDs, addresses and stacks remain private/ignored.
Gate A, containment, Hermes and production qualification remain unchanged.

## Preparation Verification

Command forms and impact were checked against Microsoft documentation; no native
debugger-engine test was performed. Hardware slot/thread behavior, automatic
module binding and the final callbacks still require actual reviewed readback
and cannot be qualified by this document.

References:
[SymChk matching/cache behavior](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/using-symchk),
[image headers](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-dh),
[bounded disassembly](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/u--unassemble-),
[hardware execution breakpoints](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/ba--break-on-access-),
[automatic breakpoint continuation](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/gc--go-from-conditional-breakpoint-).

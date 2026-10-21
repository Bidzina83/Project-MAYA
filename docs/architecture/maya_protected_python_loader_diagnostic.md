# Protected Python Loader Diagnostic Procedure

The consumed Package 4 procedure below remains historical evidence. The subsequent
document-only Package 5 proposal is
[automatic loader capture V2](maya_protected_python_loader_capture_v2.md).
Its preparation approval is not a renewed native-run allowance.

## Authority And Current Status

2026-10-19: the user approved preparation of this bounded procedure after two
operator-reported Package 4 runs, then explicitly approved debugger transfer/setup
and retrieval of matching Microsoft public symbols. Step 1 setup is now reported
complete: matching transfer ZIP hash, successful extraction, Valid CDB/SymChk
signatures, and guest ntdll PDB/DBG Matched TRUE with zero failed files. The guest
symbol key is `ntdll.pdb/C031D45B0DA18A6E74D06ED6AB2DD9E11`, age 1. The early
index2.txt 404 did not prevent its HTTP 200 PDB download and exact match.
A standard local transfer ZIP of existing
debugger files and a generated inventory are prepared under
`.codex-build/maya-loader-setup-20261019`, without adding a script or product code.
The operator supplied the Package 4 path below and its matching EXE SHA256, then
explicitly approved **one** debugger-controlled run with protections and the
30-second product limit unchanged. That allowance is now **consumed**. The
operator reports a timeout and complete cleanup; the copied log verifies child
instrumentation but does not localize the original failure. See the outcome
below. Subsequent normal Maya closure, a screenshot showing return to PowerShell
and the final log resolve debugger-session closure. No further child-startup
evidence was added. No retry or workstation launch is authorized.

Verified guest EXE path:
`D:\Maya-Protected-Python-Startup-4\Maya-Protected-Python-Startup-4\MayaProtectedPython.exe`

The active [customer-like Windows testing contract](governance_v2_customer_windows_testing.md)
and [startup component contract](maya_protected_python_startup_package.md) apply.
No supervisor, observer, wrapper, debugger command file or new product build is
created. The operator performs any subsequently approved VM actions through RDP.
The historical [25H2 loader diagnosis](governance_v2_loader_diagnosis.md) remains
separate evidence; its consumed allowance and registry experiment are not renewed.

## Question And Frozen Inputs

Question: which DLL initialization or loader operation fails in Package 4's
protected Python process on the declared Windows 11 Pro x64 build 26300.9711?
The trace may not resolve the inner cause or establish a safe correction.

- Use unchanged `MayaProtectedPython.exe`, version `0.1.0-startup.4`.
- EXE SHA256: `33c1cb9a4dcd03c79d5e18dd414d06b0d29355839d69cd5a1058b91a8561bdfe`.
- ZIP SHA256: `236f51f1877839923f132b91fd6e8e60170b60ab30539aacc1b58fe7e69a17ed`.
- Preserve its 805 embedded files, reduced same-user token, every child-token
  check, zero capabilities, six WFP denies, product-owned file grants and cleanup.
- Preserve the actual VM/account, RDP, networking, AV, UAC, boot and encryption
  configuration. No registry/file/desktop grant or loopback exemption is added.

The first Package 4 report passed both token validations and resumed the child,
then timed out. Its retained startup marker was absent; the requested Application
log window had no events. The separately approved single Task Manager diagnostic
run produced no dump. A screenshot showed `python.exe` error 0xC0000142; that
run's matching-hash report confirms exit 0xC0000142, zero stdout/stderr and no
startup beacon. Both reports say cleanup completed. These are operator reports,
not independent cleanup or containment qualification. Private identifiers are
omitted. The first timeout's cause is not retroactively proven by the later exit.

## Tool And Impact Disclosure

Use existing Microsoft CDB x64 **10.0.26100.1**, already administratively extracted
on the development PC. No SDK installer or new download is needed for this proposal.
Its source directory is:

`.codex-build/gate-a-loader-diagnostics/portable-debuggers/Windows Kits/10/Debuggers/x64`

Retain its subdirectory layout. Current inventory is 321 files, 94,399,181 bytes.
The preparation rechecked valid Microsoft signatures on CDB, SymChk, dbgeng,
dbghelp, symsrv, winxp/exts and winext/ext/uext. CDB SHA256 is:

`37095ef02baf6bb87e7d0eb4b0fc466dbe2c87cabc60afd114394db6f62edfe9`

Approved setup location: a fresh `%LOCALAPPDATA%\MayaLoaderTrace-20261019`, with
`debugger`, `symbols` and `capture` subdirectories. Copy only the debugger tree;
do not copy historical logs, command files, symbols, payloads or grants. Other
bundled utilities are not invoked. No service, driver, PATH change, postmortem
registration, IFEO setting, persistent GFlags setting or remote debugger is used.

The debugger is a trusted, same-user elevated diagnostic process outside Python's
LPAC boundary. It can inspect target memory and temporarily pauses debuggees.
Only the selected Python child's in-memory loader-snaps flag is deliberately
enabled; the setup host's flags, tokens and product binaries are not patched.
This is an instrumented launch-context difference, not a normal customer result.
No bypass, containment, performance or production acceptance follows.

SymChk would obtain the exact guest ntdll public symbols from Microsoft's symbol
server, before Maya is started. Requests disclose the Windows PDB name/identifier
and ordinary connection metadata, not a dump or trace. Cache stays in the private
diagnostic folder. The capture itself uses that local cache only. No customer
credentials/data, uploads, public sharing, full memory dump or live provider call
is included. Logs can contain local paths, SIDs, PIDs and module addresses; keep
them private and outside Git. Debugger pauses can confound the existing timeout.

## Operator Sequence And Approval Gates

This is the historical procedure for the now-consumed allowance, not permission
to repeat it. Its manual pauses can confound the product deadline. Preserve it
as evidence; do not reuse it unchanged for another diagnostic attempt.

Step 1 was reported complete; the user separately approved one Step 2 launch.
These are not a new script. Do not paste them into a saved wrapper or run the old
capture files. The transfer ZIP's SETUP-ONLY.md gives extraction and hash checks;
its SHA256 is recorded outside the ZIP to avoid a self-referential digest.

### 1. Setup And Preflight

After explicit setup permission, copy the existing debugger directory through
RDP into the proposed fresh `debugger` folder. Create the sibling `symbols` and
`capture` folders using File Explorer. Stop on a conflicting directory, signature
failure, AV warning, changed product hash or pending Maya cleanup; do not repair
permissions or bypass a warning. Verify the copied CDB hash/signature and product
hash before proceeding. Keep Package 4 at its existing verified extraction path.

In VM PowerShell, bind the diagnostic folder (no product launch):

```powershell
$trace = Join-Path $env:LOCALAPPDATA 'MayaLoaderTrace-20261019'
Get-FileHash -Algorithm SHA256 -LiteralPath "$trace\debugger\cdb.exe"
Get-AuthenticodeSignature -LiteralPath "$trace\debugger\cdb.exe"
```

The user's setup approval includes retrieval for only the guest's ntdll:

```powershell
& "$trace\debugger\symchk.exe" /v "$env:WINDIR\System32\ntdll.dll" /s "srv*$trace\symbols*https://msdl.microsoft.com/download/symbols"
```

Require an exact matching symbol result, not merely exit success or an ignored
file. If unavailable, stop before starting Maya; do not use workstation/another
build's symbols, raw structure offsets, registry GFlags or another target run.
Return the preflight output for review before the native-run permission gate.

### 2. One Debugger-Owned Product Launch

After explicit native-run permission and successful preflight, close earlier
Maya windows. Open VM PowerShell as administrator under the **same operator**,
not alternate credentials. An elevated diagnostic shell is a declared difference
from normal File Explorer product testing. The shell below must have the same
`$trace` binding. Confirm the existing EXE path/hash; replace the visible
placeholder with the verified guest path recorded above, never an old Gate A
launcher or Python path. The chat will guide the initial symbol readback, then
the remaining commands within this same attempt; do not restart between stages.

Use the fresh capture directory as the working directory; it must contain no
`ntsd.ini` and no existing `loader-01.log`. Do not reuse/append an old log.

```powershell
Set-Location -LiteralPath "$trace\capture"
& "$trace\debugger\cdb.exe" -o -hd -nosqm -noshell -noinh -sins -y "srv*$trace\symbols" -logo "$trace\capture\loader-01.log" '<VERIFIED-PACKAGE-4-EXE-PATH>'
```

This creates Maya under CDB, not Python directly. The native allowance is consumed
by this launch even if later setup, consent, child following or tracing fails.
It is not permission to correct and retry. `-o` follows children; `-hd` avoids the
debug heap. The other options disable debugger telemetry/shell commands/handle
inheritance and inherited symbol paths. There is no network debugger option.

At CDB's initial prompt, before continuing to Maya's UI, enter these **debugger**
commands (not PowerShell). Confirm ntdll symbols resolve; `!gflag` here is a
read-only host check. If that fails, do not start a protected attempt.

```text
.reload /f ntdll.dll
x ntdll!NtGlobalFlag
!gflag
.childdbg 1
sxn ibp
sxn epr
sxe cpr
sxe -c ".echo MAYA_DLL_INIT_FAILURE; .lastevent; .exr -1; kb; gn" 0xc0000142
sxe -c ".echo MAYA_ACCESS_FAILURE; .lastevent; .exr -1; kb; gn" 0xc0000022
sxe -c ".echo MAYA_ACTIVATION_FAILURE; .lastevent; .exr -1; kb; gn" 0xc0150002
g
```

Maya's window now opens. Use its unchanged disclosure and consent button once.
CDB stops when a child is created. Enter `|` and positively identify the current
child's image as the fresh attempt's `runtime\python\python.exe`. Stop on an
unexpected child; do not enable flags or blindly continue another process. Only
for that confirmed Python child, enter:

```text
sxe -c ".echo MAYA_CHILD_NTDLL; |; .reload /f ntdll.dll; !gflag; !gflag +sls; !gflag; g" ld:ntdll.dll
g
```

The ntdll-load callback runs in the confirmed child event context, before the
later initial breakpoint. This avoids the historical failure of enabling snaps at child-create
before ntdll metadata exists. It is not native-qualified on this guest. Readback
must identify the fresh product Python path/PID and show only bit 0x2 added to
that child's prior flags. Do not interpret missing output, a callback error or a
wrong-process event as successful instrumentation. The `gn` exception callbacks
leave failures unhandled rather than bypassing them. An exit status need not be
raised as an exception; absence of those callbacks does not disprove the failure.

The callbacks continue automatically after recording their commands; a failed
flag command does not itself block the product. Mark such a capture invalid,
let Maya finish its bounded cleanup, and stop without another attempt. Successful
token admission is still the product's decision, never a debugger callback value.

Do not click Open results during capture, manually launch Python, resume its
suspended thread, increase the 30-second wait, patch error handling or change an
API return value.
Maya still owns its restricted-token admission, resume, job and cleanup. If the
application-error dialog appears, record it and acknowledge OK promptly. Let the
product finish. Close Maya normally only after its result/cleanup is available;
CDB can then finish and its log remains on disk.

### 3. Stop, Abort And Evidence

Stop after this attempt, successful or not. Do not add symbols/commands/grants
mid-run to chase another dependency, rerun without the debugger, change accounts,
retry a failed capture or reuse historical diagnostics. A setup/trace failure
consumes its respective stage, not a new permission/correction budget.

If an unexpected debugger stop blocks cleanup, retain `.lastevent` and `|` output.
Do not close CDB or kill the setup host. Only if the currently selected debuggee
is positively identified as this attempt's Python child, the controlled abort is
`.kill` followed by `g`: end that child, then let Maya perform its existing cleanup.
Never apply this to another process. If identity is uncertain, stop issuing
commands and report the screen for guidance. No kill-all or new cleanup helper
is permitted. A pending cleanup result stays blocked; existing product recovery
requires its separate explicit action, not manual security-resource deletion.

Keep the new `attempt.json`, complete fresh `loader-01.log`, any application-error
screenshot and preflight result private. Correlate Python PID/path, artifact hash,
DLL/init status and flag readback; timing under a debugger is not normal timing.
A DLL mapping or a last denied lookup alone does not prove the failing initializer
or a required permission. If the trace still lacks an actionable cause, stop for
review; do not prepare another product correction automatically.

## Instrumented VM Outcome (Allowance Consumed)

2026-10-19: the operator supplied a matching-hash Package 4 report and the private
copied log `.codex-build/maya-loader-setup-20261019/vm-loader-01.log.log`.
The reviewed copy is **15,917 bytes**, SHA256:

`17591861a56d74b611825e4739cb2671fea34e003376ebc0864d5212f7b31858`

Keep the raw log ignored/private. This receipt binds this copy, not any later
version of the still-open VM log. Private operator/attempt identifiers are omitted.

Observed evidence in that copy (one-based lines):

- Lines 161-178: hexadecimal parent/child IDs match the report's decimal IDs.
  The child initially displays only `python.exe`; the later full loader image
  path binds it to the report's fresh product attempt.
- Lines 166-176: the child ntdll callback fires and `!gflag` reads back 0x2,
  Show Loader Snaps, after an initial zero. Tracing really activated in the child.
  The earlier `x ntdll!NtGlobalFlag` emitted no symbol listing; it is not evidence
  of successful named-symbol resolution by itself.
- Lines 178-186: the child begins process initialization, returns an intermediate
  0xC0000135 from loaded-DLL lookup, then enters KERNEL32 loading. No completion
  or final failure of that load, Python DLL initialization, startup beacon,
  0xC0000142 exit or final child-exit record appears in the copy. The intermediate
  lookup status does not prove a missing/corrupt KERNEL32 or a required grant.
- The failure-marker strings at lines 74-76 are callback definitions, not fired
  failure events. Parent first-chance CLR and other diagnostic events do not
  identify a fatal child initializer. The CLR event at line 177 precedes the
  first child loader message, but its managed exception is not decoded here.

The operator report says `blocked` / `python_startup_timeout`, `child_resumed`
true, both token validations passed, six filters verified and cleanup complete.
This is not independent cleanup or containment qualification. The timeout report
omits normal-return output/beacon fields; their absence is not measured zero
output. The copy may be incomplete because it lacks debugger/log closure.

`WindowsIsolation.cs` resumes the child, then uses an ordinary 30,000 ms process
wait. This procedure's manual child-create stop can compete with that deadline.
Windows debug events suspend the affected process; debugger scheduling and the
host wait are not precisely timed by this log. The parent CLR event's ordering
is consistent with deadline interference, not proof of that exception's cause.
The report's roughly 147 seconds from creation to finish includes setup and
operator/debugger time, not a measured Python startup duration.

Conclusion: instrumentation succeeded, but diagnosis of the original DLL-init
failure remains **inconclusive**, with a procedural timing confound. Do not
change Windows DLLs, registry/file grants, protections or product timeout from
this evidence. The one allowance is consumed. First obtain the existing CDB
session's current screen/state for safe closure and final-log handling; do not
issue a blind quit/kill. No new capture, run, rebuild or correction is authorized.

Timing references: [Windows debugging events](https://learn.microsoft.com/en-us/windows/win32/debug/debugging-events),
[WaitForSingleObject](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject).

### Final Log And Session Closure

The operator followed normal Maya-window closure guidance. The next screenshot
shows debugger visualizer unloading followed by the PowerShell prompt. The final
private copy is `.codex-build/maya-loader-setup-20261019/loader-01.log`,
**17,323 bytes**, SHA256:

`d917d7226e8ef956568e9c780846c8de46cc3a7e999b52baa5731cfab05d053a`

Its first 15,917 bytes hash to the earlier receipt, preserving the exact reviewed
prefix. The earlier separate copy is no longer present locally; the matching
prefix hash retains that evidence within the final file. The added 1,406 bytes
(lines 208-218) contain only NatVis visualizer-unload messages, not further Python
loader output or explicit process exit codes. No original 0xC0000142 initializer
failure is localized. Screenshot and final log establish debugger-session closure,
not independent verification of token/resource cleanup or containment. No further
closure commands, log transfer or diagnostic run are pending. The inconclusive
outcome and consumed allowance remain unchanged; stop for a separate decision.

## Preparation Verification And References

Local file/version/signature/hash reads, standard ZIP assembly and documentation
checks were done. Package 4 EXE/ZIP hashes are unchanged. No debugger, SymChk,
protected Python or native launcher was executed by this agent. The operator now
reports successful VM setup and exact ntdll symbol matching. No agent-driven VM
flags or permission change occurred. Step 2's one VM launch is now reported and
its child tracing verified as described above. The subsequent screenshot and
final log resolve debugger-session closure; explicit child exit-code evidence
and independent cleanup verification remain absent. No startup success or
qualification follows.

### Setup-Only Transfer Receipt

2026-10-19 local output:
`.codex-build/maya-loader-setup-20261019/MayaLoaderDebugger-20261019.zip`.
The standard ZIP is **38,261,923 bytes** and has 323 file entries: all 321 unchanged
Microsoft debugger files, debugger-inventory.json and SETUP-ONLY.md. Microsoft
vendor scripts/sample files are retained with the source tree but are not invoked;
no new script or test helper is added. Every archive entry was read back and
compared with its source; all debugger file sizes and hashes match the inventory.

- ZIP SHA256: `afb625e69ee71dba3da5e4c1eb57f6d08c2bef8d4984bd9f79081e60a0e0b127`.
- CDB SHA256: `37095ef02baf6bb87e7d0eb4b0fc466dbe2c87cabc60afd114394db6f62edfe9`.
- SymChk SHA256: `0ef24707284bb2f3bdc5260ec530735b082314616bda94411397105ea19b1e43`.
- CDB, SymChk, dbgeng, dbghelp, symsrv, winxp/exts and winext/ext/uext signatures
  were rechecked as Valid, Microsoft Corporation. No debugger executable ran.
- The ZIP excludes Maya, historical traces/symbols and custom launcher/observer
  binaries. Source debugger files, Package 4 and earlier artifacts are preserved.
- Sibling SHA256SUMS.txt records hashes outside the ZIP. VM transfer, extraction
  and symbol preflight are approved but still await the operator's actual result.
  No diagnostic launch or compatibility/containment claim follows this receipt.

Mechanisms: [CDB options](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/cdb-command-line-options),
[SymChk](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/using-symchk),
[child debugging](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-childdbg--debug-child-processes-),
[event commands](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/sx--sxd--sxe--sxi--sxn--sxr--sx---set-exceptions-),
[exception handling](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/controlling-exceptions-and-events),
[loader snaps](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/show-loader-snaps),
[process flags](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-gflag),
[selected-child termination](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-kill--kill-process-).

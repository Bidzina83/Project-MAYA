# Protected Python Offline Base-Initializer Review

## Authority And Status

2026-10-20: the user explicitly approved private transfer of the exact guest
KERNELBASE.dll and its already-downloaded matching public PDB, followed by a
bounded read-only offline review. The operator subsequently reported both files
copied. Receipt checks and the bounded static review are now complete; see the
dated outcome below. No specific product correction is justified by this scope.

After that outcome the user separately approved the
[final targeted diagnostic attempt](maya_protected_python_final_diagnostic.md).
Its preparation is complete, but fresh VM preflight and execution are pending.
It does not change the completed offline findings or reopen their original scope.

This is separate from the consumed
[live initializer diagnosis](maya_protected_python_initializer_diagnostic.md#captured-outcome-2026-10-20).
Its unexpected child heap-tail flag and incomplete full child-path binding remain
limitations. The offline review does not relabel that attempt as qualified.

## Two Approved Inputs

1. Guest System32/KERNELBASE.dll, SHA256
   `5c29b73622ce0976e1ada566f31f2197ba0f8beaea89c3ec033366126172c3d0`.
   Numeric version 10.0.26100.9711; text version 26100.9278. PE timestamp
   0xfb9071fb, checksum 0x411e21, image size 0x401000.
2. The existing guest-cache kernelbase.pdb with GUID
   79B50527-6F14-0450-EB83-DF0440BF06C6, age 1, cache key
   `kernelbase.pdb/79B505276F140450EB83DF0440BF06C61/kernelbase.pdb`.
   Earlier SymChk reported an exact match and 12,554,240 bytes. The received
   PDB's SHA256 and independently inspected GUID/age fields are recorded below;
   size/name alone were not used to verify identity.

The operator transfers copies through the existing RDP workflow into the local
ignored folder `.codex-build/maya-kernelbase-offline-20261020/`. Do not move,
replace or change the guest's original Windows DLL or symbol cache. No new
transfer script, service, public upload, repository commit or publication.
The workspace remains under the user's existing OneDrive location; Git-ignore
does not disable any user-configured folder synchronization.

## Review Boundary

Verify received file identities before analysis, using existing static inspection
tools/parsers. Do not install tools or download replacement binaries/symbols.
Treat the DLL and PDB as data; no LoadLibrary, regsvr32, debugger target launch,
Maya/Python execution, guest command execution or workstation security change.
If existing tools cannot perform the required inspection, report the limitation
instead of adding a toolchain.

Review one bounded pass through _KernelBaseBaseDllInitialize and its direct
failure exits, starting from the already observed wrapper tail-call at RVA
0x4e6c0 and the captured base-wrapper zero result. Do not recursively inspect
unrelated Windows subsystems or silently extend the earlier live-read allowance.
Compare the visible requirements with the frozen Maya launch/token/environment
source. Preserve the distinction between a static failure possibility and the
operation actually reached in the guest.

Assess the unexpected 0x10 only to the extent supported by available code,
documented contracts and existing evidence. Its provenance or causal relevance
may remain unknown. Do not clear flags, infer heap corruption, grant registry or
desktop access, change accounts, relax LPAC, or perform another comparison run.

## Required Outcome

Return either a specific evidence-backed Maya correction proposal with exact
impact/remaining proof requirements, or a clear statement that this offline scope
does not justify a fix. A proposal is not implementation approval. Do not promise
that disassembly identifies the dynamic root cause, and do not treat a public
symbol name as a documented internal contract.

No new test supervisor or product build is included. If the bounded review cannot
justify a correction, stop for a strategic decision instead of extending the
diagnostic chain. Gate A, containment, Hermes and production stay unqualified.

## Completed Offline Review: 2026-10-20

### Receipt And Symbol Binding

Both inputs are present in the approved ignored directory. SHA256 values:

| Input | Bytes | SHA256 |
| --- | ---: | --- |
| KernelBase.dll | 4,254,784 | `5c29b73622ce0976e1ada566f31f2197ba0f8beaea89c3ec033366126172c3d0` |
| kernelbase.pdb | 12,554,240 | `81658a0fe06f313f0370a4bd988e763bcf791da9a20124b24c3f2db4e3b36b43` |

The DLL hash matches the operator's prior guest hash. Its PE CodeView record
contains GUID 79B50527-6F14-0450-EB83-DF0440BF06C6 and image age 1. The received
PDB's MSF streams independently contain that GUID, PDB Info age 2, DBI age 1,
machine 0x8664 and DBI flags 0x2 (private symbols stripped). Do not describe both
PDB ages as 1 or treat their difference alone as a corrupt/mismatched file.

The existing Microsoft DUMPBIN 14.44.35229.0 found the adjacent PDB through
`/HEADERS /PDBPATH:VERBOSE` and resolved its symbols. The observed age fields
satisfy Microsoft's published `PDB1::OpenValidate4` rule: matching GUID, PDB age
at least image age, and nonzero DBI age equal to image age. This source supports
the binding check; it does not prove why this PDB was rewritten or that every
modern tool uses that implementation.
[Microsoft PDB validation source](https://github.com/microsoft/microsoft-pdb/blob/master/PDB/dbi/pdb.cpp).
The stream offsets/stripped flag were checked against the
[LLVM PDB Info layout](https://llvm.org/docs/PDB/PdbStream.html) and
[DBI layout](https://llvm.org/docs/PDB/DbiStream.html).

No parser/tool installation or binary/symbol download occurred. Existing Python
standard-library binary parsing read the MSF metadata and PE runtime-function
table; it did not load or execute the guest DLL. The optional pefile, capstone
and pdbparse packages were unavailable and were not installed.

### Exact Static Boundary

The DLL's own .pdata entry bounds the selected routine to RVA
`[0x4e6c0, 0x4edec)`, with unwind-information RVA 0x36dec4. Existing Microsoft
DUMPBIN `/DISASM /RANGE` decoded that range from its real function entry, using
preferred image base 0x180000000, not the guest's ASLR base. The retained complete
range output is the ignored file
`.codex-build/maya-kernelbase-offline-20261020/base-initializer-disassembly.txt`,
SHA256 `c8cab61b173073d90be8f3ba792e1829b4f0c4787b6498b45bcc2803a7f4633e`.
An initial partial continuation started inside an instruction at RVA 0x4e900;
its first decoded bytes are not evidence. The retained entry-aligned complete
output supersedes that display.

This was one bounded review of `_KernelBaseBaseDllInitialize` and its direct
return paths. Called helper bodies were not recursively disassembled. Outbound
detach/cleanup paths were not followed: the captured entry reason was process
attach, not detach. Symbol names describe this specific binary, not supported
Windows internal API contracts.

### What Can Return False

On the process-attach path, the routine contains the following explicit tested
failure routes. These are static possibilities, not six observed guest failures.
All addresses below are RVAs in the verified DLL.

| Call / symbol label | Call RVA | Result test RVA | False-return route |
| --- | --- | --- | --- |
| NtQuerySystemInformation, class 0, length 0x40 | 0x4e8fa | 0x4e906 | Negative EAX branches at 0x4e908 to 0x4ec6b |
| CsrClientConnectToServer | 0x4e992 | 0x4e99e | Negative EAX branches at 0x4e9a0 to 0x4ec6b |
| CsrpLocalSetupForSecureProcess, alternate branch | 0x4ed52 | 0x4ed57 | Negative EAX branches at 0x4ed59 to 0x4ec6b |
| BaseNlsDllInitialize | 0x4eba1 | 0x4eba6 | Zero AL branches at 0x4eba8 to 0x4ec6b |
| RtlInitializeCriticalSection | 0x4ebc1 | 0x4ebcd | Negative EAX branches at 0x4ebcf to 0x4ec6b |
| ConsoleInitialize | 0x4ebe1 | 0x4ebe6 | Zero AL branches at 0x4ebe8 directly to the epilogue at 0x4e7b6 |

The common leaf at 0x4ec6b clears AL and jumps to that epilogue. The alternative
secure-process setup is selected by a signed test on a process-parameter field;
the earlier capture did not record that field or either connection result. Do
not claim the ordinary or alternate connection branch was actually taken.

In contrast, failure of RtlUnicodeStringToAnsiString at 0x4eb50 takes a fallback
that clears the ANSI command-line storage and continues initialization; it is
not an immediate false-return route here. Detach cleanup failures cannot be
assigned to the observed process-attach failure. Other calls may have internal
or exceptional behavior not inspected within this scope.

The earlier live observation establishes a false base-wrapper result before ARI
initialization, but records none of these individual tests or initialization
stage values. The final Boolean result and 0xC0000142 do not distinguish these
routes. The unexpected child flags/full-path limitations of that capture remain;
this offline pass does not convert it into a qualified ordinary-run trace.

### Comparison With Frozen Maya Inputs

All seven source/test entries still match the Package 5 manifest. Reviewed
`WindowsIsolation.cs` inputs remain: the same-user reduced primary token,
unchanged session verification, LPAC with zero extra capabilities, atomic
one-process job assignment, three inherited pipe handles, explicit sanitized
Unicode environment/current directory and creation flags 0x08080404. STARTUPINFO
leaves its desktop field null. No source or frozen artifact was changed.

The bounded routine body contains no named environment-variable lookup or direct
filesystem/registry permission check that identifies a missing Maya grant. Its
calls could have requirements not visible in this body. Consequently:

- The server-connection result is unknown. Do not blame the reduced token,
  alter its default DACL, change accounts, or grant access to a Windows service
  based only on that call's symbol name.
- The NLS and console results are unknown. No locale, desktop, console, pipe,
  launch-flag or environment correction is established. In particular, the
  absence of SystemDrive in Maya's environment is not a demonstrated cause.
- ARI policy/repository and built-in-account branches were not reached in the
  captured base-initializer failure. Their earlier disassembly is not grounds
  for another registry or package capability grant.
- Six verified WFP filters and passing token checks do not establish that
  Windows startup succeeded or that containment is qualified.

The observed child NtGlobalFlag 0x10 remains unexplained. No direct test of that
flag was identified in this routine body, and the frozen Maya source contains no
explicit GFlags/NtGlobalFlag setter. Calls into heap/memory helpers were not
inspected, so indirect relevance is not excluded. Microsoft's
[heap-tail-checking reference](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/enable-heap-tail-checking)
identifies 0x10 as heap tail checking; it does not establish its provenance here,
heap corruption, or a reason to disable it. SEM_FAILCRITICALERRORS is a different
setting, not evidence that Maya enabled this global flag.

### Outcome And Stop

The approved offline review is complete. It provides a bounded map of possible
false-return routes, not the dynamically failing operation or an evidence-backed
Maya correction. Do not prepare Package 6 from a guessed grant, environment
variable, token change, altered desktop/console setting or cleared flag.

Stop for a strategic decision instead of automatically extending diagnosis.
No further live read/run, additional offline subsystem investigation, product
patch/build, new test software or OS/security change follows this result. The
inputs and range output remain private and ignored; no DLL/PDB was executed,
Maya/Python/debugger target launched, or VM command issued in this review.
Cleanup remains operator-reported, not independently proved by offline analysis.
Gate A, startup, containment, Hermes and production remain unqualified.

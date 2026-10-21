# Maya Protected Python Startup Package

## Scope

On 2026-10-18 the user requested preparation of the first customer-like VM test
package: Maya's protected Python runtime. This authorizes the bounded product
component's source, local compilation, inert checks and offline assembly, not
native execution or workstation/VM security changes. The active
[Windows testing](governance_v2_customer_windows_testing.md) and
[restricted execution](restricted_hermes_execution_contract.md) contracts apply.
No historical A-D comparison or automatic correction sequence is resumed.

The current `MayaProtectedPython.exe`, version `0.1.0-startup.7`, is implemented in
`src/project_maya/windows_runtime`. This product-owned setup/launcher candidate
uses ordinary AppContainer/WFP for the separately approved Package 7 comparison
below; Packages 1-6 used LPAC/WFP. It is not a test observer, supervisor,
downloader, second AgentRuntime, complete Maya installer or qualified customer
setup path. Its permission and lifecycle behavior is what is being tested.
The historical helper/reference binaries and guest layout are not dependencies.

## Fixed Profile

This section records Packages 1-6. Package 7's explicit ordinary-AppContainer
exception below supersedes only the LPAC selection and corresponding AAP probe.

- Existing Windows 11 Pro x64 **26300.9711**, through RDP; a different build,
  revision or edition blocks startup rather than reconfiguring Windows.
- CPython **3.13.14**: all 796 frozen distribution files, unchanged and embedded.
  Assembly verifies their historical reproduction-manifest hashes. The unopened
  ensurepip bootstrap wheel remains included; pip is not installed or invoked.
- One fresh package identity, **zero extra capabilities**. No registry permission
  correction, registryRead/lpacCom, privateNetworkClientServer or internet grant,
  loopback exemption, gateway or network exception is requested.
- Six persistent package-SID-specific WFP block filters: IPv4/IPv6 connect, listen
  and receive/accept. This tighter offline startup scope does not qualify later
  gateway connectivity or replace the approved mediated-runtime architecture.
- Administrator-owned runtime files with package read/execute grants, and separate
  private state read/write grants.
  Only the state folder has its integrity label lowered. State-file grants omit
  execute permission; the Windows-created container profile is also private
  operational storage. Both user and package grants are required for state I/O.
- One suspended Python process. Before resume, verify package/user SID, LPAC
  AccessCheck controls, low integrity, no elevated token/capabilities and filter
  readback. No ordinary-process or ordinary-AppContainer fallback is resumed.
- Atomic job assignment at creation, kill-on-close, no breakaway, process limit
  one and child creation restricted. Only dedicated pipe handles are inherited.
- Fixed absolute Python/check paths, `-I -S -B`, a clean eight-variable environment
  and private working directory. The built-in-only check verifies version/flags,
  exclusively creates `python-startup.txt` and sends the same fresh attempt-bound
  message to stdout. Zero exit, exact stdout and the fresh matching file are all
  required for success. No customer-resource denial probes or sockets are run.

The trusted setup/launch host is elevated for this bounded attempt; the child
must independently pass restricted-token checks. Package 4 first constructs and
verifies a reduced same-user primary token, then explicitly supplies it to the
LPAC process creation call; it does not launch an intermediate ordinary process.
The VM's current administrator
account is retained. This does not qualify standard-user installation, privilege
separation in the finished product or Hermes. Elevation under another administrator
identity is rejected, not silently applied to another user's profile. No elevated
terminal is required. The historical Python loader failure remains unresolved;
the package does not assume this tighter profile fixes it.

## Consent And Lifecycle

Opening the executable shows a disclosure and unchecked consent box. Merely
opening it creates no profile, file grant or network rule. **Open setup** requests
Windows elevation if needed, then requires product consent again. Refusal blocks
launch. A CLI switch cannot approve the disclosure. No AV/firewall default, boot,
encryption, NIC, RDP or Azure setting is changed. Windows maintains its normal
per-user container-profile metadata; no registry access grant is given to Python.
No service, startup task, public listener or external upload is installed.

After consent, Maya uses only its own administrator/SYSTEM-controlled root:

`C:\ProgramData\MayaProtectedPython-Startup1\<attempt-id>`

Each attempt has an operator-readable `attempt.json`, runtime and private state.
Unexpected existing root permissions or reparse paths are rejected, not repaired.
Embedded paths, case-insensitive duplicates, sizes, required files and SHA256
hashes are checked. No user-selected runtime/script/destination/address is accepted.

The Python wait limit is 30 seconds. The host stops and confirms the job empty
before removing grants, restoring its state label, deleting the profile and
removing/read-checking its filters. Prepared files/reports remain for inspection;
they are not recursively deleted. Unrelated settings are preserved. These are
source-level behaviors, not native lifecycle qualification.

Uncertain termination or security cleanup produces `cleanup_pending_stop`.
Network denies remain if job termination is uncertain. A durable attempt record
and exclusive product lifecycle lock block a new launch with pending cleanup.
After closing the earlier window, the same operator/artifact can explicitly use
**Recover cleanup**. It removes only this product's pending setup, never launches
Python or creates another attempt, and remains available after an OS update.
Unknown/colliding profiles, records, operators or root permissions require review,
not blind deletion. Report recovery failure rather than retrying automatically.

## VM Steps

Package 6's separately approved first ordinary run has now returned a startup
failure; see its operator result below. The handoff steps here are historical,
not permission to repeat them. Preserve all packages/reports. No retry, debugger,
new package, broader permission or further VM test is approved by that result.

1. Copy `Maya-Protected-Python-Startup-6.zip` through the existing RDP connection
   and extract into a new folder. Do not merge into `C:\MayaGateA`, run the old
   tools or manually prepare Windows permissions.
2. Compare the ZIP/executable SHA256 against this build's handoff hashes, then
   open `MayaProtectedPython.exe` from File Explorer. No new VM tools are needed.
3. Read the disclosure. Only when approving that exact scope, check the box and
   click **Start protected Python**. **Open setup** requests UAC first if needed.
   This explicit security/run consent is separate from package preparation.
4. Wait for the result, click **Open results** and return `attempt.json`. For an
   error before a report exists, send the displayed message or screenshot.
   Reports contain local SID/PID/path metadata: keep them private. Raw child stderr
   is discarded; only its bounded byte count is recorded.
5. Stop after the first result. A blocked setup/startup is a failure, not a passing
   denial or proof of containment. If cleanup is pending, report it and stop;
   recovery requires a separate explicit product action. Do not disable protection,
   manually grant resources, retry startup, reset the VM or correct registry access.
   Retain the existing snapshot and disks as rollback resources.

## Verification And Build

Local checks compile C# with warnings treated as errors, run inert C# cases for
path/inventory validation, native structure sizes and in-memory ACLs, and run
Python health-check units with synthetic version/flags/I/O. They do not invoke
the launcher entrypoint, UAC, profile/ACL/WFP changes or embedded Python. Final
archive inventory and hashes are independently read back. Native lifecycle, UAC
and Windows 26H2 compatibility remain untested until the separately consented run.

Use the existing x64 .NET Framework C# compiler with `/target:winexe /platform:x64
/optimize+ /warnaserror+`, the three component C# sources and
`ProtectedPython.manifest`. References: `System`, `System.Core`, `System.Drawing`,
`System.Windows.Forms`, `System.Web.Extensions`, `System.IO.Compression`,
`System.IO.Compression.FileSystem`. Embed resources named `MayaPython.payload.zip`
and `MayaPython.payload-index.json`. The index contains the archive SHA256 and
every embedded file's path/size/SHA256. These are generated build artifacts, not
guest tools. Standard ZIP assembly is used; no new packaging/transfer script or
framework is installed.

Trust assumptions are Windows/kernel/native APIs, .NET, trusted administrator/
control host and verified build inputs. Host/admin compromise is not tested.
API readback and startup success do not qualify bypass protection. Useful Hermes
execution and denied/bypass cases remain Gate A obligations. Production remains
blocked; the existing installer, runtime pin and historical evidence are unchanged.
This unsigned candidate is not release-qualified: stop on AV/SmartScreen blocks,
do not bypass them. Included notices are not external redistribution clearance or
Windows licence-entitlement proof.

Native contracts consulted: [LPAC launch](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer),
[process attributes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute),
[token information](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ne-winnt-token_information_class),
[profile deletion](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-deleteappcontainerprofile),
[security descriptors](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-setnamedsecurityinfow).
Those describe mechanisms, not a passing result for this artifact.

## Package 1 Build Receipt (Historical)

Local output: `.codex-build/maya-protected-python-startup-20261018/`.
`Maya-Protected-Python-Startup-1.zip` is **14,670,838 bytes**, containing 12
handoff files. The executable embeds 805 payload files (796 unchanged Python
files, the startup check and eight vendor notices). The archive includes its
guide, notice index and source/artifact hash manifest; no test fixtures or old
helper/reference/observer binaries are shipped.

- ZIP SHA256: `6e81cb45e68dd0993933e5c3cb4b0f27299a0e9d196028d32e28f424079c0ede`
- EXE SHA256: `e006c98127d2e2d4d7bc5f4abe652492ee6b70e59dd07f855ad0b256bc2d6968`
- Compiler: existing x64 .NET Framework C# compiler, warnings-as-errors, zero
  warnings/errors; PE readback confirms x64 Windows GUI executable.
- Inert C# checks: **50 passed**; Python/context/line-ending/notice unit cases:
  **14 passed**. Context guard and whitespace checks pass.
- Payload extraction through the component file-loading code passed without
  security provisioning or Python execution; every extracted/packaged file was
  independently rehashed. A prior reflection-only check under the shell's .NET
  runtime failed to load a Framework serialization type; using the compiled
  Framework unit fixture exercised extraction successfully. No native runtime
  failure or Windows permission change occurred during that local check.
- At package 1 assembly time, native launcher entrypoint, UAC, profile/ACL/WFP
  provisioning, restricted Python startup and cleanup had **not** run locally or
  on the VM. The subsequent operator-reported result is recorded below; the
  previous loader blocker is not represented as fixed.

The final ZIP hash is recorded outside the archive to avoid a self-referential
digest. These local assembly results do not grant execution/security consent.

## First VM Result And Approved Package 2 Correction

The operator supplied package 1's `attempt.json` on 2026-10-18. Its launcher hash
matches the package 1 receipt. It reports informed consent, verified payload and
six read-back network filters, then `read_child_token_20:win32_24`, with
`child_resumed=false`, `python_started=false`, `status=blocked` and
`cleanup_complete=true`. This is an operator-reported native pre-resume failure,
not a Python compatibility result, full cleanup qualification or containment proof.
Private attempt/operator/process identifiers are intentionally not copied here.

The source queried TokenElevation (class 20) using the same 4096-byte length as
variable-size token information. Windows returned ERROR_BAD_LENGTH (24).
TOKEN_ELEVATION contains one DWORD. The user explicitly approved this bounded
query correction, targeted regression checks and preparation of package 2, with
all permissions/protections unchanged. This is not another grant/capability,
diagnostic matrix, automatic retry budget or permission to bypass a later failure.

Package 2 requests exactly four bytes for class 20 and requires successful API
completion, an exact four-byte return length and a zero elevation flag. Every
other token check, job/process restriction, network filter, file/registry/capability
scope, payload and cleanup path stays unchanged. The actual native caller uses
this same checked method; its injected query delegate is only an inert unit-test
interface, not a runtime-configurable backend or a new test application.

Regression cases simulate an API that rejects the old 4096-byte call and accepts
four bytes; nonzero elevation flags, incorrect returned lengths and API failure
remain blocked. No real token query, security change or Python launch is needed
for these unit cases. Native success of the correction still needs the VM run.

Keep package 1 and its original report. Close its window, extract package 2 into
a separate new folder, verify its new hash/version and use its existing consent
flow. A completed package 1 record can remain in the product folder; no OS reset,
manual permission change or deletion is required by the reported result. If a
record instead shows pending cleanup, stop for its existing supported recovery;
package 2 does not adopt or rewrite another version's incomplete record. Return
the new `attempt.json` and stop after that result. No corrected launcher or
protected Python process is executed on the development PC during preparation.

API references: [TOKEN_ELEVATION](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-token_elevation),
[GetTokenInformation](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-gettokeninformation),
[ERROR_BAD_LENGTH](https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-).

## Package 2 Build Receipt

Output: `.codex-build/maya-protected-python-startup-20261018-2/`.
`Maya-Protected-Python-Startup-2.zip` is **14,673,354 bytes**, with 12 handoff files.

- Version: `0.1.0-startup.2`; file version `0.1.0.2`.
- ZIP SHA256: `9a6cfcfda59ba22207b4ca3de91bee0e48998f7e3cc41f67842b2a2b62e9f34c`
- EXE SHA256: `eca4d33581bd903c34f5e54d2a1e09271c17e2cb5f377ae1cc7556840722253a`
- C# warnings-as-errors compilation passes; **60 inert C# checks** and **15 unit
  cases** pass, including the exact-length and fail-closed regressions. Context
  guard and whitespace checks pass.
- All 805 embedded files unpack/hash-check successfully without provisioning or
  Python execution. Embedded payload bytes and the security-scope manifest match
  package 1 exactly. Every handoff archive entry was independently rehashed.
- Reconstructing the original source by reversing only this correction/version
  change reproduces package 1's recorded source hashes. Product file setup/cleanup,
  startup check and application manifest hashes remain identical to package 1.
- Original ZIP/executable hashes remain unchanged. The failed operator report and
  package 1 receipt are retained rather than relabelled as corrected success.
- Corrected native query/launcher, UAC, security lifecycle and Python startup have
  not been executed on either machine during package 2 preparation. A separately
  consented VM result is still needed; no compatibility/containment claim follows.

The current hashes are also in the sibling `SHA256SUMS.txt`, outside the ZIP.

## Second VM Result And Approved Package 3 Reporting Update

The operator supplied package 2's report on 2026-10-18. Its launcher hash matches
the package 2 receipt. It reports verified payload, six read-back filters, then
`child_token_restriction_mismatch`, with `child_resumed=false`,
`python_started=false` and `cleanup_complete=true`. This generic code was shared
by the AppContainer flag, capability count and elevation flag checks. The report
does not identify the failed property; do not infer that elevation was definitely
the rejected value, that the corrected query was reached or that Python ran.
Private attempt/operator/process identifiers are intentionally omitted here.

The user explicitly approved a reporting-only update and package 3 preparation.
The three rejection predicates remain exactly the same: AppContainer flag must
equal one, capability count must equal zero and elevation flag must equal zero.
Failure is still immediate, before resume; no subsequent checks are queried to
fill a report after rejection. API failure or malformed query size still blocks
without inventing an observed value.

Package 3 supplies distinct reason codes:

- `child_token_is_appcontainer_mismatch`
- `child_token_capability_count_mismatch`
- `child_token_elevation_mismatch`

For these failures only, the existing `attempt.json` gains an optional
`token_check_failure` object with `check`, `information_class`, `expected` and
`observed`. Only fixed check names and numeric scalar values are included, never
raw token buffers, capability identities, credentials or customer content.
The report schema and existing cleanup fields remain compatible. The startup
record writer is the actual product path, not a separate observer or test runner.

Inert regressions compare accepted/rejected outcomes with the original predicates
for zero, one, other nonzero values and the full unsigned DWORD range boundary.
They verify each reason code and exact details through JSON serialization, check
that the elevation API path uses the same reporting, and ensure query failures
and unrelated exceptions have no fabricated token values. The previous four-byte
query regression and all earlier checks remain in force.

No payload, native API query parameters/order, permissions, capability grants,
job/process restrictions, filters, cleanup, recovery or startup admission decision
is changed. Package 3 changes only failure reporting and version identifiers.
No native launcher or protected Python run occurs locally during preparation.
Retain packages 1/2 and their reports. Close the previous window, copy/extract
package 3 into a new folder and use its unchanged product consent flow. Based on
reported complete cleanup, no reset/manual OS change is required. Return the new
report and stop; this approval does not authorize bypassing or correcting whichever
property it identifies, another diagnostic sequence or Gate A acceptance.

## Package 3 Build Receipt

Output: `.codex-build/maya-protected-python-startup-20261018-3/`.
`Maya-Protected-Python-Startup-3.zip` is **14,675,630 bytes**, with 12 handoff files.

- Version: `0.1.0-startup.3`; file version `0.1.0.3`.
- ZIP SHA256: `42ab7a51627d720fbbf988980037357811b9e6a6da7fccbad7948f9a4e942f56`
- EXE SHA256: `3f3561404efde138ded834506396f05ce6b1e5c2e1ec9b8015fef1e23706bd8c`
- Warnings-as-errors compilation passes. **90 inert C# checks** and **16 unit
  cases** pass, including unchanged acceptance/rejection predicates, exact
  failure fields through JSON and no fabricated values on query failure.
- All 805 embedded files unpack/hash-check without security provisioning or
  Python execution. Payload bytes and security scope match package 2 exactly;
  every handoff archive entry was independently rehashed.
- Reversing only the reporting/version changes reproduces package 2's recorded
  source hashes. Filesystem setup/cleanup, startup check and application manifest
  remain unchanged. Both earlier ZIP/executable artifacts are preserved.
- Package 3's native query/launcher, security lifecycle and Python startup have
  not been executed on either machine during preparation. The next report must
  establish the rejected property; no fix, native qualification or acceptance
  is claimed from these local checks.

Sibling `SHA256SUMS.txt` records the current hashes outside the archive.

## Third VM Result And Approved Package 4 Correction

The operator supplied package 3's report on 2026-10-18. Its launcher hash matches
the receipt. It reports `child_token_elevation_mismatch`, with class 20 returning
**1**, expected **0**, after payload and six filter checks. Python was not resumed
or entered; cleanup is reported complete. Earlier package/user, low-integrity,
AppContainer and zero-capability checks precede elevation in the source. Group
enumeration and the LPAC AccessCheck controls follow it and were not reached.
This flag alone is not proof of unrestricted effective administrator authority.
Private operator/attempt/process identifiers are intentionally omitted here.

The previous launch used `CreateProcessW` from the elevated setup host. The user
approved assessment and preparation of a same-user privilege-reduction correction,
preserving every existing check and stopping if the method cannot satisfy them.
Package 4 uses one fixed product-owned method, not token discovery or fallbacks:

1. Open the setup process's primary token with query, duplicate, assign-primary
   and adjust-default handle access. Derive a new token with `CreateRestrictedToken`
   using **DISABLE_MAX_PRIVILEGE | LUA_TOKEN**, and explicitly disable the
   Administrators SID. No linked-token assumption is made for the current
   built-in Administrator account. No other user's token or credentials are used.
2. Lower only the new in-memory token to medium integrity. Verify same user,
   primary type, unchanged session, zero elevation, zero sandbox-inert/UIAccess
   flags, non-AppContainer base, medium integrity and deny-only Administrators
   membership. Verify that no privilege remains except, optionally,
   SeChangeNotifyPrivilege. Token API failures, wrong sizes/pointer bounds or
   unexpected properties stop before process creation; LUA behavior is checked,
   not assumed to produce elevation zero on this OS/account.
3. Supply that verified token explicitly to `CreateProcessAsUserW`, with the
   existing LPAC security attributes, atomic job assignment, suspended/no-window
   flags, three-handle inheritance list, paths, environment and working directory.
   No intermediate ordinary process is launched. Close the non-inheritable token
   handles on success/failure. The elevated host's token is never modified.
4. Run the **unchanged** child-token checks before resume, including elevation
   zero and all four LPAC AccessCheck controls. Failure stops; no alternate token,
   ordinary launch, relaxed predicate or automatic retry is available.

This changes the process-creation API/base token, not the Python payload, file
permissions, private state label, network filters, capabilities, registry access,
job constraints, cleanup or recovery. No account/UAC/desktop ACL/security-policy
change, service or additional test application is installed. The API may temporarily
enable required privileges already held by the trusted caller; Maya grants no
account privilege and calls no privilege-enabling API itself. Missing privilege
or desktop/access compatibility is a blocking result, not permission to repair it.

The disclosure now names same-user token reduction. The existing report records
`reduced_launch_token_verified` separately from `restricted_token_verified`:
the former alone does not mean a child exists or that its LPAC checks passed.
Base scalar failures use `launch_token_*_mismatch` and the existing optional
numeric check object; child reason codes/predicates remain unchanged. No raw
token contents or new personal metadata are reported. Recovery does not invent
a new base-token verification result or rewrite an older version's report.

Inert tests exercise the real validation methods using bounded synthetic buffers:
same-user success; wrong primary/session/elevation/inert/UIAccess/container flags;
wrong user/integrity/admin membership/privileges; every queried API failure;
truncated/oversized buffers; and invalid SID pointers/counts. Static wiring checks
verify explicit reduced-token launch with no fallback and no host-token mutation.
These checks do not execute token construction, native process creation or Python.

Native references: [CreateRestrictedToken](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-createrestrictedtoken),
[CreateProcessAsUserW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessasuserw),
[SetTokenInformation](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-settokeninformation),
[mandatory label](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-token_mandatory_label).
The documented restricted-token GUI/desktop warning is not resolved merely by
CREATE_NO_WINDOW. This fixed payload has no GUI workload; desktop/message/IPC
bypass resistance and general worker protection remain unqualified. The existing
desktop selection is unchanged; no desktop grant or separate desktop is added.

Native compatibility of this combination on 26300.9711 remains unproven. The
historical Python loader denial is not fixed by inference. Existing complete
cleanup reports do not require an OS reset/manual preparation. Close the earlier
window, retain its artifact/report, extract package 4 separately, verify hashes
and use product-owned consent through RDP. Return the first result and stop;
failure does not authorize another correction. No protected Python/native setup
run is performed on either machine during preparation. This is not qualification
of standard-user installation, customer-population compatibility, containment,
Hermes, Gate A or production activation.

## Package 4 Build Receipt

Output: `.codex-build/maya-protected-python-startup-20261018-4/`.
`Maya-Protected-Python-Startup-4.zip` is **14,680,309 bytes**, with 12 handoff files.

- Version: `0.1.0-startup.4`; file version `0.1.0.4`.
- ZIP SHA256: `236f51f1877839923f132b91fd6e8e60170b60ab30539aacc1b58fe7e69a17ed`
- EXE SHA256: `33c1cb9a4dcd03c79d5e18dd414d06b0d29355839d69cd5a1058b91a8561bdfe`
- Warnings-as-errors compilation passes. **168 inert C# checks** and **17 unit
  cases** pass, including reduced-token validation, earlier elevation/reporting
  regressions and static no-fallback wiring. Context and whitespace checks pass.
- All 805 embedded files unpack/hash-check without provisioning or Python
  execution; payload/index bytes match package 3 exactly. Independent readback
  verifies every final ZIP entry and confirms x64 GUI PE/version metadata.
- Frozen pre-edit native sources match package 3's manifest hashes. Direct source
  comparison confirms unchanged child-token checks, LPAC AccessCheck controls,
  profile/filter provisioning and cleanup, job stop/disposal and output capture.
  Filesystem code, startup check and application manifest are byte-identical.
- The archive ships no fixture, historical launcher, observer or source-before
  files. Its guide includes the fixed correction contract; this final receipt
  and ZIP hash remain outside the archive to avoid a self-referential digest.
- Token construction, CreateProcessAsUserW, UAC, native security lifecycle and
  protected Python have **not run** during preparation. Native compatibility and
  containment are not established. All earlier artifacts and reports are retained.

Sibling `SHA256SUMS.txt` records both current artifact hashes.

## Package 4 Operator Results And Diagnostic Preparation

The first Package 4 report matches its EXE hash and records both launch-token and
restricted-child verification, child resume, `python_startup_timeout` and complete
cleanup. The retained startup marker was absent. The read-only Application-log
query found no events in the selected time window. Timeout does not establish
the interpreter's stopping point or the success of any Python script step.

The user then separately approved one unchanged-package Task Manager diagnostic
run. No dump was obtained. The operator captured a `python.exe` application-error
dialog showing 0xC0000142. This run's matching-hash report independently records
`status=startup_failed`, `child_exit_hex=0xC0000142`, both token verifications,
child resume, zero stdout/stderr, no fresh state/stdout beacon and complete cleanup.
It is not a successful Python startup or proof of containment. The screenshot and
report agree on DLL-initialization failure, not which DLL or why; the earlier
timeout's connection to an error dialog remains an inference. Private attempt,
operator and PID identifiers are intentionally omitted here.

On 2026-10-19 the user approved preparation of the
[loader-diagnostic procedure](maya_protected_python_loader_diagnostic.md), including
scope, evidence and stop conditions. That record proposes one instrumented run
with existing Microsoft tools, keeping this artifact and protections unchanged.
VM tool transfer/setup, public-symbol retrieval and native execution still need
explicit permission. No new product patch, script, supervisor, OS preparation,
runtime upgrade, registry grant or automatic correction/retry is authorized.
The four package archives and their embedded guides/manifests remain frozen;
this later source record does not rewrite their build-time execution statements.

The user's subsequent 2026-10-19 approval covers debugger transfer/setup and
matching Microsoft public-symbol retrieval only. See the loader procedure for the
setup-only ZIP and operator preflight. This does not authorize another native
Maya/Python run, alter any package or establish that VM setup has completed.

The operator then reported matching transfer ZIP hash, Valid debugger signatures
and exact guest ntdll PDB/DBG matching, with zero failed symbol files. The supplied
guest EXE path/hash matches Package 4. The user explicitly approved one
debugger-controlled run, preserving protections and its 30-second wait. The loader
procedure records the binding and initial readback stage; native capture/cleanup
results are pending. No new build, permission grant or automatic retry follows.

### Instrumented Package 4 Outcome (2026-10-19)

The one approved debugger-controlled run reports `python_startup_timeout`, child
resumed, both token checks passed, six filters verified and complete cleanup.
The copied private log matches that report's host, child and attempt path. It
confirms child loader snaps enabled, but stops during early KERNEL32 loading;
there is no captured failing initializer or original 0xC0000142 exit. Manual
debugger pauses can compete with `ResumeAndWait`'s unchanged 30-second wait.
The trace is inconclusive, not evidence that KERNEL32 is missing or permissions
need expansion. Cleanup is operator-reported, not independently qualified, and
the copied log lacks final debugger exit/closure. The allowance is consumed;
establish the current session state before closure guidance. No further run,
timeout change, product correction or security grant is authorized. The full
evidence receipt is in the loader diagnostic procedure; Package 4 is unchanged.

Subsequent normal Maya closure returned CDB to PowerShell in the operator's
screenshot. The final log adds only visualizer-unload messages to the exact
reviewed prefix. Session closure is resolved without additional startup or
explicit exit-code evidence; diagnosis remains inconclusive. No more closure
steps or captures are pending, and no new run or correction is authorized.

## Package 5 Approved Reporting Correction (2026-10-20)

The user approved the source-review recommendation to correct the first two
findings, not the missing-initial-journal recovery gap. That gap remains open;
do not silently delete or adopt a journal-less attempt. Package 5 has no claimed
fix for the actual 0xC0000142 DLL-initialization failure. Prior artifacts, raw
evidence and the consumed debugger allowance remain unchanged.

The bounded changes are:

- Before opening the UI, read the host process error mode, add only
  SEM_FAILCRITICALERRORS (0x1), set it and require exact readback. Preserve every
  existing bit. Python inherits this process-local setting because creation
  flags remain unchanged. This avoids critical-error message boxes for supported
  error classes; it does not promise to suppress every possible Windows dialog.
  No WER suppression, registry/IFEO/GFlags, desktop change or machine policy is
  added. Native error-mode behavior remains unqualified until an approved VM run.
- On a failed resumed attempt, first stop the job and join its output readers
  through the existing stop path. Only then record available stdout/stderr byte
  counts, exact stdout-beacon matching and the fresh state beacon, before file
  grants are revoked. The report never includes raw child output or stderr.
- Preserve the original failure reason, blocked status and `python_started=false`
  even if both beacons exist after a timeout. The 30-second process wait is
  unchanged; this is evidence retention, not a longer run or startup acceptance.
- Add `output_capture_complete`. Unavailable/failed capture has null counts and
  null `stdout_beacon_matches`, not a fabricated zero/false. A completed empty
  capture has numeric zero counts. The bounded existing readers are unchanged.
- Add `child_exit_observed_before_cleanup`. `child_exit_hex` is present only
  when the normal wait observed a natural exit before stopping; never substitute
  TerminateJobObject's forced exit code as the original failure. A timeout can
  therefore still have no observed exit code.
- Failure evidence has `evidence_phase=after_job_stop`. An unreadable state
  marker is null with a fixed `evidence_reason_code`; evidence failure does not
  prevent security cleanup or replace the original startup failure. If stopping
  is uncertain, do not inspect the state or revoke protection; retain the existing
  cleanup-pending behavior. Recovery does not create or re-evaluate startup evidence.

The Python payload/index, startup check, application manifest, filesystem setup,
token admission/reduction, LPAC capabilities, process/job limits, inherited handles,
WFP definitions, cleanup/recovery and success predicates are unchanged. No new
test script, supervisor or diagnostic tool is added. Inert error-mode delegates
and report dictionaries test the correction without calling native error-mode,
security or process APIs. Source wiring checks cover stop-before-inspection,
unchanged wait/flags and preservation of failure classification.

References: [SetErrorMode](https://learn.microsoft.com/en-us/windows/win32/api/errhandlingapi/nf-errhandlingapi-seterrormode),
[process-creation flags](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags).
The existing error-dialog screenshot supports the reporting concern, not proof
of the earlier timeout's cause or of the DLL initializer that failed.

## Package 5 Build Receipt

Output: `.codex-build/maya-protected-python-startup-20261020-5/`.
`Maya-Protected-Python-Startup-5.zip` is **14,688,556 bytes**, with 12 handoff files.

- Version: `0.1.0-startup.5`; file version `0.1.0.5`; x64 GUI executable.
- ZIP SHA256: `3523429149640869ef4237011e44d6ffb01dcb747ea14b95fa74a66c354457df`
- EXE SHA256: `6709bb7673c1eca2fecec006cf2c72dd7b3059278c3e7a92d59034c6bac92b66`
- Warnings-as-errors compilation, **208 inert C# checks** and **20 Python unit
  cases** pass, including prior token regressions, process-local error-mode
  delegates, failed-child report dictionaries and source-wiring checks.
- All 805 payload files pass extracted size/hash checks; payload ZIP and index
  match Package 4 byte-for-byte. Read-only PE metadata/resource parsing confirms
  both resources in the final product executable match the frozen inputs without
  loading or executing that product assembly. Every final ZIP file matches its
  handoff source and the handoff/source manifests verify.
- Frozen source-before files match Package 4's source hashes. Direct comparisons
  preserve native launch attributes/flags, token reduction/validation, profile/WFP
  setup/cleanup, bounded readers, 30-second wait, job stop and disposal. Filesystem
  setup, Python check and application manifest remain byte-identical. The separate
  initial-journal recovery gap is not repaired or hidden by this package.
- The archive contains only the product EXE, guide, third-party notices and
  manifest. No fixture binary, source-before tree, old launcher, supervisor or
  debugger is shipped. This receipt/hash stays outside the archived guide to
  avoid self-referential digests; sibling `SHA256SUMS.txt` binds both artifacts.
- The first local compiler invocation rejected forward-slash source paths;
  absolute Windows paths corrected that build invocation. No native product or
  security action occurred. Error-mode APIs, UAC, protected Python and native
  setup/cleanup have **not run** during preparation. All earlier packages remain
  unchanged. Separate VM-run approval/product consent are still required.

This reporting correction is not a claimed DLL-init fix, supported-platform
qualification, containment proof, Gate A acceptance or production activation.

## Package 5 Operator Result (2026-10-20)

After reporting the package ready on the VM, the operator supplied its first
result. The chat had requested confirmation for one normal RDP run; no separate
textual confirmation or launch transcript was supplied. The report itself records
informed consent. Treat this as reported execution, not retroactive approval of
any further run. Its launcher SHA256 matches the Package 5 build receipt.

- Windows build 26300.9711, elevated host, payload verified, six filters read back,
  reduced launch token and restricted-child token verified, child resumed.
- `status=startup_failed`, `startup_status=startup_failed`, `python_started=false`.
- `child_exit_observed_before_cleanup=true`, `child_exit_hex=0xC0000142`.
  This is an exit observed by the normal wait, not the job's forced-stop code.
- `output_capture_complete=true`, stdout and stderr byte counts both zero,
  `stdout_beacon_matches=false`, `fresh_state_beacon=false`.
- `cleanup_complete=true` is product/operator-reported, not independent security
  cleanup verification. Production and containment qualification remain false.

The complete attempt spans approximately 18.43 seconds, including setup/cleanup;
this is not an isolated Python startup timing measurement. The report is not a
timeout and does not exercise the new after-stop timeout-evidence branch. It
confirms that normal-exit reporting captured a real DLL-initialization failure
with measured-empty output, not unavailable capture. Reaching this path is
consistent with passing the host error-mode readback, but no dialog observation
or child error-mode readback was supplied. Do not claim complete qualification
of dialog suppression or native timeout diagnostics from this one result.

The original failure persists; the failing DLL/resource remains unidentified.
No Windows-file repair, new grant/capability, timeout increase, automatic retry,
new trace or further product correction is justified or authorized by this result.
Preserve Package 5 and its report. Private SID/attempt/PID metadata is intentionally
omitted from tracked documentation. No code, package or frozen evidence changed
while recording this result; Gate A and production activation remain blocked.

The user's subsequent approval covers preparation of the separate
[automatic loader-capture proposal](maya_protected_python_loader_capture_v2.md)
for review, not execution. It preserves this Package 5, protections and deadline,
using existing CDB/cache with notification callbacks configured before consent.
The actual guest EXE path and separate one-launch approval remain pending. No
new product build, script/tool, permission change or renewed historical allowance
follows this documentation-only preparation.

## Package 5 Instrumented Loader Result (2026-10-20)

After separate one-run approval, the operator supplied the
[V2 capture result](maya_protected_python_loader_capture_v2.md#captured-outcome-2026-10-20)
and a matching fresh Package 5 report. The correct child has loader snaps enabled
and exits naturally with 0xC0000142. KERNELBASE.dll maps successfully, but its
DLL_PROCESS_ATTACH initializer fails during Windows KERNEL32 initialization,
before any observed python313.dll mapping. This identifies the failing initializer,
not its internal cause or a safe correction.

The report confirms payload/token/filter checks, child resume, complete empty
output capture, no startup beacon and reported complete cleanup. Python startup,
containment and production qualification remain false. The pasted trace lacks
host/debugger closure evidence. No product files, frozen inputs or VM protections
changed while recording this result. The diagnostic allowance is consumed; stop
for a separate decision before another run, trace, grant or product correction.

The operator then confirmed normal session closure and approved the
[launch-source review](maya_protected_python_launch_review.md). Package 5 source
and executable hashes match, and 11 current unit/static checks pass. No confirmed
startup correction was identified. Desktop/bootstrap resource leads are not
permission to change them. No Package 6, native run or VM change was performed.

## Package 5 Initializer Observation Result (2026-10-20)

The subsequent separately approved
[initializer attempt](maya_protected_python_initializer_diagnostic.md#captured-outcome-2026-10-20)
returned a matching report and actual four-point hardware installation readback.
Initializer entry reason 1 and base-helper EAX=0 were observed; ARI's return and
the later failure leaf did not fire. This narrows the observed failure to the
base-initialization path without identifying its internal operation/resource.

The child global flag was unexpectedly 0x10 (heap tail checking), not the required
zero; the log also lacks independent full child-image-path confirmation. The
zero t9 guard does not validate those conditions. This is partial instrumented
evidence, not the intended clean-profile diagnostic or a safe correction.
Natural child exit remains 0xC0000142, output is measured empty, no beacon appears
and cleanup is reported complete. Host exit zero and debugger unload tail are
present. Both budgets are consumed; no more VM action, retry, grant or patch
follows. Startup, containment, Hermes, Gate A and production remain unqualified.

## Package 6 Approved Console-Mode Candidate (2026-10-21)

The separately approved final Package 5 diagnostic localized a false Windows
ConsoleInitialize result, then the user approved a focused source review.
See [the console-launch review](maya_protected_python_console_launch_review.md).
No pipe/layout defect or inner failing console resource was established. The
user then explicitly approved preparation of Package 6, without running it.
The consumed debugger allowances remain consumed; no new trace is included.

The only runtime behavior change is replacing CREATE_NO_WINDOW with
DETACHED_PROCESS. The named LaunchCreationFlags constant is 0x0008040c; the old
value was 0x08080404. Extended startup information, Unicode environment and
suspended creation remain set. This console choice is not job breakaway and
does not add a permission. Native compatibility remains unproven.

Version/provenance become 0.1.0-startup.6 / file version 0.1.0.6. Explicit pipe
handles, STARTF_USESTDHANDLES, Python payload/arguments, environment/cwd, reduced
token, all child admission predicates, LPAC/zero capabilities, atomic job limits,
child-process policy, six WFP denies, grants/labels, 30-second wait, beacons,
consent, reporting, cleanup/recovery and fail-closed behavior remain unchanged.
The initial-journal recovery gap is not fixed or hidden.

The existing inert fixture gains flag-mask assertions and a package-6-only
extraction destination; it is not shipped. Python source-wiring checks bind the
new constant to the actual native call and preserve pipe/job/admission ordering.
There is no new supervisor, test script, debugger, pythonw payload or installer.
Only local compilation, inert checks, payload extraction and offline packaging
are included. Separate VM-run approval and product consent remain necessary.

## Package 6 Build Receipt

Output: `.codex-build/maya-protected-python-startup-20261021-6/`.
`Maya-Protected-Python-Startup-6.zip` is **14,676,996 bytes**, with 12 handoff files.

- Version: `0.1.0-startup.6`; file version `0.1.0.6`; x64 GUI executable,
  **14,854,144 bytes**.
- ZIP SHA256: `3670183913c296a8e739d8f0242a2b74b0ea08440ef25678e63a7f4208b9fea4`
- EXE SHA256: `a878ed4c4e9518a0da402e67ca19c193ac4f7e8dff2299d4b69c73072d7601e6`
- Both product and inert-fixture compilations passed with the existing x64 .NET
  Framework compiler, optimization and warnings-as-errors. **215 inert C# checks**
  and **12 Python unit/static checks** pass. No fixture binary is shipped.
- The inert fixture extracted and verified all **805 payload files** without
  security provisioning or Python execution. Independent size/hash readback
  matches every extracted file to the frozen index. Payload ZIP SHA256 remains
  `09f1a84b211a1c40e4c18d34201f8f5242321bcccadf6c58100043b43a04a4ed`;
  index SHA256 remains
  `e2e71b5e3e375c85e7ea37a62cd19022697fccf84180b503fdadba8e19ed8575`.
- File-byte PE/CLI metadata/resource parsing verifies both exact named payload
  resources in the final product EXE, without loading or executing that assembly.
- Exact normalized source comparison against frozen Package 5 proves the only
  product edits are the named creation-flags constant/call use and three version
  strings. ProductFiles.cs, startup_check.py and ProtectedPython.manifest remain
  byte-identical. The dedicated source-before tree matches all seven Package 5
  source/test hashes. Frozen Package 5 EXE/ZIP digests are unchanged.
- Every final ZIP entry matches its handoff file; source and artifact inventory
  hashes verify. Notices are unchanged. The ZIP contains no source-before files,
  fixture, supervisor, debugger or new script. Its sibling `SHA256SUMS.txt` binds
  ZIP and EXE; digests stay outside the archived guide to avoid self-reference.
- Context guard and whitespace checks pass. Compiler/launch-contract metadata,
  exact source hashes and preparation-only authority are in package-manifest.json.
  No UAC, native error-mode, profile/ACL/WFP, token construction, process creation,
  product GUI or embedded-Python execution occurred during preparation. Only the
  inert fixture's managed assertions and dedicated local payload extraction ran.

The archive is ready for handoff, **not execution-approved**. The earlier
Maya/debugger session still requires normal closure confirmation before a later
separately approved ordinary RDP run with product consent. Package 6 has no native
startup result; the original cause, containment, Gate A and production remain
unqualified. No further fix or retry is authorized by this preparation receipt.

## Package 6 Operator Result (Received 2026-10-21)

After preparation, the operator explicitly reported the prior debugger and Maya
launcher closed, supplied the extracted Package 6 path on the VM and returned
the exact expected EXE SHA256. The user then explicitly approved one normal RDP
run using product consent, unchanged permissions/cleanup and the 30-second limit,
without a debugger or automatic retry. That single-run allowance is now consumed.
Closure of the older session is resolved at operator-report level, not by a new
debugger exit transcript or independent security-resource verification.

The returned JSON matches version 0.1.0-startup.6 and launcher SHA256
`a878ed4c4e9518a0da402e67ca19c193ac4f7e8dff2299d4b69c73072d7601e6`.
The report's UTC timestamps are 2026-10-20T20:21:58.9078970Z through
2026-10-20T20:22:12.5652238Z; private account, profile, attempt and process IDs
are omitted from this tracked record.

- Windows build 26300.9711, elevated host and informed product consent reported.
- Payload, reduced launch token, restricted child token and six network filters
  verified; child resumed.
- `status=startup_failed`, `startup_status=startup_failed`, `python_started=false`.
- Natural exit observed before cleanup: **0xC0000022**, not the earlier
  Package 5 exit 0xC0000142 and not a forced-stop exit or timeout.
- Complete output capture, stdout/stderr byte counts both zero, no stdout match
  and no fresh state beacon.
- `cleanup_complete=true` is product/operator-reported. Containment and
  production qualification remain false; no independent cleanup proof is supplied.

Microsoft's [NTSTATUS reference](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55)
names 0xC0000022 STATUS_ACCESS_DENIED. This report contains no failing operation,
denied object, access right, call stack or DLL-mapping evidence for Package 6.
The changed exit code does not establish that ConsoleInitialize succeeded, that
execution advanced beyond the Package 5 failure, or that this has the same
SideBySide/registry cause as historical 25H2 experiments. It is not permission to
grant registryRead/lpacCom, change ACLs, token checks, console settings or account.

The detached-mode candidate did not meet its Python-startup acceptance criteria.
Retain the unchanged Package 6 source, artifact/build manifest and this failed
result. Do not relabel the frozen preparation manifest as a run receipt or
rebuild the archive to add the result. No product correction or security change
was made while analyzing this report.

Stop ordinary VM testing and the diagnostic chain here. If the current Maya
window remains open, the existing authorized normal-close step can follow its
reported complete cleanup; do not relaunch, force-kill or perform manual cleanup.
Recommend a strategic reassessment of the isolation implementation before more
startup iterations, not abandonment of Maya or a claim that LPAC cannot work.
No alternative implementation, resource provisioning, Package 7, grant, trace
or retry is authorized by this recommendation. Gate A and production stay blocked.

## Package 7 Approved AppContainer Comparison (2026-10-21)

After researching alternatives and rejecting VM/Docker product prerequisites,
the user explicitly approved one ordinary-AppContainer plus unchanged WFP
comparison and asked to prepare and try the package. The Azure VM remains a
test machine, not a product dependency. This is a bounded comparison, not an
adopted production isolation architecture or automatic retry sequence.

The runtime delta from Package 6 is removal of the All Application Packages
opt-out process attribute; attribute allocation/count becomes four instead of
five. Before resume, the synthetic AAP AccessCheck must now allow, while the
package grant must allow and no-grant/wrong-package controls must still deny.
An LPAC token or any other unexpected control result is rejected. This is an
intentional changed predicate for the selected mode, not deletion of admission.

Version becomes 0.1.0-startup.7 / 0.1.0.7. Product consent explicitly discloses
ordinary AppContainer's broader implicit resource access and reports include
isolation_mode=appcontainer-wfp. WFP does not compensate for broader file,
registry or local-IPC access. No customer-data containment claim follows.

Keep the same embedded payload/index bytes, -I -S -B, clean environment/cwd,
three pipes, DETACHED_PROCESS flags, reduced same-user token, scalar/identity/
integrity/admin checks, zero capabilities, six WFP denies and readbacks,
filesystem/label scope, atomic one-process job, child policy, error mode,
30-second wait, beacons and stop/cleanup/recovery. No new registry grant,
loopback exemption, capability, debugger, supervisor or external model call.
The initial-journal recovery gap remains open. Earlier artifacts stay frozen.

Preparation permits local compilation and inert tests/extraction only. The
single normal RDP startup attempt is approved, conditional on exact new artifact
hashes, confirmation the earlier Maya/debugger windows are normally closed and
cleanup was reported complete, and fresh informed product consent. Pending old
cleanup requires review; do not use Package 7 to recover another version's record.
Stop on AV/SmartScreen blocks or after the first result; no bypass, forced close,
manual security preparation, diagnostic or second run is approved. No local
native launcher/Python/security execution is authorized. Startup success alone
does not qualify Hermes, containment, Gate A, Metabase or production.

## Package 7 Build Receipt

Prepared separately in `.codex-build/maya-protected-python-startup-20261021-7/`.
The handoff ZIP contains 12 files, without an observer, debugger, fixture or new
script. The existing x64 Framework compiler hash matches Package 6. Compilation
with warnings-as-errors passes; **231 inert C# checks** and **13 Python unit/static
checks** pass. The context validator and whitespace checks pass.

- ZIP: `Maya-Protected-Python-Startup-7.zip`, **14,677,120 bytes**.
  SHA256: `c54dde7d91d45246647dec6c3e33c967c2f5d142e745452db62378d24158e80c`.
- EXE: `MayaProtectedPython.exe`, **14,854,656 bytes**, x64 GUI PE.
  SHA256: `167854f54de205b34f644080c8d34619c31ca0ad0820ca893a1bd980fddac81b`.
- All 805 files are independently size/hash-verified after inert extraction.
  Payload ZIP/index remain byte-identical to Package 6, with the same historical
  hashes. File-byte inspection verifies exact length-prefixed payload/index bytes
  inside the product EXE without loading its assembly. All 12 ZIP entries and all
  manifest file digests verify. Notices are copied unchanged.
- All seven source-before hashes match Package 6's frozen manifest. ProductFiles.cs,
  startup_check.py and ProtectedPython.manifest remain unchanged. Package 6 EXE
  and ZIP hashes still match their receipt. Neither artifact is overwritten.
- The 16 synthetic access-predicate combinations accept only package-positive,
  AAP-positive, no-grant-negative and wrong-package-negative. This tests decision
  wiring, not native AppContainer access. Existing scalar/reduced-token, flag,
  error-mode, beacon and failure-report regressions pass.
- Product consent names ordinary AppContainer and its broader implicit access;
  the report mode is appcontainer-wfp. Existing journal-less recovery limitations
  remain disclosed. No product entrypoint, UAC/profile/ACL/WFP setup, native token
  construction/AccessCheck, restricted-child launch or embedded Python ran locally.

The native attempt is still unperformed/unreported. The user's one-run approval
remains subject to exact guest hash, prior-session closure/cleanup confirmation
and fresh product consent. A failure stops for review, not another correction.

## Package 7 Operator Result (2026-10-21)

The operator supplied a result with version 0.1.0-startup.7, isolation_mode
appcontainer-wfp and the exact EXE SHA256 in the build receipt above. The reported
UTC interval is 2026-10-21T14:38:58.2603616Z to 14:39:13.9707063Z. Private user,
profile, attempt and process identifiers are deliberately not copied here.

- Windows 11 Pro baseline build 26300.9711, elevated setup host and informed consent.
- Payload verified, six WFP filters read back, reduced launch token and child
  restriction checks passed, then the Python child resumed.
- Natural pre-cleanup child exit 0x00000000; output capture complete.
- Stdout 66 bytes, exact fresh attempt-bound stdout beacon; stderr zero bytes.
- Fresh state beacon matched and python_started=true.
- Status/startup_status: startup_completed_not_containment_qualified.
- cleanup_complete=true is product/operator-reported; no independent cleanup
  evidence, security bypass probes or broker/connector/model tests were supplied.

This is the first successful reported bundled-Python startup under the bounded
ordinary-AppContainer/WFP profile. The unchanged Package 6 payload failed under
LPAC; the controlled source delta supports the practical compatibility benefit
of ordinary AppContainer on this baseline. It does not identify the denied LPAC
resource or prove LPAC cannot work. The full attempt interval includes setup and
cleanup, not an isolated Python launch-performance measurement.

The single native attempt allowance is consumed. Preserve the frozen Package 7
manifest/archive and all earlier failure evidence; do not rebuild them to add
this result. No new source or security change was made while recording it.
If the result window remains open, close normally after reported cleanup; no
relaunch, manual cleanup, diagnostic or second attempt follows. Before further
native work, review ordinary AppContainer's ambient file/registry/IPC exposure
and plan effect-level containment qualification. Hermes, gateway model traffic,
connectors, Metabase, Gate A and production remain unqualified/unapproved.

## Subsequent Screen 8 Preparation (2026-10-21)

After the user approved the containment recommendation and subsequent
continuation, a separate product-owned synthetic Screen 8 candidate is prepared.
Its exact contract, impact, limitations, test receipt and artifact hashes are in
`maya_protected_python_containment_screen.md`; the operator handoff is
`maya_protected_python_screen_handoff.md`. Version is 0.1.0-screen.8, scope is
synthetic-containment-screen-v1, not another Package 7 startup attempt.

The candidate preserves Package 7's protections and 805 payload files, adds one
fixed probe and freezes 47 child observations plus product cleanup. Preparation
passes 231 existing and 44 new inert C# checks, 23 Python checks, and independent
806-file payload verification. New native lifecycle behavior is unproven. No
product or payload ran locally, and no VM action occurred. Separate exact-artifact
and impact review/run approval remains required. No first-screen result alone
can establish containment, independent cleanup, Hermes compatibility or Gate A.

## Screen 8 Setup Failure And Screen 9 Preparation

The operator subsequently supplied a matching-hash Screen 8 report: payload
verified, NotSupportedException during setup, no child resume, blocked and cleanup
reported complete. It contains no native containment-probe result or independent
cleanup verification. The generic error does not prove the failing VM line.

The user approved the bounded fixed-ADS Windows-file-API correction, precise stage
reporting, inert checks and separate Screen 9 preparation. The successor is
0.1.0-screen.9; its correction scope, exact hashes and build receipt are in
`maya_protected_python_containment_screen.md`. It passes 231 existing C# checks,
65 screen/evidence/stream checks and 25 Python checks. All 806 payload files and
the 48-case inventory remain unchanged. No native execution occurred. Preserve
Screen 8 and stop for separate artifact/impact review and native-run approval.

## Screen 9 Observations And Screen 10 Preparation

The operator subsequently reported matching-hash Screen 9 startup, natural exit
zero and all 47 child observations, with no host-observed unauthorized effect
and cleanup reported complete. The aggregate diagnostic failed its own-token
query with error 24; four UDP rows and spawn error 367 remained inconclusive.
Preserve that report and its frozen classification; it is not containment or
independent-cleanup qualification.

The user approved bounded Screen 10 preparation: exact scalar token-query sizing,
bounded capability-size negotiation, admission of 367 only for C06.spawn and
retaining UDP as inconclusive. The separate 0.1.0-screen.10 artifact/impact receipt
is in `maya_protected_python_containment_screen.md`. It passes 231 existing and
118 screen/evidence C# checks, 32 Python checks and independent verification of
806 payload files. Only the fixed probe changes in the payload; 48 case IDs and
all permissions/enforcement/budgets remain fixed. No native execution occurred.
An aggregate pass is not expected while UDP evidence remains unresolved. No
run, UDP redesign, additional correction or qualification is approved here.

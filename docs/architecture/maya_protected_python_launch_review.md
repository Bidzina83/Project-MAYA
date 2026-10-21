# Package 5 Windows Launch Review

This is the historical pre-localization review. The user's separately approved
2026-10-21 [focused console-launch review](maya_protected_python_console_launch_review.md)
uses the later observed ConsoleInitialize failure and recommends a bounded,
unimplemented compatibility candidate. Preserve this earlier assessment as
evidence, not instructions to repeat its diagnostic sequence.

## Scope And Decision

2026-10-20: the operator confirmed normal Maya/debugger closure, then approved a
source review against the captured KERNELBASE.dll initialization failure.
This is review and documentation only. No product correction, new package,
security provisioning, native launch or further VM diagnostic is approved here.

**Conclusion:** no confirmed source defect explains the captured 0xC0000142.
The evidence identifies the failing Windows initializer, not its failed internal
operation. There is no evidence-backed Package 6 startup correction yet.
The next useful decision is whether to authorize preparation of a narrowly
targeted initializer-level diagnostic using the existing Microsoft debugger.
Preparation and execution would remain separate decisions, not an automatic retry.

The user subsequently approved preparation of the
[targeted initializer diagnostic](maya_protected_python_initializer_diagnostic.md).
That staged proposal is now present; exact guest symbols/disassembly and capture
commands remain pending. No setup, download or native execution follows preparation.

## Reviewed Inputs

Subsequent evidence: the one separately approved
[initializer observation](maya_protected_python_initializer_diagnostic.md#captured-outcome-2026-10-20)
records base-helper return zero before ARI. Unexpected child heap-tail checking
and missing full image-path readback prevent the intended diagnostic-profile
qualification. This narrows an instrumented path, not its underlying cause or
a source correction. Both targets exited; no retry or deeper inspection follows.

- Product-owned Windows runtime source, application manifest and startup check.
- Existing C# inert fixtures and Python unit checks.
- Package 5 package-manifest.json and the frozen executable, SHA256
  `6709bb7673c1eca2fecec006cf2c72dd7b3059278c3e7a92d59034c6bac92b66`.
- The [matched VM capture and report](maya_protected_python_loader_capture_v2.md#captured-outcome-2026-10-20).
- The historical pinned Microsoft reference source, read without executing it.
  Its different token, console, handles and lifecycle are confounders, not a
  supported substitute or an approved comparison run.

All seven source/test hashes in the Package 5 manifest and the executable hash
match the current reviewed files. No source mismatch explains this VM result.

## Launch Contract Readback

References below are repository-relative source locations for this review.

| Area | Source | Assessment |
| --- | --- | --- |
| Native layouts | WindowsIsolation.cs:128-151; fixtures:307-310 | x64 Startup 104 bytes, StartupEx 112, Capabilities 24, JobLimits 144; existing inert size checks are present. No layout mismatch identified. |
| Base token | WindowsIsolation.cs:394-505 | Same-user reduced primary token, medium integrity, same session, deny-only Administrators and bounded privileges verified before use. This is not proof of Windows bootstrap compatibility. |
| LPAC attributes | WindowsIsolation.cs:347-357 | Five attributes: package security capabilities with zero extra capabilities, AllApplicationPackages opt-out, no child process creation, job list and handle list. No ordinary fallback found. |
| Creation flags | WindowsIsolation.cs:377-378 | 0x08080404 is CREATE_NO_WINDOW, EXTENDED_STARTUPINFO_PRESENT, CREATE_UNICODE_ENVIRONMENT and CREATE_SUSPENDED. No contradictory console/detached flag identified. |
| Standard handles | WindowsIsolation.cs:358-366, 373-374 | Three real inheritable pipe ends in the handle list; parent-only ends made non-inheritable. STARTF_USESTDHANDLES and inherit=true agree with that design. |
| Environment | WindowsIsolation.cs:367-372 | Eight names sorted case-insensitively, double-NUL Unicode block, explicit SystemRoot/WINDIR, private state paths and bounded PATH. No inherited host environment or malformed termination identified. |
| Image and cwd | WindowsIsolation.cs:367-378 | Absolute application path, quoted command path and private-state cwd. Trace confirms the intended child image/cwd. This does not prove every later file read is permitted. |
| Admission and deadline | WindowsIsolation.cs:379, 559-613 | Child-token checks precede resume; native exit is read after the unchanged 30-second wait. Report and trace agree on natural exit, not forced cleanup or timeout. |

The documented [LPAC attribute construction](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer)
matches the package identity/opt-out pattern. The
[handle-list contract](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute)
requires inheritable listed handles and inherit=true. The
[environment contract](https://learn.microsoft.com/en-us/windows/win32/procthread/changing-environment-variables)
requires sorted names. These source checks are not native compatibility proof.

## Unresolved Leads, Not Confirmed Causes

### Window Station And Desktop Access

STARTUPINFO.desktop remains null in WindowsIsolation.cs:373-374; there is no
product-owned desktop selection/access validation. The
[CreateProcessAsUser contract](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessasuserw)
describes desktop/window-station access prerequisites and deferred DLL initialization.
[CREATE_NO_WINDOW](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags)
controls console creation, not a desktop-access grant. The
[restricted-token warning](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-createrestrictedtoken)
also requires desktop isolation to be considered for protection.

However, the capture shows neither a denied desktop operation nor a USER32/GDI32
load. Windows documents window-station connection on
[first USER32/GDI32 use](https://learn.microsoft.com/en-us/windows/win32/winstation/process-connection-to-a-window-station).
Null desktop alone is not an invalid argument or proof of this failure. Do not
promote this unresolved compatibility/protection concern to the root cause,
select winsta0/default, grant desktop access or create a private desktop as a
speculative fix. The existing package contract already leaves this area unqualified.

### LPAC Bootstrap Resource Access

The child has zero extra capabilities. Microsoft's LPAC documentation explains
that ordinary AppContainer resource access, including registry and COM access,
is not automatically available to LPAC. This makes startup-resource access a
plausible lead, not an identified denied resource in this capture.

KERNELBASE.dll was mapped successfully; its initializer can still fail later.
API-set redirection names do not prove registry/COM calls occurred. Earlier
25H2 SideBySide evidence cannot identify this 26H2 initializer's internal failure.
Do not add registryRead, lpacCom, broad ACL grants or an ordinary-mode comparison
on this inference.

### Token And Launch Context

The scalar/AccessCheck admission controls show the intended restriction predicates,
not every Windows bootstrap prerequisite. Logon identity details, default object
security and internal subsystem interactions are not explained by the JSON.
The source does not prove a defective token, nor justify removing reduction or
admitting an elevated child. The reference launcher does not supply Maya's reduced
base token and is not a one-variable control for this issue.

## Recommended Next Evidence

Before selecting a product correction, identify the operation/status that makes
the matched KERNELBASE.dll initializer fail. Any proposed bounded follow-up should
target that already identified initializer, preserve the product and protections,
disclose debugger timing interference and any additional matching-symbol need,
and stop after its fixed allowance. No new supervisor or test application is
needed or authorized. No follow-up commands, symbol downloads or native attempt
are performed by this review.

Replacing Windows DLLs, changing Python health-check code, increasing the deadline
or relaxing security would not be an evidence-backed response to this capture.
Keep the separate missing-initial-journal recovery finding open; it did not cause
this recorded child initialization failure and is not corrected by this review.

## Verification And Limits

All 11 current Python unit/static-wiring checks pass. No C# native fixture, token,
process, debugger or security API was executed for this review. Existing size
fixtures and earlier inert receipts were inspected, not rerun as native evidence.
Context validation and whitespace checks pass. Source review cannot identify the
unobserved internal Windows failure or qualify startup, cleanup, containment,
Hermes, Gate A or production activation.

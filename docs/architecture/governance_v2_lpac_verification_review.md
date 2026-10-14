# Gate A LPAC Verification - Bounded Decision

## Status

The user approved this bounded correction on 2026-10-14. Implementation and
paired suspended-token controls passed on the observed Windows host. The resumed
Python child subsequently returned STATUS_ACCESS_DENIED without a worker frame;
Step 3 remains blocked. Step 3 previously stopped before native execution;
see [the progress record](governance_v2_gate_a_step3_progress.md). Preserve the
failed direct-query evidence. Gate A and production remain unqualified.

## Finding

The prototype assumed GetTokenInformation class 46 supplied a usable DWORD LPAC
status through Win32. On the observed host, it returns error 87. Correcting the
startup opt-out attribute to SDK value 131087 (0x2000F) did not change that result.
The suspended child is an AppContainer; its LPAC authorization behavior has not
been demonstrated. No child thread was resumed and no Hermes request ran.

Microsoft defines LPAC by its exclusion from ALL_APPLICATION_PACKAGES access, but
the Win32 enumeration's class-46 description does not give the same explicit
buffer/query contract as TokenIsAppContainer. Do not convert an error into an
affirmative LPAC determination or assert all builds lack support.
[Enumeration](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ne-winnt-token_information_class),
[SDK attribute](https://microsoft.github.io/windows-docs-rs/doc/windows/Win32/System/Threading/constant.PROC_THREAD_ATTRIBUTE_ALL_APPLICATION_PACKAGES_POLICY.html).

## Approved Correction Within Step 3

Replace the assumed direct-status query gate in host and worker with a bounded
authorization-behavior check. Keep documented AppContainer/SID/low-integrity checks
and the exact LPAC creation attribute. Use DuplicateToken plus AccessCheck against
synthetic security descriptors, not protected customer files or new policy writes.

Before resuming any business worker, require successful API calls showing:

1. Explicit package-SID resource access is allowed for the selected token.
2. Access granted solely through ALL_APPLICATION_PACKAGES is denied.
3. A separate ordinary-AppContainer negative control permits that same AAP-only
   access. It is created suspended for token comparison and terminated; it never
   runs Hermes or becomes an execution fallback.
4. Wrong-package and no-grant descriptors deny, while descriptor construction,
   access masks, token duplication and cleanup errors block startup.

DuplicateToken and AccessCheck are documented primitives; this composition must
be qualified, not advertised as a Microsoft purpose-built IsLPAC API.
[DuplicateToken](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-duplicatetoken),
[AccessCheck](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-accesscheck).

If this comparison cannot reliably distinguish authorization behavior, stop for
a strategic decision. Do not repeatedly substitute additional status probes or
grant broader capabilities. A passing check would permit resuming Step 3, not
satisfy A01-A20, the full bypass matrix or platform qualification.

Approval is limited to this verification-method correction and its
positive/negative controls. Network/file capability ceilings and model/runtime
pin remain unchanged. Security reprovisioning still requires its own permission.
The approved evaluation envelope is not expanded; this is not another WP sequence.

## Observed Correction Results (2026-10-14)

The native helper completed `verify-tokens` with exit code zero:

- Selected LPAC: explicit package grant allowed, AAP-only grant denied.
- Ordinary AppContainer control: AAP-only grant allowed. It was never resumed.
- Both tokens: same intended package/user, low integrity, wrong-package and
  no-grant denial. Both suspended processes were terminated before reporting.
- API success and authorization status are checked separately. Nine portable
  fault-injection tests check the worker guard, including API/cleanup failures;
  these mocked tests are not native LPAC evidence.

The first paired-control attempt exposed an implementation error: updating an
already-added startup attribute returned error 31. The ordinary control now has
its own initialized attribute list without the LPAC opt-out. This is a correction
to the approved control implementation, not a fallback or new permission.
Attribute storage persists until list deletion as documented by
[UpdateProcThreadAttribute](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute).

Qualified inputs for this bounded token comparison:

| Input | SHA256 |
| --- | --- |
| Native helper source | `b4d235ec86b6c37216ed803bdef28e8cf35acd82279a8ac2a6c980d1015aa992` |
| Compiled x64 helper | `e72f101bea8222d14e908c2f39e7fecdca122b2f13b2abe9d5293490b7856f63` |
| Worker source | `5c95be2a0d53e203804e34e8d120e2151312fdc97fb4e61e56ce62361169e118` |
| Staged runtime manifest | `0ed977a4f7269ec86d01468e19820d616fc4e74cacd21b2919131d88457a5b32` |

The same helper then resumed only the checked LPAC child for the synthetic native
slice. It exited with 3221225506 (`0xC0000022`, STATUS_ACCESS_DENIED), with an empty
stdout frame. Microsoft defines that code as access denied, not identification of
the denied resource. The runner now reports a fixed missing-protocol error and
numeric child status rather than an unhandled JSON parse exception.
[NTSTATUS values](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55).

Only starter config exists in the isolated Hermes state; no native session or
MEMORY.md/USER.md output and no host broker audit file were created. No successful
Hermes import, loop, broker service effect or native memory operation is claimed.
Read-only ACL inspection confirms the selected package SID inherits RX on the
staged python.exe. It does not establish startup dependency access or the exact
failure root. No system-directory access, capability widening, ordinary execution
fallback or Hermes change was attempted.

Stop here for review of the new startup failure. Recommend locating the exact
denied Windows startup resource before considering another correction; do not
automatically extend the evaluation budget. Token behavior success is not A01-A20,
effect-level WFP containment, Gate A acceptance or Windows production qualification.

Validation: 51 broker/preflight/token-guard/Local API tests passed outside the Codex
sandbox. The earlier sandbox-only run had temporary-directory permission errors;
those are retained as environment failures, not interpreted as guard denials.

Test security cleanup completed after the startup stop: removed the profile,
eight filters/sublayer, loopback exemption and runtime/state SID grants. Native
read-back returns FWP_E_FILTER_NOT_FOUND (2150760451); the exemption listing has
no target SID, and executable ACL read-back no longer contains that SID. Private
state was restored to medium integrity. Prepared artifacts remain ignored; no
installed product, default Hermes home or general firewall policy was changed.
Context validation, Python compilation and `git diff --check` pass. Git reports
the existing LF-to-CRLF checkout warnings; no global line-ending setting changed.

## Startup-Denial Diagnosis (2026-10-14)

The user requested diagnosis, not another permission correction. Reproduced with
the unchanged helper and runtime, separately permitted reprovisioning, an inert
admission token, no broker/listener and no provider/customer credentials. No
capability, registry ACL, executable flag or Hermes source was changed.

Downloaded Microsoft Process Monitor into ignored diagnostics with separate
permission; Authenticode is Valid, signer Microsoft Corporation, binary SHA256
`fc3af5317c707e0555ad6e7590ad65ceb5c5085b053b41221944ac3ca3492d9c`.
EULA acceptance/privileged capture was separately permitted. The first 30-second
capture ended before child launch (zero python.exe rows); it is not denial evidence.
A synchronized 20-second capture included the selected child. No unrelated trace
rows are included in this diagnosis; raw local traces must not be committed/shared.
[Microsoft startup tracing guidance](https://learn.microsoft.com/en-us/troubleshoot/windows-client/shell-experience/troubleshoot-apps-start-failure-use-process-monitor).

Observed selected LPAC child PID 26192; ordinary suspended control PID 21868 was
terminated with exit zero without resume. Parent helper PID 23300. Selected-child
events, local time 20:05:51:

| Time | Operation/resource | Result |
| --- | --- | --- |
| .7272881 | Process Start, staged python.exe -I -S worker.py | SUCCESS |
| .8866057 | HKLM System/CurrentControlSet/Control/Nls/CodePage, read | ACCESS DENIED |
| .8870753 | HKLM System/CurrentControlSet/Control/Session Manager, query | ACCESS DENIED |
| .8874157 | HKLM SOFTWARE/Microsoft/Windows NT/CurrentVersion/Image File Execution Options, query/enumerate | ACCESS DENIED |
| .9076632 | HKLM SOFTWARE/Policies/Microsoft/Windows/safer/codeidentifiers, query | ACCESS DENIED |
| .9081705 | HKLM System/CurrentControlSet/Control/FileSystem, read | ACCESS DENIED |
| .9165637 | Staged python313.dll, Load Image | SUCCESS |
| .9168197-.9176292 | HKCU maximum-allowed open, four attempts | ACCESS DENIED |
| .9180100 | HKLM SOFTWARE/Microsoft/Windows/CurrentVersion/SideBySide, read | ACCESS DENIED |
| .9213464 | Process Exit | 0xC0000022 |

### Root And Confidence

Confirmed: the selected process reaches Windows initialization with its staged
Python DLL mapped, but cannot read several OS registry resources. The final denied
read is the SideBySide key, immediately followed by DLL close, thread teardown and
access-denied process exit. This localizes the failure to the Windows startup
permission model, not a broker/provider failure or demonstrated Hermes failure.
The worker protocol never begins. Earlier registry denials are not individually
proved fatal merely because they appear in the trace.

Read-only inspection of the SideBySide key's protected DACL found ReadKey grants
to ALL_APPLICATION_PACKAGES and the named `registryRead` capability SID:
`S-1-15-3-1024-1065365936-1281604716-3511738428-1654721687-432734479-3232135806-4053264122-3456934681`.
There is no selected-package or ALL_RESTRICTED_APPLICATION_PACKAGES grant on that
key. The unchanged launcher supplies only privateNetworkClientServer, not
registryRead. Its verified LPAC token intentionally cannot rely on the AAP grant.
The launcher design allowed staged files but omitted necessary OS-registry reads.

Microsoft's own LPAC launcher documents explicitly supplying capabilities and
uses registryRead for its cmd.exe example. That is evidence this is a recognized
LPAC compatibility requirement, not proof that the same capability alone will
make Python/Hermes operational or preserve Maya's full protection contract.
[Microsoft launcher](https://github.com/microsoft/SandboxSecurityTools/blob/main/LaunchAppContainer/README.md),
[Microsoft test profile](https://github.com/microsoft/SandboxSecurityTools/blob/main/LaunchAppContainer/LaunchSandboxMSRC.bat).

Strong terminal-blocker evidence identifies SideBySide read denial. A controlled
permission comparison has NOT run; sufficiency and any later startup blockers
remain unproven. No broad registryRead/lpacCom grant is implied by the diagnosis.

### Decision Required, Not An Applied Fix

Recommend reviewing one reversible, package-SID-only, non-inheriting ReadKey grant
on the exact SideBySide key as the narrowest compatibility experiment, rather
than automatically enabling a capability recognized by many registry ACLs.
This still modifies an OS registry DACL and requires explicit impact approval,
exact prior-descriptor capture, controlled comparison and cleanup verification.
Other denied keys/HKCU are not automatically included. A passing comparison would
justify only the observed startup correction, not full-loop or A01-A20 acceptance.

Any additional correction needs an explicit decision about the already-used
one-correction budget. Do not implement another fix, expand the sequence, grant
HKCU/HKLM-wide reads, change pin or fall back to ordinary AppContainer automatically.

### Evidence Retention

Raw evidence remains in ignored `.codex-build/gate-a-startup-diagnostics`:

| Evidence | SHA256 |
| --- | --- |
| startup-synchronized.pml | `b640e7c6c85dc6ee2d726a14995596b27cf021cad17869dce429cc071a4e2ee8` |
| startup-synchronized.csv | `9876eb53ae198ca54224a6993ba8e8a712da8a0398f6e276c3e65e84b714ae74` |

Helper source/binary hashes still match the earlier correction table. Diagnostic
process/driver counts are both zero after capture/export. Security-resource
cleanup completed: filter read-back reports FWP_E_FILTER_NOT_FOUND, target
exemption count is zero, and the executable ACL no longer grants the test SID.
The SideBySide DACL exactly matches the read-only pre-cleanup observation.
No security fallback or OS-registry permission change was made. Gate A remains open;
no installer, runtime pin, model route or production-qualification change follows.

## Approved Exact-Key Comparison (2026-10-14)

The user approved the preceding recommendation and its explicit additional
correction-budget exception. Authorization is limited to one reversible,
non-inheriting package-SID ReadKey grant on the 64-bit SideBySide key. No other
registry key, broad capability, Hermes patch or production activation is approved.

`scripts/measure_governance_v2_sidebyside.ps1` implements only that host-side
experiment. It binds the unchanged helper hash and its derived profile SID,
captures owner/group/DACL in durable original SDDL/binary form before mutation,
requires explicit consent, read-backs the expected grant, detects unexpected
descriptor drift, and verifies original SDDL and bytes on restoration. The SACL
is never read or written. No registry values are written. Snapshot and outcomes
remain in ignored test-host state, not an installer or product setup path.

### Implementation Failures Preserved

The first .NET write attempt opened its administrative handle in read-only mode;
the descriptor remained unchanged. Microsoft documents that permission-check
mode takes precedence over the rights mask. The host mode was corrected while
retaining only ReadKey/ChangePermissions in its OS handle rights; the LPAC grant
remained ReadKey only.
[OpenSubKey](https://learn.microsoft.com/en-us/dotnet/api/microsoft.win32.registrykey.opensubkey?view=netframework-4.8.1).

The .NET SetAccessControl attempt then added the expected ACE but also set the
SE_DACL_AUTO_INHERITED control bit. Strict read-back blocked child testing of that
descriptor. The original owner/group/DACL was restored and verified byte-for-byte
using RegSetKeySecurity. The final script uses that registry-specific DACL-only
API for both grant and restore; the original rollback snapshot was not replaced.
Rollback recognizes only the exact known ACE addition, optionally with that one
observed control bit, not arbitrary administrator/policy drift.
[Automatic-inheritance behavior](https://learn.microsoft.com/en-us/windows/win32/secauthz/automatic-propagation-of-inheritable-aces),
[RegSetKeySecurity](https://learn.microsoft.com/en-us/windows/win32/api/winreg/nf-winreg-regsetkeysecurity).

Read-only descendant inspection found 35,078 keys and zero occurrences of the test
SID in their DACLs. This confirms no descendant test-principal grant, not a claim
that every descendant descriptor byte was captured before the initial .NET write.
Preserved failure reports: `sidebyside-first-grant-failure.json` and
`sidebyside-auto-inheritance-failure.json` in the ignored host directory.

### Controlled Result

All selected-child executions use the unchanged launcher, LPAC token controls,
WFP policy, managed runtime and inert diagnostic admission. No broker, provider,
live credential, customer data or ordinary-process fallback is involved.

| State | Selected child exit | Worker frame |
| --- | --- | --- |
| Original registry descriptor | 3221225506 / 0xC0000022 | Empty |
| Exact non-inheriting ReadKey grant, verified | 3222601730 / 0xC0150002 | Empty |
| Original descriptor restored and verified | 3221225506 / 0xC0000022 | Empty |

An early attempted before-control was blocked by missing filters while provisioning
was still pending; it is not startup evidence. The table's original-state result
was observed after provisioning, before the successful exact grant, and the final
reversal confirms it on the same enforcement profile.

The verified grant changes the original failure reproducibly. It does not make
the Python worker operational. Microsoft identifies 0xC0150002 as
STATUS_SXS_CANT_GEN_ACTCTX, failure to process application binding information.
The follow-up Application/SideBySide query returned no matching staged-runtime
events; the exact remaining manifest/assembly/resource cause is not localized.
Do not assume missing assemblies, corruption or a required subkey grant solely
from that status.
[NTSTATUS reference](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55).

Conclusion: exact-key access was an effective correction of the observed access
denial, but was insufficient for startup. Neither native Hermes construction nor
loop, memory, service/network containment or A01-A20 acceptance is demonstrated.
No broad registryRead/lpacCom capability or subkey grant was attempted. Stop at
the new activation-context blocker; another correction is not automatically
authorized. Before proposing more permissions, assess the complete Windows
startup dependency/access requirement rather than continuing a key-by-key grant
sequence. This recommendation is not authorization for another evaluation batch.

### Final Cleanup And Validation

The original owner/group/DACL SDDL and binary descriptor both match the durable
snapshot after restoration, including the original control flags. Only DACL was
written; SACL was untouched. The isolated profile, eight filters/sublayer,
loopback exemption and staged-directory SID grants were removed. Native read-back
returns FWP_E_FILTER_NOT_FOUND; exemption count is zero and executable SID grant
is absent. No installed product/default Hermes home was touched.

| Retained input | SHA256 |
| --- | --- |
| Final test-only PowerShell script | `ffb0e3ab7420589f4a3ee59628a0805d5a69a7654bc011c8e1e8ce3fd1f6686a` |
| Original-descriptor snapshot (ignored host state) | `35d82006f1b33486622271e1f83d7e95a9772d0ea7cc021b673ada20d100a6d6` |
| Unchanged helper binary | `e72f101bea8222d14e908c2f39e7fecdca122b2f13b2abe9d5293490b7856f63` |
| Unchanged staged runtime manifest | `0ed977a4f7269ec86d01468e19820d616fc4e74cacd21b2919131d88457a5b32` |

All 51 broker/preflight/token-guard/Local API regressions pass; final PowerShell
syntax validation, context validation and diff checks pass. These tests do not
qualify the activation-context failure or promote this script into product setup.

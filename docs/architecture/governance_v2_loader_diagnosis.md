# Gate A Bounded Loader Diagnosis

## Decision And Scope

2026-10-15: the user approved the recommended bounded loader-level diagnosis
after the startup assessment and web research. This is an explicit diagnostic
budget exception, not another runtime correction or Gate A acceptance.
The selected LPAC/WFP profile, unpatched Hermes pin and staged payload remain
unchanged. No broader registryRead/lpacCom capability, other registry grant,
ordinary-mode execution, model request or product activation was authorized.

The allowance is now consumed. The exact activation dependency remains unresolved;
stop this candidate at the startup feasibility decision. Do not automatically add
another diagnostic batch, permission sequence or alternative implementation.
References: [evaluation contract](governance_v2_gate_a_evaluation_contract.md),
[startup assessment](governance_v2_windows_startup_assessment.md),
[plan revision 2](maya_governance_integration_plan_v2.md).

## Method And Retained Setup Failure

No debugger was present in the checked standard installation locations. With
separate download/extraction permission, the Microsoft-signed SDK bootstrapper
downloaded only the debugger component in layout mode. The signed x64 debugger
MSI was administratively extracted into ignored diagnostic output, not installed.
CDB reports version 10.0.26100.1. No system debugger registration, machine-wide
GlobalFlag or Image File Execution Options value was written.

The first capture was not a valid activation-failure reproduction:

- Its command requested `!gflag +sls` at the child-create event, before ntdll
  metadata was available; CDB reported that NtGlobalFlag could not be found.
- The elevated preparation wrapper returned zero, but subsequent exact-descriptor
  read-back proved that SideBySide still had the original descriptor. The old
  grant-result file was not fresh evidence. That attempt returned 0xC0000022.
- The wrapper did not retain an error explaining the omitted script invocation;
  do not claim its exact cause is proven. The failed capture remains unchanged.

One corrected attempt was separately permissioned. Preparation used explicit
process-local PowerShell script execution permission and terminating errors; the
actual owner/group/DACL was compared with the expected temporary descriptor
before capture. It reproduced only the earlier approved non-inheriting package-SID
ReadKey grant on the exact 64-bit SideBySide key. No additional resource was granted.

The unchanged helper's WFP read-back succeeded. CDB followed the helper's children,
used the standard heap, and enabled loader snaps at the ntdll module-load event.
Read-back showed NtGlobalFlag 0x00000002. This was diagnostic process memory, not
a changed payload binary or registry policy. The helper retained its suspended
LPAC/ordinary-token comparisons, job assignment and explicit resume ordering.
The ordinary comparison was not an unrestricted execution fallback.

Input was only `{}`: even a successful Python bootstrap would reject admission
before native Hermes import. No broker listener or provider transport was started.
The trace is debugger-instrumented diagnosis, not an effect-level containment test.

## Observations And Limits

The executing Python child was PID 17788 (hex 457c); the other observed child was
PID 14588 (hex 38fc). Native helper completion reported 3222601730 / 0xC0150002;
the worker result file was empty. Selected-child loader output records:

1. Resolution and mapping of the staged VCRUNTIME140.dll and python313.dll
   succeed; ucrtbase.dll is mapped from System32.
2. `LdrpFindDllActivationContext` reports: querying the active activation context
   failed with status 0xc0150002.
3. `LdrpProcessWork` identifies python313.dll, with python.exe as parent module.
4. `LdrpInitializeProcess` reports failure while walking the executable's static
   import tables, followed by process-initialization failure with the same status.

The KnownDLL lookup miss for a staged DLL is not proof that the DLL is missing:
the subsequent ordinary file lookup/mapping succeeds. Similarly, absent embedded
manifest probes for other modules are not the recorded fatal activation failure.
Do not prescribe Visual C++ reinstallation from these intermediate messages.

The capture does not identify an inner failing API, a denied registry key/file/IPC
object, a missing assembly, or a safe minimum grant list. It does not prove that
registryRead or lpacCom would fix the failure, or that CPython is incompatible with
all LPAC configurations. No native Hermes construction or A01-A20 acceptance follows.

Conclusion: the failure is more precisely localized to DLL activation during
Windows static-import initialization, but the exact root cause and safe correction
remain unknown. The approved bounded investigation has not established a viable
startup profile. Further work requires an explicit strategic decision or separately
approved vendor-reproduction investigation, not another automatic permission fix.

## Cleanup And Evidence

Original SideBySide owner/group/DACL SDDL and binary descriptor were restored and
verified against the retained snapshot; SACL was untouched. The helper's cleanup
completed successfully. Independent read-back found the test filter missing
(FWP_E_FILTER_NOT_FOUND), zero matching loopback exemptions, no test-SID grants on
the staged runtime/state directory DACLs, and zero CDB/helper processes.
The process-local loader flags died with their diagnostic processes.

Raw logs, command files, symbols and downloaded debugger artifacts remain ignored
under `.codex-build/gate-a-loader-diagnostics`; do not commit or publicly share raw
host traces. The older startup evidence and frozen runtime inputs are unchanged.

| Evidence | SHA256 |
| --- | --- |
| First capture, invalid instrumentation | `a1c2e05fc47248fcb81c64a5ae18f17dff55f87ce1f6ded0f74ec544e0f52f73` |
| Corrected loader capture | `49bafa365fe24d07d1afaa8e4a86f6a03193ceca740747fabc6f55d730aa7090` |
| First debugger command file | `2916219a62aa6ef8c41a0f962f1034bb3073f9ed12f05dd8d6dbb337a755e143` |
| Corrected debugger command file | `23c305752f57d536a7fd3a73d352c593da26ad1d1b017f6002bf24d02cce32a0` |
| Microsoft CDB executable | `37095ef02baf6bb87e7d0eb4b0fc466dbe2c87cabc60afd114394db6f62edfe9` |
| Microsoft SDK bootstrapper | `5535188a9aeea1cebcbf04de3c2c37d76f10600a65867ff65f6153d507b60488` |

The helper binary remains
`e72f101bea8222d14e908c2f39e7fecdca122b2f13b2abe9d5293490b7856f63`;
the fully rechecked runtime manifest remains
`0ed977a4f7269ec86d01468e19820d616fc4e74cacd21b2919131d88457a5b32`.

Microsoft documents [loader snaps](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/show-loader-snaps)
and the [process diagnostic flag](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-gflag).
Those mechanisms expose loader activity; they do not establish a safe compatibility
profile. Product pins, policies, memory/SSE wiring, wheels, installers and production
guards were not modified.

Validation: all 55 existing startup-inventory, broker, preflight/token-guard and
Local API tests pass. Product-context validation and tracked diff checks pass;
Git retains its existing LF/CRLF checkout warning for the integration plan.
These are regression checks, not native startup, containment or Gate A acceptance.

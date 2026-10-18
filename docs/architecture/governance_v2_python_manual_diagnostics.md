# Manual Python Startup Diagnostics On The Existing Azure VM

## Superseded Operational Procedure

Later on 2026-10-18 the user directed and clarified
[customer-like Windows testing](governance_v2_customer_windows_testing.md).
That is now the active workflow. Do not apply the manual ACL/WFP/registry,
loopback, offline/SAC or per-case reset instructions below. The pending A-D
execution request was not approved; zero attempts were consumed and no authority
to resume or relabel that matrix follows. Preserve this document's kit and
completed rehearsal records as historical evidence. Maya must request and
provision required permissions itself through its actual setup/runtime path.
No extra test automation or unrestricted-product fallback is authorized.

## Approved Scope

2026-10-18: the user approved replacing the observer-dependent comparison with
manual startup diagnostics, to use the existing VM without building more test
infrastructure. This is the active operational addendum to
[Plan V2 Gate A](maya_governance_integration_plan_v2.md) and supersedes the
automation prerequisites in the [Azure procedure](governance_v2_python_azure_procedure.md).
The frozen 25H2/26H2 contracts, binaries, manifests and observer reviews are not
rewritten. Their stronger evidence requirements are not represented as satisfied.

Use existing launchers and the existing Python-only probe. No downloader,
supervisor, remote-access agent, custom packager or test-runner is installed.
The unfinished transfer sources, observer host/library and disabled execution
templates were excluded from the kit. The user's subsequent 2026-10-18 repository
cleanup request authorizes removal of obsolete transfer sources: the unused
`prepare_governance_v2_transfer.py` was deleted. Removal of `Get-MayaGateAKit.ps1`
was denied by the patch tool and by a permissioned native deletion attempt outside
the sandbox. It remains obsolete, must not be executed and is not a test
prerequisite. Its deletion failure does not establish the cause or authorize an
antivirus change, ACL reset, rename or other bypass. Retain the frozen observer
evidence and disabled templates; no additional transfer implementation is needed.

This replaces the single A-D matrix, not adds another. One attempt per case in
order; no retries, alternative profiles, new captures or automatic corrections.
VM-security changes, paid snapshot/restoration resources and startup execution
retain their explicit impact/permission decisions. Local assembly changes no VM.

## Access And Responsibilities

The operator uses the existing local administrator and Azure portal. The agent
supplies individual commands, reviews returned output and changes product code
only within approved scope. This chat has no direct VM terminal connection.
Do not send passwords, Azure credentials or provider keys; no new cloud role or
remote service is needed. Existing guest/build/encryption inventory is already
recorded privately and need not be supplied again.

RDP file copy is allowed only during setup. Close RDP and remove clipboard,
drive and device redirection before baseline capture or any startup attempt.
Use the already-working Serial Console/SAC for the attempts. Guest network
adapters must be disabled and read back through SAC before each attempt;
do not detach the Azure NIC, broaden RDP access or change the workstation.

## Files To Transfer

The local manual kit contains only these existing inputs, with original paths:

| Component | Path under the extracted `C:\MayaGateA` root |
| --- | --- |
| Frozen Python-only bundle | Original 803 files, including `reproduction-manifest.json` and four historical comparison documents |
| Prepared CPython 3.13.14 and probe | `.codex-build\governance-v2-lpac-stage\runtime` |
| Unchanged Maya native helper | `.codex-build\governance-v2-native-tools\GateANative.exe` (already in the bundle) |
| Pinned Microsoft reference executable | `.codex-build\governance-v2-reference-tools\LaunchAppContainer.exe` |
| Vendor notices and inventory | `docs\third-party\governance-v2-python-comparison` (11 files) |

Do not copy the repository, a virtual environment, local evidence directories,
old case state, cloud inventories or credentials. The Python standard library
contains its original ensurepip bootstrap wheel; do not run pip or install it.
No Python, Hermes, Maya installer, build tools or debugger installation is needed
for this startup-only workload. Notices are not Windows licence-entitlement proof.

## Manual Preparation Checklist

1. Copy the prepared ZIP to the VM using the existing IP-restricted RDP session.
   Use built-in file copy, not a new download service, public link or SAS token.
2. Check its SHA256 in guest PowerShell with
   `Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\Users\Public\Downloads\MayaGateA-manual.zip'`.
   Compare with the local archive hash recorded below. A mismatch stops setup.
3. Extract with Windows' built-in ZIP support into a new `C:\MayaGateA` directory.
   Its direct children must include `.codex-build`, `docs` and
   `reproduction-manifest.json`, not an extra enclosing kit directory. Do not
   merge into an existing stage or launch any executable to check installation.
4. End RDP, remove sharing/redirection and continue through Serial Console.
   Keep all customer information and live service credentials outside the VM.
5. Use the already-reviewed manual snapshot/OS-disk-swap procedure: one clean
   baseline and one inert restoration/NIC rehearsal before attempts. Retain the
   original disk. Disclose/approve actual snapshot/disk costs before allocation.
   Rehearsal failure stops; no boot repair or security downgrade is authorized.
6. Before A, review the exact commands and guest-only security changes together:
   the same eight package-SID-scoped WFP filters, loopback exemption, private
   filesystem grants and non-inheriting SideBySide ReadKey grant. Record original
   descriptors and restoration data in the VM, not from the workstation. Obtain
   the outstanding security/execution permission before applying or launching.

Preparation file transfer is not startup execution. No new helper implementation
or observer acceptance round is a dependency of this checklist.

## Run And Restore Manually

| Order | Existing launcher | Requested extra token capabilities |
| --- | --- | --- |
| A | Byte-identical Maya helper | None |
| B | Pinned Microsoft launcher | None |
| C | Same Microsoft binary | registryRead |
| D | Same Microsoft binary | registryRead and lpacCom |

All retain the common requested privateNetworkClientServer/profile settings.
Use the same workspace, operator and derived package identity. A uses the existing
helper's suspended controls and interactive admission; those controls are not an
ordinary-mode fallback. B-D retain the declared launcher/environment/console
differences, including the reference's HKCU Console value change and its exact
restoration. They are not a single-variable proof of a Maya helper defect.

Use a visible timer: 100 seconds is the manual stop threshold, not a guaranteed
automatic deadline. No new outer-job supervisor is present; the native helper's
existing checks/job handling are not silently attributed to the reference cases.
Record each attempt in an operator-held journal outside the restored disk before
launching. A failed/uncertain launch consumes its attempt; restoration never
resets that journal. Restore the clean baseline before B, C and D and recheck
inputs, identity and offline state. Do not run all four against one dirty disk.

If a process hangs, cleanup is uncertain, security setup fails or inputs drift,
stop the sequence and stop/deallocate through the Azure portal. Keep guest
networking off; do not reconnect an uncertain guest to retrieve logs. Preserve
the disk for a specific recovery decision, not another automatic attempt.

## Evidence And Decision

For each case retain the requested command/profile, time, console result,
fresh `python-startup.json` beacon if present, and child exit only when actually
available. Mark unavailable PID/token/exit/cleanup evidence as unverified.
The reference launcher's exit code is not the Python child's exit code.
An old beacon or launcher exit zero is not proof of Python entry.

A fresh exact beacon establishes that the prepared probe reached its entry point;
observed errors establish only the recorded failure. Without independent token
evidence, say "Python entered under the requested launch profile", not "LPAC was
verified". Manual operation does not establish exact deadline compliance or full
descendant cleanup. Do not infer those facts from a screenshot or helper success.

Prepare one findings report and stop for the next product decision. Startup
success or a capability correlation is not Hermes execution, safe production
permission, governance containment, Gate A acceptance or supported Windows release.
Customer-protection requirements and later integration gates remain unchanged.

## Baseline And Rehearsal Result - 2026-10-18

The user separately approved snapshot creation, then the single inert
restoration/NIC rehearsal. Evidence below is operator-supplied console output,
screenshots and portal JSON, not direct agent access to Azure or the guest.

- The full Standard LRS baseline snapshot deployment completed successfully.
- The rehearsal disk was created from that exact snapshot in East US, Zone 1.
  Its resulting JSON reports 127 GiB, Premium_LRS, P10, 500 IOPS, 100 MB/s,
  Windows, V2, x64, TrustedLaunch and platform-managed encryption. The earlier
  portal review's 80,000 IOPS/2,000 MB/s line was not the resulting disk setting;
  the exported request had no performance override. No capacity change was used.
- Before restoration, the operator created the 31-byte rehearsal marker and
  confirmed the approved Ethernet disable/read-back/re-enable round trip through
  Serial Console. The original adapter identity matched the recorded inventory.
- After disk swap and boot, the marker was absent. The reproduction-manifest,
  Maya-helper and reference-launcher SHA256 values matched the local kit record.
  This verifies those three digests, not a separate hash of every guest file.
- The private case state directory was empty. The operator SID and Windows build
  26300.9711 matched the original observations. Reported BitLocker conversion,
  percentage, encryption method, protection status and protector fields matched;
  the lock-status line was obscured by console interleaving.
- The final VM JSON reports the same VM identity, the rehearsal disk as its OS
  disk, the same NIC, TrustedLaunch, Secure Boot enabled and vTPM enabled.

The bounded operator-reported restoration/NIC rehearsal has passed. No Python
probe, Maya launch or reference launch was reported; zero A-D attempts have been
consumed. Shell-selection and console-rendering errors during read-only checks
were not new startup attempts. Retain the original disk and baseline snapshot;
this record grants no deletion or automatic recovery permission.

At completion, preparation-checklist item 6 was proposed next: separate exact
VM-security and A-D execution permission. That request was not approved and was
subsequently superseded by the customer-like Windows testing decision above.
No further baseline rehearsal, additional observer or transfer tooling is a
prerequisite. This result establishes a usable reset procedure, not LPAC/WFP
containment, Hermes startup or Gate A acceptance.

## Local Kit Record

Prepared locally with standard file-copy/ZIP facilities, not a new packaging
script. The archive has 815 files: the unchanged 803-file base, one reference
executable and 11 notice files. Every archived file was checked against the
assembled input bytes; all 802 base-manifest entries and the manifest itself
were verified unchanged. Empty private state/host directories are retained.

- Local archive: `.codex-build/governance-v2-manual-kit-20261018/MayaGateA-manual.zip`.
- ZIP size: 15,197,343 bytes; expanded files: 36,922,090 bytes.
- ZIP SHA256:
  `3ae88df025ef542380e32c4512d9bc595761010af03775871500e42e5d9ca756`.
- Original reproduction manifest SHA256:
  `17ad01535d3a70da86cc264b011cbb22528fdee5bf4b29203d9e7ed4daaeda60`.
- Maya helper SHA256:
  `e72f101bea8222d14e908c2f39e7fecdca122b2f13b2abe9d5293490b7856f63`.
- Microsoft reference SHA256:
  `812ab69ebcc45a241131b79b3c6c26319aaec802377d10ea733c5f70fcb36606`.

Frozen manifests keep their original permission/status fields; this addendum
does not relabel them as authorized or production-qualified. No archive transfer,
guest modification or startup attempt was performed during local preparation.

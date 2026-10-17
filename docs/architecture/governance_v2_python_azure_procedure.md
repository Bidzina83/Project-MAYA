# Python Comparison - Azure Preparation And Execution Proposal

## Status And Evidence

2026-10-17: document preparation following the user's report that the USD 200
credit is now visible and instruction to proceed. The user deployed an Azure VM
and supplied a winver screenshot showing Windows 11 26H2, build 26300.9711.
Earlier provisioning screenshots selected Pro, x64, Standard_D2as_v4, two vCPUs,
8 GiB RAM, Trusted Launch, Secure Boot and vTPM. The unrestricted RDP rule was
removed by the user; the retained custom rule restricts TCP/3389 to one public
IPv4 /32. These are user-supplied observations, not an independent cloud inventory,
credit audit, licence determination, or containment result.

This is a proposed Azure procedure under [Plan V2 Gate A](maya_governance_integration_plan_v2.md),
not a new product architecture. The [26H2 contract](governance_v2_python_comparison_26h2.md)
and [JSON](governance-v2-python-comparison-26h2.json) retain their original bytes,
labels and remaining prerequisites. Preserve the 25H2 failure evidence and old
bundle. This document authorizes no upload, build, security/boot/network change,
snapshot, disk swap, process launch, test execution or external publication.
Production activation remains blocked.

The single startup budget remains A, B, C, D in order: one attempt each,
100 seconds per case including child cleanup, zero automatic retries/corrections,
one findings report. No second OS matrix, live provider, Hermes installation,
new runtime patch, wheel or installer is included.

## Proposed Control Method

Use Azure Serial Console/SAC as the out-of-band administrative control path.
Microsoft documents network-independent serial access and SAC availability for
Windows 11 when enabled:
[Windows Serial Console](https://learn.microsoft.com/en-us/troubleshoot/azure/virtual-machines/windows/serial-console-windows).
This is a candidate method, not verified access to this guest. If SAC is not
enabled, disclose the exact guest-only EMS boot-setting changes, original values
and reboot impact before asking permission. Do not disable Secure Boot/vTPM,
alter the workstation boot settings, install a debugger or enable serial access
across the whole subscription.

Use the same named local administrator for the console and every launcher;
verify its SID, elevation and selected child token. No SYSTEM/default-actor
fallback is permitted. Differences introduced by serial launch, including parent
session/desktop, cwd and environment, belong in the execution manifest and must
be held constant across A-D. Existing Microsoft/Maya launcher differences remain
declared confounders; the console does not eliminate them.

Before every startup attempt, disable every inventoried non-loopback network
adapter INSIDE the guest and verify the disabled state through Serial Console.
RDP disconnection alone, an NSG deny rule or loss of internet access is not this
read-back. Preserve loopback for the unchanged diagnostic profile; no broker
listener runs. Do not detach Azure's primary NIC or modify shared cloud networks.
Microsoft confirms that disabling the guest NIC removes RDP access:
[Disabled-NIC behavior](https://learn.microsoft.com/en-us/troubleshoot/azure/virtual-machines/windows/troubleshoot-rdp-nic-disabled).

Launch only through the reviewed host-side token/lifecycle observer with the
existing per-case deadline. Serial Console is a control channel, not that observer
and not evidence of an LPAC token. Its administrator can affect the guest; it is
part of the trusted lab control plane, not an allowed Python capability.

Networking may be re-enabled only after all selected launcher/child processes
and descendants are proven terminated and exact per-case security cleanup is
verified. No unconditional timer, finally-block reconnect or timeout reconnect.
On uncertain cleanup, keep networking disabled, deallocate through the Azure
control plane, preserve evidence and stop the matrix for review. Never use RDP,
VM Run Command or the guest agent as the required control path while offline.

## Ordered Work And Acceptance

1. **Local preparation.** After explicit approval, add an explicit 26H2-contract
   binding to the existing preparer without changing its historical default.
   Produce a fresh ignored output; never rewrite the 25H2 bundle. Build the pinned
   unmodified Microsoft reference with recorded toolchain/project/source/binary
   hashes. Implement and review the external child-token, exit and deadline
   observer against both launchers. Fixture tests may use inert inputs, not launch
   the managed Python on the workstation. No payload is production-qualified.

2. **Approve the exact VM preparation impact.** Record VM, resource group, region,
   OS disk size/type/security/encryption, guest edition/architecture/build/patch
   inventory, adapters, operator SID and workspace. User screenshots alone do not
   freeze those values. Proposed workspace is C:\MayaGateA, with reviewed inputs
   separate from empty private state. Record boot/console originals, transfer
   locations, planned snapshot/restore disk names, storage retention and estimated
   incremental cost. Request permission for these exact VM-only changes before
   performing them. No actual subscription IDs or passwords belong in Git.

3. **Prepare and verify the clean lab baseline.** With that permission, establish
   working SAC access, install only the reviewed diagnostic artifacts, and verify
   all hashes. No Maya installer, Hermes, cloud SDK/CLI credentials, customer data,
   account sync, mapped drives, clipboard/device redirection or provider keys.
   Capture the baseline with networking enabled and no case automatically armed.
   No payload/helper/reference launch occurs during preparation.

   Proposed reset method: a cleanly stopped/deallocated OS-disk snapshot, a fresh
   compatible managed disk made from that snapshot and an explicit OS-disk swap
   on the same deallocated VM. Do not generalize/Sysprep or recreate operator
   accounts. Microsoft documents [disk snapshots](https://learn.microsoft.com/en-us/azure/virtual-machines/snapshot-copy-managed-disk)
   and [OS-disk swaps](https://learn.microsoft.com/en-us/azure/virtual-machines/windows/os-disk-swap).
   This is not a Hyper-V memory checkpoint. It does not reset the Azure NIC, NSG,
   public IP, RBAC or other control-plane resources; compare those separately.

   Verify same disk size, zone compatibility, generation, security type and
   encryption requirements. Retain Trusted Launch/Secure Boot/vTPM; account for
   associated guest state, not an assumed ordinary disk-only reset. Microsoft
   describes guest-state coupling and potential snapshot failures:
   [Trusted Launch FAQ](https://learn.microsoft.com/en-us/azure/virtual-machines/trusted-launch-faq).
   The procedure must work with this actual guest. Failure is a stop, not permission
   to remove Trusted Launch, unlock TPM state, repair Windows or change images.

   Proposed bounded prerequisite rehearsal, requiring explicit approval: one
   inert marker round trip through snapshot/restore plus one NIC disable/read-back/
   re-enable through SAC. No Python/helper/reference process, LPAC grant or extra
   startup scenario. After restoring, require the marker to be absent, case state
   empty, inputs unchanged and guest/operator identities intact. One rehearsal,
   no automatic retry or correction. A simple reboot is not accepted as a reset.

4. **Freeze and authorize execution.** Record the immutable baseline snapshot,
   read-back, new bundle and contract hashes, reference binary, observer, exact
   case commands and parent context, all security descriptors and expected cleanup.
   Disclose the original eight SID-scoped WFP filters, loopback exemption,
   filesystem grants and exact non-inheriting SideBySide ReadKey change, plus
   registryRead in C and registryRead/lpacCom in D. Obtain explicit VM-security and
   A-D execution approval. Baseline/preparation approval does not grant these.

5. **Run the existing matrix and report once.** Use the verified baseline for A,
   then restore it before B, C and D. Recheck exact common identities, inputs,
   control-plane configuration and offline state each time. Missing token/child
   read-back, cleanup uncertainty, exposure or input drift stops remaining runs.
   Keep failed attempts as failed/partial/invalid; no substitute run. Produce the
   single scoped findings report and stop. Python entry is not Hermes operation,
   WFP effect-level qualification, Gate A acceptance or product readiness.

These are the existing comparison prerequisites and execution on Azure, not
permission to insert another startup investigation or extend the experiment.
If a prerequisite cannot meet this proposal, present the exact conflict before
reordering work, adding a service/capture or changing the candidate.

## Transfer And Evidence Proposal

Transfer is not authorized yet. Proposed input channel: one reviewed archive
in a private, dedicated Azure Blob container, downloaded over HTTPS during setup
only. Approval must identify the storage account/container/blob, region, retention,
size/cost and access method. Review distribution/licence disclosures before upload;
the current reproduction is local-only and cannot simply be relabelled for cloud.

Any proposed short-lived read-only blob SAS is a bearer secret: supply it only
through reviewed interactive secret input, keep it in memory, exclude it from
command-line arguments, histories, transcripts, manifests and screenshots, and
expire/revoke it before baseline capture. Never put a cloud administrator token,
storage-account key or live inference/connector secret inside the fixture or
LPAC environment. Public blobs, permanent upload/download links and host-folder
redirection are not substitutes. No storage resource or SAS is created by this
proposal. Hash-verify input bytes in the guest before use.

Proposed evidence channel: the observer writes allowlisted fixed-code JSON and
hash inventories locally; review them through SAC and extract only sanitized
text. Exclude credentials, raw console streams, full environment values,
operator/cloud identifiers and application dumps from shared reports. Keep
operator-specific execution/rollback data private. No raw process output is
automatically public or safe just because the workload is synthetic. If cleanup
fails, retain the case disk for approved recovery/extraction; do not reconnect
the uncertain guest merely to obtain logs. An extra recovery VM is not preapproved.

## Costs, Rollback And Permission Envelope

The user reports that credit is visible; amount remaining, expiration, spending
protection and licensing are not independently re-audited by this proposal.
Do not change billing plans or consume the entire credit as an assumed budget.
Compute, input storage, snapshot and replacement disks need an actual estimate
before VM preparation. The earlier local 80/120 GiB planning envelope does not
establish the actual Azure OS-disk size or permitted cloud allocation.

Plan for one baseline snapshot and up to four replacement OS disks over the
procedure (one rehearsal and three between-case resets), not four simultaneous
VMs. Exact size, concurrent retention and deletion permissions require approval.
Retain the original disk until baseline restoration is proven. Never automatically
delete a failed-case disk, snapshot, resource group or existing user resource.
No resizing, new paid service, second VM, expanded cost/storage budget or additional
restore attempt is automatically authorized by a failure.

On each approved cleanup restore captured guest security descriptors and exact
profile/filter/exemption state. Keep the workstation untouched. Restore guest
EMS settings when approved testing is complete, or disclose intentional retention;
no permanent administrative change is silently adopted by the product. Snapshot
restoration and descriptor cleanup are distinct evidence requirements.

## Current Next Decision

The user approved this procedure and Step 1 local preparation on 2026-10-17.
That approval does not extend to installing missing system build tools, VM changes,
transfers or executing either launcher. The bounded progress and current build
prerequisite are recorded below. Before Step 2's VM changes, present exact resource
identities, permissions, costs and affected values. Step 3's rehearsal and Step 4's
security/execution allowance remain separate explicit decisions. No cloud upload,
reboot, snapshot, NIC change or A-D attempt has been performed by the agent.

## Step 1 Local Progress - Partial, Build Prerequisite Blocked

2026-10-17: the existing preparer now accepts an explicit `--profile 26h2`.
Its default remains the historical 25H2 layout and contract. The successor validates
four frozen document hashes, includes both predecessor documents without modifying
them, records its selected contract/runbook paths and hashes, and refuses drift or
an existing output directory. It performs no network, subprocess, native security
operation or application import. Input copying does not execute the managed Python.

Prepared local-only output:
`.codex-build/governance-v2-python-repro-26h2-20261017`.

- Files listed and individually hash-verified: 802, plus its manifest.
- Manifest SHA256: `17ad01535d3a70da86cc264b011cbb22528fdee5bf4b29203d9e7ed4daaeda60`.
- 26H2 contract SHA256: `07b04c4577277780a2352e970185f949e7f3cdf755bc3f1c5a6312cd29f29a27`.
- 26H2 runbook SHA256: `4009eef072a7c1e2b160ac72aa07d9b488342ffa8138d2f01ae3c599f7f242f3`.
- Historical bundle manifest remains
  `3d67d3d0153391c42f8759768e67b9d19ce5c2e47f821f218298a279cb6c1b2b`.
- The 30 preparation/probe tests pass, including eight added profile/default,
  drift, preservation and CLI checks. These use inert file fixtures/mocked probe
  calls, not native startup or containment tests.
- Execution, external sharing, Gate A and production flags remain false. The
  reference binary and observer are not present; this is not a VM-ready test kit.

The public Microsoft repository was downloaded into the ignored local directory
`.codex-build/governance-v2-reference-source-20261017` and checked out at the pinned
commit `8102bfc8dc3e244ec08e8204bd7d989e26a016e4`. No source modification or launcher
execution occurred. Source inputs verified:

- LaunchAppContainer.cpp: `833b26e3ea4524accea712cf2f01f52faf4941ee2feaf8199fcb0bd661484973`.
- LaunchAppContainer.vcxproj: `4c726b3ae40e3803e8d045137bb3ed15e76e5f6b0de6e4001ec9168a8de381e7`.
- Repository LICENSE: `9906940f61b1f0b533fa7d99baf55178b2808fbe113ea51dfbfad8572ccd5f2b`.

The unmodified project selects v143 and Windows SDK 10.0. No MSVC C++ installation
or Windows SDK was found in the inspected registered/standard locations. The
available .NET Framework MSBuild build attempt for Release/x64 failed at project
import with MSB4019, missing Microsoft.Cpp.Default.props, before C++ compilation.
No reference binary was produced, so no successful build record or binary hash
is claimed. This is a build-machine prerequisite failure, not another LPAC startup
finding or an A-D attempt.

The next decision is to identify an already installed compatible C++ toolchain or
approve a minimal Microsoft Build Tools v143 plus compatible Windows SDK
installation on the LOCAL BUILD MACHINE. Microsoft publishes the components in
its [Build Tools catalog](https://learn.microsoft.com/en-us/visualstudio/install/workload-component-id-vs-build-tools?view=vs-2022).
Disclose installation/download/cache sizes and any reboot before installation;
do not install the full IDE/workloads or retarget/patch Microsoft's project to
bypass the missing prerequisite. Record actual compiler/SDK versions and build
input/output hashes once available. The external observer remains the next Step 1
sub-item after that build; it has not been implemented or qualified. Do not reorder
the work or move to guest preparation to evade this blocker.

### Build Tools Preparation - No Installation Authorized

The user authorized preparing the minimal selection and reporting requirements
before installation. That does not authorize running the bootstrapper, installing
even the Visual Studio Installer itself, accepting installation terms or rebooting.

Prepared selection for Visual Studio Build Tools 2022, English, v143:

- `Microsoft.VisualStudio.Component.VC.CoreBuildTools`: native MSBuild targets and
  required C++ core support.
- `Microsoft.VisualStudio.Component.VC.Tools.x86.x64`: compiler, linker and native
  libraries for the unmodified Release/x64 project.
- `Microsoft.VisualStudio.Component.Windows11SDK.26100`: Windows headers and
  import libraries, including the project's Userenv/OneCoreUAP dependencies.
- Build Tools product prerequisites, including MSBuild, must be resolved by the
  official installer; this is not a promise to omit required shared components.

The selection is saved as `minimal-buildtools.vsconfig` in the ignored directory
`.codex-build/governance-v2-buildtools-preparation-20261017`. It is configuration,
not an installed toolchain or a verified offline layout. No IDE, recommended or
optional workload expansion, ATL/MFC, CMake, ARM toolset or test tools is requested.
Required dependencies may still include support files for other architectures.
Build-machine tools are not additions to the Maya customer installer.

Microsoft's release history and channel metadata identify 17.14.42,
build 17.14.37806.7, as the current 2022 release on 2026-10-17. However, the
downloaded catalog failed verification. The channel advertised 30,443,686 bytes
and SHA256 `a871a5ff41acebbe5037455fd6f51fcd4907b47d8f3c9860871ea0b222a2fd45`;
both the initial transfer and one identity-encoding retry returned 17,954,770
bytes with SHA256
`99dda859c4ae3c446eb25620d1a6237bb135d95d14d55cd1d30a15340bb39d80`.
The copies are retained only as unverified diagnostic metadata. The reason for
the mismatch is unknown; neither compromise nor benign rewriting is established.
Do not execute packages, suppress verification, adopt a different release or
calculate an authoritative installation total from this catalog.

Current download, installed, retained-cache and peak temporary-space requirements
therefore remain unverified, not zero. C: had 278,438,932,480 bytes free
(approximately 259 GiB) at preparation time; free space alone does not qualify
the installation. Reboot requirements cannot be guaranteed before the installer
evaluates machine state; any eventual installation must prohibit an automatic
restart and report a reboot-required result for a separate decision.

Preparation is partial. Resolve catalog integrity before approving component
installation. If an official installer-only preparation is proposed to obtain
the dependency calculation, disclose that it installs machine software and obtain
separate permission first. No bootstrapper or downloaded package was executed,
no system component was installed, and no reboot or VM operation occurred.

### Subsequent Local Toolchain Installation Authorization

On 2026-10-17 the user explicitly requested downloading and installing whichever
tools are suitable. This supersedes the preparation-only permission above for the
local toolchain, not its retained catalog-integrity finding or the VM/run gates.
No unverified downloaded catalog is supplied to setup and no verification bypass
is permitted. Exact dependency sizing was unavailable before this authorization.

Selected fixed Microsoft Build Tools 2022 17.14.42 bootstrapper from Microsoft's
release-history page: 4,474,848 bytes, SHA256
`68978bb28916156802e60e04c5ee50b94348d802fe151a3ca24433f27984187b`.
The downloaded bytes match that published URL hash and Windows Authenticode reports
Valid, signer Microsoft Corporation. This independently verifies the bootstrapper;
it does not retrospectively validate the earlier catalog copies.

Installation requests only the three prepared component IDs, with required product
dependencies, at the standard BuildTools path. Flags: `--quiet --wait --norestart
--nocache`; no optional/recommended expansion, alternate catalog or signature/hash
override is supplied. The official installer retains its own package verification.
The no-cache request avoids retaining optional package payload caches; required
installer/system caches may remain. No automatic restart, VM operation, launcher
execution, production activation or customer installer change is authorized.

### Installation And Reference Build Result

The approved installation finished with exit code 0. `vswhere` confirms a complete,
launchable Build Tools 2022 17.14.37806.7 installation with both selected compiler
and SDK components; `isRebootRequired` is false. No reboot occurred. Setup's error
log is empty, its native manifest verifier reports Success, and package hash checks
remain enabled. The earlier independently downloaded catalog mismatch remains
unexplained; those files were not used as installation inputs or relabelled verified.

Installed compiler/linker tools: v143 directory 14.44.35207, compiler file version
19.44.35229.0, linker/debug-symbol DLL version 14.44.35229.0. MSBuild file version:
17.14.60.43110. Selected SDK library directory: 10.0.26100.0; SDK resource-compiler
file version: 10.0.26100.7705. The unmodified project retains WindowsTargetPlatformVersion
10.0, v143 and Release/x64 `/MT`; it was not retargeted or patched.

The first build compiled successfully but failed at linking with LNK1101 inside
the command sandbox despite matching linker/debug-symbol DLL versions. Retained
log: `reference-build.log`. A permissioned retry outside that command sandbox
succeeded, followed by one complete clean rebuild, also outside that sandbox:
0 warnings, 0 errors, exit code 0. The first failure is not evidence of an
incorrect installed DLL or a Windows LPAC startup finding; its exact sandbox
interaction was not separately diagnosed. No security restriction for the product
or comparison payload was weakened. This used ordinary developer compilation only.

Build outputs remain in ignored local directories, not the prepared bundles or
customer installer. Final reference executable:
`.codex-build/governance-v2-reference-source-20261017/LaunchAppContainer/LaunchAppContainer/x64/Release/LaunchAppContainer.exe`.

- Size: 160,256 bytes.
- SHA256: `812ab69ebcc45a241131b79b3c6c26319aaec802377d10ea733c5f70fcb36606`.
- Clean build-log SHA256: `e894f5081fbabd8a589777c16190b29a790ced469c6345ca3e95212c440e6a05`.
- Read-only PE inspection: x64 console image, dynamic base/NX compatible;
  imports USERENV, KERNEL32, ADVAPI32 and api-ms-win-security-base-l1-2-2.
- Tracked source checkout remains clean at the pinned commit. CPP/project hashes
  still match the source-input values above. No launcher execution occurred.

The local machine-readable record is `reference-build-record.json`, alongside
the retained setup preparation and build logs in
`.codex-build/governance-v2-buildtools-preparation-20261017`. Current C: free space
is 276,273,381,376 bytes. The change from the earlier free-space observation is
not an exact installation/download/cache size: other machine activity may occur,
and required shared/system installer caches remain despite `--nocache`.

The missing C++ toolchain/reference-build prerequisite is now resolved. Step 1
remains incomplete: next is the approved external process/token observer and its
review, not uploading or running the reference. No bundle execution flag, VM,
profile, WFP rule, registry permission, runtime wheel or product installer changed.
No A-D attempt or Gate A/production acceptance follows this successful build.

### Observer Preparation - First Implementation Stage

The user authorized observer implementation and explicitly approved the common
outer-job design for A-D. Consult [the observer preparation review](governance_v2_observer_review.md)
for its fixed implementation sequence, declared launch-context change, limitations
and evidence. The unarmed x64 library now supplies process/token evidence rules,
native read/job primitives and deadline decision rules. Its 57 inert checks pass;
they make no native token/job/process calls. Launcher supervision adapters and
their joint source review remain the next Step 1 work, not completed supervision.
Do not claim the 100-second watchdog, ancestry discovery, ordinary-control
correlation, nested-job behavior or native cleanup is qualified. No launcher,
managed Python, VM/security operation or startup comparison was executed.
The user subsequently requested the next observer stage. Fixed A-D adapters,
the single-use supervisor and the native backend are now source candidates with
inert fixture coverage and a joint source review in the same observer document.
They remain an unarmed library. Stage 3 freeze/manifest/invocation review is next;
no actual launcher, token/job operation, managed Python or VM action was executed.
Callback-based operational approval does not replace the future exact VM,
network/security and human-permission read-backs. Step 1 remains incomplete.

### Observer Review Package - Partial Stage 3

The 2026-10-17 continuation records final source/artifact fingerprints, the
proposed `C:\MayaGateA\observer` library location and A-D invocation inputs in
`governance-v2-observer-review-package.json`; consult the observer review for
scope and validation. This is an unarmed review record, not an execution manifest,
transfer archive or installed supervisor. There is no executable host/approved
run command yet. The host must bind the exact guest, explicit permission, security
read-backs and a durable one-attempt record before its invocation can be reviewed.
That remains part of existing observer stage 3; Step 1 is not closed and Step 2
VM changes must not start. No native/VM operation or extra startup test occurred.

### Compiled Host Candidate For Review

The subsequent continuation supplies the separate host candidate in
`governance_v2_observer_host_review.md` and its successor JSON. The frozen library,
helper, reference and base bundles remain unchanged. Source/fixture checks now
cover explicit manifest/VM permission binding, a single-use callback, an exclusive
local claim before dispatch and sanitized persisted outcomes; the actual host
was not executed. Its command format and disabled template are review artifacts,
not A-D permission. The local claim survives host restart, not snapshot restore;
the out-of-band ordered attempt reservation must remain outside the guest and
baseline disk. Review this candidate, then continue the existing Step 2 exact
preparation-impact decision. Console/baseline rehearsal and Step 4 security/
execution approval remain separate; no VM changes or startup experiment occurred.

### Step 1 Accepted; Step 2 Inventory Pending

2026-10-17: the user explicitly reviewed and approved the compiled host candidate.
The dated acceptance in `governance_v2_observer_host_review.md` binds the unchanged
review-record hash and closes Step 1 local preparation, including the observer's
Stage 3 candidate review. Frozen records retain their original labels. Native
operation, Gate A and production are not accepted by this decision.

Current work is Step 2: gather the actual VM/disk/console inventory and prepare
an exact impact/cost/rollback disclosure for permission. Screenshots supplied
earlier remain historical observations, not a verified current inventory. The
agent has no established Azure management or guest session in this task; request
read-only Overview, Disks and Serial Console observations before assuming cloud
access or preparing exact resource changes. Do not ask for passwords, SAS links
or cloud administrator credentials. No guest collector, CLI installation, console
enablement, security/boot/NIC change, transfer, snapshot or startup is authorized
by this acceptance. Present missing facts as unknown, not estimated identities.

## Step 2 Observations And Preparation Impact Draft

2026-10-17: the user supplied current VM Overview, disk Overview, disk Encryption
and SAC screenshots, plus guest command output. These are user-supplied evidence,
not an agent Azure API inventory. The user then requested continuation of this
impact proposal, not execution of changes. Exact resource/operator identifiers
are kept in the ignored local preparation record, not copied into this runbook.

| Item | Supplied Observation | Remaining Limit |
| --- | --- | --- |
| Compute | Existing VM running in East US, Zone 1; Standard_D2as_v4, 2 vCPU, 8 GiB | Actual resource IDs, current charge plan and Windows client licensing not independently verified |
| Guest | Windows 11 Pro; command prompt build 26300.9711 | Full patch inventory, hardware UUID, operator SID, session and adapter GUIDs still need private read-back |
| Console | SAC initialized; user authenticated; local account; administrator-role check True | Offline NIC/control rehearsal has not run |
| Disk | Attached 127 GiB OS disk, Premium SSD LRS, P10, Trusted Launch | Generation/VMGS and exact snapshot/restore metadata must be verified before creating a replacement |
| Azure encryption | Platform-managed key selected | This does not establish guest BitLocker or encryption-at-host settings |
| Guest encryption | C: reports 126.45 GB, used-space-only encrypted, 100%, XTS-AES 128, Protection Off, Unlocked, no key protectors | Preserve the exact state; do not add protectors, activate, suspend or decrypt BitLocker |

No deliberate boot-disk, boot-setting or encryption change was performed. A
running guest may still write logs/update state; these observations do not prove
byte-identical disk contents. No snapshot, disk swap, VM payload deployment or
startup comparison has occurred. SAC already works, so no EMS enablement/reboot
is proposed just to obtain console access.

### Bounded Proposed Impact

This refines the existing proposal, not the four-case budget or approved runtime:

1. After transfer/licence/identity prerequisites and permission, place only the
   reviewed Python-only kit, frozen helper/reference, observer host/library and
   required notices under `C:\MayaGateA`. Keep authorization and attempt records
   outside child private state; no live authorization is present in the baseline.
   Do not install Maya/Hermes, an Azure SDK, build tools, a debugger, drivers,
   services, customer data or provider/connector credentials in the guest.
2. Preserve Trusted Launch, Secure Boot, vTPM, existing VM identity and the
   supplied encryption configuration. Record originals; do not clear/unlock TPM,
   change security type, account identities or licensing to make restore work.
3. With separate preparation permission, cleanly shut down and deallocate before
   a full Standard LRS baseline snapshot. This planned downtime disconnects RDP
   and SAC until restart. Keep the existing OS disk; do not delete or resize it.
4. The separately approved prerequisite rehearsal would create one matching
   127 GiB Premium_LRS/P10 replacement disk from that snapshot, swap it onto the
   same deallocated VM and start it. Verify the marker round trip and unchanged
   guest/operator/inputs/security. Restore operations must preserve the actual
   Trusted Launch/VMGS requirements. No boot repair, security downgrade or retry
   follows a failure. Exact original disk reattachment is a proposed rollback
   requiring permission, not an automatic swap on failure.
5. A successful rehearsal permits a later execution decision, not the A-D tests
   themselves. The existing three between-case resets would create three further
   disks, one each for B/C/D. At most four new disks, one baseline snapshot and
   the existing VM are contemplated. Retain the original disk and any uncertain
   case disk. No deletion, second VM, additional snapshot or resource-group change
   is authorized by this draft.
6. The existing single inert NIC round trip still needs separate rehearsal
   approval: guest non-loopback adapters only, through working SAC, with read-back
   before any reconnect. Do not detach Azure's primary NIC, change shared NSGs,
   add a public service or automatically reconnect on timeout. LPAC/WFP/filesystem/
   SideBySide/capability changes belong to the separate final execution decision.

Proposed new snapshot/disk names, subject to collision and metadata verification:
`maya-gatea-26h2-baseline-20261017`, `maya-gatea-26h2-rehearsal-20261017`, and
`maya-gatea-26h2-case-b-20261017` / `case-c` / `case-d` using the same full prefix.
If an object already exists, stop; never overwrite/adopt it or silently choose
another name. Region stays East US; replacement disks must match Zone 1 and all
required disk security/encryption properties. No resource has been created.

### Cost Evidence And Proposed Review Envelope

Microsoft's unauthenticated [Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices)
was queried on 2026-10-17 for East US USD Consumption rates, without Azure login
or resource access. This provides retail estimates, not an invoice/credit audit:

| Meter | Returned Rate | Budget Use |
| --- | --- | --- |
| Premium SSD Managed Disks, P10 LRS Disk | USD 19.71 / month per disk | Each new 127 GiB replacement remains in the P10 tier |
| Standard HDD Managed Disks, Snapshots LRS, LRS Snapshots | USD 0.05 / GB-month | Full Standard LRS snapshot; actual billed used size unknown |
| General Block Blob v2, Hot LRS Data Stored, first tier | USD 0.0208 / GB-month | Only if the separately approved transfer method uses this storage |
| Dasv4 D2as v4, non-Spot base compute | USD 0.096 / hour | Matches the earlier portal indication; actual Windows client entitlement/offer is not established |
| Dasv4 D2as v4 Windows, non-Spot | USD 0.188 / hour | Alternative published Windows meter for sensitivity only, not a quote or licence for this Windows 11 VM |

Arithmetic uses 730 hours/month for planning. Four new disks retained for 24 hours
cost about `4 * 19.71 * 24 / 730 = USD 2.59`. Allowing 138 decimal GB for a snapshot
capacity estimate (conservatively covering the 127 GiB disk, not measured usage)
adds about `138 * 0.05 * 24 / 730 = USD 0.23`. Thus additional disk/snapshot storage
is approximately **USD 2.82 for 24 hours**, before taxes/other meters. Retaining all
four replacements is deliberately budgeted; no deletion permission is presumed.

Including the existing P10 disk and 24 hours of running compute gives illustrative
totals of about USD 5.77 at the base meter or USD 7.98 at the alternative Windows
meter, before public IP, transfer, transactions, taxes and other existing charges.
These are sensitivity estimates, not a claim that either compute rate applies to
the actual client licence. No paid plan/offer or entitlement is changed or certified.

Recommend a **USD 10 planning allowance for one 24-hour work window**, subject to
portal cost confirmation and explicit approval. This is not an Azure-enforced
cap, a spending-limit setting, permission to charge USD 10, or permission to let
resources accumulate for a month. At 24 hours stop new allocations/work and review
retention/cost; retained disks and snapshots still accrue charges. Do not silently
delete evidence to meet the estimate. Deallocation stops compute charges but
storage and some networking charges continue. Sources:
[managed-disk pricing](https://azure.microsoft.com/en-us/pricing/details/managed-disks/),
[snapshot used-size billing](https://learn.microsoft.com/en-us/azure/virtual-machines/snapshot-copy-managed-disk),
[VM state billing](https://learn.microsoft.com/en-us/azure/virtual-machines/states-billing).

### Transfer And Exact-Approval Prerequisites Still Open

The immutable base contains 803 files including its manifest, totalling
36,640,963 bytes. The frozen reference, host and library add 226,304 bytes; a
future reviewed kit is approximately 36.9 MB before notices and packaging.
An archive/expanded-size ceiling of 64 MiB is proposed, not measured archive size.
Do not upload the whole repository, source checkouts, test executables or build
output directory. No transfer archive has been assembled or uploaded.

Inspection found no LICENSE/COPYING/NOTICE-named files in the frozen base. The
pinned Microsoft reference checkout contains its MIT notice; matching Python
and bundled-library notices/provenance must also be resolved and supplied as
separate disclosed sidecars in a new kit, never by rewriting the frozen base.
This is the previously listed sharing prerequisite, not a new startup experiment
or an assertion of infringement. Exact notices/artifact inventory and any relevant
redistribution restrictions require review before external transfer.

No dedicated storage account/container/blob or safe secret-input transfer tool
has yet been selected/reviewed; do not create one from a generic instruction to
proceed. The exact transfer resource/access/retention/cost disclosure and approval
remain mandatory. No SAS/password/cloud token belongs in Git or shared screenshots.
No VM CLI/SDK or cloud login is required merely to read public prices.

Before requesting operational approval, finish private resource-ID/security
metadata and guest inventory binding, notice/transfer review, exact resource
names and original-state/rollback capture. The supplied screenshots are enough
to size this proposal, not to populate the host's final execution manifest.
Ask for only the remaining relevant read-only facts together; do not turn this
into an open-ended diagnostic or start changing settings while facts are missing.
Preparation, the one rehearsal and A-D execution remain separate approvals.

Trusted Launch's VMGS is associated with the OS disk, and unusable/locked guest
state can prevent restoration. Nothing in the BitLocker output guarantees a
successful snapshot boot. Preserve the stop rule rather than weaken security:
[Trusted Launch FAQ](https://learn.microsoft.com/en-us/azure/virtual-machines/trusted-launch-faq),
[OS-disk compatibility](https://learn.microsoft.com/en-us/azure/virtual-machines/windows/os-disk-swap).

### Notice Sidecar Prepared - 2026-10-17

At the user's request, the separate notice collection is now in
`docs/third-party/governance-v2-python-comparison/`. It retains nine original
Python, Microsoft reference-launcher and bundled-library notice files with
source/version records and byte hashes in `notices-manifest.json`. All 796 frozen
Python files match the installed distribution supplying the Windows licence.
No bundled Python or native payload was executed for this comparison.

The notices belong beside a future reviewed kit, not inside the frozen base.
The base manifests, runtime/helper/reference binaries and frozen observer review
inputs are unchanged. This completes creation of the notice files, not legal
clearance or transfer approval. Applicable redistribution conditions and exact
archive/transfer review remain open. No cloud resources, VM settings, snapshot,
disk swap, upload or test run are authorized by this housekeeping task.

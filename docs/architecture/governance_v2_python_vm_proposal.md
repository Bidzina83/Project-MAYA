# Python Comparison VM Impact And Permission Proposal

## Status

2026-10-16: preparation proposal only, following the user's instruction to proceed
after committing the Python-only reproduction. The
[comparison contract](governance_v2_python_comparison.md) and
[four-case JSON](governance-v2-python-comparison.json) remain unchanged historical
inputs. The user subsequently approved document-only replacement of the planned
OS baseline with 26H2. The active environment revision is the
[26H2 addendum](governance_v2_python_comparison_26h2.md) and its successor JSON.
No VM provisioning, capability experiment, reference build, token observer,
comparison run, external publication or renewed workstation diagnosis is approved
by this document. Gate A remains blocked.

## Read-Only Checks

- Branch: Maya-Governance-Integration-V2; working tree was clean before this proposal.
- Commit: d393d87593f2a974406ab652bc0652cbfe30fdcb.
- GitHub reports successful Workflow lint, Example caller for ingest workflows and
  CI Diagnostics runs for that commit. These three workflows are not a new native
  qualification result or proof that every product test runs on this branch.
- Host registry: Professional, 26H2, build 26300, UBR 9711. Win32_OperatingSystem
  independently reports version 10.0.26300. This is newer than the frozen failing
  environment; it does not retroactively explain the retained failure.
- Hyper-V module is available; vmms and vmcompute services report Running;
  HypervisorPresent is true. No feature/service/network change was performed.
- Physical RAM is approximately 8 GB, eight logical processors. Observed free
  physical memory was 938796 KiB, approximately 0.9 GiB, at this one observation.
- C: had 279671431168 free bytes, approximately 260 GiB, at inspection.
- Existing VM inventory could not be read (VirtualizationException). Do not infer
  that there are no VMs, or modify any existing VM to obtain resources.
- Availability of matching installation media or an existing clean guest is unknown.

## Recommended Placement And Resource Envelope

Do not start a Windows guest on the current host under the observed memory load.
Prefer an existing customer-controlled test host with sufficient spare memory,
or wait for the operator to provide adequate headroom on this host. Do not close
applications, terminate processes, stop existing guests or purchase resources
automatically. This is test infrastructure, not a changed Maya deployment target.

Proposed single guest: two virtual processors, 4 GiB fixed RAM, an 80 GiB dynamically
expanding virtual disk, and one clean baseline checkpoint restored between cases.
Allow up to 120 GiB of planning space for disk, checkpoint and reviewed transfers;
this is a proposed monitored budget, not an enforced storage quota or an assurance
that checkpoint growth cannot exceed it. Confirm free memory/disk immediately before
allocation and stop rather than increasing the approved resource budget.

These are proposed laboratory allocations, not Maya product requirements. Microsoft
lists 4 GB RAM and a 64 GB storage device as Windows 11 minima:
[Windows specifications](https://www.microsoft.com/en-us/windows/windows-11-specifications).
Meeting minima alone does not establish acceptable host or guest performance.

## Required Guest And Media Decision

The planned guest is Windows 11 Pro 26H2 AMD64, build 26300, UBR 9711, based
on the earlier host observation; no matching guest/media has been verified.
The user confirmed having 26H2, not possession of a clean VM or installation ISO.
The original failed 25H2 build 26200.9457 remains historical evidence only.
The host need not run the guest's build, but the guest must be verified before
comparison; results must not be called reproduction of the original OS failure.
Record the operator-provided VM/image/ISO provenance, SHA256, installation and
servicing inputs, valid usage rights and supported setup method. No image source,
download size or licensing entitlement is assumed or accepted on the user's behalf.

Historical media lead only, not an instruction for the revised 26H2 guest:
Microsoft identifies KB5129195 as the update delivering build 26200.9457 for
Windows 11 25H2. Its x64 instructions list checkpoint KB5043080 before the target
update, subject to the checkpoint already being present:
[Microsoft installation instructions](https://support.microsoft.com/en-us/servicing/os/windows-11/2026/09/kb5129195-windows-11-24h2-25h2-security-update).
This is an official servicing lead, not a verified matching base image or proof
that an arbitrary newer image can be downgraded to the target. Confirm compatible
25H2 base media, applicable package ordering, signatures and SHA256 values before
proposing downloads or installation. No package was downloaded or installed.

If only another build is available, stop for an explicit changed-environment
decision. Do not silently revise JSON, download unofficial archived images or
downgrade the workstation. Do not bypass Windows setup, activation, TPM or account
requirements to manufacture a matching guest. No personal account sync, customer
credentials, tenant enrollment or cloud resources belong in this fixture.

## Impact Requiring Explicit Permission

The following is the proposed approval envelope, not an execution instruction:

1. Create/import one identified disposable guest in an operator-approved local
   directory. Disclose the exact disk/checkpoint paths and resource allocations.
   Do not alter existing guests, global Hyper-V settings, boot configuration,
   networking or host Windows features. Any required host feature enablement or
   reboot needs a different impact decision.
2. Use a supported Windows guest configuration, with any guest-only Secure Boot/
   virtual TPM state kept outside the repository. Obtain consent before downloads,
   installers or generation of guest account/VM security material. Never pass raw
   account passwords through command-line arguments, manifests or logs.
3. Supply only reviewed fixture artifacts. During comparison disconnect the guest's
   network adapters and use no host-folder mounts, clipboard, drive/device or
   credential redirection. Do not enable enhanced-session sharing or Guest Services
   file-copy integration. Package transfers into the guest and sanitized evidence
   extraction must be specified before execution, without exposing host data to the
   restricted process. Microsoft documents enhanced-session resource sharing:
   [VMConnect sharing](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/enhanced-session-mode).
4. Separately approve the existing eight SID-scoped deny filters, disposable LPAC
   profile, private-folder permissions, loopback exemption and exact non-inheriting
   SideBySide ReadKey grant INSIDE the guest only. Capture that guest's original
   descriptors; do not reuse the workstation rollback snapshot.
5. Separately approve VM-only registryRead in C and registryRead plus lpacCom in D.
   These capabilities may expose additional guest registry/COM surfaces. The VM
   must contain no customer data. Success grants no permission to enable those
   capabilities in Maya or on the workstation.
6. Specify VM shutdown, checkpoint reset, exact descriptor/resource cleanup and
   evidence retention. Guest deletion is not approved in advance: confirm the
   exact new VM/files and retain required evidence before any destructive cleanup.

## Prerequisites Still Open

Before any A-D run, provide and verify matching 26H2 guest/media, obtain the above
permissions, build/hash the pinned unmodified Microsoft reference, and implement/
review the external child-token/lifecycle observer and execution manifest. This
proposal does not silently authorize those implementation or build steps. The
existing preparation script/bundle remains bound to 25H2. A reviewed explicit
successor-contract binding and fresh output must be approved before preparing
new artifacts; never relabel or rewrite the historical bundle.

The budget stays exactly one A, B, C and D run, in order, one findings report,
100 seconds per case and no automatic retry, correction or additional profile.
Missing resources, unavailable exact media, failed permission/token read-back or
an uncontrolled difference is a stop, not a passing test or permission expansion.

## Immediate Decision Requested

Identify the test host and matching clean guest or official installation/servicing
media first. The user has been asked for its location or confirmation that none is
available. The user confirmed 26H2 but has not supplied media or VM paths. Once
known, present the actual provisioning paths, downloads and impact
for explicit permission. Do not start comparison execution from a generic Proceed.

This revision changes documentation/contracts only. No VM was created, started,
stopped or modified;
no capability or registry/network permission was changed; no payload was executed.

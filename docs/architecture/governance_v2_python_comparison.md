# Python-Only LPAC Comparison Contract

## Status And Approval Boundary

2026-10-16: the user approved preparation of a minimal Python reproduction and
the exact four-case comparison contract recommended after the consumed
[loader diagnosis](governance_v2_loader_diagnosis.md). This is the next strategic
preparation step under [plan revision 2](maya_governance_integration_plan_v2.md),
not renewal of the previous workstation diagnostic allowance.

Preparation only is authorized. No VM is provisioned, capability added, native
comparison executed, reference binary built, installer changed or report published
by this step. VM impact/provisioning, broader VM-only diagnostic capabilities and
external sharing each require separate explicit approval. Gate A stays blocked.

## Narrow Question And Inputs

Can the exact prepared CPython start under LPAC, and which launcher/profile
differences correlate with the recorded activation failure? This is not a Hermes
test, a new execution runtime, a sandbox escape assessment or product qualification.

The machine-readable contract is [governance-v2-python-comparison.json](governance-v2-python-comparison.json).
Freeze its SHA256 and the derived bundle manifest SHA256 before execution. Retain
the old failed reports and original input hashes unchanged.

- Original managed-runtime manifest:
  `0ed977a4f7269ec86d01468e19820d616fc4e74cacd21b2919131d88457a5b32`.
- Unchanged Maya helper executable:
  `e72f101bea8222d14e908c2f39e7fecdca122b2f13b2abe9d5293490b7856f63`.
- CPython: 3.13.14, AMD64; every recorded file under runtime/python is retained
  byte-for-byte, including Lib and DLLs. This minimizes the application workload,
  not the standard-library artifact set. No Python binary/manifest rewrite.
- Microsoft SandboxSecurityTools commit:
  `8102bfc8dc3e244ec08e8204bd7d989e26a016e4`; exact launcher source hash is in JSON.
  The launcher must be built unmodified, with toolchain, SDK, project inputs and
  resulting executable hash recorded before execution. No latest-branch execution.
- The derived bundle includes only Python artifacts, the unchanged Maya helper,
  a new tiny Python-only worker and this contract. Hermes, project_maya, third-party
  site-packages, customer config, old state, secrets and raw traces are excluded.

The bundle is local-only. Its prepared Python artifacts have not received a new
redistribution/license-disclosure review; do not publish the bundle or assume it
is a supported product payload.

## Reproduction Preparation

`scripts/prepare_governance_v2_python_repro.py` performs no network access,
subprocess execution, security provisioning or application imports. It verifies
the frozen manifest/helper hashes and exact Python file inventory, rejects
reparse paths and generated/startup files, and requires a fresh ignored output.
Partial preparation without a completed manifest is invalid; never reuse it as
successful evidence or automatically overwrite/delete it.

```powershell
.\.venv\Scripts\python.exe scripts/prepare_governance_v2_python_repro.py `
  --output .codex-build/governance-v2-python-repro-20261016
```

The output root is a future VM workspace, with the unchanged helper's expected
`.codex-build/governance-v2-lpac-stage` and native-tools layout inside it. The
original stage is never overwritten. Only the derived worker is replaced with
`scripts/governance_v2_python_probe.py`; that adaptation is declared in its manifest.
Empty state and host directories contain no workstation rollback descriptors.

The probe requires Python 3.13.14 and `-I -S`, imports only sys/time, exclusively
creates a fixed `python-startup.json` in its working directory, prints that same
fixed beacon, holds for five seconds for external token observation and exits.
It does not read stdin, credentials, environment values, business files or any
Maya/Hermes API. An old marker, bad flags/version or failed write is not success.
The marker says only python_entered, never healthy/contained/qualified.

## VM Preconditions And Execution Gate

Before any run, separately approve the VM's licensing/download/storage impact and
the exact security changes below. Use one disposable, snapshotted Windows VM with
no customer data, keys, account sync, mapped host folders, shared clipboard,
redirected drives/devices or credential integration. Disconnect its network
adapters during comparison. Transfer reviewed artifacts before disconnection.

Match the observed Professional 25H2 AMD64 build 26200, UBR 9457. Record OS API
version, servicing inventory and relevant initial ACLs. If that exact image/build
is unavailable, stop for a changed-environment decision; another build is not an
equivalent reproduction. Do not upgrade/downgrade the user's workstation.

Freeze a separate execution manifest containing VM identity/snapshot, operator
SID, VM workspace, derived package SID, input/contract hashes, reference binary
and build hashes, environment/cwd/command line, token observer and cleanup methods.
No operator paths or identifiers belong in public reports.

The external token/lifecycle observer is NOT implemented by this preparation.
Its executable/hash and how it captures the selected child PID, user, package,
integrity, capability SIDs and LPAC positive/negative controls must be reviewed
before execution. The probe's five-second hold is an observation window, not a
substitute for that evidence. Missing observation makes the case uninterpretable.
No Python-entry marker can establish the token or containment by itself.

## Frozen Four-Case Matrix

Exactly one ordered run per case, A then B then C then D. Reset to the same clean
VM snapshot between cases, and recreate the same workspace/user/package identity.
No retries, additional profiles, second OS build or automatic correction. The
timeout is 100 seconds per case, including child cleanup, followed by one report.
Provisioning failure or an uncontrolled difference stops the comparison; it is
not a passing startup denial.

| Case | Launcher | Additional Token Capabilities |
| --- | --- | --- |
| A | Byte-identical Maya helper | None |
| B | Unmodified pinned Microsoft launcher | None |
| C | Same Microsoft binary | registryRead |
| D | Same Microsoft binary | registryRead and lpacCom |

All rows retain privateNetworkClientServer, the same eight SID-scoped WFP deny
filters for port 18765 and the earlier profile-specific loopback exemption; no
broker listener runs. Grant prepared runtime RX and private state Modify/Low IL
only. All rows receive the same exact, non-inheriting package-SID ReadKey grant
on the 64-bit SideBySide key, captured/restored against that VM's descriptor.
This selects the previously observed 0xC0150002 profile, not the earlier ungranted
0xC0000022 control. Do not import the workstation's rollback snapshot into the VM.

The unchanged Maya helper defines the package identity from VM workspace/user and
owns the common provisioning/cleanup. Use that exact moniker for B-D so the WFP
and filesystem grants apply to the observed token. A different package/SID, failed
filter read-back, or capability mismatch blocks interpretation.

Use the helper from the VM workspace root in A. In B-D launch the reference from
the empty private state directory, with its parent environment restricted to the
same eight names in JSON and VM-local values matching A. HERMES_HOME is merely
the helper's private-path variable; no Hermes code or state is included.
The intended child command is quoted Python plus `-I -S` and the absolute derived
worker path. The reference passes its `-i` argument as a command line; verify the
actual child command/cwd rather than relying on the usage label alone.

## Reference Differences That Cannot Be Hidden

The pinned [Microsoft source](https://github.com/microsoft/SandboxSecurityTools/blob/8102bfc8dc3e244ec08e8204bd7d989e26a016e4/LaunchAppContainer/LaunchAppContainer/LaunchAppContainer.cpp)
uses CreateProcessAsUser, inherited environment/cwd and a new console, without
Maya's suspended verification/job/pipe setup. It also writes HKCU Console's
LowBoxConsoleEnabled value. Capture whether that key/value existed, its type/data
and restore it exactly inside the VM; creation must also be reversed when absent.
Do not enable `-k` just to change output handling: that adds a mitigation difference.

Use `-l` and `-w`, but not `-r`: the pinned cleanup condition deletes the profile
when both wait and retain flags are true. External VM provisioning/cleanup must
own that lifetime. A's token controls include an ordinary suspended comparison;
that control is not an authorized ordinary-mode fallback.

These differences are declared confounders, not a fair single-variable proof of
a helper defect. Reference success with A failure points to a launcher/context
compatibility lead. No conclusion may silently replace Maya's restrictions with
the reference launcher's weaker lifecycle controls.

## Required Evidence And Decision

For each case record preparation/launch result, selected PID/token/capabilities,
actual command/environment names/cwd, native child exit code, fresh beacon/hash,
deadline result and cleanup read-back. Launcher exit zero alone is insufficient.
Reference stdout PID is not the child exit code. Do not invoke a debugger or add
extra diagnostic captures within this matrix.

Only a fresh exact beacon, child exit zero, expected version/flags and externally
verified intended LPAC profile establish Python startup under that case. Capture
partial beacon/exit/token outcomes as partial or invalid, not success. Stop all
remaining runs on exposure, unknown privilege, cleanup failure or scope mismatch.

- A fails/B works: launch-context compatibility lead, not a proved code defect.
- B fails/C works: registryRead correlates with compatibility in the test VM;
  exact necessary accesses and a customer-safe alternative are still unknown.
- C fails/D works: adding lpacCom correlates with compatibility; not permission
  to grant COM or registry access in Maya.
- All fail, or results are invalid/inconsistent: no safe startup path established.
  Retain the minimal reproduction for specialist/vendor review, without posting it.
- Any works: startup only; Hermes, native memory/SSE, networking protection and
  all A01-A20 product obligations remain separate and unqualified.

At the end, issue one pass/partial/blocked findings report and stop. Without a
credible narrowly scoped path, recommend rejecting the current LPAC candidate
for the frozen inputs and seek a new architecture decision. No automatic
alternative, Hermes patch sequence, product activation or installer rebuild.

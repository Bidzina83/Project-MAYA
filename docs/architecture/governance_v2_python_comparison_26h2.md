# Python-Only LPAC Comparison - 26H2 Environment Revision

## Approved Change And Limits

On 2026-10-16 the user approved document preparation changing the planned
comparison baseline to Windows 11 Pro 26H2. This is the active environment
revision under Gate A of [Plan V2](maya_governance_integration_plan_v2.md).
It is not permission for downloads, VM provisioning, reference compilation,
observer implementation, capability grants, execution or publication.

The [26H2 JSON contract](governance-v2-python-comparison-26h2.json) records the
revised target. The original [25H2 runbook](governance_v2_python_comparison.md),
its JSON, failed reports and prepared bundle remain unchanged historical inputs.
All original probe, artifact, isolation, observation, cleanup, launcher-confounder
and stop requirements apply except for the explicit environment replacement here.
The predecessor hashes are recorded in the successor JSON.

## New Baseline, Not Original-Failure Reproduction

The planned guest target is Professional 26H2 AMD64, build 26300, UBR 9711,
based on the earlier read-only host observation. The user's confirmation of 26H2
does not verify a guest, installation media or servicing inventory. Verify the
guest's exact edition/version/build/UBR and inventory before freezing execution
inputs. A different patch level requires a documented target decision, not a
silent substitution or another automatic matrix.

The original failure occurred on Professional 25H2 AMD64, build 26200.9457.
This revision replaces the planned comparison environment; it does not add a
second OS matrix. Any future result assesses startup feasibility on the verified
26H2 guest only. Success would not explain the old failure, prove an OS update
fixed it, or qualify 25H2, Hermes, containment or Windows product support.

## Unchanged Single Comparison Budget

One ordered A/B/C/D comparison, one run per case, 100 seconds per case including
cleanup, zero automatic retries/corrections and one findings report. Restore the
same clean snapshot between cases. Do not run the historical 25H2 matrix in
addition to this revision under this approval.

| Case | Launcher | Additional Token Capabilities |
| --- | --- | --- |
| A | Byte-identical Maya helper | None |
| B | Unmodified pinned Microsoft launcher | None |
| C | Same Microsoft binary | registryRead |
| D | Same Microsoft binary | registryRead and lpacCom |

The pinned Python/helper/reference source, eight SID-scoped WFP deny filters,
privateNetworkClientServer, loopback exemption, exact non-inheriting SideBySide
ReadKey profile and private filesystem/environment remain as in the original
contract. No broader production permission or new Hermes patch is authorized.
These VM security changes still require separate explicit approval.

## Preparation And Execution Remain Blocked

The existing preparation script still binds the historical 25H2 contract and
runbook. Do not run it and label its output a 26H2 bundle, change the old bundle's
manifest, or substitute this JSON without updating its recorded input hashes.
No script or prepared artifact is changed by this document-only approval.
Before any new bundle preparation, review an explicit successor-contract binding
and fresh-output approach. That implementation needs separate approval.

Before execution, obtain matching supported media/guest and usage rights, confirm
sufficient host RAM/disk, disclose actual provisioning/transfer paths and impacts,
obtain VM/security permissions, build/hash the pinned reference, review the
external child-token/lifecycle observer and freeze the execution manifest and
new bundle/contract hashes. Missing inputs stop the process, not a passing denial.
Keep the guest disconnected during comparison with no host sharing or secrets.
Do not use the workstation itself as the substitute test environment.

The earlier observation of approximately 0.9 GiB free RAM on an 8 GB host does
not establish capacity for the proposed 4 GiB guest. No process termination,
host upgrade/downgrade, purchase or deployment change is authorized.

Next is identifying usable media and a host with adequate capacity, then a
specific provisioning/remaining-preparation permission decision. Consult the
[VM impact proposal](governance_v2_python_vm_proposal.md). No execution occurred;
Gate A and production activation remain blocked.

# Customer-Like Windows Product Testing

## Decision And Scope

On 2026-10-18 the user directed testing in an environment resembling a potential
Windows 11 Pro customer's machine, then clarified that Maya may request needed
permissions, but must do so itself. This supersedes the operational instructions
in the [manual diagnostics](governance_v2_python_manual_diagnostics.md) and
[Azure procedure](governance_v2_python_azure_procedure.md), not their evidence.
It is the active test method within [Integration Plan V2 Gate A](maya_governance_integration_plan_v2.md).

The workflow is: retain the declared Windows baseline, copy/install the selected
component, run it through Remote Desktop, collect its output and analyze the
result. Do not build additional transfer, supervisor, observer or test-runner
software as a prerequisite. The operator performs VM actions; this chat has no
direct guest session. No passwords, cloud credentials or new remote-access agent
are needed by this decision.

The earlier pending A-D security/execution request was not approved. No A-D
attempt was reported. Do not resume it, change its frozen inputs or relabel an
ordinary Windows run as one of its restricted comparison cases. No replacement
matrix, extra startup budget or automatic retry sequence is created here.

## Starting Environment

Keep the existing restored Windows 11 Pro 26H2 guest, build 26300.9711, with its
observed permissions, security and network policies. Do not reset Windows or
change settings merely to assert that they are defaults. This is one declared
customer-like environment, not proof of the configuration of an average customer
or of support across all Windows installations. Record material differences,
including Azure hosting, the existing administrator account and RDP execution;
an administrator session does not qualify standard-user consent behavior.

No test-only preparation of filesystem/registry ACLs, integrity labels, WFP
filters, AppContainer grants or loopback exemptions is allowed to make a run pass.
Do not disable antivirus, firewall, Secure Boot, vTPM, encryption or ordinary OS
protections. Keep the existing IP-restricted RDP access; do not expose new public
listeners or broaden Azure access. Guest networking stays in its ordinary state;
no adapter-disable/SAC-only rule applies to this workflow. Serial Console remains
available for recovery, not the required normal launch channel.

Keep synthetic test data and customer-controlled diagnostic output. This decision
does not authorize live provider/connector credentials, real customer data or
external publication of evidence. Retain the original disk and baseline snapshot
as rollback resources. No additional rehearsal, per-case disk swap, cloud
allocation, resource deletion or automatic recovery is required or authorized.

## Product-Owned Permissions

Maya's actual setup/runtime component must:

- Detect and explain needed permissions, elevation or OS prerequisites before
  changing them; obtain explicit informed user consent through the product's
  supported setup flow, not an instruction to perform ad hoc OS configuration.
- Apply only the approved scope, validate the effective result and report what
  was changed. Required OS/API restrictions and unsupported environments must
  be reported accurately rather than hidden behind a readiness success.
- Handle refusal and provisioning failure by blocking the affected operation.
  Do not silently retry with broader rights, suppress protection failures or
  switch to an unrestricted runtime.
- Own supported cleanup/rollback or clearly report partial/uncertain changes
  and the supported recovery action. Preserve unrelated existing configuration.

An elevation prompt alone is not an explanation of the scope of security changes.
The product may request permissions; this workflow approval is not advance
consent to every future request or permission expansion.

The present Gate A native helper and frozen Python/reference bundle are
diagnostic artifacts, not an established customer installer. Manually invoking
their provisioning commands is not evidence of product-owned consent/setup.
If the needed product entry or permission lifecycle is absent, report and address
that bounded product gap under the existing implementation/impact approvals.
Do not substitute another lab helper or claim a stub is installed enforcement.

## Execution Order

1. Identify the exact bounded component/artifact, version/hash, normal setup/start
   entry, purpose, expected result and required permission scope. Use existing
   product entry points; do not invent a parallel runtime or testing framework.
2. Prepare that product component within its approved implementation scope, then
   have the operator copy/install it into the VM through the normal customer
   path. Any needed permission must be requested and applied by the component.
   Preserve applicable artifact, security-impact and execution approvals.
3. Have the operator run it through RDP using the intended customer launch path.
   Ordinary execution should not require an elevated terminal merely because
   the lab account can elevate. Collect the actual result, exit/failure state
   and applicable consent/setup records without exposing secrets.
4. Analyze the result against the declared component criteria. A refused or
   failed prerequisite is meaningful evidence, not permission to precondition
   the OS. Report a product gap and obtain approval before changing scope/order,
   adding another diagnostic, widening rights or modifying runtime artifacts.

A standalone dependency startup result proves only that dependency started.
An accepted permission prompt does not prove restricted execution. Customer-like
product acceptance requires useful execution and required denied/bypass cases
through the actual product path, without manually supplied lab prerequisites.

## Unchanged Protection And Release Gates

The [restricted execution contract](restricted_hermes_execution_contract.md)
still applies. Product-owned permission setup does not replace Maya authorization,
grant direct access to customer files/provider credentials or qualify an ordinary
Hermes launch as governed. Missing protection must block startup or the affected
operation. Gate A remains open; Gates B-E and production activation remain
unchanged. No runtime pin change, old patch removal, wheel/installer rebuild or
production/platform qualification is authorized solely by this workflow decision.

The subsequent specific first-package preparation request is recorded in
[Maya protected Python startup](maya_protected_python_startup_package.md).
It prepares one product-owned offline startup component, not the full installer
or another test framework. Its security changes and VM execution remain subject
to the component's explicit informed consent; native behavior is not locally run.

The package 3 report identifies a nonzero elevation flag before child resume.
The approved package 4 correction constructs and checks a reduced same-user
launch token inside the product; it preserves every child-token check and the
existing permission/filter scope. It does not require another account, UAC change,
desktop ACL change or manual VM preparation. No local native launch, fallback or
automatic further correction is approved. The startup package record retains the
failed evidence, exact mechanism and pending native qualification.

The two subsequent Package 4 reports pass pre-resume token checks but fail startup
(timeout, then 0xC0000142), with complete cleanup reported. The separately approved
Task Manager diagnostic produced no dump. The 2026-10-19 continuation approves
preparation of the [bounded loader-diagnostic procedure](maya_protected_python_loader_diagnostic.md)
only. Tool transfer/setup, symbol downloads and one proposed native run remain
permissioned separately. An instrumented result is not normal customer-path or
containment qualification. No protection change or additional framework is added.

The user subsequently approved debugger transfer/setup and matching Microsoft
public-symbol retrieval on 2026-10-19. A standard ZIP preserves existing tool
files; no additional script or installed system component is added. The operator
performs this setup through RDP and returns the symbol-checker output. Its actual
completion is pending; the later debugger-owned Maya/Python run remains unapproved.

The subsequent operator output confirms setup and exact ntdll PDB/DBG matching,
with zero failed symbol files; the supplied guest EXE hash matches Package 4.
The user explicitly approved one debugger-controlled VM run with unchanged
protections and 30-second product wait. Operator capture and cleanup results are
pending; this is not approval for another attempt, correction or security grant.

The single debugger run is now reported and its allowance consumed. The copied
log verifies tracing in the matching Python child, not the original DLL-init
failure's cause. Manual debugger pauses can compete with the unchanged product
deadline; the operator reports timeout and complete cleanup. This is inconclusive
diagnosis, not evidence for changing customer Windows permissions or DLLs. Final
debugger exit/closure remains unrecorded. Establish the current session state
before closure guidance; no new run, timeout change, grant or rebuild follows.

The subsequent screenshot shows CDB returned to PowerShell after normal Maya
closure. The final log adds only visualizer unloading, not new startup evidence.
Session closure is resolved; cleanup remains operator-reported and the failure
unlocalized. No further closure/capture steps or new run are authorized or pending.

On 2026-10-20 the user approved the source-review recommendation for Package 5's
process-local critical-error handling and stopped-child timeout evidence only.
See the startup package record. No machine permission/policy, payload, protection
or deadline changes are included. Preparation/inert checks are not approval for
a new VM run or diagnostic capture; product consent and the existing stop gates
still apply. The missing-journal recovery issue remains outside this correction.

The operator then supplied Package 5's matching-hash result, recording product
consent and a natural pre-cleanup 0xC0000142 exit, not a timeout. Complete output
capture measured zero stdout/stderr and no startup beacon; cleanup is reported
complete. Preserve this failed startup result. It does not validate the timeout
branch, localize a DLL/resource or authorize another run, grant or correction.

The user subsequently approved document preparation of the
[automatic loader-capture proposal](maya_protected_python_loader_capture_v2.md)
for review before a run. This is a bounded proposed debugger exception, not a new
normal testing framework or execution approval. Preserve Package 5 and current
Windows settings; exact guest binding and separate native-run consent are pending.

The subsequent separately approved one-run capture is now reported. Its matching
Package 5 child trace localizes 0xC0000142 to KERNELBASE.dll initialization during
DLL_PROCESS_ATTACH, before observed Python runtime loading. The underlying
operation/resource remains unknown; cleanup is reported complete, not independently
qualified. See the [capture outcome](maya_protected_python_loader_capture_v2.md#captured-outcome-2026-10-20).
The diagnostic allowance is consumed. Preserve the customer-like VM and product
protections; no retry, new trace, manual OS preparation or product correction
follows this result.

On 2026-10-21 the user approved the separately versioned Package 7 comparison:
ordinary AppContainer instead of LPAC, retaining WFP and every other startup
protection. See the startup package record for the changed AAP admission predicate,
broader-access consent disclosure, preserved inputs and one normal RDP attempt.
The existing VM is only a test environment; VM/Docker product prerequisites are
rejected. No manual OS conditioning, unrestricted fallback, automatic retry,
debugger, Hermes run or production qualification follows.

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

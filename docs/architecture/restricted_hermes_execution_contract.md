# Restricted Hermes Execution And Customer-Protection Contract

## Status

Approved architectural requirements on 2026-10-14; enforcement implementation,
Windows isolation mechanism and feasibility are unqualified. Follow
[plan revision 2](maya_governance_integration_plan_v2.md), starting at Gate A.
This does not activate governance or authorize patch removal or installer changes.

## Product-Owned Windows Setup

The clarified 2026-10-18 testing decision is
[customer-like Windows testing](governance_v2_customer_windows_testing.md).
Permission prerequisites must be established by the actual Maya setup/runtime
component after informed user consent, not manually applied by test operators.
Start from the declared Windows baseline and use the normal RDP installation/run
path. Do not disable protections or pre-grant access to make startup succeed.
Missing setup, refused permission or failed enforcement blocks the affected
operation; it does not authorize an unrestricted Hermes fallback. A user may
consent to product-required changes, but the product must own their disclosed
scope, validation, failure reporting and supported cleanup/recovery. This is a
requirement, not proof that the current prototype implements that lifecycle.
Customer-protection boundaries below and all qualification gates are unchanged.

## Trust And Authority

The trusted Maya control plane owns identity, local policy decisions, credentials,
authoritative business stores and audit. Hermes supplies execution, context,
skills and native conversations within a restricted local environment. Model
output, prompts, skills and tool results cannot grant authority. Local placement
does not make Hermes entitled to customer files or credentials.

Bind host-authenticated principal, request/job identity, targets, classification,
expiry and cancellation at each protected service. Saved session IDs are routing
data, not authentication. No shared default actor or admin fallback. Concurrency,
multi-owner profiles and background execution require explicit qualified scopes.

## Required Boundaries

- Filesystem: direct writes confined to approved operational storage. Customer
  files, SMB stores, policy, audit, credentials and service data are accessible
  only through authorized Maya interfaces. Resolve links/path escapes safely.
- Network: prevent direct provider, connector and arbitrary external access.
  Mediate all effective model requests, auxiliary calls, retries and fallbacks;
  local model routes still require policy. Evaluate endpoint/model, payload,
  classification, minimization/redaction, consent and budgets before transport.
- Processes: restrictions extend to subprocesses and arbitrary execution. Native
  shell/code, plugins or SDKs cannot recreate unrestricted filesystem/network
  access. Tool menus and environment variables are not containment.
- Credentials: secret values stay in approved local backends/control-plane
  services, never bundled or logged. Any runtime admission credential must be
  narrowly scoped, revocable and unable to become provider or administrator access.
- Services: the existing gateway authorizes every business read/action/write;
  correlate identity, target, approvals, replay/idempotency and actual outcomes.
  Validate tool results before further use or disclosure as applicable.
- Delivery: validate final responses and any enabled streaming before sending.
  Errors, progress, logs and diagnostics cannot bypass disclosure protection or
  expose secrets. No raw provider exceptions or unvalidated interim output.

Missing identity, enforcement, policy or required audit fails closed. Cancellation
revokes future protected operations; an already committed action is reported
accurately. A configured base URL or disabled tool is not evidence of enforcement.

## Operational Storage Exemption

Hermes owns separate customer-local conversations, MEMORY.md, USER.md, caches and
compression state. Confined housekeeping need not obtain per-mutation Maya policy
decisions. These stores remain sensitive, non-authoritative business context,
subject to access isolation, ownership, retention, safe diagnostics, backup and
recovery. No automatic copying into SMB memory. Cross-store access, ingestion,
external disclosure and policy changes remain governed. Qualify native memory
functionality rather than redirecting it into Maya's SQLite/vector store.

## Threat Model And Qualification Register

Gate A must name the actual trusted OS/control-plane/artifact assumptions and
adversaries. Untrusted content, model-generated code, tools, SDKs and plugins must
not bypass protection. Customer administrator/OS compromise and physical access
assumptions require explicit review; no broad adversary exclusion may conceal a
runtime bypass. This is a requirements threat model, not a completed security audit.

Maintain a new-contract coverage register before implementation: boundary,
entrypoint, principal/lifetime, protected effect, enforcement mechanism, allowed
control, bypass/denial/failure test, artifact hash, evidence level and unresolved
assumptions. Existing frozen machine-readable registers remain historical; do
not relabel their outcomes as revision-2 qualification.

Required probes include direct SDK/alternate endpoint access, redirects/proxies,
subprocess/child execution, arbitrary plugins/code, path/link escapes, unauthorized
local services, stale/replayed authority and cancellation/restart. Include useful
allowed controls and actual installed enforcement. No skipped required tests or
configuration-only containment claim can satisfy acceptance.

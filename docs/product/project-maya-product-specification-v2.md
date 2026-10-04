# Project Maya Product Specification

## Version 2

**Product:** Maya the Info Manager

**Project:** Project MAYA / IM AI Employee

**Core execution runtime:** Hermes Agent

**Status:** Approved product architecture specification

## 1. Product Definition

Maya is an installable, governed AI employee for information management. It
works with customer-controlled files, communications, calendars, documents,
persistent memory, workflows, and operational dashboards.

Maya combines:

- Hermes Agent as the execution engine;
- Project MAYA identity, configuration, orchestration, and public API;
- persistent local memory and retrieval;
- local governance and action authorization;
- approved external connectors;
- Metabase for local business intelligence and visualization;
- document processing and optional browser automation;
- installation, diagnostics, backup, and update tooling.

The controlling principle is:

> Customer files, persistent memory, governance records, operational state,
> business data, task state, and secrets remain local and customer-controlled.
> Cloud services may assist with authentication, licensing, updates,
> diagnostics, and optional model inference, but they are not Maya's
> authoritative memory, governance engine, or operational state.

## 2. Editions

### 2.1 Maya Standard

Maya Standard provides a local runtime with guided setup, optional Maya
account and licensing, broker-assisted Google and Slack authorization,
optional Maya-managed model billing, and customer-owned Telegram integration.

The target experience is:

```text
Install -> sign in when required -> connect services -> validate -> start
```

Standard users should not need to create Google or Slack developer
applications when broker-assisted integrations are available.

### 2.2 Maya Enterprise

Maya Enterprise uses the same core runtime and supports customer-owned
credentials, optional or disabled broker participation, offline and sovereign
policy, external secrets infrastructure, configuration import and export, and
customer-controlled networking and updates.

Edition is a policy and capability choice. It must not create a second runtime
implementation.

## 3. Deployment and Trust Model

Target deployment classes are Windows, macOS, Linux, customer-controlled
servers, and containers. A platform is supported only after its installation,
lifecycle, health, backup, restore, update, and rollback paths pass acceptance
tests.

The architecture has four trust zones:

1. Local trusted runtime: Maya, Hermes, memory, governance, secrets access,
   connectors, local API, and audit.
2. Local managed services: Metabase, document processing, browser automation,
   databases, and local models.
3. Customer-approved external services: Google, Slack, Telegram, model
   providers, email, and future connectors.
4. Maya-operated services: OAuth Broker, licensing, update metadata,
   diagnostics, and optional model proxy.

Every trust-zone transition is authenticated, authorized, governed, and
audited.

## 4. Local Authority

The local deployment is authoritative for:

- persistent memory and retrieval indexes;
- governance policies and decisions;
- operational context;
- workflow, task, and Kanban state;
- local files and processed-document indexes;
- configuration and secret references;
- integration tokens where technically possible;
- business and analytics data;
- Maya-managed Metabase state;
- logs, audit records, migrations, and backups.

## 5. Runtime Architecture

### 5.1 Mandatory Flow

```text
Input
  -> local API or connector adapter
  -> identity and input policy
  -> governed context and memory retrieval
  -> Project MAYA Agent lifecycle facade
  -> Hermes Agent runtime and model adapter
  -> proposed response or action
  -> local action authorization gateway
  -> approved connector or local tool
  -> result validation and audit
  -> governed memory-write decision
  -> response
```

No connector, plugin, skill, workflow, model adapter, or broker callback may
bypass local action authorization.

### 5.2 Public API

`project_maya` is the canonical product namespace. Its `Agent` is a lifecycle
facade over a concrete `AgentRuntime`, not a substitute implementation of
Hermes.

```text
created -> starting -> running -> stopping -> stopped
                    \-> failed <-/
```

Startup has defined ordering and rollback. Shutdown releases resources. Failed
components are never reported as loaded or healthy.

### 5.3 Hermes Adapter

The versioned Hermes adapter implements:

- runtime construction and compatibility reporting;
- identity and profile loading;
- session creation and termination;
- model configuration;
- memory-provider attachment;
- skill and plugin registration;
- request execution;
- governance event forwarding;
- health, shutdown, and recovery.

Maya adapts Hermes's existing contracts and does not create parallel fake
runtime, model, memory, plugin, or skill systems.

## 6. Component Profiles

The product uses coordinated profiles:

- `maya-core`
- `maya-metabase`
- `maya-documents`
- `maya-messaging`
- `maya-browser`
- `maya-local-models`

Metabase is included and enabled by default in a normal Standard installation.
Heavy components remain separately managed and health-checked so constrained
or policy-controlled deployments can disable them explicitly.

### 6.1 Included Installer and Source-Controlled Artifacts

Maya-owned, Maya-curated, or Maya-pinned components ship with the installer or
are produced from the Project MAYA source and release process. They may be
updated by the Maya maintainer through normal versioned releases, but they are
not silently pulled from arbitrary local paths at runtime.

Included artifacts cover:

- the `project_maya` core runtime, CLI, configuration, lifecycle, local API,
  doctor, repair, backup, restore, migration, and update-check surfaces;
- the pinned compatible Hermes Agent runtime artifact and the Maya-Hermes
  adapter;
- local governance, authorization, audit, redaction, and policy templates;
- the persistent-memory provider, retriever, registry, migration, and backup
  contracts;
- connector and gateway adapter code for approved services such as Google,
  Slack, Telegram, and future Microsoft Teams integration;
- model adapter, model-egress governance, and local-model configuration
  contracts;
- dependency and readiness contracts for all component profiles;
- approved, allowlisted, sanitized, and versioned Maya skills and plugins;
- document capability adapters and Metabase integration, provisioning, and
  health-check code;
- managed-local service definitions and, for full Standard installers where
  supported, bundled runtime artifacts such as Metabase;
- installer manifests, dependency metadata, software bill of materials,
  signed update metadata, and release provenance.

Included code or artifacts do not imply configured, credentialed, enabled,
healthy, authorized, or supported operation. A connector adapter, skill,
plugin, service integration, or managed-local component may ship with Maya
while remaining disabled until setup, credentials, allowlists, governance
policy, platform checks, and readiness validation succeed.

### 6.2 On-Demand and Customer-Managed Dependencies

Profile-specific heavy dependencies, native applications, customer
infrastructure, and external-service credentials are installed, connected, or
validated on demand. Maya reports their readiness and supplies safe setup
hints, but it does not silently install system software, create customer
tenant resources, or claim support when lifecycle and recovery tests have not
passed.

This restriction does not prohibit a supported Maya Standard installer from
bundling pinned, curated, disclosed, license-compatible, Maya-managed runtime
artifacts such as a managed Python runtime, the compatible Hermes Agent
runtime, Metabase, Java, LibreOffice, or Poppler. Those artifacts must come
from the Maya release process or an explicitly declared artifact input, include
hashes and provenance, install into Maya-owned locations where practical, and
remain subject to setup, health, backup, restore, update, rollback, and
readiness qualification. Missing bundled artifacts must be reported as blocked
readiness rather than healthy operation.

On-demand or customer-managed dependencies include:

- optional Python extras such as document and preview packages installed into
  Maya's managed runtime environment;
- native document tools such as Poppler, LibreOffice, and customer-managed
  Microsoft Office desktop applications;
- browser binaries and approved browser-automation runtimes or drivers;
- Java runtimes, Metabase service runtimes, application databases, and
  analytics data sources when not bundled and managed by a supported Standard
  installer;
- local model runtimes, model artifacts, and OpenAI-compatible endpoints such
  as Ollama, LM Studio, and vLLM;
- customer-owned Google, Slack, Telegram, Microsoft Teams, and future
  connector applications, bots, tokens, OAuth grants, webhooks, scopes, and
  allowlists;
- Enterprise vaults, TPM/HSM integrations, master-key backends, databases,
  networking, certificates, and offline update channels.

These dependencies remain governed by profile readiness checks, connector
contracts, secret-reference rules, local authorization, audit, backup and
restore policy, and platform-support qualification.

## 7. Persistent Memory

Maya distinguishes:

1. A Hermes `MemoryProvider` for session initialization, prompt prefetch, turn
   synchronization, memory tools, and shutdown.
2. A provider-agnostic `Retriever` for normalized persistence and search
   through `upsert`, `get`, `search`, vector query, and related operations.

Key-value `read` and `write` methods are not the persistent-memory contract.

Memory must remain local by default, preserve stable identifiers and
provenance, support trust and retention policy, apply governance to reads and
writes, and expose schema, migration, and health state.

Migrations default to dry-run, require explicit write consent, back up existing
destinations, handle conflicts deterministically, validate results, and
produce audit reports.

## 8. Governance and Authorization

The Maya-owned native Hermes governance plugin adapts model and tool execution
middleware to the local gateway. Observer hooks are not security gates. Runtime
activation requires a qualified fail-closed contract covering main and auxiliary
inference, mandatory middleware, and trusted identity propagation. The current
pinned Hermes runtime does not meet that contract; production qualification
remains blocked. Unknown and unbounded tools are denied. Implementation status
and acceptance work are tracked in `docs/architecture/hermes_native_governance.md`.

The Stage 2a/2b mandatory-dispatch and central auxiliary-call patches are test-only
candidates, not a qualified runtime replacement. They must not unlock activation
or production qualification. Stage 2c adds explicit main-loop mandatory-error
stop handlers plus tool/preflight denial propagation, not full-loop qualification.
Typed denials propagate through the native tool dispatcher and registry; catalog
bridge operations remain blocked in mandatory mode until governed.
The candidate native `tool_result` boundary validates final content, and scoped
generic tool errors use fixed codes. This fork extension is not upstream-qualified.
Scoped provider diagnostic summaries/hooks are redacted and request debug dumps
are suppressed in mandatory mode; streaming/recovery diagnostics remain open.
The initial streaming/recovery/background review records additional activation
blockers in `docs/architecture/hermes_streaming_recovery_background_review.md`.
That source review is not full-loop qualification or authorization to activate.
Patch 8 gates each iteration-limit summary attempt and disables native inner
transport retries in mandatory mode. SDK retries must be zero; unqualified
transports remain blocked. This scoped closure does not qualify the full runtime.
Patch 9 suppresses native early text/reasoning/tail/interim delivery and scoped
conversation display sinks in mandatory mode. It does not validate final output,
observers or persistence; those boundaries and activation remain blocked.
Patch 10 adds a candidate native model-output validator using Maya's gateway.
The finalizer checks content before its saves, after transforms and before
return, but loop-level incremental writes and observers are not qualified.
Activation remains blocked; model-output authorization is separate from egress.
Patch 11 preserves typed mandatory denials through the native compression-summary
consumer and observer dispatcher, and blocks unqualified background review before
thread/agent construction, with denial propagation through its finalizer caller.
Its separately versioned eleven-patch wheel passes scoped extracted-artifact
denial/consumer probes, not installed-product qualification. The dedicated test
host originally bound that eleven-patch wheel; older installers remain unchanged.
Installed qualification adds scoped compression and finalizer-background denials.
Other recovery, persistence and worker
paths remain open. No production gate, runtime pin or capability marker changes.
Patch 12 adds scoped content checks before native session/SQLite, JSON and
trajectory writes, and suppresses raw API observers in mandatory mode. Hermes
keeps its own session stores; Maya SMB memory remains separate. These checks
reuse model.output authorization, not a complete session-write policy. The
patch is now bundled in a separately versioned twelve-patch test wheel. Direct gateway
writers, outer catches, diagnostics and workers remain unqualified; production
activation stays blocked.
Patch 13 adds scoped outer-caller denial propagation for incremental tool
persistence, compression rotation/boundary callbacks and CLI session operations.
Reviewed hook callers stop on typed mandatory failures; ordinary-mode recovery
is retained. Compression releases its native lock on the touched denial paths,
but earlier mutations are not rolled back. This source-only candidate is not
in build 013; direct writers, full-loop callers and workers remain unqualified.
Patch 14 validates effective SQLite append arguments after native content and
attribute-based tool-call mapping, and propagates typed denials at that sink.
Tests use the native Hermes SQLite backend; Hermes conversation storage stays
separate from Maya SMB memory. This source-only candidate is not in build 013.
Direct SessionDB callers still require a trusted session-write contract; partial
batch writes, frontend callers and workers remain unqualified. Activation stays
blocked.
Patch 15 introduces a test-only trusted session-write contract through native
middleware and Maya's existing gateway. Atomic append batches validate serialized
rows before one transaction; incremental flush tracking advances only after commit.
Request-scoped authority binds identity, session, database, operation and execution
context. Unmapped native writes are blocked, not implicitly permitted. Direct
frontend bindings, create/rewrite/compaction descriptors, schema initialization
and audit reconciliation remain unqualified. Build 013 and production activation
are unchanged; no installer rebuild is qualified by these source tests.
Patches 16-17 add native descriptors for session creation, prompt metadata,
transcript rewrite/compaction and explicit message clearing, plus scoped denial
propagation through native initialization, transcript and mirror callers.
Replacement rows are prepared before destructive statements; SQLite rollback
preserves transcript, counters and FTS state. These source-only candidates do not
bind connector identities or qualify gateway session-index lifecycle, other
metadata/lock writers, schema provisioning or audit reconciliation. Build 013
and production activation remain unchanged; do not rebuild as a ready product.
Patch 18 adds scoped end/reopen, cwd, model/config and token-accounting metadata
descriptors. Mandatory accounting requires an existing authorized session; it
does not implicitly create one. Close reports finalization denial after resource
cleanup, not lifecycle rollback. This source-only candidate does not qualify
frontend identity bindings, session-index ordering, other callers/locks, schema
provisioning or audit reconciliation. The wheel, build 013 and production gate
remain unchanged.
Patch 19 adds scoped compression-lock metadata descriptors and stops mandatory
compression on denied, missing, broken or busy lock storage. Release denials
propagate rather than becoming debug-only diagnostics. Native ordinary-mode
fallback remains. These source tests do not qualify full compression, frontend
bindings, lock cleanup recovery, provisioning or audit reconciliation; the wheel,
installer 013 and production gate remain unchanged.
Stage 2 Step 1 now has an explicit source-candidate Local API session binding.
Bearer credentials map to a host-configured actor; session, database, operations
and classification cannot come from request fields. Per-write policy gates remain.
Patch 20 blocks unqualified gateway create/reset/switch before index mutation.
Authenticated gateway/CLI and setup/maintenance bindings remain incomplete.
Do not advance to remaining Steps 2-4 or rebuild until Step 1 acceptance is met;
the installed host, wheel and production activation gate are unchanged.
Step 1 also has an explicit source-candidate CLI client over that bound Local API.
It reads the local API token from stdin, verifies binding readiness, requires the
binding contract on execution, and refuses redirects/proxies/unbound fallback.
The server still chooses actor/session authority; no CLI administrative identity
is fabricated. Normal CLI, gateway mapping and setup/maintenance authentication
remain incomplete. Continue Step 1; do not infer production or installer readiness.
The approved Stage 2 Step 1 sub-sequence starts with customer-owned Telegram
private-text polling intake, then scoped native task/executor handoff, authorized
session-index transitions, and normal CLI/setup/maintenance identities. A source
intake callback now maps exact host-approved bot/user/chat identities and audits
binding, but native registration/transport provenance remain unqualified. It grants
no session-write or worker authority; no production activation or installer change.
Consult `docs/architecture/hermes_session_write_contract.md` before proceeding.
Patch 21 adds source-only native Telegram polling registration before application
start. The pinned SDK dispatcher passes scoped allow/deny tests using synthetic
transport; no live Telegram authentication or full connection lifecycle is qualified.
Ordinary handlers are inaccessible in this candidate, not an authorized fallback.
The next approved dependency is bounded request-task/executor handoff; session
writes, queued delivery, wheel/installer integration and production remain blocked.
Patch 22 adds a source-only, single-use native executor handoff for one
host-selected callable under an authenticated session lease. Receiver authority
expires on request exit/cancellation and still requires per-write governance.
Patch 22 alone does not bind the request-task hop or native conversation closure;
stay in the second approved sub-item before session-index transition work. This
does not qualify general workers, full-loop execution, wheel or installer changes.
Patch 23 adds a source-only main-conversation scheduling seam and bounded native
async Task hop before Patch 22's executor. One host-selected closure inherits the
same authenticated session limits; cancellation revokes its lease before delivery.
Background/unrelated jobs and nested delegation remain blocked. Scoped scheduling
and SQLite tests are not the complete conversation loop or Telegram-to-agent
qualification. Stay in the second Step 1 sub-item for full native caller/lifecycle
evidence; session-index transitions, wheel, installer and production stay unchanged.
The user approved `docs/architecture/maya_governance_integration_plan.md` on
2026-10-03. Its G0-G7 sequence supersedes the earlier implementation sequence;
G0 bounded baseline acceptance passed on 2026-10-03; G1 implementation is authorized
after the accepted security checkpoint. Consult its work packages and acceptance gate before
editing. See `docs/architecture/governance_g0_baseline.md` and the machine-readable
coverage register for evidence and unresolved roots. Full-fork and governed-path
qualification remain open. Production activation, runtime pin, wheel and installer
are unchanged.
Mandatory tool batches use native serial dispatch until parallel workers are
qualified. Provider-error redaction,
automatic-route attribution, direct SDK paths, and trusted worker coverage must
still be qualified before activation.

An explicit test-only candidate host may bind the four native governance gates
before Hermes construction using the exact hashed twelve-patch wheel. It requires
acknowledgement, isolated newly initialized test state, a loopback-only local
model, disabled broker/connectors and an unqualified health label. This does not
activate production governance, add a capability marker or change the runtime
pin. See `project_maya.hermes_plugins.candidate` and the native-governance ADR.

The dedicated governance-test installer uses a separate AppId, installation
root, shortcuts and test-data root. Its offline qualification uses installed
artifacts and inert external transports; it is core-only, not normal Standard
or Windows production qualification. Unsigned executables still require an
explicit local-smoke override. Preserve existing Maya and default Hermes homes.

Candidate installed qualification also exercises allowed model output and denied
native file-tool dispatch using the real SDK with zero retries and synthetic
HTTP fixtures. A bounded allowed read of one synthetic document also validates
the native result before a separately authorized follow-up model request. This
is not live-provider, socket, general-tool, recovery or full lifecycle
qualification; production activation remains blocked.
The native file-read fixture requires an explicitly reported customer-managed
shell; it does not establish readiness without a curated managed shell runtime.

The local action authorization gateway evaluates actor, tenant, capability,
target, data classification, memory trust, connector scopes, customer policy,
approval requirements, idempotency, and replay information.

It may allow, deny, redact, constrain, request confirmation, require an
authorized approver, or defer an operation.

Governance applies before:

- external model egress;
- messages, emails, and platform changes;
- file access and mutation;
- calendar and document operations;
- browser automation;
- analytics queries and publication;
- external API calls;
- persistent-memory use and writes;
- configuration, policy, and credential changes.

## 9. Model Providers

Supported modes are:

1. Maya-managed model proxy and billing;
2. customer-owned provider credentials;
3. local or customer-hosted model endpoints.

Providers remain behind a Hermes-compatible adapter. Targets include OpenAI,
Anthropic, Google Gemini, OpenRouter, and OpenAI-compatible local endpoints
such as Ollama, LM Studio, and vLLM.

Before external inference, governance evaluates provider, endpoint, data
classification, redaction, minimization, residency, and required consent. A
model proxy may process inference payloads but is not persistent memory.

## 10. Secrets

Configuration stores secret references rather than raw values.

Default backends are Windows DPAPI or Credential Manager, macOS Keychain,
Linux Secret Service, and supplied master keys, TPM/HSM, or external vaults for
headless and Enterprise deployments.

An encrypted file with its key stored beside it is not an acceptable vault.
Secrets are rotatable, revocable, auditable without value disclosure, and
excluded from logs, diagnostics, telemetry, errors, fixtures, and commits.

## 11. Maya OAuth Broker

Broker mode is one enum:

```text
runtime
setup_only
disabled
```

The broker may assist with account registration, licensing, OAuth setup,
short-lived setup sessions, encrypted credential handoff, update metadata,
consented diagnostics, and optional model billing.

The broker must not own customer files, memory, vector stores, governance
records, workflow or task state, business records, or local analytics data.

The protocol must define instance authentication, proof of private-key
possession, signed responses, approved algorithms, state, nonce, PKCE,
expiration, replay prevention, scopes, token-refresh ownership, key rotation,
revocation, recovery, rate limits, deletion policy, and versioning.

Production broker implementation requires an approved threat model and
provider-specific token lifecycle design.

## 12. Connectors

Every connector declares capabilities, secret references, scopes, identity
mapping, governed reads and writes, idempotency, retries, event verification,
allowlists, redacted health, reset, and revocation.

### Google

Standard may use a Maya-owned OAuth application through the broker. Enterprise
may use a customer-owned OAuth client. Each Google capability uses a minimal,
declared scope set. Token refresh ownership must be explicitly designed.

### Slack

Standard may use a Maya-owned distributed Slack application. Enterprise may
use a customer-owned application. Incoming events are authenticated and
deduplicated. Workspace, channel, and user allowlists are enforced.

### Telegram

Maya does not provide a shared Maya-managed Telegram bot. Standard and
Enterprise customers create their own bot. Maya guides setup, validates and
stores the token locally, and enforces chat, user, and action policy.

Any future Telegram cloud relay is a separately disclosed product mode and is
outside this specification.

## 13. Metabase Data Visualization

Metabase is Maya's included, open-source business-intelligence and
data-visualization capability and an alternative to Power BI for supported
Maya use cases.

Metabase provides dashboards, charts, governed operational reporting, and
visualization of approved customer and Maya analytics datasets. It runs
locally or on customer-controlled infrastructure as a managed service or
sidecar.

The architecture distinguishes:

1. **Metabase application database:** users, dashboards, settings,
   permissions, and internal Metabase state.
2. **Maya analytics data sources:** approved operational and business data
   queried for visualization.
3. **Maya persistent memory:** agent memory, which is not automatically an
   analytics source.

Configuration must not use an ambiguous `metabase.db_path`. Application
storage and analytics sources are explicit. Maya manages lifecycle, health,
secure credential injection, provisioning, backup guidance, compatibility,
and local API integration when it manages the service.

Metabase uses least-privilege database users, approved views, tenant isolation,
governed publication, and audited provisioning. Raw memory, secrets, prompts,
files, and customer data are not exposed by default.

## 14. Local API

The local API binds to loopback by default, authenticates clients, versions
routes, limits requests, applies CORS and CSRF controls where applicable,
verifies webhooks, separates privileges, and avoids secret disclosure.

Non-loopback binding requires explicit policy, authentication, and TLS. Remote
access is disabled by default.

## 15. Installation and Setup

Standard setup:

```text
Install
-> choose local data directory
-> initialize instance identity and secrets
-> sign in when required
-> select model mode
-> connect Google and Slack as needed
-> connect customer-owned Telegram bot as needed
-> initialize memory and governance
-> initialize Metabase and analytics sources
-> validate components
-> start Maya
```

Enterprise setup adds broker-mode selection, offline policy, credential or
secret-reference import, customer-controlled model endpoints, audit policy,
and customer-controlled Metabase configuration.

## 16. Health and Recovery

`maya doctor` reports Maya and Hermes compatibility, lifecycle state, enabled
profiles, filesystem permissions, disk space, memory schema, governance state,
secrets-backend status, model reachability, connector status and scopes,
Metabase service and database health, document and browser capabilities, local
API status, backups, migrations, and signed update status.

Required commands include:

```text
maya doctor
maya repair
maya reset-integration <name>
maya rotate-secret <name>
maya export-config
maya import-config
maya backup
maya restore
maya migrate --dry-run
maya update --check
maya update --rollback
```

Destructive actions require explicit confirmation and a recovery plan.

## 17. Configuration Model

Configuration is typed, versioned, validated before startup, and migrated
between product versions. Raw secrets are represented by secret references.

```yaml
schema_version: 2

product:
  edition: standard
  instance_id: "<generated>"

deployment:
  class: desktop
  network_policy: standard
  data_dir: "/path/to/maya-data"

runtime:
  hermes_compatibility: "<supported-range>"
  enabled_profiles: [core, metabase, documents, messaging]

broker:
  mode: runtime
  endpoint: "https://broker.maya.example"

llm:
  mode: maya_managed
  provider: openai
  model: "<configured-default>"
  fallback_model: null
  credential_ref: null
  endpoint: null
  timeout_seconds: 60

integrations:
  google:
    enabled: true
    credential_mode: broker
    credential_ref: "secret://integrations/google"
  slack:
    enabled: true
    credential_mode: broker
    credential_ref: "secret://integrations/slack"
  telegram:
    enabled: false
    credential_mode: customer_owned
    credential_ref: "secret://integrations/telegram"

memory:
  hermes_provider: local
  retriever: local_vector
  registry: sqlite
  governance_enabled: true

governance:
  policy_file: "/path/to/maya-data/governance/policies/default.yaml"
  audit_enabled: true
  default_action: deny
  minimum_memory_trust: 0.7

metabase:
  enabled: true
  deployment: managed_local
  endpoint: "http://127.0.0.1:<configured-port>"
  application_database:
    engine: "<supported-engine>"
    credential_ref: "secret://metabase/application-db"
  analytics_sources:
    - name: maya_operational
      engine: "<supported-engine>"
      credential_ref: "secret://metabase/maya-operational"

local_api:
  bind: "127.0.0.1"
  port: "<assigned>"
  remote_access: false
```

Editions are `standard` and `enterprise`. Credential modes are `broker`,
`customer_owned`, `local_only`, and `disabled`.

## 18. Local Data Layout

```text
maya-data/
  config/
  secrets/
  identity/
  memory/
    registry/
    vector/
    holographic/
    context/
  governance/
    policies/
    audit/
  tasks/
  integrations/
    google/
    slack/
    telegram/
  analytics/
    sources/
    exports/
  metabase/
    application/
    provisioning/
  documents/
  logs/
  cache/
  backups/
  migrations/
```

Physical paths vary by platform and are resolved through configuration rather
than hardcoded locations.

## 19. Audit and Telemetry

Local audit records cover authentication, integration authorization,
configuration and policy changes, model egress, memory decisions, proposed and
executed actions, approvals, rejections, analytics provisioning, migrations,
backups, restores, and updates.

Telemetry is disabled by default unless policy and explicit consent enable it.
Default telemetry excludes messages, files, memory, prompts, completions,
secrets, document names, database values, dashboards, and query results.
Optional diagnostic bundles show their exact payload before transmission.

## 20. Supply-Chain Security

Production releases require signed packages and installers, signed update
manifests, dependency locking where practical, SBOM generation, vulnerability
and secret scanning, artifact provenance, migration checks, rollback, customer
update controls, and offline Enterprise updates.

Unsigned updates never execute automatically.

## 21. Nonfunctional Requirements

Each supported deployment defines measurable targets for supported OS and CPU,
minimum resources, installation and lifecycle time, API latency and
concurrency, storage limits, backup and restore time, offline behavior,
connector retries, model timeout and fallback, audit retention, update
rollback, accessibility, and recovery objectives.

## 22. Implementation Roadmap

On 2026-10-03 the user approved a security checkpoint before G1: verify the 28
CodeQL review items against the effective runtime, fix or explicitly exclude
reachable risks, document the 29 metadata false positives, then resume G1 only
after checkpoint acceptance. Patch 24 is a separate source-only security overlay;
it does not rewrite the accepted 23-patch G0 baseline or installed artifacts.
The checkpoint passed in Linux run 37147131920 at commit
`5eaaca2e007760fb007c43c064b4f78ab69acf41`; G1 implementation is now authorized.
Consult `docs/architecture/governance_g1_request_lifecycle.md`: work package 1
defines the host contract and bounded lease foundations; work package 2 adds
source-only native caller-entry enforcement through Patch 25. Cancellation and
complete-loop qualification were work packages 3-4 in order. Bounded G1 acceptance
is recorded below; these historical implementation stages alone were not acceptance.
No production activation, runtime pin, wheel or installer change.

G1 work package 3 now has source-only host revocation controls: cancelling the
selected task revokes its root before cancellation delivery, task failures revoke
the root and are observed without diagnostic output, and caller cleanup has an
owner-bound synchronous revocation operation. Source-only Patch 26 connects native
cleanup and inactivity timeout, preserves exception scope, observes bounded cleanup
and disables unqualified supporting delivery tasks in mandatory mode. Scoped native
method probes pass; complete caller/agent-loop qualification remains work package 4.
Scoped method probes alone were not G1 acceptance; no production, wheel or installer
activation follows from them.
G1 work package 4 now has complete-caller source diagnostics using the actual
native conversation closure, AIAgent, real SDK with synthetic HTTP transport,
and native SQLite. The fixed resumed-session profile excludes connectors, tools,
first-turn title workers, schema provisioning and session-index transitions.
The fourteen-case matrix now includes repeated/swallowed cancellation and late
callback denial; ordinary controls pass on patched and unpatched native sources.
Its hashed inputs are in `docs/architecture/governance-g1-full-caller.json`.
Bounded source-level G1 was accepted on 2026-10-04 after the criterion review and
the user's instruction to proceed. The frozen input contract retains its original
pending-review label; the decision is in the G1 lifecycle runbook, not a rewritten
test artifact. Production model routing, plugin activation, wheels and installers
remain unqualified. G2 work package 1 is the owner-scoped transition design in
`docs/architecture/governance_g2_session_ownership.md`; transitions remain blocked
pending work package 3's implementation and native tests. Work package 2's design
is in `docs/architecture/governance_g2_session_consistency.md`: native SQLite is
authoritative, the index is a recoverable projection, and cross-store atomicity is
not claimed. Recovery requires explicit maintenance authority; production schema
provisioning and durable audit reconciliation remain G3. G2 is not accepted.
G2 work package 3 has source-only create authority and an explicit native create
entry in `docs/architecture/governance_g2_create_transition.md`. Patch 27 and the
Maya coordinator atomically allocate native SQLite records and strictly publish
the index in isolated fixtures; unfinished publication/audit outcomes quarantine
routing. Source-only Patch 28 adds a verified published-route reader, detached
cache and append-only G1 scope; legacy loaders/writers remain denied. Step 3's
scoped reader evidence is separate from step 4's full crash/race matrix;
do not advance to reset/switch/rotation or frontend composition yet. Production
activation, wheels, installers and accepted G1 inputs remain unchanged.
The approved caller-completion refinement is defined in
`docs/architecture/governance_g2_caller_acknowledgement.md`: pending caller
publication stays blocked until guarded normal-exit acknowledgement. This is
design-only; a separate source overlay and native qualification are next.
Legacy published receipts must not be silently adopted. G2 remains unaccepted.

Before each implementation step, consult the applicable agreed plan and identify
its current step and acceptance criteria. If inspection requires a different
sequence, recommend the specific revised order and wait for user approval before
deviating. Do not infer approval to reorder from a general request to proceed.

### Phase 0: Contracts and Threat Models

Approve Hermes compatibility, governance, connector, model, secrets, local API,
broker, updater, and Metabase architecture.

**Exit:** reviewed ADRs and testable protocols with no placeholder runtime.

### Phase 1: Minimal Local Product

Implement the concrete Hermes adapter, typed configuration, first secrets
backend, local memory provider and retriever, action authorization gateway,
authenticated local API, lifecycle, and `maya doctor`.

**Exit:** Maya installs from a clean artifact, executes through Hermes,
retrieves governed memory, authorizes actions, and shuts down cleanly.

### Phase 2: Enterprise BYO

Implement customer-owned model, Google, Slack, and Telegram credentials;
connector validation and revocation; configuration import and export; local
models; and broker-disabled operation.

**Exit:** Enterprise operates without Maya cloud services.

### Phase 3: Metabase and Documents

Package or connect an approved Metabase deployment, separate application and
analytics databases, provision governed data views and dashboards, integrate
LibreOffice, and add managed-service lifecycle and backup checks.

**Exit:** dashboards visualize approved data without exposing memory, secrets,
or unapproved records.

### Phase 4: Setup and Recovery

Implement edition setup flows, guided connectors, model and Metabase setup,
health checks, repair, backup, restore, and migration UX.

**Exit:** a clean supported machine can install, configure, validate, start,
stop, back up, and restore Maya.

### Phase 5: Broker and Standard OAuth

Implement a mock broker and conformance tests, cryptographic instance protocol,
approved token lifecycle, production Google and Slack OAuth, and optional
Maya-managed model billing.

**Exit:** independent security review and credential-lifecycle tests pass.

### Phase 6: Production Distribution

Produce signed platform installers, update metadata, SBOM, release provenance,
and tested upgrade, rollback, migration, and offline update paths.

**Exit:** qualification passes on every advertised platform.

## 23. Acceptance Criteria

Maya is not complete unless:

1. Public execution delegates to a real compatible Hermes runtime.
2. Memory and governance function without Maya cloud.
3. Risky actions pass through local authorization.
4. External model egress is governed and auditable.
5. Secrets use an approved platform or Enterprise backend.
6. Broker-disabled Enterprise operation passes end-to-end tests.
7. Telegram uses a customer-owned bot.
8. Metabase visualizes approved analytics data and remains separate from
   persistent memory.
9. Install, lifecycle, backup, restore, migration, update, and rollback are
   tested for every supported deployment.
10. Clean-install tests use built artifacts, not repository path shims.
11. Logs and diagnostics do not expose secrets.
12. Stubs are never reported as installed, loaded, or healthy capabilities.

## 24. Non-Goals

Project MAYA will not:

- become a pure SaaS agent;
- store authoritative memory in Maya Cloud;
- require the broker for Enterprise sovereign mode;
- create a fake parallel Hermes runtime;
- expose raw credentials;
- bind permanently to one model provider;
- permit governance bypass;
- provide a shared Maya-managed Telegram bot;
- treat Metabase application storage as persistent memory;
- expose memory or customer files to analytics by default;
- advertise untested platform support.

## 25. Final Product Model

```text
Maya Standard
  = local Maya and Hermes runtime
  + local memory and governance
  + included Metabase visualization
  + guided setup
  + optional Maya OAuth Broker
  + optional Maya-managed model billing
  + customer-owned Telegram bot

Maya Enterprise
  = the same local core runtime
  + customer-owned credentials and infrastructure
  + included or customer-controlled Metabase deployment
  + runtime, setup-only, or disabled broker mode
  + offline and sovereign policy
```

Maya Cloud may assist with setup and commercial services, but the local Maya
instance remains the authority and enforcement point for customer memory,
files, business data, operational state, secrets, governance, and actions.

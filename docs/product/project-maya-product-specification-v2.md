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

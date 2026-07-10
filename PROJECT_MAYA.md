# Project MAYA: Product and Architecture Context

## Purpose

Project MAYA is the foundation of **Maya the Info Manager**, the installable
Information Manager AI Employee.

Maya assists with organizational information, local documents,
communications, calendars, governed workflows, persistent memory, and business
intelligence. Maya is accountable software, not a generic chatbot. Its defining
properties are local customer control, governance, persistence, transparency,
auditability, recoverability, portability, and long-term organizational memory.

The authoritative product requirements are defined in
`docs/product/project-maya-product-specification-v2.md`.

The repository protects this source-of-truth relationship with
`scripts/validate_project_maya_context.py` and the Project context guard CI
workflow. If product guidance is changed, update `AGENTS.md`, this file, and
the V2 specification together.

## Product Model

Project MAYA has one core runtime and two editions.

### Maya Standard

Maya Standard provides:

- local execution on the customer's machine or server;
- guided installation and setup;
- optional Maya account and licensing services;
- optional Maya OAuth Broker support for Google and Slack;
- optional Maya-managed model billing and proxying;
- customer-owned Telegram bot integration;
- local persistent memory, governance, business data, and dashboards.

### Maya Enterprise

Maya Enterprise uses the same core runtime and adds:

- customer-owned integration and model credentials;
- broker runtime, setup-only, or disabled modes;
- offline and sovereign deployment policies;
- external vault, TPM, or HSM integration where required;
- customer-controlled networking, updates, licensing policy, and
  infrastructure;
- audit-friendly configuration import, export, and validation.

Edition is a capability and policy choice. Standard and Enterprise must not
diverge into separate runtime implementations.

## Local-First Principle

The customer's local or customer-controlled deployment is authoritative for:

- persistent memory and retrieval indexes;
- governance policy and decisions;
- operational context;
- files and processed-document indexes;
- workflow, task, and Kanban state;
- business and analytics data;
- configuration and secret references;
- integration tokens where technically possible;
- local logs, audit records, and backups;
- Maya-managed Metabase state.

Cloud components may assist with account registration, licensing, OAuth,
update metadata, consented diagnostics, and optional model inference. They are
not Maya's authoritative memory, governance engine, or operational state.

## Logical Architecture

```text
Users, channels, local clients, and connector events
                         |
                         v
              Local API and identity policy
                         |
                         v
       Governed context and persistent-memory retrieval
                         |
                         v
          Project MAYA Agent lifecycle facade
                         |
                         v
                Hermes Agent runtime
                         |
              model response or action proposal
                         |
                         v
          Local action authorization gateway
                  /              \
                 v                v
        Local tools/files     External connectors
                  \              /
                   v            v
             result validation and audit
                         |
                         v
              governed memory-write policy
```

Governance is a mandatory control boundary. It is not merely a downstream log
processor. No connector, plugin, skill, broker callback, model adapter, or
workflow may bypass local authorization.

## Canonical Public API

`project_maya` is the canonical product namespace.

The public `Agent` is a lifecycle facade over a concrete `AgentRuntime`. It
coordinates configuration, startup, runtime execution, plugin loading, memory
attachment, rollback, and shutdown. It does not implement a fake agent runtime.

The lifecycle is:

```text
created -> starting -> running -> stopping -> stopped
                    \-> failed <-/
```

Components are reported as loaded or healthy only after real initialization
and validation succeed.

## Hermes Agent

Hermes Agent is the current core execution runtime. It hosts execution of:

- Maya identity and role;
- skills and operating procedures;
- context assembly;
- model-provider interaction;
- tool selection and workflow orchestration;
- memory-provider lifecycle;
- runtime events and sessions.

A versioned Hermes adapter must provide:

- runtime construction and compatibility reporting;
- profile and identity loading;
- session creation and termination;
- model configuration;
- memory-provider attachment;
- skill and plugin registration;
- request execution;
- governance event forwarding;
- health, shutdown, and recovery.

Maya must adapt existing Hermes contracts rather than creating parallel model,
plugin, skill, or memory abstractions.

Hermes is architecturally replaceable in the future, but it is the required
execution core of the current supported product. Portable Maya identity,
skills, policies, procedures, connector definitions, and durable knowledge
must survive future runtime replacement.

Production installers may bundle pinned, curated, disclosed,
license-compatible, Maya-managed runtime artifacts, including managed Python,
the compatible Hermes runtime, Metabase, Java, LibreOffice, and Poppler, when
those artifacts are produced or consumed through the Maya release process with
hashes and provenance. This is distinct from silently installing uncontrolled
system software. Missing managed artifacts must block readiness and platform
support claims rather than being reported as healthy operation.

## Authority Model

Authoritative state must exist outside the LLM. Depending on its domain, it
resides in:

- files and versioned repositories;
- local registries and databases;
- governance and audit records;
- task and workflow stores;
- customer-owned operational systems;
- approved analytics data sources.

Conversation history, model memory, embeddings, indexes, and transient Hermes
runtime state are not authoritative. Indexes and embeddings are disposable,
reproducible derivatives.

## Governance and Action Authorization

The local action authorization gateway evaluates:

- actor and tenant identity;
- requested capability and target;
- data classification and egress;
- memory provenance and trust;
- connector scopes and allowlists;
- customer policies;
- confirmation or approver requirements;
- idempotency and replay information.

It may allow, deny, redact, constrain, request confirmation, require an
approver, or defer an operation.

Governance applies to:

- model-bound context and sensitive-data egress;
- tool calls and workflows;
- external messages and platform changes;
- file reads, writes, moves, sharing, and deletion;
- calendar and document operations;
- browser automation;
- analytics queries and publication;
- persistent-memory retrieval and writes;
- policy, configuration, and credential changes.

Every consequential action must be explainable, traceable, and auditable.

## Persistent Memory

Persistent memory preserves organizational knowledge independently of model
provider, model version, session history, operating system, deployment host,
and product upgrades.

Maya distinguishes:

1. **Hermes MemoryProvider:** session initialization, prefetch, prompt context,
   turn synchronization, memory tools, and session shutdown.
2. **Project MAYA Retriever:** normalized persistence and search through
   `upsert`, `get`, `search`, vector query, and related retrieval operations.

Key-value `read` and `write` methods are not the canonical memory contract.

Memory records preserve stable identifiers, provenance, trust, provider and
model metadata, retention policy, and governance decisions. Migrations default
to dry-run, require explicit write consent, back up existing destinations,
handle conflicts deterministically, validate results, and produce reports.

The logical derivation chain is:

```text
Authoritative files and records
             |
             v
       normalized records
             |
             v
          registry
             |
             v
     indexes and embeddings
             |
             v
          retrieval
```

## Model Providers

Maya supports:

- Maya-managed model proxy and billing;
- customer-provided provider credentials;
- local or customer-hosted model endpoints.

Provider-specific behavior remains behind a versioned adapter compatible with
Hermes. Target providers include OpenAI, Anthropic, Google Gemini, OpenRouter,
and OpenAI-compatible local services such as Ollama, LM Studio, and vLLM.

External model calls are governed data egress. Policy evaluates provider,
endpoint, data category, redaction, minimization, residency, and required
consent before a request leaves the local trust boundary.

## Secrets

Configuration contains secret references, never raw credentials.

Approved defaults are:

- Windows DPAPI or Credential Manager;
- macOS Keychain;
- Linux Secret Service;
- a supplied master key, TPM/HSM, or external vault for headless and Enterprise
  deployments.

An encrypted secrets file with its key stored beside it is not sufficient.
Secrets must be rotatable, revocable, auditable without value disclosure, and
excluded from logs, errors, diagnostics, telemetry, fixtures, and commits.

## Maya OAuth Broker

The broker reduces setup complexity without becoming the operating brain.

Broker mode is one enum:

- `runtime`
- `setup_only`
- `disabled`

The broker may support account registration, licensing, OAuth setup,
short-lived setup sessions, encrypted credential handoff, update metadata,
consented diagnostics, and optional model proxying.

The broker must not own customer files, memory, vector stores, governance
records, workflow state, task state, business records, or local analytics data.

Production broker work requires an approved threat model covering instance
authentication, private-key proof of possession, signed responses, PKCE,
state, nonce, expiration, replay prevention, provider-specific token refresh,
key rotation, revocation, recovery, rate limits, and protocol versioning.

## Connectors

Every connector declares:

- capabilities and minimal scopes;
- credential references;
- identity mapping;
- governed read and write operations;
- idempotency and retries;
- webhook or event verification;
- allowlists;
- redacted health reporting;
- reset and revocation behavior.

Standard may use broker-assisted Google and Slack OAuth. Enterprise may use
customer-owned applications and credentials.

Telegram always uses a customer-owned bot created through Telegram's supported
process. Maya guides token setup, validates it, stores it locally, and applies
chat and user allowlists. A shared Maya-managed Telegram bot is not part of the
product.

## Metabase Business Intelligence

Metabase is an included, locally deployable business-intelligence and data
visualization capability. It is positioned as an open-source alternative to
Power BI for supported Maya use cases.

Metabase provides dashboards and charts for approved operational and business
data. It runs locally or on customer-controlled infrastructure as a managed
service or sidecar.

Keep these stores distinct:

1. **Metabase application database:** Metabase users, dashboards, settings,
   permissions, and internal state.
2. **Maya analytics data sources:** governed operational or business datasets
   queried for visualization.
3. **Maya persistent memory:** agent memory, which is not automatically an
   analytics data source.

Do not use an ambiguous `metabase.db_path`. Metabase application storage and
analytics-source configuration must be explicit. Data sources use
least-privilege credentials, approved views, tenant isolation, and governed
publication. Raw memory, prompts, secrets, files, and customer records are not
exposed by default.

## Component Profiles

The product is packaged through coordinated profiles:

- `maya-core`
- `maya-metabase`
- `maya-documents`
- `maya-messaging`
- `maya-browser`
- `maya-local-models`

Metabase is included and enabled by default in the normal Standard
installation. It remains separately managed, upgraded, backed up, and
health-checked.

LibreOffice, browser automation, messaging gateways, local models, and other
heavy dependencies are installed through declared profiles rather than hidden
core dependencies.

Maya distinguishes source-controlled installer artifacts from on-demand or
customer-managed dependencies. The installer or release artifact includes
Maya-owned, Maya-curated, or Maya-pinned components such as `project_maya`, the
pinned compatible Hermes runtime, the Maya-Hermes adapter, governance,
persistent memory, local API, connector and gateway adapter code, model
adapters, readiness contracts, approved sanitized skills and plugins,
Metabase/document integration code, manifests, SBOM, and signed update
metadata. Included code does not mean the related capability is configured,
credentialed, enabled, healthy, authorized, or supported on a platform.

Profile-specific heavy dependencies remain installed, connected, or validated
on demand. These include optional Python extras, Poppler, LibreOffice,
customer-managed Microsoft Office, browser binaries and automation runtimes,
Java, customer-managed Metabase runtimes or databases, local model runtimes and
model artifacts, connector applications and bot registrations, OAuth grants,
webhooks, allowlists, Enterprise vaults, certificates, networking, and offline
update channels. Maya reports their readiness and setup hints without silently
installing system software or creating customer tenant resources.

## Local API

The local API:

- binds to loopback by default;
- authenticates clients;
- versions routes;
- applies request and rate limits;
- protects browser-facing routes with appropriate CORS and CSRF controls;
- verifies connector webhooks;
- separates administrative and runtime privileges;
- requires TLS and explicit policy for non-loopback access;
- never exposes secret values through errors or health checks.

Remote access is disabled unless explicitly configured and secured.

## Installation and Operations

Supported deployment classes are Windows, macOS, Linux, customer-controlled
servers, and containers. A platform is advertised only after its installer,
lifecycle, health, backup, restore, update, rollback, and clean-install tests
pass.

Use configurable roots such as `MAYA_HOME` and `MAYA_DATA_DIR`. Hostinger,
Docker, Linux, `systemd`, `/opt/data`, and `/root/.hermes` may be development
details but are not product architecture requirements.

Required operational capabilities include:

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

Destructive operations require explicit confirmation and a recovery plan.

## Configuration

Configuration is typed, versioned, validated before startup, and migrated
between releases. It separately represents:

- product edition;
- deployment class and network policy;
- enabled component profiles;
- Hermes compatibility;
- broker mode;
- model mode and endpoint;
- connector credential modes and secret references;
- memory provider and retriever;
- governance policy;
- Metabase deployment, application database, and analytics sources;
- local API binding and remote-access policy.

Valid editions are `standard` and `enterprise`. Connector credential modes are
`broker`, `customer_owned`, `local_only`, and `disabled`.

## Audit and Telemetry

Local audit records cover authentication, integration authorization,
configuration changes, model egress, memory decisions, tool proposals and
results, approvals, rejections, analytics provisioning, migrations, backups,
restores, and updates.

Telemetry is disabled by default unless product policy and explicit consent
enable it. Default telemetry excludes message contents, files, memory, raw
prompts, completions, secrets, tokens, document names, database values,
dashboard contents, and query results.

## Supply-Chain Security

Production releases require:

- signed installers and packages;
- signed update manifests;
- pinned dependencies where practical;
- software bills of materials;
- vulnerability and secret scanning;
- artifact provenance;
- migration compatibility checks;
- update rollback;
- offline update packages for Enterprise.

Unsigned updates must never execute automatically.

## Implementation Sequence

1. Approve runtime, governance, connector, model, secrets, and threat-model
   contracts.
2. Implement the concrete Hermes adapter and minimal governed local product.
3. Implement Enterprise BYO and broker-disabled operation.
4. Integrate Metabase and document capabilities.
5. Implement setup, health, recovery, backup, restore, and migration UX.
6. Implement and independently review the broker protocol and Standard OAuth.
7. Produce signed, tested platform installers and update channels.

Features do not count as complete when only interfaces, placeholders, or mock
services exist.

## Engineering Principles

Prefer:

- explicit contracts and deterministic behavior;
- local governance and least privilege;
- typed configuration and versioned migrations;
- stable identifiers and idempotent operations;
- auditability and recoverability;
- provider adapters and portable formats;
- clean installation tests using built artifacts;
- cross-platform libraries;
- documented compatibility and deprecation plans.

Avoid:

- hidden state and implicit side effects;
- runtime-only persistence;
- broad exception suppression;
- unsafe migration defaults;
- raw secrets in files or logs;
- provider-specific behavior outside adapters;
- duplicate runtime, plugin, or memory abstractions;
- platform claims without lifecycle and recovery evidence.

## Decision Rule

When architectural uncertainty remains, choose the option that best maximizes:

1. Local governance and customer control
2. Security and least privilege
3. Persistence and data integrity
4. Auditability
5. Recoverability
6. Transparency
7. Cross-platform compatibility
8. Provider independence

Maya Cloud may assist Maya, but the local Maya instance remains the authority
and enforcement point for customer memory, files, business data, operational
state, secrets, governance, and actions.

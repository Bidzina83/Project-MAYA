# Project MAYA Agent Guidance

This file contains mandatory instructions for coding agents and automation
working in this repository.

## Required Context

Before making architectural, implementation, refactoring, memory, governance,
workflow, infrastructure, packaging, security, or integration decisions, read:

1. `PROJECT_MAYA.md`
2. `docs/product/project-maya-product-specification-v2.md`
3. Relevant architecture decisions and existing runtime contracts

If implementation instructions conflict with the product specification, stop
and report the conflict. Do not satisfy a narrow task by inventing a parallel
architecture.

## Source-Of-Truth Guard

`AGENTS.md`, `PROJECT_MAYA.md`, and
`docs/product/project-maya-product-specification-v2.md` are coupled product
context files. Changes that alter product architecture, implementation order,
runtime boundaries, governance, connectors, secrets, packaging, or deployment
policy must keep all three aligned.

Run `python scripts/validate_project_maya_context.py` before merging such
changes. The same check runs in CI and fails when the V2 product specification
is missing or when required V2 guidance anchors disappear from the context
files.

## Product Identity

Project MAYA is the foundation of Maya the Info Manager, an installable and
governed AI employee for information management. Maya is not a generic chatbot
and is not a pure SaaS product.

The product has two editions using one core runtime:

- Maya Standard: local runtime, guided setup, optional Maya OAuth Broker, and
  optional Maya-managed model billing.
- Maya Enterprise: the same local core with customer-owned credentials,
  optional or disabled broker participation, and sovereign deployment policy.

Customer files, persistent memory, governance records, business data,
operational state, task state, and secrets remain local and
customer-controlled.

## Canonical Package and Runtime

`project_maya` is the canonical product namespace.

Hermes Agent is the current core execution runtime. The public Maya `Agent` is
a lifecycle facade over a concrete `AgentRuntime`; it is not an alternative
implementation of Hermes.

Follow these rules:

- Integrate against versioned Hermes construction and lifecycle contracts.
- Adapt existing Hermes model, memory, plugin, and skill interfaces.
- Do not create fake runtimes, duplicate plugin registries, or placeholder
  memory abstractions.
- Do not report a component as loaded or healthy when only a stub exists.
- Preserve explicit startup ordering, rollback, shutdown, and failure states.
- Keep Maya identity, skills, policies, procedures, connector definitions, and
  durable knowledge as portable, versioned product artifacts.

Hermes is architecturally replaceable in the future, but a supported Maya
release currently requires a compatible Hermes runtime.

The governing principle is:

> Hermes executes Maya. Local governance authorizes Maya. Customer-controlled
> records define Maya's durable state.

## Mandatory Execution Boundary

All requests and actions follow this logical path:

```text
Input
  -> identity and input policy
  -> governed context and memory retrieval
  -> Hermes runtime and model adapter
  -> proposed response or action
  -> local action authorization gateway
  -> connector or local tool
  -> result validation and audit
  -> governed memory-write decision
  -> response
```

No connector, plugin, skill, workflow, broker callback, or model adapter may
bypass the local action authorization gateway.

Governance must mediate consequential reads, external data disclosure, tool
calls, workflow execution, external mutations, file operations, analytics
publication, persistent-memory writes, and policy-sensitive configuration.

## Authority and State

- Important state exists outside the LLM in customer-controlled files,
  repositories, registries, databases, audit logs, and operational systems.
- Conversation history, model memory, embeddings, and indexes are not
  authoritative.
- Indexes and embeddings are reproducible derived artifacts.
- Operational context must be reconstructable from durable records.
- External systems may be authoritative for their own business records; Maya
  changes to those systems remain governed and audited.
- Cloud services are helpers, not Maya's memory, governance engine, or
  operating brain.

## Persistent Memory Contracts

Keep these roles distinct:

1. A Hermes `MemoryProvider` participates in session initialization, prompt
   prefetch, turn synchronization, tools, and session shutdown.
2. A provider-agnostic `Retriever` performs normalized persistence and search
   through `upsert`, `get`, `search`, vector query, and related operations.

Key-value `read` and `write` methods are not the canonical persistent-memory
contract.

Memory changes must preserve provenance, stable identifiers, trust metadata,
schema compatibility, backup safety, and governance decisions. Migration tools
must default to dry-run and require explicit consent before modification.

## Connector Rules

Every connector must declare capabilities, credential references, scopes,
identity mapping, read and write operations, governance integration,
idempotency, retry behavior, event verification, redacted health status, and
revocation behavior.

- Standard may use broker-assisted Google and Slack OAuth.
- Enterprise may use customer-owned Google and Slack applications.
- Telegram always uses a customer-owned bot and token.
- Do not implement or recommend a shared Maya-managed Telegram bot.
- Minimize scopes and enforce customer-defined user, channel, workspace, and
  resource allowlists.

## Broker Rules

Broker mode is one enum: `runtime`, `setup_only`, or `disabled`.

The broker may assist with account registration, licensing, OAuth setup,
encrypted credential handoff, update metadata, consented diagnostics, and
optional model proxying. It must not own persistent memory, customer files,
governance records, workflows, business records, local analytics data, or
authoritative task state.

Broker protocol work requires an approved threat model covering proof of key
possession, signed responses, PKCE, state and nonce binding, replay protection,
session expiration, token-refresh ownership, key rotation, revocation,
recovery, and protocol versioning.

## Secrets

Configuration stores secret references, never raw credentials.

Use approved platform storage:

- Windows DPAPI or Credential Manager
- macOS Keychain
- Linux Secret Service
- supplied master keys, TPM/HSM, or external vaults for headless and Enterprise
  deployments

An encrypted file with its key stored beside it is not an acceptable vault.
Secrets must be redacted from logs, diagnostics, errors, telemetry, fixtures,
and committed files.

## Metabase

Metabase is an included local business-intelligence and data-visualization
capability, positioned as an open-source alternative to Power BI for supported
Maya use cases.

Keep three stores distinct:

1. Metabase application database
2. Maya analytics data sources
3. Maya persistent memory

Do not use an ambiguous `metabase.db_path`. Do not expose raw memory, prompts,
secrets, files, or business data to Metabase by default. Use approved data
sources, least-privilege credentials, governed views, and audited provisioning.

## Packaging and Platform Support

Use coordinated component profiles:

- `maya-core`
- `maya-metabase`
- `maya-documents`
- `maya-messaging`
- `maya-browser`
- `maya-local-models`

Metabase is included and enabled by default in the normal Standard
installation, while remaining separately managed and health-checked.

Separate included/source-controlled artifacts from on-demand or
customer-managed dependencies. The installer or release artifact may include
Maya-owned, Maya-curated, or Maya-pinned components such as `project_maya`, the
pinned Hermes runtime, the Maya-Hermes adapter, governance, persistent memory,
local API, connector and gateway adapter code, model adapters, readiness
contracts, approved sanitized skills and plugins, Metabase/document integration
code, manifests, SBOM, and signed update metadata. Included code does not mean
the capability is configured, credentialed, enabled, healthy, authorized, or
supported.

Profile-specific heavy dependencies are installed, connected, or validated on
demand. These include optional Python extras, Poppler, LibreOffice,
customer-managed Microsoft Office, browser binaries and automation runtimes,
Java, customer-managed Metabase runtimes or databases, local model runtimes and
artifacts, connector applications and bot registrations, OAuth grants,
webhooks, allowlists, Enterprise vaults, certificates, networking, and offline
update channels. Do not silently install system software or create customer
tenant resources.

Do not claim support for Windows, macOS, Linux, server, or container deployment
until installation, lifecycle, health, backup, restore, update, and rollback
tests pass for that artifact.

Use configurable application-data roots such as `MAYA_HOME` or
`MAYA_DATA_DIR`. Do not hardcode `/opt/data`, `/root/.hermes`, Hostinger,
Docker, `systemd`, or operating-system-specific paths into product contracts.

## Local API and Network Security

The local API binds to loopback by default and requires authenticated clients.
Remote binding requires explicit policy, TLS, and appropriate authorization.
Apply request limits, route versioning, CORS and CSRF protections where
applicable, webhook verification, privilege separation, and secret-safe error
handling.

External model requests are governed data egress. Record the provider,
endpoint, data classification, redaction decision, and applicable consent
without logging prompt contents or secrets.

## Engineering Rules

Prefer:

- deterministic behavior and explicit contracts;
- typed, versioned configuration and migrations;
- auditability and recoverability;
- provider independence through adapters;
- least privilege and deny-by-default policy;
- idempotent operations and stable identifiers;
- clean installation tests using built artifacts;
- cross-platform libraries and portable formats;
- focused compatibility layers with documented removal plans.

Avoid:

- broad exception suppression;
- hidden state and untracked side effects;
- autonomous self-modification;
- provider-specific behavior leaking across boundaries;
- runtime-only persistence;
- unsafe migration defaults;
- secrets in configuration or logs;
- tests that validate only mocks or private dictionaries;
- packaging generated caches, tests, or repository artifacts in product wheels.

## Implementation Order

Work in this order unless an approved architecture decision changes it:

1. Runtime, governance, connector, model, secrets, and threat-model contracts
2. Concrete Hermes adapter and minimal governed local product
3. Enterprise BYO and broker-disabled operation
4. Metabase and document capabilities
5. Setup, recovery, backup, and health experience
6. Broker protocol and Standard OAuth
7. Signed production installers and updates

Each phase must satisfy its acceptance gate before downstream convenience
features are treated as complete.

## Decision Rule

When uncertain, choose the option that best maximizes, in order:

1. Local governance and customer control
2. Security and least privilege
3. Persistence and data integrity
4. Auditability
5. Recoverability
6. Transparency
7. Cross-platform compatibility
8. Provider independence

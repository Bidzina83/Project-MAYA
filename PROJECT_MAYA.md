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

Maya owns a native Hermes governance plugin that adapts model and tool
execution middleware to the existing local gateway, not a second policy engine.
Observer hooks are not security gates. The current pinned Hermes middleware is
fail-open and does not cover auxiliary inference; activation and production
qualification remain blocked until the fail-closed execution contract is
qualified. Unknown and unbounded tools remain denied. The staged contract and
remaining acceptance work are in `docs/architecture/hermes_native_governance.md`.

Stage 2a/2b adds test-only candidate patches for opt-in mandatory dispatch and
central synchronous/asynchronous auxiliary inference, with legacy behavior
preserved outside mandatory mode. Stage 2c adds explicit main-loop mandatory-error
stop handlers plus tool/preflight denial propagation, including native dispatcher
and registry typed-denial propagation. The candidate native final-result validator
checks final content; scoped generic tool errors use fixed
codes. This fork extension is not upstream-qualified.
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
Mandatory tool batches use native serial dispatch until parallel workers are qualified. Full-loop
qualification, provider-error redaction, automatic-route
attribution, direct SDK paths, and worker coverage remain open. The patches are
not a qualified runtime replacement and activation stays blocked.

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
design-defined; source-only Patch 29 implements its bounded caller scope and
staged native sink/reader. Full acknowledgement/failure qualification is next.
Legacy published receipts must not be silently adopted. G2 remains unaccepted.
The separate Step 3 caller failure matrix has bounded native receipt/reader and
restart evidence in `docs/architecture/governance_g2_caller_qualification.md`.
Complete create-to-agent caller qualification remains open; do not advance yet.
The real empty-history first-turn diagnostic found blocked native lazy session
recreation; see `docs/architecture/governance_g2_create_loop.md`. A new bounded
existing-session recognition dependency was approved by the user. Source-only
Patch 30 recognizes exact reader-bound acknowledged state without create or
metadata authority; see `docs/architecture/governance_g2_existing_session_recognition.md`.
Native prompt-cache metadata denial/catch remains outside that contract and
requires review before complete create-loop acceptance. G2 remains unaccepted.
The cache boundary review in `docs/architecture/governance_g2_prompt_cache_review.md`
records the approved fixed no-snapshot behavior for the append-only profile.
Patch 31 is a separate source-only candidate with fresh request-bound policy/audit
decisions; no snapshot metadata grant, G2 acceptance or production activation follows.
Bounded two-process conversation evidence is in
`docs/architecture/governance_g2_restart_loop.md`. It checks fresh authority over
existing native records, not frontend credentials or production provisioning.
Remain in create qualification/acceptance review before another transition.
The approved final-profile closure is in
`docs/architecture/governance_g2_create_acceptance_review.md`: 80 native cases
pass, including process contention/crash and separate write/fsync failures.
The user accepted bounded source-level create on 2026-10-05.
Next is the reset transition within G2 work package 3; consult its owner-scoped
design and consistency criteria before implementation. Reset remains blocked.
Reset Step 1's source-informed contract and ordered Steps 1-4 are in
`docs/architecture/governance_g2_reset_transition.md`, approved on 2026-10-06.
Reset Step 2 is the source-only Patch 32 authority and atomic SQLite sink candidate.
Source-only Patch 33 adds Step 3 publication, reset-specific normal-exit
acknowledgement and lineage-checked reader composition. Its 15 composition cases
and 22 unchanged atomic cases pass on the combined candidate; 88 ordinary native
session tests pass. Fresh agent/history/cache isolation and independent model
denial use real native callers and synthetic SDK transport. This initial
create-to-reset profile is pending review; repeat reset, tool-approval transfer,
uncertain acknowledgement/quarantine combinations and Step 4's crash/race matrix
remain unqualified. No schema, production activation, wheel or installer change.
Work package 3, G2, production activation, wheels and installers remain unchanged.

Before each implementation step, consult the applicable agreed plan and identify
its current step and acceptance criteria. If inspection requires a different
sequence, recommend the specific revised order and wait for user approval before
deviating. Do not infer approval to reorder from a general request to proceed.

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

Hosted CI jobs use explicit Ubuntu 24.04 runners and reviewed Node 24 actions.
This CI maintenance does not qualify a product platform or alter Hermes pins,
governance acceptance, credentials, deployment policy or installed artifacts.

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

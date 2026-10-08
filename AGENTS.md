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

Maya's native Hermes governance plugin must enforce model and tool execution
boundaries through the existing local gateway. Observer hooks are not security
gates. The current pinned Hermes middleware is fail-open and auxiliary inference
is uncovered; plugin activation and production qualification remain blocked
until a qualified fail-closed runtime contract covers those paths. Unknown and
unbounded tools remain denied. See `docs/architecture/hermes_native_governance.md`.

The Stage 2a/2b mandatory-dispatch and central auxiliary-call patches are test-only
candidates, not a qualified Hermes replacement. Stage 2c adds explicit main-loop
mandatory-error stop handlers plus tool/preflight denial propagation. Typed
denials also propagate through the native tool dispatcher and registry.
The candidate `tool_result` boundary validates final content; scoped generic tool
errors use fixed codes. This fork extension is not upstream-qualified.
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
Mandatory tool batches use native serial dispatch until parallel workers are qualified.
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
On 2026-10-07 the user approved the bounded reset gate restriction in
`docs/architecture/governance_g2_reset_composition_review.md`. Source-only Patch 34
adds exact native approval cleanup before acknowledgement, denies unqualified
mandatory approval mutation/resolution, and requires host-confirmed completion
in addition to durable reset lineage. Missing confirmation, reported uncertainty
and a new host/restart deny reset routing; no automatic reconciliation is granted.
The final 56-case native suite passes; the two identified review blockers are
closed for this bounded source profile. The user's bounded Step 3 acceptance
is recorded in that document. Do not infer
Step 4, G2, full-fork or production acceptance from this restriction. Earlier
frozen profiles, runtime pin, wheel and installer remain unchanged.
The user explicitly closed bounded reset Step 3 on 2026-10-07 and authorized
Step 4's failure matrix on the frozen Patch 34 profile. Consult
`docs/architecture/governance_g2_reset_failure_matrix.md` before continuing;
its process-crash/restart, four contention and three old/new native caller
cancellation cases and eighteen descriptor/revocation/expiry cases do not complete
the remaining storage-fault and path matrix. Thirteen combined commit/publication/
acknowledgement/audit cases pass on 2026-10-08, including four fresh-process probes;
uncertain outcomes stay blocked even when quarantine is unavailable. The late old
executor cannot borrow a fresh reset-session lease
in that fixed synthetic-transport profile; general workers remain unqualified.
Separate storage/audit qualification on 2026-10-08 passes eleven of twelve cases.
The short-write regression fails: the Maya-owned publication helper ignores the
write count and replaces the projection before verifying complete bytes. Routing
denies, but the old-or-new complete-file requirement fails. Preserve this failing
evidence and frozen Patch 34. On 2026-10-08 the user approved a separately
versioned host-only publisher correction: Patch 35 checks the reported write count
and completed temporary-file bytes before strict replacement. Requalify affected
create/reset paths on that candidate before resuming unsafe paths and ordinary-mode
parity. Hermes source, runtime pin, wheels and installers remain unchanged.
All 200 bounded native requalification cases pass on the corrected candidate:
167 create/reset plus 33 process/descriptor/late-caller cases. The original failing
regression and earlier inputs remain unchanged. Unsafe paths and ordinary-mode
parity are next; see `docs/architecture/governance_g2_publisher_correction.md`.
Reset Step 4, G2 and production remain unaccepted.
On 2026-10-08 all 26 remaining bounded reset path cases pass on unchanged Patch 35.
The final 331-case ordinary comparison matches pinned unpatched Hermes: 322 pass
and nine known Windows shell-path assertions fail on each profile, with no skips.
These failures are retained and remain relevant before shell/platform qualification.
The criterion review recommends bounded initial-reset acceptance with exclusions;
explicit user acceptance is still required before another transition. Consult
`docs/architecture/governance_g2_reset_paths_parity.md` and
`docs/architecture/governance_g2_reset_acceptance_review.md`.
Work package 3, G2, production activation, wheels and installers remain unchanged.
Full-loop qualification, provider-error redaction,
automatic-route attribution, direct SDK paths, and worker coverage remain open;
do not activate the plugin or change the production gate on these patches alone.

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

This does not prohibit a Maya Standard installer from bundling pinned,
curated, disclosed, license-compatible, Maya-managed runtime artifacts through
the release process, including managed Python, the compatible Hermes runtime,
Metabase, Java, LibreOffice, or Poppler. Such artifacts must be hashed,
provenanced, installed into Maya-owned locations where practical, and qualified
honestly; missing artifacts remain blocked readiness, not healthy operation.

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

Hosted CI jobs use explicit Ubuntu 24.04 runners and reviewed Node 24 actions.
This CI maintenance does not qualify a product platform or alter Hermes pins,
governance acceptance, credentials, deployment policy or installed artifacts.

Before each implementation step, consult the applicable agreed plan and identify
its current step and acceptance criteria. If inspection requires a different
sequence, recommend the specific revised order and wait for user approval before
deviating. Do not infer approval to reorder from a general request to proceed.

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

# Maya Governance Product Integration Plan

## Status And Scope

Approved by the user on 2026-10-03 after the user-authorized
[integration assessment](maya_governance_integration_assessment_20261003.md).
The G0-G7 sequence is now the approved strategy. G0 bounded baseline acceptance
passed on 2026-10-03, with reviewed Linux control/candidate receipts in the
baseline runbook. G1 implementation was authorized after the security checkpoint.
The user subsequently approved the [pre-G1 security checkpoint](governance_security_checkpoint.md)
on 2026-10-03. Its four steps must be satisfied before G1 resumes. The approved
G1-G7 work packages are unchanged; Patch 24 is a separate security overlay, not
a new accepted G0 baseline or an installer authorization.
Security checkpoint run 37147131920 passed at commit
`5eaaca2e007760fb007c43c064b4f78ab69acf41`. G1 work package 1 is recorded in
[the request lifecycle contract](governance_g1_request_lifecycle.md); its source
foundations do not satisfy the complete G1 gate. Work package 2 now has a
source-only caller-entry candidate and complete-method probes. Work packages 3-4
subsequently completed the bounded evidence described below. No session-index
transition or installer was enabled by those changes.
This does not authorize plugin activation or rebuilding a ready installer.

Work package 3's Patch 26 source candidate and scoped method evidence are recorded
in the lifecycle runbook. Work package 4 now exercises the actual caller/closure,
native AIAgent, controlled real SDK transport and SQLite under a fixed resumed
session. Its fourteen-case matrix now includes cancellation-race and late-callback
checks; ordinary controls pass on patched and unpatched sources. Exact inputs are
pinned in `governance-g1-full-caller.json`. Bounded source-level G1 was accepted
on 2026-10-04 following the criterion review and the user's instruction to proceed.
The frozen input contract is unchanged. See the acceptance decision in the G1
runbook. G2 work package 1 is recorded in
[the session-ownership design](governance_g2_session_ownership.md). Work package 2
is specified in [the consistency protocol](governance_g2_session_consistency.md);
packages 3-5 remain sequential. No product qualification or installer authorization
follows these design deliverables.

This sequence supersedes the earlier session-write implementation order while
preserving its contracts and dependency order within G1-G3. Its Stage 2 Step 1
second sub-item remains incomplete. Existing descriptors/callers are useful evidence;
they do not satisfy earlier identity gates retroactively.

## Strategy

Keep one local Hermes execution runtime and one Maya action authorization gateway.
Keep the Maya-owned plugin as the policy adapter. Maintain only the native fork
extensions required to make selected boundaries genuinely mandatory. Observer
hooks, system-prompt instructions and tool-menu filtering are not security gates.

Change the unit of progress from an individual patch to a complete product path:

```text
Prepared local installation and authenticated identity
  -> owner-scoped native session
  -> leased native task/executor
  -> Hermes context plus governed Maya SMB retrieval
  -> final effective model request authorization
  -> real native AIAgent loop
  -> bounded tool authorization and result validation
  -> independently authorized follow-up inference
  -> governed conversation persistence and final disclosure
  -> accurate audit outcome and deterministic shutdown
```

The first qualification slice is deliberately bounded: one local instance, one
explicitly approved operator and customer-owned Telegram private-text polling;
the same principal contract for the authenticated loopback Local API; one selected
customer-owned model route; approved local business-memory retrieval and one
bounded document read. This is an integration milestone, not the complete Standard
edition and not a reason to remove required SMB capabilities from Product Spec V2.

Default exclusions for that slice: Hermes remote-runtime proxy, profile multiplexing,
automatic route/fallback, arbitrary plugins/hooks, general shell/code, delegation,
cron/Kanban/process workers, queued/steered/synthetic continuation, media and
unqualified external connectors. Exclusions require startup/entrypoint tests.
They must not be enabled by an existing Hermes home, environment variable,
configuration change or ordinary fallback. Maya-managed model billing is
not the same as Hermes remote-runtime proxy; its later contract is preserved.

Preserve three distinct stores: Hermes conversations and MEMORY.md/USER.md;
Maya SMB SQLite/vector memory; Metabase application/analytics storage. Context
retrieval and ingestion use local policy, provenance and classification. No
automatic conversation copy into business memory is introduced.

## Working Rules

1. Every work package states supported roots, excluded roots, failure behavior,
   evidence level and acceptance gate before coding.
2. A new finding joins the coverage register. If it alters milestone order or
   expands scope, stop, propose the precise change and obtain approval.
3. Do not create another patch simply to move a focused test from red to green.
   Show its effect on the complete mapped caller and a legitimate allowed control.
4. Maintain baseline-native ordinary-mode regressions as isolated controls;
   production may never fall back to ungoverned mode.
5. Do not mark a milestone complete when required tests skip, use a replacement
   runtime, rely only on rewritten AST catch bodies, or omit required dependencies.
6. Native complete-method probes and mocks are useful diagnostics, but only real
   native class/loop integration can qualify the product path. Replace transport
   I/O with controlled fixtures in offline tests, not AIAgent/session/governance.
7. No commit, fork publication, source-pin update, patch consolidation, signing-key
   change or production activation is implied by this plan.

## Milestone 0: Reproducible Coverage Baseline

Dependencies: user approval received. G0 progress and acceptance evidence are
recorded in [the baseline runbook](governance_g0_baseline.md). Do not infer G0
acceptance merely from reconstruction or focused test success.

### Work Packages

1. Build a credential-free assessment/test stage from Git objects at the exact pin.
   Verify source blobs, patch bytes/order, packaging-only changes and dependency
   locks. Do not use dirty working files as a release baseline.
2. Create a maintained coverage register keyed by lifecycle boundary and actual
   entrypoint, with supported/blocked/unresolved classification, patch/function,
   exact test, observed sink and artifact qualification level.
3. Fix the qualification profile and test fixtures. Select the actual provider API
   compatible with the explicitly configured model; do not assume Chat Completions
   and Responses are interchangeable or silently change provider/model.
4. Define a bounded ordinary-Hermes regression suite for every changed subsystem
   and a full-fork qualification job with prepared dependencies. Separate unrelated
   environmental failures from changed-path failures without suppressing either.

### Acceptance Gate G0

Two independent clean stages reconstruct the same native bytes and patch manifest.
All supported and excluded roots are registered; unknown dynamic roots block
profile acceptance. Every required test has its dependency and must execute.
Documented test scopes, including older four-boundary installer evidence, are
accurate. Do not require every Hermes feature to become supported.

## Milestone 1: Trusted Request And Caller Lifecycle

Maps to session-write Stage 2 Step 1's current second sub-item. No allowed session
index transitions are introduced here. Use an explicitly provisioned fixed test
session until the next milestone passes.

### Work Packages

1. Define the versioned host request/lifecycle contract: authenticated requester,
   any explicit execution delegation, request ID, session/database, classification,
   permitted operations, expiry and owning thread/task. No prompt/body/DB record
   supplies authority. Define root cancellation and timeout semantics separately
   from forcibly terminating a Python thread or undoing an authorized transaction.
2. Close caller-entry paths before provider selection, profile/cache work, proxy
   dispatch or supporting-task creation. Missing binding/factory denies with fixed
   error. Block unqualified proxy and alternate roots at their effective entry.
3. Ensure cancellation/error/timeout revokes governed executor authority before
   cleanup awaits. Preserve essential resource cleanup, propagate typed denials,
   observe task failures and prevent late model/tool/write/delivery callbacks.
4. Exercise the complete native `_run_agent` / `_run_agent_inner` callers and actual
   conversation closure, using native AIAgent with controlled SDK transport and
   real native SQLite. Cover missing scope, wrong owner, normal return, construction
   failure, policy/audit/storage failures and cancellation races.

### Acceptance Gate G1

An authenticated request traverses the actual native caller/task/thread with the
same permitted identity/session/database/classification. Missing or expired authority
causes zero protected effects. Proxy, background and nested jobs cannot reuse it.
Caller cancellation, swallowed child cancellation, timeout and cleanup failure
produce no subsequently authorized effects. Already-authorized transactions are
reported accurately rather than claimed rolled back. Ordinary controls pass.

## Milestone 2: Session Ownership And Remaining Frontend Identities

Depends on G1. Preserves the previously approved order: authorized session-index
transitions next, then normal CLI/setup/maintenance identities. It does not use
stored session ownership as proof of a newly authenticated caller.

### Work Packages

1. Design owner-scoped create/resume/reset/switch and session rotation. Separate
   authentication binding from per-operation permissions and storage provisioning.
   Enumerate post-compression index writes, cached-session rewinds and direct index
   writers, not just Patch 20's three methods.
2. Define the SQLite/index consistency protocol: authoritative record, atomic file
   replacement, operation correlation, crash recovery and compensation. Validate
   before mutation. Do not promise a cross-store atomic transaction.
3. Implement/re-enable one transition at a time only after its denied and allowed
   native-path tests pass. Reset never silently elevates delete/create permission.
4. Compose the pinned SDK polling intake with the complete native conversation
   path. Bind the exact host-approved owner/session before dispatch; no ordinary
   handler fallback or identity transfer from a queued/synthetic event. Qualify
   bot registration/start/stop/reconnect separately with synthetic platform I/O.
5. Unify normal loopback API/CLI caller identity with the same lifecycle authority.
   The public runtime may not overwrite it with a configured default actor. Define
   separate explicitly consented local setup and maintenance principals.

### Acceptance Gate G2

Authenticated Telegram/private-text and loopback API execution reach native AIAgent,
not an echo/storage-only harness. Wrong/revoked bot/user/chat/token never invokes
the agent. Fresh and resumed sessions are isolated; reset/switch/rotation cannot
leave an unauthorized index or partial replacement after crash/failure. CLI and
setup/maintenance identities cannot borrow conversation or administrator authority.
This closes Step 1 only for the explicitly documented profile; broader ingress
remains blocked. Mark excluded features as excluded, not qualified.

## Milestone 3: Memory, Storage, Provisioning And Durable Outcomes

Depends on G2. Completes session-write Stage 2 Steps 2-4 using the existing
descriptor/caller work rather than starting a parallel persistence architecture.

### Work Packages

1. Reconcile all five native gate registrations and startup compatibility. Review
   every direct SessionDB, transcript/index/trajectory, mirror, built-in memory and
   skill writer. Map any intentional no-op separately from a missing required store.
2. Qualify explicit setup/schema/repair/migration permissions before native database
   construction. Make runtime reopen distinguish validation from automatic repair.
   Maintenance writes require consent, backup/recovery and dry-run where applicable.
3. Bind governed business-memory retrieval/ingestion to authenticated or explicitly
   delegated authority and classification. Reconcile native provider and fallback
   bridge contracts; refuse incompatible tool schemas. Do not guess owners from
   record contents or lower confidential input to `internal` by default.
4. Define approved Hermes builtin-memory behavior under governance. Test MEMORY.md
   and USER.md purpose/root boundaries, session history retrieval, explicit writes
   and revocation without redirecting them into Maya SMB memory. Background review
   stays blocked until separately qualified; disclose the temporary limitation.
5. Prove final serialization, atomic append/rewrite/compaction, lock/accounting and
   outer-caller behavior on real native databases. Qualify compression rotation with
   new session authority, rather than silently rebinding a fixed-session lease.
6. Design durable outcome correlation using existing stores, for example a reviewed
   transaction outbox/reconciliation protocol. Record attempted/committed/rolled-back/
   uncertain outcomes, replay and startup recovery. The exact design needs review
   before implementation; adding an authorization JSONL entry is insufficient.

### Acceptance Gate G3

Schema/maintenance cannot run with conversation privilege. Denied batches, replacements
and locks leave the promised storage state intact. Crash recovery distinguishes
authorization from commit. Retrieval denies before reading unapproved SMB content,
and provenance/classification survives final prompt assembly. Hermes conversation
and preference memory remain separate and their supported operations actually work.

## Milestone 4: Model Egress, Disclosure And Recovery Qualification

Depends on G3. Extends prior model/tool patch evidence to complete calls and actual
delivery/persistence sinks for the selected provider API.

### Work Packages

1. Observe final wire requests after native transforms/transport adapters. Verify
   endpoint/provider/model, credential source, classification and consent. Disable
   SDK retries and uncontrolled redirects; each permitted new attempt needs a fresh
   gate with its effective payload/route. Network spying is fixture-level evidence,
   not a substitute for request-policy design.
2. Cover auxiliary title/compression/summary/plugin calls, refresh/fallback/error
   paths and direct clients. Unsupported APIs/provider workers fail before transport.
   Distinguish model inference from other credential/control-plane network requests.
3. Keep early streaming/reasoning/interim/progress muted in the initial profile.
   Validate final output after gateway formatting and before delivery/log/storage.
   Qualify buffered streaming separately; no unvalidated delta or diagnostic text.
4. Replace raw provider, invalid-response, header/cause, gateway and cleanup errors
   at actual public/persistent sinks with fixed diagnostics. Retain private typed
   errors only where necessary for classification; no prompts or key fragments.
5. Make unavailable/missing identity, gate failure, audit failure and typed denial
   terminate without provider fallback, observer success, tool continuation or
   healthy-looking recovery. Cover ordinary legitimate transport failure controls.
6. Test token-budget/iteration exhaustion, partial stream, disconnect, user interrupt,
   cancellation, compression and reconnect as distinct complete-path scenarios.

### Acceptance Gate G4

Denied egress produces zero fixture transport requests. Each allowed request/tool/
follow-up request has the corresponding gate in observable order. Denied output
never reaches platform sends, API response bodies, logs or persistence. Seeded
markers in arguments, provider bodies, exception causes, headers and cleanup remain
absent from all public outputs. Genuine transport failure does not fabricate success.
Selected ordinary-Hermes regressions and required fork checks pass without skips.

## Milestone 5: Useful SMB Capabilities And Enforced Exclusions

Depends on G4. A safe narrow conversation is not yet the promised Info Manager.
No generic terminal/code permission is granted to make a skill appear functional.

### Work Packages

1. Add bounded Maya-owned/native adapters for governed document ingestion/search,
   approved document conversion, business-memory write/embedding rebuild and approved
   Metabase queries/publication. Bind every operation to targets, credentials, limits
   and outcome/idempotency semantics through the existing gateway.
2. Add explicitly consented customer-owned Telegram delivery and the selected SMB
   connector workflows. Google/Slack broker and Microsoft delegated setup keep their
   approved product/protocol requirements; no silent tenant or OAuth-app creation.
3. Define approval/redaction/constrained-action handling. Either implement the actual
   approved action binding and payload transformation, or honestly block that action.
   A confirmation/redaction result is never equivalent to ALLOW.
4. Maintain capability profiles and advertised tool/skill catalogues matching tested
   operations. Test skills as workloads, not simply installed markdown. Preserve
   useful Hermes context/skills behavior without allowing autonomous code mutation.
5. Explicitly block/exclude remaining cron, delegation, arbitrary plugins/MCP/shell,
   process/Kanban jobs, synthetic continuation and remote-runtime proxy at their real
   startup/dispatch roots. Supported workers require a separately approved job
   identity/lifecycle contract, not inheritance from a completed request.

### Acceptance Gate G5

End-to-end synthetic SMB workloads succeed: retrieve approved local information,
answer through the configured model, create an approved business record/document,
produce an approved analytics result, and perform a consented connector action.
Denied counterparts produce no unauthorized side effects. Missing dependencies
or permissions are clearly blocked, never healthy. Excluded routes cannot be
enabled by saved native state, environment, plugin commands or fallback.

This milestone must name the exact supported workflows. It does not imply that
every Google/Slack/Microsoft capability or every native Hermes tool is supported.

## Milestone 6: Reviewed Fork Artifact And Test Installer

Depends on G5 and independent review of the fork contract/threat assumptions.
This is session-write Stage 3, not a shortcut around its preceding gates.

### Work Packages

1. Consolidate candidate patches only after behavioral equivalence tests, preserving
   original hashes and a reviewed old-to-new boundary map. Changes to the baseline
   Hermes pin require a separate compatibility review; no automatic upstream upgrade.
2. Produce one versioned governance contract and a profile-specific qualification
   manifest. Include all five gates, lifecycle authority, exclusions and evidence
   references. Registry presence/capability strings alone cannot grant readiness.
3. Build a wheel from clean pinned Git objects with patch/dependency/source hashes,
   license and provenance. No tests, caches, repo paths, raw credentials or host
   configuration may enter product artifacts. Stage it in managed Python offline.
4. Update the isolated five-boundary candidate host and installed qualification only
   for this reviewed artifact. Verify normal native discovery before construction,
   not only direct test registration. Keep separate AppId/home/data/shortcuts.
5. Run the complete supported-path and denial/recovery matrix from installed artifacts
   only. Qualify Windows shell/document/model dependencies actually used; supplied
   customer dependencies cannot prove clean-machine readiness.

### Acceptance Gate G6

Built and installed native modules match reviewed bytes. All required artifact
tests execute with zero skips and no repo/import shims. Tampered/missing callbacks,
unapproved wheels and unsafe profiles block startup. Candidate reports remain
test-only until the final Windows/product gates pass. Unsigned compiled installers
still require explicit local-smoke override; no signing keys enter the repo.

## Milestone 7: Product Setup And Clean Windows Release

Depends on G6. Re-enters Product Spec V2 setup/recovery/distribution acceptance,
not an alternative Phase 6 architecture.

### Work Packages

1. Qualify first-run noninteractive and guided setup, provider/model choice and local
   DPAPI/Credential Manager storage. Reject ambient credential fallback in the managed
   host; do not print key fragments. Reinstall must distinguish reused local state
   from a clean profile and show that choice without revealing secrets.
2. Validate customer-owned Telegram authorization and explicit connector consent.
   Start runs the usable product action; Doctor reports actual governance and profile
   readiness. A listening Local API port is not proof Telegram or inference is healthy.
3. Test fresh Windows install, start/stop/restart/reconnect, cancellation/shutdown,
   uninstall/reinstall data retention, backup/restore, schema migration, signed update
   and rollback. Protect Hermes and SMB stores as separate backed-up components.
4. Run an explicitly authorized live-provider/Telegram test with synthetic business
   data, customer credentials in the approved local backend and fixed usage bounds.
   Offline fixtures remain the safety regression suite; a live denial test need not
   transmit prohibited content and must count zero denied transport attempts.
5. Independent review approves the supported scope and evidence. Release tooling may
   then change production qualification, runtime pin and compatibility marker through
   a reviewed release decision. Sign the final executable and update metadata.

### Acceptance Gate G7

A genuinely clean Windows machine completes the disclosed supported Standard
workflows and lifecycle/recovery matrix using installed artifacts. Readiness,
secrets, consent, local-first storage, audit outcomes and rollback all pass.
No Windows production support claim precedes this gate. Enterprise broker-disabled
and sovereign requirements remain compatible and explicitly tested where advertised.

## Acceptance Matrix Minimum

For each supported entrypoint test allowed and denied operations, missing/removed/
replaced gate, missing/wrong/revoked identity, expired lease, audit unavailability,
storage failure, duplicate/replay, cross-user/session isolation, cancellation and
restart. Observe transport calls, handler calls, platform sends, database/index/file
state, task liveness and audit outcomes; output booleans alone are insufficient.

For each excluded root test actual startup and dispatch with hostile saved
configuration/environment and absent profile prerequisites. For each changed native
subsystem run ordinary-mode controls against the exact unpatched baseline.

Required repository commands remain:

```text
python -m unittest tests.test_phase6_release tests.test_phase1_update tests.test_phase4_setup_health tests.test_phase6_closure -v
python scripts/validate_project_maya_context.py
python -m py_compile scripts/build_phase6_release.py scripts/verify_phase6_release.py
```

Those checks are necessary, not replacements for G0-G7. No subscription/time estimate
is asserted from patch count. Size each implementation work package after its
dependencies and exact native test harness are established.

## Approval And Next Action

Current decision, 2026-10-08: the user explicitly accepted bounded initial-reset
Step 4 on unchanged Patch 35 with every exclusion in
`governance_g2_reset_acceptance_review.md`. Create and initial reset are accepted
source-level transitions, not completion of work package 3 or G2. The remaining
work package 3 transitions are switch and rotation, each requiring its own
reviewed contract and ordered native qualification before frontend composition
in work package 4. Repeat reset remains denied; no scope extension, production
activation, runtime-pin change, wheel or installer rebuild is authorized.
The chronological progress notes below retain earlier evidence and decisions.
Switch Step 1's approved source-informed contract and ordered Steps 1-4 are in
`governance_g2_switch_transition.md`. It bounds the first switch to the retained
same-owner parent after an accepted initial reset. The user approved the contract
on 2026-10-08 and authorized Step 2's separate Patch 36 authority/atomic-sink
candidate. Ordinary mandatory switch stays denied; publication, caller/reader
composition and dispatch remain Step 3. No installer or production change follows.

G0, the pre-G1 security checkpoint and bounded source-level G1 are accepted.
The G1 decision and immutable evidence references are in the lifecycle runbook.
G2 work package 1's owner-scoped transition design and effective writer inventory
are documented in `governance_g2_session_ownership.md`. Work package 2's design is
in `governance_g2_session_consistency.md`: authoritative native SQLite, recoverable
index projection, correlation, recovery and compensation without cross-store
atomicity. Next is package 3: implement and test create first, then each remaining
transition individually. Package 3's first create authority/preflight increment is
recorded in `governance_g2_create_transition.md`. Source-only Patch 27 now exercises
native SQLite allocation/commit and strict index publication. Source-only Patch 28
adds step 3's published-route reader, detached cache and bounded append-only G1
scope. Step 4 crash/race evidence remains required before another transition.
The approved Step 4 caller-completion refinement is now design-defined in
`governance_g2_caller_acknowledgement.md`; source-only Patch 29 now implements
the bounded scope in an isolated native/Maya source overlay. Next is its full
native qualification, then create acceptance review. Design tests alone are
not runtime qualification, and the normal product runtime remains unchanged.
The separate caller failure matrix now has bounded evidence in
`governance_g2_caller_qualification.md`; complete create-to-agent caller evidence
is still Step 3 work before create acceptance review.
The empty-history native-loop diagnostic now identifies blocked lazy session
recreation. The user approved the bounded existing-session recognition dependency;
source-only Patch 30 implements the read-only contract in
`governance_g2_existing_session_recognition.md`. Native prompt-cache metadata
denial/catch still needs review before complete create-loop acceptance; no broad
metadata grant, reordered milestone or ready installer is authorized.
The boundary review is now in `governance_g2_prompt_cache_review.md`. It recommends
an explicitly governed no-snapshot profile with mandatory-denial propagation and
ordinary parity. The user approved that bounded decision; Patch 31 implements a
separate source-only overlay. Qualify its mode and cache paths before resuming
Step 3/create acceptance review. Accepted parent inputs and installed runtime stay unchanged.
The separate two-process conversation qualification is recorded in
`governance_g2_restart_loop.md`: bounded continuation/denial evidence under the
frozen Patch 31 profile, not production startup, frontend or general resume
qualification. Next reconcile Step 3/create-loop evidence against Step 4 criteria;
create, work package 3 and G2 remain unaccepted.
The approved evidence closure is reviewed in `governance_g2_create_acceptance_review.md`:
80 final-profile native cases, including independent-process contention/crash and
separate write/fsync failures, pass. The user accepted bounded source-level create
on 2026-10-05 with the review's exclusions. Next is reset within work package 3:
consult the owner-scoped design and consistency criteria before implementation;
reset remains disabled until its own native allowed/denied and failure tests pass.
Reset Step 1's specialized contract and ordered implementation sequence are in
`governance_g2_reset_transition.md`, pending explicit review before Step 2.
The existing G2 order is unchanged; no reset runtime candidate is implemented.
Frontend composition, work package 3/G2 acceptance and production remain open;
no runtime patch or installed artifact changed.
No operational transition or frontend is enabled by the source-only receipt path.
G2 runtime acceptance, frontend composition, production governance
activation and installers remain unqualified. Do not jump to an installer.
Record milestone acceptance and evidence incrementally;
an unforeseen dependency changes the plan only through a new approval checkpoint.

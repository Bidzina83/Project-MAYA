# G2 Create-To-Agent Loop Diagnostic

## Scope

Caller refinement Step 3 in G2 work package 3/create Step 4. The separate
`governance-g2-create-loop.json` pins the new diagnostic and the unchanged
caller-qualification inputs. The staged native/Maya overlay is verified by the
existing qualification verifier; no parent patch, host implementation or artifact
is changed. This is not accepted create-loop qualification.

The diagnostic composes real native preparation, acknowledgement, reader,
append-only G1 lease, bounded task/executor handoff, GatewayRunner conversation
closure and AIAgent. It uses the new session's actual empty transcript, the real
SDK with synthetic HTTP transport and zero retries. Native initialization is
fixture-owned. Title generation is explicitly replaced by an inert fixture;
tools, connectors, provider sockets and background workers are not qualified.

## Observed Blocker

The allowed first-turn attempt reaches AIAgent but fails before model transport.
`agent.turn_context.build_turn_context` invokes `AIAgent._ensure_db_session`.
The fresh agent's `_session_db_created` flag is false, so it attempts native
`SessionDB.create_session` despite an existing caller-acknowledged session.
The reader's separate authority correctly permits only append, not create.
The mandatory session-write gate denies this lazy recreation.

The regression now asserts that denial, zero model requests, no new messages,
unchanged database contents, acknowledged receipt retained and cleaned reader
state. Passing this test proves the blocker is reproduced; it does not prove an
allowed conversation succeeds. Preparation, acknowledgement, reader and model
denial cases are also exercised. Model denial may be preceded by lazy-create
denial; it does not independently qualify the model boundary in this new path.

## Proposed Dependency, Approval Required

Validation: five native blocker/denial tests passed with one known pytest
cache_dir warning and no skips. The input-provenance test and 47 required product
regressions passed (48 unittest cases total). Context validation, Python syntax
and whitespace checks passed. No allowed new-session conversation passed;
the successful tests explicitly preserve and verify the blocked behavior.

Before completing Step 3, introduce a separately reviewed source-only contract
for recognizing the already created session at the native lazy-initialization
boundary. Validate exact database/session, authenticated live request identity,
ownership, acknowledged route and executor lease before recognizing existing
state. Do not add create/metadata permission to an append-only lease, set private
flags in the host/test to bypass the gate, fabricate history, or permit ordinary
lazy creation in mandatory mode. Preserve ordinary Hermes initialization.

Proposed order: define that bounded contract; implement a separate hashed overlay
and denial/parity tests; rerun the real new-session allowed loop and independent
model-denial cases; then resume the existing Step 3 matrix and Step 4 acceptance
review. No other G2 transition, production activation, wheel or installer follows.

## Approved Recognition Increment

The user subsequently approved that bounded dependency. The separate read-only
contract and source-only Patch 30 are in
`governance_g2_existing_session_recognition.md` and
`governance-g2-recognition.json`. Original blocker inputs/tests remain frozen
against the original overlay; the new recognition tests use a separately verified
overlay. No private host/test flag bypass or create/metadata grant is introduced.

The allowed actual new-session loop now reaches synthetic model transport and
appends its user/assistant messages without lazy recreation. Native optional
system-prompt cache metadata is denied by append-only authority, but its caller
logs and continues. That catch and intentional omission versus required
persistence are not qualified by recognition. Complete create-loop acceptance
remains open pending review of this explicitly recorded boundary.

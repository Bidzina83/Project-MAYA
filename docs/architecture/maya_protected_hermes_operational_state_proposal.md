# Protected Hermes Operational State 1 Proposal

## Status

2026-10-22: the user approved proposal preparation after the successful
Construction 2 test and scoped manual cleanup review. This is a document-only
proposal. No new package, code correction, payload execution or VM/security
change is authorized by preparing it. Existing frozen packages and contracts
remain unchanged. Gate A and production activation remain blocked.

The proposed first state test covers native Hermes session persistence only.
File-based MEMORY.md/USER.md, external memory providers, context compression,
skills, task/Kanban state and governed customer-data access remain separate work.

## Construction 2 Outcome

The operator supplied the matching launcher SHA256
A101E3D3D4E6A11C30FB8884C1DBC58F317F0B80BB2F633A34DC7E7CBD1161E4
and report for version 0.1.2-hermes-construction.2 on Windows 26300.9711.
Its UTC interval is 2026-10-22T16:31:48.0742780Z through
16:33:56.0311179Z, including host preparation/cleanup rather than a measured
Python-only duration. Product consent, payload, reduced/restricted token and
six-filter readbacks passed. The child naturally exited 0 before cleanup;
both exact Python beacons, output capture and admitted construction evidence
matched. The real class and all 64 distribution versions matched, with no
outside-runtime module origin found in the completed scan.

The report confirms real agent/client construction, empty tools, disabled
memory, consumed and unchanged config, zero Hermes model-call counter,
context-shutdown return, close return and the SDK closure-method result.
The verdict is construction_completed_pending_independent_cleanup. The
corrected closure query worked in this bounded configuration; this is not full
Hermes operation, complete resource cleanup or no-network proof.

After normal launcher closure, the operator's read-only checks found:

- No matching host/child/Maya process and no recursive reparse points.
- No package-SID ACE across 7,386 entries, with zero processing failures.
- State restored to Medium integrity, with the expected system/administrator
  full access and operator Modify permissions.
- A successful WFP state export (exit 0, 2,169,814 bytes) and complete
  fragment-aware XML traversal found none of the exact six filter keys or
  sublayer key for the attempt.

These manual checks are scoped independent evidence. AppContainer profile
removal remains product-reported only. Do not change the retained report's
independent-cleanup flag or claim complete independent cleanup. No listener
fixture was created in this profile, so no invented listener check is required.
The one Construction 2 run allowance is consumed; no rerun follows its success.

## Source Basis And Store Choice

The retained pinned Hermes source is commit
b13e2fd6948a59eeb59fe618914147d97a2ee90a, not a patched or replacement runtime.
Read-only inspection identifies:

| Interface | Relevant behavior |
| --- | --- |
| hermes_state.SessionDB.__init__, line 690 | Uses get_hermes_home()/state.db by default; creates the directory/schema, enables foreign keys and requests WAL. read_only=True opens an existing DB without schema initialization. |
| SessionDB.create_session, line 1379 | Inserts a real native session record. |
| SessionDB.append_message, line 2490 | Appends a stored message and updates session counts; it is storage, not inference. |
| SessionDB.get_session/get_messages, lines 1766/2762 | Reads the session and messages in insertion order. |
| run_agent.AIAgent constructor | Accepts a concrete session_db and attempt-specific session_id; initial row creation is normally deferred until conversation use. The test must explicitly create its synthetic row without invoking a conversation. |
| run_agent.AIAgent.close | Attempts end_session(session_id, 'agent_close') for an attached DB; errors can be suppressed, so persisted end state needs readback. |
| SessionDB.close, line 1011 | Attempts a TRUNCATE WAL checkpoint, then closes and clears its connection; checkpoint errors can be suppressed. |
| apply_wal_with_fallback, line 240 | Existing native code can choose DELETE journal mode for recognized filesystem incompatibilities. Record the actual mode; do not silently call it WAL success. |

MemoryStore.load_from_disk/add/replace/remove and its Windows msvcrt locking
and atomic replacement are real separate interfaces, not substitutes for
SessionDB. They are intentionally excluded from this first package to keep
the permitted writes and interpretation narrow. No duplicate state abstraction,
new database schema, mocked runtime or hand-written alternative store is needed.

## Proposed One-Attempt Sequence

1. Reuse the product-owned consent/setup/restricted-launch/report/cleanup path,
   Python 3.13.14 and the same pinned Hermes and dependencies. Start with a fresh
   private state directory; do not migrate or import any existing profile/DB.
2. Verify runtime identities, HERMES_HOME/state binding and fixed config as in
   Construction 2. Require no pre-existing state.db or its SQLite sidecars.
3. Construct the real SessionDB at exactly state/state.db. Inspect its actual
   DB path and journal mode. Native schema initialization and optional indexing
   may create SQLite objects; do not inject a replacement schema or add modules.
4. Create exactly one attempt-bound synthetic session through create_session.
   Construct the real AIAgent with the same bounded offline constructor settings,
   except session_db is this concrete DB instead of None. Verify that binding
   rather than reusing Construction 2's expected-None assertion unchanged.
5. Append exactly two fixed synthetic records (user/assistant roles) through
   append_message, each at most 512 ASCII characters including the attempt
   marker. The assistant record is explicitly fixture text, not a model answer.
   No run_conversation, model API, tool dispatch or user prompt is invoked.
6. Read back exact session identity, both contents/roles/insertion order and
   counts through native getters. No extra session or message is acceptable.
7. Invoke context shutdown and agent.close as in Construction 2, even on an
   operation failure where an agent instance exists. Verify the SDK method
   result and that the stored session is ended with reason agent_close.
8. Close the writer DB in finally, independently of agent cleanup. Reopen the
   same path with native SessionDB(read_only=True), verify both exact records
   and ended-session state again, then close that connection. Do not patch
   native close methods or infer success from their return alone.
9. Admit the bounded result only after the existing confirmed job stop and
   product cleanup. Preserve synthetic DB/report files for inspection; no
   session deletion, transcript-file cleanup or machine reset is needed.

This is close/reopen persistence within one restricted process. It is not an
OS/process restart, crash recovery, power-loss durability, concurrency or backup
test. A later process/persistence test would need its own explicit scope.

## Fixed Configuration And Impact

Keep the same public non-secret placeholder, synthetic model, custom .invalid
URL, chat-completions API mode, empty enabled toolsets, skip_memory=True,
skip_context_files=True, load_soul_identity=False, checkpoints disabled,
quiet/no trajectory logging and no credential pool/fallback. Fixed config
continues to select the built-in context engine, context size 131072, disabled
compression, environment probe and tool search. No secret or server is added.

New disclosed writable content is state.db and native SQLite sidecars such as
state.db-wal/state.db-shm or a rollback journal during an unsuccessful attempt,
plus a bounded state-test report. Existing private config/cache/logs/sessions
paths remain. The DB is operational conversation state, not Maya's authoritative
memory, business state, governance or audit. No copying to another store occurs.

Exactly one writer and one subsequent read-only connection, one session and two
small messages are planned. Check aggregate DB/sidecar size against a proposed
32 MiB acceptance ceiling at bounded operation checkpoints. This is a fail-closed
postcondition, not a filesystem quota or guarantee that a buggy library cannot
temporarily exceed it. No customer content is available to this attempt.

No permissions are added: ordinary AppContainer, zero capabilities, reduced
same-user token, one-process job, child-process block, three inherited pipes,
isolated Python and all six WFP denies remain. All network access, including
model/metadata/localhost traffic, stays denied. No registry grant, loopback
exemption, manual ACL/label setup, supervisor, OS tuning, new dependency or
machine-wide Python/PATH change. Existing All Application Packages access is
still a containment limitation, not proven customer-data isolation.

Keep the 22-second cooperative budget, 30-second host deadline, payload bounds,
4,096-byte stdout bound and 65,536-byte captured-text/report bounds. No automatic
increase if SQLite initialization, locks or closure exceed the budget.

## Evidence, Failure And Limits

Require exact identities, natural exit 0, both Python beacons, no outside-runtime
module origins, correct effective/unchanged config, successful construction and
closure, exact native storage readbacks before/after reopen and reported product
security cleanup. Report DB relative path, actual journal mode, size/counts and
stage outcomes; fixed synthetic contents can be compared against their immutable
contract without dumping entire DB rows, logs, environment or raw exceptions.

For the proposed local-disk test, WAL must be observed for a full pass. If native
code chooses its existing DELETE fallback, preserve that fact and stop without
claiming WAL qualification; do not force journal mode or patch Hermes. Optional
FTS/trigram availability can be recorded, but full-text search is outside this
test's acceptance scope. Missing evidence or storage errors cannot be treated as
an optional healthy DB or substituted with another backend.

Keep failure stages distinguishable: import, DB/schema open, row creation,
agent binding, append/readback, agent closure/session end, writer closure,
read-only reopen/readback and security cleanup. Native schema recovery paths
exist upstream; no malformed fixture or repair experiment is approved. A fresh
DB failure stops for review, not a grant, new runtime patch or repeated attempt.

This proposed direct native storage exercise does not qualify tool-mediated
memory authorization, customer-data ingestion, model-generated writes, action
approval or gateway bypass resistance. Bound internal operational storage is
evaluated under restricted_hermes_execution_contract.md; production activation
remains blocked until the required independent enforcement is qualified.

## Next Decision

Approve preparation of this session-storage-only product package, including the
disclosed SQLite files, native DB/agent attachment, fixed two-record fixture and
acceptance checks. During preparation verify the exact pinned interfaces and
bounded evidence with static/inert checks, not local native Hermes execution.
Return any new dependency, permission or scope requirement for review. Then
review exact artifacts/impact before separately approving one RDP VM run with
fresh product consent. This proposal issues no VM command or runnable package.

## Subsequent Preparation Approval

The user approved this session-storage-only package preparation on 2026-10-22.
The implemented candidate and exact impact are described in
maya_protected_hermes_operational_state_handoff.md. This supersedes the earlier
proposal-only preparation gate, not the separate exact-artifact VM-run gate.
No native execution, additional permission, dependency change or further runtime
correction follows from this preparation approval.

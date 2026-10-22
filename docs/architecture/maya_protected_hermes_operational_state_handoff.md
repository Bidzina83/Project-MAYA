# Protected Hermes Session State 1 Handoff

## Scope And Approval

The user approved preparation of the session-storage-only package described in
maya_protected_hermes_operational_state_proposal.md. Version
0.1.3-hermes-state.1, scope offline-hermes-session-state-v1, targets the existing
customer-like Windows 11 Pro x64 26300.9711 VM through Remote Desktop.
This is an unsigned development component, not a production installer.
Preparation permits static/inert checks and compilation, not a native local
Hermes run or VM execution. Exact-artifact VM-run approval and fresh product
consent remain required. Construction 2 and all earlier artifacts are preserved.

## Product Behavior

The product uses the real pinned Hermes commit
b13e2fd6948a59eeb59fe618914147d97a2ee90a, Python 3.13.14 and the identical
63 dependency versions. No dependency download, native installation, patched
runtime, alternative schema/backend or mocked client is included. The existing
6,687 payload members remain unchanged; a state entry and immutable contract
are added. Previous source/payload files are not rewritten to add the profile.

The entry first verifies fresh HERMES_HOME/state binding, class/module origins,
all distribution versions and the existing fixed config. It requires absence
of state.db and its named sidecars before native SessionDB construction.
SessionDB creates its own schema and optional indexes; no custom schema is
injected. Actual main-database path, read-only binding and journal mode are
read through the native connection. WAL is required; a native DELETE fallback
is reported as failure, not forcibly changed or silently accepted.

The product creates exactly one session with ID maya-state-<attempt nonce> and
source maya-state-fixture. It constructs the real AIAgent using the same offline
settings as Construction 2, except session_db is this real writer connection.
It checks that exact binding. Two fixed ASCII records, each below 512 bytes,
are appended through the native append_message API:

- user: MAYA_SYNTHETIC_USER_STATE_V1:<attempt nonce>
- assistant: MAYA_SYNTHETIC_ASSISTANT_FIXTURE_NOT_MODEL_V1:<attempt nonce>

The assistant text is explicitly fixture data, not a model response. No user
prompt, run_conversation, inference, tool dispatch, connector or external
memory provider is invoked. MEMORY.md/USER.md and task/Kanban state are excluded.

Native getters must return exactly one session and two messages, with correct
source/model, roles, content, session IDs, increasing positive row IDs, counts
and initially unended status. Context shutdown and agent.close then run; the
real SDK's is_closed() method must return True and the client must be detached.
The native session row must show end reason agent_close and a non-null end time.

The writer DB is closed and its captured connection must reject a read with
sqlite3.ProgrammingError; merely clearing a reference is insufficient. The
database is reopened via SessionDB(db_path=..., read_only=True), verified again
through native getters, then closed and checked the same way. Remaining DBs
are closed on failure where possible, and any cleanup exception is reported
by type. Failure never becomes success because later best-effort cleanup runs.
Confirmed host job stop remains the outer process-cleanup boundary.

This tests close/reopen persistence within one process, not process/OS restart,
crash recovery, power loss, concurrent writers, backups or full-text search.
Native optional FTS/trigram availability is observed but not qualified. Native
malformed-schema recovery is not deliberately exercised or patched.

## Configuration And Paths

Fixed configuration and constructor settings are unchanged except for the
disclosed real DB/session binding. Tools, memory providers, context files,
checkpoints, compression, tool search and environment probing remain disabled.
The built-in context engine and context size 131072 remain. The real SDK/TLS
client still uses the fixed public non-secret placeholder, synthetic model and
https://maya-construction.invalid/v1; no model or gateway server is provided.
No credentials, existing home/.env, customer data or authoritative store is copied.

Each attempt uses the existing ProgramData/MayaProtectedPython-Startup1 root,
read/execute runtime and low-integrity writable operational state. Additional
disclosed files are state/state.db, SQLite WAL/SHM or rollback-journal sidecars
and state/hermes-state.json. Existing private config/cache/logs/sessions paths
remain; all files/reports are retained after security cleanup. The database is
synthetic internal conversation state, not Maya's authoritative memory,
governance, audit or business database.

Exactly state.db, state.db-wal, state.db-shm and state.db-journal contribute to
the 32 MiB acceptance ceiling. Named files must be regular, non-reparse files
within state. Aggregate size is checked after bounded storage/lifecycle stages
and the peak is retained; exceeding the ceiling blocks acceptance even if size
later shrinks. This is a postcondition, not a filesystem quota or a temporary
growth guarantee during native calls. Only one writer and one subsequent
read-only connection, one session and two small messages are intended.

## Unchanged Restrictions

Ordinary AppContainer, zero capabilities, reduced same-user token, one-process
job, child-process block, three inherited pipes, isolated Python flags and all
six package-scoped WFP denies remain. No ACL expansion, registry permission,
loopback exemption, network exception, new listener, mapping, supervisor,
global Python/PATH or Windows-policy change. Existing All Application Packages
access remains a limitation, not proven customer-data isolation. Model,
metadata, auxiliary and localhost networking all remain denied.

Payload bounds remain 8,192 files, 4 MiB index, 32 MiB per file and 256 MiB
expanded. The cooperative budget remains 22 seconds, outer host deadline
30 seconds, stdout bound 4,096 bytes and captured text/report bound 65,536.
No deadline increase, ordinary execution fallback or automatic retry is allowed.

The new compile-time HERMES_STATE profile requires HERMES_CONSTRUCTION and
HERMES_IMPORT. It reuses existing private-config setup and the exact product
security lifecycle. Legacy profile resource limits and behavior remain intact.
No VM-side test automation or manual security setup is added.

## Evidence And Stop Rule

Bounded untrusted child evidence includes import/config/construction/SDK
closure predicates, DB origin/path, actual journal mode, exact-count/readback
results, session-end result, writer/reopen/reader-close results and peak size.
Raw DB contents, environment, credentials and raw exception text are not
exported. Host admission requires the immutable identities, fixture version,
attempt/session binding, all required predicates, WAL, one session, two messages,
bounded positive peak size and empty failure fields. It does not accept an
import-only or construction-only report as storage evidence.

Only natural exit 0, exact startup beacons, admitted complete evidence and
reported product security cleanup yield state_completed_pending_independent_cleanup.
All production, containment and independent-cleanup flags remain False. Missing
evidence, timeout, fallback journal mode, denied resource, bad readback, closure
uncertainty or size violation blocks the attempt. Stop after the first separately
approved VM result; no new grant, runtime patch, replacement dependency or retry.

AppContainer profile removal still needs stronger independent evidence; prior
manual checks are scoped, not complete cleanup qualification. The existing
journal-less recovery issue is not addressed and forced-crash testing is not
approved. Full Hermes operation, governed customer/model actions, memory,
connectors, Metabase, Gate A and production activation remain unqualified.

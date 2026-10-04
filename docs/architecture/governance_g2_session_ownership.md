# G2 Owner-Scoped Session Transition Design

## Current Step

G2 work package 1, following bounded G1 acceptance on 2026-10-04. This is a
source-informed design, not a runtime capability or accepted G2 milestone.
Work package 2 defines the consistency/recovery protocol; work package 3 implements
one transition at a time. Telegram composition and normal CLI/setup/maintenance
identity work remain packages 4-5. The approved order is unchanged.

Source inspected: Hermes pin `b13e2fd6948a59eeb59fe618914147d97a2ee90a`, accepted
G0 patches 1-23, security overlay 24 and G1 overlays 25-26, verified through the
G1 composition contracts. Paths/lines below refer to that effective source, not
unpatched upstream or the older installed wheel. No native source is edited here.

## Authority And Ownership

Three independent checks are required:

1. Fresh host authentication selects the actor and classification using the G1
   binding. Prompt text, session IDs, index entries, transport display names and
   stored `user_id` fields never authenticate a request.
2. A durable, locally controlled owner binding determines whether that actor may
   address the selected conversation and routing slot. Ownership is not an
   operation permission and cannot replace fresh authentication.
3. Maya's existing action gateway authorizes the exact proposed operation and
   every consequential read/write. Existing append/metadata permission does not
   grant routing changes, creation, transcript replacement or deletion.

The initial profile has one explicitly configured principal per session; shared
groups, cross-owner delegation and ownership transfer remain denied. Token/bot
credential rotation does not create a new owner implicitly. A newly authenticated
identity must still resolve to the same approved principal and connector binding.

The proposed durable owner descriptor is associated with the existing Hermes
session store: instance ID, canonical database identity, native session ID,
host-approved principal ID, classification floor, connector/route binding reference,
binding version, lifecycle status and optional parent session ID. It contains no
credential values. It is not a new Maya memory database or parallel session engine.
Work package 2 must choose the precise native SQLite representation and protection
of that record; production schema creation remains G3 provisioning work.

Routing-slot identity is host-selected: local instance, approved connector
registration, approved private conversation and authenticated principal. Native
`SessionSource` and `sessions.json` may supply routing evidence, never authority.
Telegram bot/user/chat matching remains the approved host mapping; Local API bearer
tokens map to a configured principal, not a principal inferred from token contents.
Customer-chosen IDs are lookup selectors only. Resolve and authorize before returning
existence, titles, history or other owners' routing metadata.

Legacy rows/index entries with no verified owner remain unavailable in mandatory
mode. Do not automatically claim them from `origin.user_id`, filenames, titles or
the first requester. Explicit legacy ownership adoption belongs to separately
consented maintenance design, not a conversation fallback.

## Proposed Transition Contract

Use one host-prepared, single-use transition descriptor alongside G1 request
authority; it must not turn one fixed-session lease into a wildcard grant.
Fields: authenticated principal/request ID, canonical database, host-selected slot,
operation, source/target session IDs, expected owner-binding and routing versions,
classification, owning task/thread, revocable bounded root lease, expiry and unique
transition correlation ID. Target IDs are created
by the host or resolved from an existing verified owner binding. No request field
can enlarge the descriptor or its operation set.

Candidate gateway capability `session.transition` has distinct operations
`create`, `resume`, `reset`, `switch` and `rotate`. These names are design only,
not implemented or enabled. They supplement, not replace, consequential
`session.read` and native `session.write` gates. Unknown operations deny by default.

First-session creation necessarily precedes a fixed-session conversation binding.
The existing G1 `CandidateSessionRequestBinding` requires a pre-provisioned session;
it is not a creation authority and must not be weakened to accept arbitrary IDs.
The proposed transition gate must require its own versioned, host-authenticated
descriptor using G1's bounded lease/owner checks before allocation. A bare identity
context or stored owner row is insufficient. This descriptor gives only the
prepared transition permission through the existing gateway, not model, tool or
append authority. The first fixed-session conversation scope is issued only after
the target owner/route state passes work package 2's consistency conditions.
The native transition contract and registration remain unimplemented until
work package 3; no current plugin callback gains this authority from the design.

| Operation | Required scope and effects | Explicit non-permission |
| --- | --- | --- |
| Create | Authorize allocation in one owned routing slot, create session plus owner binding, then bind a new fixed-session request scope | No implicit schema repair, old-session deletion or adoption |
| Resume | Authenticate again, verify target owner/classification and authorize history access; reopen only with separate lifecycle write permission | Knowledge of an ID/title is not access; no foreign-session enumeration |
| Reset | Explicitly authorize source finalization, new-session allocation and slot replacement; retain old transcript by default | Does not confer delete, clear, rewrite or ownership-transfer permission |
| Switch | Verify ownership and permissions for both source and target, authorize slot replacement and any end/reopen writes | No actor change, classification downgrade or transfer of cached state |
| Rotate | Under the same authenticated owner, authorize child allocation and source finalization before native compression mutations; preserve parent lineage | Compaction permission alone cannot allocate a child or rebind the route |

Classification cannot fall below the verified source/target floor. Incompatible
classification or owner changes fail closed; do not silently constrain by downgrading.
Expiry/revocation is rechecked before each new authorization. A completed external
or SQLite effect is not falsely undone by revocation. Reporting and reconciliation
must follow the later consistency/outcome contracts.

The old request's executor lease cannot be mutated to authorize a new session.
Revoke the old scope and issue a separately host-bound scope only after the
transition's required owner/route state is verified. Work package 2 defines the
visibility point, version recheck, exclusion/locking and crash recovery. Cached
agents, prompt history, approval state, pending images/events and provider overrides
are not transferable solely because the new route has the same session key.
Unqualified queues/background workers cannot perform transitions on the user's behalf.

## Effective Native Writer Inventory

Patch 20 denies `get_or_create_session`, `reset_session` and `switch_session`
before mutations in mandatory mode. It does not gate every `_save` or transcript
path below. All listed paths are design inputs, not newly qualified capabilities.

| Root / effective location | Effects to mediate | G2 treatment |
| --- | --- | --- |
| `gateway/session.py:997` get/create, including expiry, suspended and resume-pending branches | Slot lookup/touch, replacement, old end/new SQLite row | Split read/resume/touch from create/reset; keep existing deny until each is qualified |
| `gateway/session.py:1274`, `:1329` reset/switch | Index replacement before separate end/create/reopen SQLite calls | Source and target ownership plus all distinct permissions; no JSON-only fallback |
| `gateway/session.py:1101`, `:1117`, `mark_resume_pending`, `:1161`, `prune_old_entries` | Touch/accounting, suspend/recovery flags and pruning | Owner-scoped metadata/maintenance descriptors; recovery workers remain excluded |
| `gateway/session.py:830` `_save`; `:800` `_ensure_loaded_locked` | Index serialization/replacement, load and directory creation | One guarded transition entry plus guarded sink; index contents never grant authority |
| `gateway/session.py:1412`, `:1456`, `:1492` | Append/mirror, hard rewrite, SQLite soft rewind | Separate transcript permissions; rewind cannot bypass owner checks or typed denial propagation |
| `agent/conversation_compression.py:590-640` | Old session end, temporary agent ID change, new child creation and failure restoration | Preauthorize owner-scoped rotation; precise sequencing deferred to package 2, full compression to G3 |
| `gateway/run.py:16319-16322` native closure | Post-compression direct entry ID replacement and `_save` | Do not trust `agent.session_id` as authorization; verify prepared child binding before route update |
| `gateway/run.py:9772-9774` outer result handler | Replaces entry ID from result and saves routing index | Result cannot mint target authority; reconcile with the same transition/version |
| `gateway/run.py:9385-9403` hygiene compression | Temporary agent rotation, direct save and transcript rewrite | Excluded until owner-bound executor and full compression permissions qualify |
| `gateway/slash_commands.py:2862-2893` manual compression | Temporary agent rotation, direct save, rewrite and token update | Same rotation/compaction distinction; no ad hoc administrative identity |
| `gateway/slash_commands.py:1818-1835`, `:2066-2067` retry/undo | Truncated transcript rewrite and soft rewind | Owner plus rewrite/rewind permission; cached-agent history must agree with committed state |
| `gateway/slash_commands.py:3214-3222`, `:3386`; `gateway/run.py:6121-6127` | Resume, branch switch and CLI-to-gateway handoff | Verify both identities/targets; normal CLI binding remains package 5 |
| `gateway/run.py:4902`, `:6283`, `:6300`, `:6685`, `:9753` | Restart suspension, expiry deletion/flags, clearing resume-pending | Not user authority; background/maintenance roots stay unqualified |
| `gateway/run.py:8935-8977`, `:11839`, `:11993` | Initial session selection and Telegram topic restore/binding | Topic/bot/chat record is not authentication; compose only in package 4 |
| `plugins/platforms/slack/adapter.py:2259` | Slack-triggered native session creation | Outside initial customer-owned Telegram/Local API profile; keep excluded |
| `gateway/mirror.py`, `gateway/channel_directory.py` index readers | Route/session metadata lookup that may feed writes/disclosure | No inferred owner from JSON; mirror writers belong to G3, other ingress remains excluded |

This inventory covers the searched effective SessionStore mutators, direct gateway
`_save` callers, compression producers and principal ingress callers. It is not
a claim of exhaustive dynamic/plugin coverage. Before enabling any transition,
repeat the source search and native caller tests; a newly discovered root blocks
that transition until mapped, without changing milestone order automatically.

## Failure And Required Test Matrix

Missing/revoked identity, unknown owner, foreign target, classification mismatch,
stale descriptor/version, replay, expiry, busy slot, missing required store, policy
denial or unavailable audit must deny before new unauthorized effects. Existing
ordinary-mode recovery must never become a mandatory-mode fallback.

Work package 3 must test allowed and denied transitions using actual native
SessionStore/callers and SQLite, not private dictionaries alone. Required cases:
same-owner create/resume/reset/switch; wrong owner even with a correct ID; forged
origin/index data; independent create/end/reopen/read permissions; reset without
delete; stale/replayed descriptor; revoke during transition; old executor still
running; cached history/approvals not carried across owners; post-compression
inner/outer route writers; denied rewind preserving transcript; restart/expiry
and unbound direct sink denial. Each test checks disk index, SQLite, audit,
in-memory routing and observed agent dispatch as applicable.

Crash/failure injection between stores, authoritative record selection, atomic
file replacement, compensation and recovery are work package 2's protocol inputs,
not a cross-store atomicity guarantee in this design. Full compression and durable
outcome reconciliation retain their G3 gates. No new schema, ownership table,
transition descriptor implementation, native patch or installer is produced here.

## Work Package 1 Exit

The owner/identity/permission distinction, operation matrix, cached-state and
rotation constraints, effective writer inventory, exclusions and required tests
are documented. Work package 1's design deliverable is complete; runtime G2
acceptance is not. Next, in the agreed order: work package 2 specifies SQLite/index
consistency and recovery before work package 3 enables any transition.

Verification for this documentation-only step on 2026-10-04: 25 provenance
checks and all 47 required release/update/setup/closure tests pass. Product-context
validation, required release-script syntax checks and diff checks pass. Native
source, G1 frozen inputs, runtime modules, wheels and installers are unchanged;
the native suites were not rerun for this design-only change.

# G2 Existing-Session Recognition Contract

## Approval And Scope

The user approved implementation after the empty-history native-loop diagnostic
in `governance_g2_create_loop.md` (current execution date 2026-10-05). This is the bounded dependency within G2 work
package 3/caller-refinement Step 3, not a new milestone or create acceptance.
Patch 30 is a separate source-only overlay over the unchanged Patch 29 caller
and failure-matrix inputs. Production plugin activation, runtime pin, wheels and
installers remain unchanged.

## Read-Only Contract

`project-maya.existing-session-recognition.v1` recognizes an existing native
session at `AIAgent._ensure_db_session`. In mandatory mode the native initializer
requires the exact Maya published-reader class bound to its database. It calls
recognition even if its private created flag is already true. Only exact `True`
permits native initialization to record that existing state and return. There is
no ordinary-mode fallback, SQL mutation, transcript retrieval, schema provision,
session allocation, metadata write, model call or additional write grant.

The host reader checks the exact database object and host registration, active
reader selection, authenticated identity/classification, request and session,
database path, append-only operations, owning thread/task and live lease ancestry.
Recognition is limited to a bounded synchronous executor descendant of that
reader's root; an unbound caller, unrelated lease or main async task cannot use it.
Records and the private agent flag never supply authentication or authority.

Under native store/database exclusion, the existing reader revalidates ownership,
acknowledged receipt, route/version, instance/database binding and projection
integrity. It requires fresh `session.read` / `existing_session` authorization
and secret-safe audit acceptance, then checks binding, durable state and lease
again. Any missing, replaced, revoked, expired, foreign, legacy, pending, stale,
unavailable or unsupported input fails closed with a fixed native error. Each
subsequent initialization call repeats recognition; no durable grant is minted.
The existing G1 per-model/per-write gates still enforce actual effects. Recognition
is not a synchronized transaction with later effects or a grant surviving revocation.

Ordinary Hermes lazy initialization stays unchanged outside mandatory mode.
No system-prompt/model metadata is implicitly stored as part of recognition;
separately governed metadata and provisioning remain outside this read-only grant.

## Qualification Gate

Reconstruct and verify complete parent and modified native/host inventories with
`prepare_governance_g2_recognition.py`. Test the real newly created session's empty
history through acknowledgement, reader, G1 task/executor, AIAgent and the real SDK
using bounded synthetic transport. Prove no lazy SQL recreation, normal transcript
append, audited recognition before independently authorized model egress/output,
and cleanup. Model denial must now be observed after successful recognition.
Exercise missing/replaced registration, wrong identity/session/database, expired
or revoked authority, pending/legacy/stale state, projection/policy/audit/gate
failure, unbound/main-task/late caller, and cached-flag bypass attempts. Preserve
ordinary lazy-initialization controls against patched and exact unpatched Hermes.

Title/background workers, tools, external connectors, live provider sockets,
frontend authentication, schema setup and cross-store audit reconciliation are
excluded. Source-level results cannot qualify create, G2 or a production installer.

The real first-turn loop additionally attempts native system-prompt cache metadata.
Append-only authority denies that optional write; the native prompt-building caller
currently catches the denial and logs a warning. This read-only recognition contract
does not grant metadata access or qualify that catch. Intentional omission versus
required persistence and mandatory-error propagation needs a separately reviewed
decision before complete create-loop acceptance. Do not hide this limitation by
granting broad metadata permission or seeding a synthetic resumed history.

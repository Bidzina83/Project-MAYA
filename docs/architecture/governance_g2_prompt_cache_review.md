# G2 Prompt-Cache Boundary Review

## Current Step And Decision Status

This review is within G2 work package 3/create Step 4/caller-refinement Step 3.
The agreed plan requires a reviewed decision on optional prompt-cache behavior
before complete create-loop acceptance. Patch 30's inputs and recognition contract
remain unchanged. The user approved the bounded implementation order on
2026-10-05. Patch 31 is source-only; the approval does not authorize new write
permissions, milestone acceptance, wheels, installers or production activation.

The fixed host decision is `project-maya.prompt-cache-mode.v1`, returning only
`rebuild_without_snapshot`. The existing published reader validates exact live
executor authority and acknowledged state before and after fresh `session.read`
authorization for operation `prompt_cache_rebuild_without_snapshot`. No request,
environment or saved-session field selects this mode. The native helper checks
the exact reader and bound method, and converts unavailable decisions to a fixed
mandatory error before accessing the snapshot or building the prompt. Every
mandatory turn visits that decision, including cached in-process prompts.
Native per-agent caching is retained after the fresh decision; fresh agents build
normally without SQLite snapshot restore/update. Session-start hooks are not
repeated merely to refresh the mode decision. Independent transcript and model
gates remain mandatory. Touched read/write catches propagate fixed typed denials.

Reconstruction and full-tree/hash verification are defined in
`scripts/prepare_governance_g2_prompt_cache.py` and
`governance-g2-prompt-cache.json`; frozen Patch 30 inputs remain unchanged.

## Effective Native Path

Reviewed source: the pinned Hermes checkout plus the separately verified Patch 30
overlay, whose manifest SHA256 is
`89446a4f051e42884cc525623efa48c0e73f4336575cf0f9305dc0a688e620b0`.

`agent.turn_context.build_turn_context` first invokes governed existing-session
recognition. When the agent lacks an in-process prompt,
`agent.conversation_loop._restore_or_build_system_prompt` attempts to restore the
SQLite `sessions.system_prompt` snapshot. If unavailable or stale, it builds a
prompt from current native inputs and calls `SessionDB.update_system_prompt`.
That sink has a mandatory metadata-write descriptor; the reader lease permits
only append. The gate correctly denies it, but the native caller catches generic
Exception, logs a warning and continues to the model loop. This exception behavior
does not satisfy the mandatory-denial stop contract.

The actual new-session recognition test proves model execution and conversation
append without a successful snapshot write. It does not qualify the swallowed
metadata denial, snapshot restore authorization, cache correctness, credits
helpers, all hook callers or other metadata writers.

## Data Roles And Functional Impact

The SQLite system-prompt snapshot is a derived context/prefix-cache optimization.
It is not the session transcript, Hermes MEMORY.md or USER.md, Maya SMB persistent
memory, governance policy or an authoritative business record. It may nevertheless
contain sensitive derived context and stale identity/policy/runtime information;
calling it a cache does not exempt its reads or writes from governance.

An explicit no-snapshot profile can still assemble the native prompt, retrieve
governed SMB information, use Hermes's normal preference/general memory and append
authorized conversation messages. It may rebuild more often across fresh agent
instances/restarts, increasing latency or provider-cache cost. No numeric estimate
is established. In-process prompt behavior and current artifact/context loading
must be tested, not assumed to preserve freshness automatically.

## Options

| Option | Assessment |
| --- | --- |
| Add general metadata to the append lease | Reject: elevates a conversation request to unrelated model/config/lifecycle/cache mutation and violates the current contract. |
| Only rethrow the existing cache-write denial | Fail-closed, but every legitimate first turn remains blocked while that write is attempted. Not a complete allowed-path solution. |
| Narrowly authorize only a classified snapshot write/read | Potential later option, but requires field-scoped descriptors, exact effective-payload validation, provenance/freshness, sensitive-data policy and native storage/outcome tests. Coordinate with G3 rather than silently expanding G2. |
| Explicitly omit persistent snapshot use for the initial append-only profile | Recommended bounded option: no snapshot grant, native prompt construction remains, and mandatory failures are not treated as successful fallback. |

## Recommended Contract And Order

1. Approve a source-only, fixed `rebuild_without_snapshot` mode for this bounded
   profile. It affects only native SQLite prompt snapshot restore/persistence,
   not conversation/session records, Hermes memory files or Maya SMB memory.
   Describe the rebuild/cache limitation honestly. Do not accept a mode from
   prompt fields, environment, saved customer session contents or tool arguments.
2. Define a versioned request-bound decision through the existing published reader
   and local authorization gateway. Require the exact authenticated identity,
   acknowledged session/database/route, live bounded lease and fixed host profile.
   Fresh policy/audit approval of the mode decision must precede cache-helper use.
   Missing/replaced/unsupported decisions, stale authority or failed audit deny;
   absence never selects ordinary snapshot behavior in mandatory mode.
3. Implement a separate hashed source overlay. Choose omission before the cache
   helper's snapshot restore and before its SQL update, not inside an exception
   handler after a denied write. Build the native prompt normally. At the touched
   native cache read/write catches, propagate mandatory errors rather than warn
   and continue; preserve ordinary Hermes behavior outside mandatory mode.
   Required transcript/model/tool/write boundaries retain their independent gates.
4. Qualify real first-turn and resumed/restarted fresh-agent paths using actual
   transcripts, native AIAgent/SQLite and bounded real-SDK synthetic transport.
   Observe no cache-helper snapshot restore/update, unchanged snapshot bytes,
   correct native prompt assembly, allowed transcript writes, model allow/deny
   and mode audit order. Seed a stale/sensitive fixture snapshot to prove it is
   not incorporated in the effective request by that helper. Other SessionDB
   metadata reads are separate coverage, not implicitly qualified by this test.
5. Test missing/replaced mode binding, unknown mode, wrong request/owner/session/
   database, expiry/revocation, audit/policy failure and public secret-safe errors.
   Mandatory-denial injection at touched catches must stop, never log raw details
   or continue to model transport. Run ordinary controls on patched and exact
   unpatched source; rerun frozen parents and required product checks. Then resume
   the existing Step 3 evidence and Step 4/create acceptance review. Do not move
   to other transitions or infer G2 acceptance from the cache increment.

No implementation reordering, automatic metadata grant or installer rebuild is
implied by this recommendation. Source qualification remains narrower than the
product's complete memory, recovery and persistence requirements.

## Windows Line Endings

The local Git installation has `core.autocrlf=true`; unprotected LF text therefore
may be checked out as CRLF. This is informational, not evidence of an application
failure. Byte-hashed inputs require repository `text eol=lf` attributes. Existing
patch/manifest/native-test protections are retained, with targeted protections
for current context, tooling, provenance tests and review files added. Binary and
Windows launcher handling is unchanged. No global Git configuration, whole-repo
renormalization, forced checkout or index staging is needed for these additions;
the relevant Git index blobs were already LF. A synthetic Git checkout test under
`core.autocrlf=true` verifies LF/hash preservation and unrelated-file controls.

Seventeen checkout/provenance/design tests pass, including two real synthetic
Git checkout controls. The affected working-tree files were normalized in place
to LF without staging; Git reports LF in index/worktree with explicit LF
attributes. Hash-pinned runtime inputs and global Git configuration are unchanged.
Context validation, Python syntax and whitespace checks pass. The initial review
did not implement a cache runtime overlay.
All 47 required product regressions also pass. No runtime pin, production gate,
wheel or installer changed; no files were committed or staged by this increment.

## Patch 31 Qualification Boundaries

The native matrix uses actual AIAgent, the native conversation caller and SQLite,
and the real SDK with synthetic HTTP transport and zero retries. The resumed
case uses the actual persisted transcript and a fresh agent. It does not restart
the complete host process. Snapshot checks target only the prompt-cache helper;
other native metadata readers are not qualified. In-process reuse has separate
scoped helper evidence, not complete reused-agent lifecycle qualification.

Mode-denial helper probes exercise missing/replaced binding, contract/method and
unsupported mode, failed import, policy/audit failure and revocation. Additional
executor probes cover identity, request, session, database, operations, thread,
task, expiry and revocation. The read/write catch probes change the mandatory
flag at the failing sink to exercise otherwise omitted branches; they are not
an authorized persistent-snapshot profile or full-loop storage qualification.

Actual native-loop policy/audit/contract denials originate as the existing fixed
`mandatory_middleware.callback_failed`. The frozen executor converts that error
to its fixed governance failure; the gateway exposes the typed
`mandatory_middleware.session_write_failed`. The tests inspect the native
helper traceback as well as the public failure and zero model transport. They
do not claim exact reason-code preservation through the frozen outer caller.
No handoff contract is modified to improve this diagnostic behavior.

First-turn title/background workers, schema provisioning, connector identity,
other metadata writers, live providers, process-restart conversation qualification
and complete create-loop acceptance remain open. Continue the approved Step 3
qualification before Step 4 acceptance review; do not advance to reset/switch,
frontend composition, wheel or installer rebuilding on these results.

## Bounded Source Evidence (2026-10-05)

The final candidate matrix passes 26 native cases plus two patched ordinary
controls. Both ordinary controls also pass on the exact unpatched pinned source.
The unchanged Patch 30 parent passes its 24 native cases and three ordinary
controls; the frozen caller/failure matrix passes all 20 cases. No tests skip.
Native pytest reports the existing unknown `cache_dir` configuration warning
because its cache plugin is disabled; this is not a runtime failure.

All 47 required product regressions pass. Six final input-provenance and Windows
checkout tests pass, including Patch 31 hash preservation under `autocrlf=true`.
Context, syntax and whitespace checks pass. The final source/test input manifest
SHA256 is `3eb251230aa8dd8f5e0631c1cc4567ede6bafa4d0c687d430e94a1a52bf52cc0`.
The overlay is reconstructed from pinned Git objects and frozen parent inputs,
not edited into the customer's Hermes clone or installed runtime. Source-only
mode behavior is evidenced; complete Step 3/create-loop and G2 acceptance are
not asserted. No runtime pin, production gate, wheel or installer changes.

Next, within the approved Step 3 qualification: exercise the governed conversation
after a complete host/process restart, then reconcile the create-loop evidence
against its acceptance criteria. Do not infer that existing receipt restart tests
already establish this new conversation/cache behavior.

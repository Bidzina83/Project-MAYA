# G1 Trusted Request Lifecycle

## Current Step

G1 was authorized on 2026-10-03 after security checkpoint run 37147131920 passed
at Maya commit `5eaaca2e007760fb007c43c064b4f78ab69acf41`. Work package 1 defines
the versioned host contract and implements bounded lease foundations. Work package
2 now adds the source-only native caller-entry candidate described below. G1 itself
is not accepted: cancellation and complete native caller/loop qualification remain
work packages 3-4, in that order. No wheel or installer is produced.

Work package 3's source candidate now includes host revocation and native
cleanup/timeout wiring through Patch 26. Scoped native method tests pass; complete
caller/agent-loop behavior is still work package 4 and G1 acceptance remains open.

## Contract And Authority

`project-maya.request-lifecycle.v1` extends the existing `SessionWriteContext`,
not a parallel request registry or policy engine. The trusted host supplies:

| Field | Authority and meaning |
| --- | --- |
| identity | Authenticated actor plus host-selected classification; never prompt/body data |
| request_id | Unique host-generated correlation ID; not a permission or replay grant |
| session_id/database | Explicitly provisioned fixed native session and canonical database |
| operations | Host-bounded operation set; each effect still needs gateway authorization |
| thread_id/task | Exact owning execution context, not ambient inherited context |
| lease | Revocable root authority with monotonic expiry and dependent child leases |

No implicit actor substitution or classification downgrade is permitted. An
execution delegation is only the existing one-time factory selection of the
native conversation closure: root -> selected task -> selected executor. Each
receiver retains exactly the same identity, request, session, database and
operations, with its own thread/task owner and a lease depending on the root.
It cannot delegate to arbitrary workers, nested jobs or another session. No
independent execution principal or administrative authority is fabricated.

The candidate Local API host binding now supplies a finite timeout (120 seconds
by default, host-configurable within 0 < seconds <= 3600). Boolean, nonnumeric,
infinite and NaN values fail validation. Low-level historical source probes may
omit a deadline for compatibility; such scopes do not qualify this G1 host
contract. Request payloads cannot supply or extend the deadline.

## Revocation And Outcomes

Completion, exception, cancellation and timeout revoke authority. A root deadline
is checked on every lease validity test; all child leases depend on the root.
Expiry is terminal even if a captured context is reused. Explicit host revocation
uses only fixed termination reasons: completed, cancelled, timeout or failed.
The first recorded reason is retained. Scope cleanup cannot relabel a timeout as
successful completion. Termination labels are in-memory lifecycle facts, not
durable transaction-outcome or audit-reconciliation receipts.

Revocation does not forcibly terminate Python threads, cancel an in-flight SDK
request, undo an authorized committed transaction or recover external effects.
An effect authorized before revocation may complete; it must be reported as
committed or uncertain as appropriate, not falsely rolled back. Durable outcome
correlation remains G3 work. There is no lease-only authorization bypass.

Work package 3 must revoke the root before cleanup awaits on caller cancellation,
error or timeout, including swallowed child cancellation and cleanup failure.
The candidate native cleanup handler revokes before its first await; the host
deadline interrupts the owning task and native inactivity timeout is terminal.
These scoped controls are NOT yet complete native caller cancellation ordering
proof. Unbound identity-only legacy callbacks are not qualified
by this contract.

### Work Package 3 Host Controls

The selected `_LeasedRequestTask.cancel()` now revokes the root request before
delivering cancellation, rather than only its receiver lease. Sibling/root
callbacks therefore lose governed authority too, even if receiver cleanup awaits
or cancellation is swallowed. Cancelling an already finished task is a no-op.
Receiver exceptions revoke the root before the receiver's own context cleanup.
A completion callback retrieves abandoned task failures without logging their
contents; awaiting the task still propagates the original typed failure.

The existing conversation factory supplies `revoke_caller`, a synchronous,
owner-bound cleanup operation using the same caller scope and root lease. It
checks runner, identity, task/thread and session; an already expired scope can
still be revoked and retains its first termination reason. This operation is
called by Patch 26's native cleanup/timeout helpers and grants no execution authority.

Scoped tests observe root revocation before a receiver cleanup await, denied
late parent SQLite writes and actor access, worker error propagation, abandoned
failure observation, completed-task cancellation, wrong cleanup owners and
preserved timeout reasons. They do not exercise the complete native outer
cleanup, native inactivity timeout or delivery callback lifecycle. In particular,
revoking in `_receive` after a native helper raises does not prove revocation
before that helper's own internal cleanup awaits.

Patch 26 provides the native connection sites and scoped evidence below. Work
package 4 must verify them through the complete actual caller and conversation
closure before G1 acceptance; method probes cannot substitute for that gate.

Local verification on 2026-10-04: 54 request-lifecycle/handoff/authentication
tests and 19 baseline/caller-provenance checks pass. Re-running the 24 complete
native caller-entry method probes with the changed Maya host source also passes,
with zero skips. These receipts cover the controls described here, not the
complete native caller/agent-loop qualification.
All 47 required release/update/setup/closure tests, context validation, syntax
checks and diff checks also pass. No accepted baseline or security-contract
bytes, frozen fixture, wheel or installer were changed by these host controls.

## Supported And Excluded Roots

The first candidate is a host-authenticated fixed-session Local API request and
the selected native conversation task/executor path. Customer-owned Telegram
identity composition remains G2, after G1 caller qualification. Session index
creation/reset/switch/rotation, setup/schema/maintenance, proxy routing, profile
multiplexing, automatic fallback, background/recovery jobs, queued or synthetic
continuations and arbitrary hooks/workers remain blocked or unqualified. Existing
Hermes session and preference memory remain separate from Maya SMB memory.

Work package 2's contract requires denying missing binding/factory before provider selection,
profile/cache work, proxy dispatch or supporting-task construction at actual
`GatewayRunner._run_agent` / `_run_agent_inner` entries. Current scheduling helper
checks alone do not prove that earlier entry ordering. Unknown roots do not inherit
authority because a context variable was copied.

## Evidence And Remaining Gate

Foundation tests check the versioned context, finite deadlines, normal/error/
cancellation scope exit, captured context expiry, terminal revocation and parent
lease expiry. A real native SQLite test allows an append before the deadline,
denies the next append at expiry and observes the preserved committed row. These
are scoped source tests, not a full caller/agent loop or installed-product test.

Local verification on 2026-10-03: the request/authentication/handoff run passed
46 tests; the final foundation/plugin/Telegram-intake run passed 39 tests,
including all six lifecycle foundation cases. The explicit native SQLite deadline
and host-timeout validation controls also pass. All 47 required Phase 6/update/
setup/closure tests, product-context validation, syntax checks and diff checks
pass. Overlapping suites are not additive independent qualification receipts.

Work package 3's source candidate is recorded below. Work package 4 and G1 acceptance require the
complete native caller and AIAgent loop with controlled SDK transport, real SQLite,
wrong/missing/expired owner, construction/policy/audit/storage failures, cancellation
races and ordinary controls. No production activation, runtime pin, wheel,
capability marker or installer change follows from work package 1.

## Work Package 2: Native Caller Entry

Implemented as a separate source-only Patch 25 after the accepted G0 series and
Patch 24 security overlay. It changes native `gateway/run.py`,
`gateway/slash_commands.py` and the fixed-error allowlist in
`hermes_cli/middleware.py`. The historical G0/security contracts and fixtures are
not rewritten. The [candidate contract](governance-g1-caller-entry.json) pins the
patch, final native bytes and complete-method test bytes.

The existing Maya conversation executor factory now supplies
`project-maya.native-caller-entry.v1`. One native caller entry is selected per
authenticated root request. It requires the active finite root lease, matching
identity/session/database, exact owning task/thread, unchanged factory/resolver
and native executor method. A local authentication audit must succeed before
entry. Its scope is not a permission grant; every subsequent protected effect
still needs the existing gateway. Nested/replayed callers are rejected.

| Effective entry | Source candidate behavior | Observed boundary |
| --- | --- | --- |
| `_run_agent` | Requires trusted caller scope before profile routing | Missing/replaced binding, wrong/expired owner or database: zero proxy/config/profile lookup |
| `_run_agent_inner` | Requires the same active outer caller scope | Direct/unrelated-task entry rejected before proxy lookup |
| `_run_agent_via_proxy` | Excluded in mandatory mode | Denied before HTTP client import/dispatch |
| `_run_background_task` | Excluded in mandatory mode | Denied before agent import, adapter lookup or execution |
| `_handle_background_command` | Excluded in mandatory mode | Denied before event parsing and `asyncio.create_task` |
| Multiplexed profiles / interrupt continuation | Excluded at outer caller entry | No profile scope or inner execution |

Configured proxy routes are rejected after authenticated lookup but before proxy
dispatch. Missing mandatory callback bindings, audit errors and factory errors
produce fixed native errors, not request/provider text. The native ordinary-mode
branches are retained. Exclusion of these roots is not qualification of every
other worker, event handler, hook or prior intake side effect; those remain in
the G0 coverage register and later milestone work.

The probe loads the complete actual native `GatewayRunner` class and caller
methods. It uses a real native SQLite database and the real Maya factory and
five governance callbacks through native plugin registration. Fixture provisioning
is explicit and separate from conversation authority. The allowed control stops
at an observed configuration boundary, before provider selection/agent
construction. It is NOT an AIAgent conversation or product-qualification receipt.
The runner labels it `source_entry_methods_not_complete_loop` and exposes the
Maya source hashes used through an explicit source-test import path.

Local verification on 2026-10-04: all 24 final native entry probes pass without
skips. The selected existing ordinary-Hermes proxy/background/profile/model-route
controls pass on both final patched and unpatched sources (57 tests each), with
no failures, skips or omitted files. Independent final stages
`governance-g1-entry-20261004-d` and `-e` have identical caller-entry manifest
SHA256 `40ab17cf9b5049f36f05355359e64a0fbffd34fb263fa449a0246e37d9d4d7b8`.
The final -d stage retains `native-caller-entry-result.json`,
`native-caller-controls-result.json` and the locked dependency receipt. These
ignored generated stages are not product artifacts and must not be committed.
The 29 existing lease/handoff checks and all 47 required product tests also pass.
These are scoped source controls, not G1 acceptance or Windows support.

Work package 3's native candidate is described below. Work package 4 runs the
complete native caller, conversation closure and
AIAgent loop with controlled SDK transport and real SQLite. No session-index
transition, wheel rebuild, runtime pin or production activation is authorized here.

Reproduction commands (prepared pinned Git checkout and locked Python required):

```text
python scripts/prepare_governance_g1_caller_entry.py --source-repo <Hermes-clone> --output <new-stage>
python scripts/run_governance_native_regressions.py --stage <new-stage> --python <prepared-python> --mode caller-entry --g1-caller-entry
python scripts/run_governance_native_regressions.py --stage <new-stage> --python <prepared-python> --mode caller-controls --g1-caller-entry
python scripts/run_governance_native_regressions.py --stage <unpatched-stage> --python <prepared-python> --mode caller-controls
```

## Work Package 3: Native Cleanup And Timeout Candidate

Separate source-only Patch 26 follows Patch 25 without rewriting the accepted
G0/security contracts. Its [composition contract](governance-g1-caller-lifecycle.json)
hashes the parent contract, patch, effective native modules and native test file.
The release wheel, installer and production gate remain unchanged.

The native `_run_agent_inner` finally block calls `_maya_finish_caller` in
mandatory mode. It uses the factory captured at authenticated entry, revokes the
root synchronously before any cleanup await, cancels supporting tasks and the
selected executor task, and observes their exceptions without printing contents.
It does not flush a stream after cancellation or failure. Observation is bounded
to one second; an uncooperative task is observed when it eventually finishes and
blocks successful cleanup. The generation-aware native session slot is released
even when observation fails or cleanup is cancelled again. Existing typed denial
or cancellation is not replaced by an ordinary cleanup-task failure.

The caller wrapper passes exception information to the host scope, so failures
before inner cleanup still revoke the root. The host installs a monotonic deadline
timer at caller entry; expiry revokes authority before cancelling the owner task,
and scope exit cancels the timer. Native inactivity timeout calls a terminal fixed
error helper before raw diagnostics, result processing or continuation handling.
Neither mechanism kills a Python executor thread or rolls back committed effects.

Mandatory-mode progress, stream-consumer, heartbeat and interrupt-transcription
tasks are not started, and interim assistant delivery and inactivity-warning sends
are disabled. These unqualified delivery paths therefore cannot continue after
request revocation. Ordinary mode retains its existing task creation and cleanup.
This is not qualification of other frontends, callbacks, final delivery, general
workers or arbitrary adapters; those remain in the agreed downstream gates.

The native probes load the complete staged class and invoke its actual cleanup,
timeout and scope methods with real native SQLite and real Maya governance gates.
They test cleanup ordering, cancelled/failed/completed/timed-out roots, swallowed
cancellation, fixed cleanup errors, resource-slot release, host expiry, denied late
model/tool dispatch and SQLite append, plus excluded/ordinary delivery controls.
AST assertions separately prove the native finally/timeout connection sites; they
are explicitly structural evidence, not a complete `_run_agent_inner` execution.

Local verification on 2026-10-04: 13 native lifecycle probes and 24 caller-entry
probes pass with zero skips or omitted files. The result is labelled
`source_cleanup_methods_not_complete_loop`. Next is work package 4's actual native
AIAgent caller/closure, construction failures and complete cancellation races.
Do not advance to G2 or rebuild an installer from these method tests alone.

The final native overlay is reconstructed in the ignored
`governance-g1-lifecycle-20261004-b` stage. All 57 selected ordinary native controls,
55 host lifecycle/authentication/handoff tests and 22 baseline/overlay provenance
checks pass. These source receipts do not grant G1 or installed-product acceptance.
The final host-source rerun also passes all 13 + 24 native method probes. All 47
required product tests, context validation, syntax checks and diff checks pass.

```text
python scripts/prepare_governance_g1_caller_lifecycle.py --source-repo <Hermes-clone> --output <new-stage>
python scripts/run_governance_native_regressions.py --stage <new-stage> --python <prepared-python> --mode caller-lifecycle --g1-caller-lifecycle
python scripts/run_governance_native_regressions.py --stage <new-stage> --python <prepared-python> --mode caller-controls --g1-caller-lifecycle
```

## Work Package 4: Complete Caller Diagnostics

The `caller-loop` diagnostic mode verifies the exact Patch 26 source composition
before making a disposable offline copy. It copies the hash-checked caller-entry
fixture and records the complete-loop test bytes and Maya host-source hashes in
`native-caller-loop-result.json`. The fourteen-case inputs are now fixed by
`governance-g1-full-caller.json`, with pending acceptance and no production claim.
Earlier twelve-case receipts were evolving diagnostics, not acceptance evidence.
Neither receipt is installed-product qualification. Network sockets are blocked,
ambient credentials are removed, and required skips remain failures.

The test invokes the actual `_run_agent` and `_run_agent_inner`, selected native
`run_sync` closure, `AIAgent` constructor/conversation loop, OpenAI SDK and native
SQLite backend. Constructor/conversation wrappers only observe the original calls;
they do not replace the agent, closure or session store. Provider HTTP uses
synthetic Chat Completions responses and zero SDK retries. This does not qualify
the production GPT-6 Luna Responses route, live provider authentication or billing.

The host prepares a fixed existing session/database outside mandatory execution,
permits only create/append/metadata for that fixed session with per-write policy,
and supplies an explicit synthetic session model override. Three prior synthetic
exchanges exclude the native first-turn title worker without modifying its code.
No connector adapter, tool catalogue, profile multiplexing, session-index transition
or background worker is qualified. Native gateway construction/service startup,
schema provisioning and fixture teardown are not conversation authority.

The matrix observes normal completion and governed persistence, missing/wrong/
expired ownership before construction, policy denial, model-egress audit failure,
SDK construction failure and a real SQLite insert-abort trigger. Native fixed
mandatory errors are expected, not raw injected exception messages. Cancellation
and deadline expiry occur while the synthetic transport is blocked: its already
authorized request may complete, but the real worker finishes without another
stored message after revocation. Cleanup failure after a successful response must
propagate while preserving the already committed response, not claiming rollback.

G1 remains open for acceptance review. The evidence update below covers
complete-caller cancellation races, late callback denial, ordinary controls and
fixed inputs. Do not advance to G2, create Patch 27, rebuild a wheel/installer or
change the production gate on these source receipts alone.

Local verification on 2026-10-04: all 12 complete-caller diagnostic cases pass
with zero skips or omitted files. The final loop-test SHA256 is
`6a8074516176702d2867530b6bf1de7add95045d22500fc7b7f3c53f3f3f0a6f`.
The ignored Patch 26 stage retains `native-caller-loop-result.json` labelled
`source_full_caller_diagnostic_not_g1_acceptance`. All 23 baseline/overlay
provenance checks and 47 required product regression tests pass, as do context,
syntax and diff checks. The previously passing 57 ordinary native controls were
not rerun in this diagnostic slice; native source and host runtime bytes are
unchanged. No new Hermes patch, wheel, installer or production activation.

```text
python scripts/run_governance_native_regressions.py --stage <Patch-26-stage> --python <prepared-python> --mode caller-loop --g1-caller-lifecycle
```

### Cancellation-Race Evidence Update

The additional two cases keep the real caller, closure, agent and SQLite. One
fault-injects a suspended cleanup await after actual native synchronous revocation,
then cancels the owning request a second time. The other catches cancellation
only after invoking the original selected executor handoff, holds that child
await beyond native bounded observation, then lets it finish without restoring
authority. These are adversarial await faults, not replacement conversation loops
or claims that ordinary Hermes deliberately swallows cancellation.

After the original conversation loop exits, callback probes execute on its real
executor thread under the same child scope. They assert owner/thread matching
and revoked authority before attempting model execution, native tool dispatch,
model output and SQLite append. No transport/handler executes and no row is
added. Denial audit records are expected; no new allow record may appear. The
already authorized model request is counted as completed or uncertain, not
undone. Both selected child tasks are observed to finish, and the native running
slot is released even on repeated cancellation.

Local verification on 2026-10-04: fourteen full-caller cases pass with zero skips.
All 57 ordinary controls pass on both the Patch 26 composition and unpatched
native source. The new review contract binds the Patch 26 composition contract,
all three Maya authority modules, the full-loop test SHA256 and exact test count.
Tampered hashes, paths, host inventory, count or acceptance/production claims
are rejected. Test SHA256:
`d6d8ec97e090fd61f6922f020b46a8dae94080fca43905a867844d6c781908be`.
The result label is now `source_full_caller_g1_review_pending`.

The final pinned-input rerun passes all 14 full-caller cases, and the separate
native entry/cleanup rerun passes 24 + 13 cases, without skips or omitted files.
The host/product combined run passes 125 checks (55 lifecycle/authentication,
23 then-current provenance and 47 required product checks). A separate final
provenance run passes 25 checks, including both new input-contract tests.
Context validation, required release-script syntax checks and diff checks pass.
These overlapping suites are not additive independent qualification receipts.

| G1 criterion | Bounded evidence | Review limitation |
| --- | --- | --- |
| Same owner/session/database/classification across caller/task/thread | Actual construction scope and root-lease ancestry; native handoff and authenticated SQLite tests | Fixed pre-provisioned session, not G2 ownership transitions |
| Missing, wrong or expired authority denies effects | Full caller rejects before agent/transport; real SQLite deadline controls | No frontend transport lifecycle claim |
| Alternate roots cannot borrow authority | Native proxy/background/profile entry exclusions and unrelated/nested handoff tests | General workers remain excluded, not supported |
| Cancellation, timeout and cleanup failure remain terminal | Full caller cancellation/deadline, repeated cleanup cancellation and swallowed-child fault cases | No thread termination or external-effect rollback claim |
| Late effects cannot gain new authorization | Real executor model/tool/output/write probes; denial-only audit suffix and unchanged rows | Connector final delivery is outside the fixed profile |
| Prior effects reported accurately | One already-authorized request retained; committed response survives cleanup failure | Durable commit/outcome reconciliation remains G3 |
| Ordinary behavior retained | Same 57 native controls pass on patched and unpatched sources | Not complete upstream feature or full-fork qualification |

This is bounded source-level G1 evidence. Frontend transport/final delivery,
session-index ownership, provisioning, durable outcome reconciliation, production
provider routing, useful SMB tools and installed lifecycle remain their agreed
later milestones. No native patch or product-runtime source changed here, and
no wheel/installer was rebuilt. The next action is G1 acceptance review, not G2.

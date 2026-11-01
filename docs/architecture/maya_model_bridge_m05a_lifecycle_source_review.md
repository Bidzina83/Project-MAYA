# M05a Lifecycle Correction Source Review

2026-11-01. User approved M05a-only source correction and lifecycle tests after
maya_model_bridge_m05a_lifecycle_review.md. Candidate0.2.1-offline-budget.2,
file version0.2.1.12, unchanged scope offline-hermes-same-client-budget-v1 and
HERMES_MODEL_BUDGET profile/exclusions. No successor package, native product/
bundled Python/Hermes/SDK execution, VM/security change or additional run.
Companion contract: maya_model_bridge_m05a_lifecycle_tests.json. Budget1 and all
frozen predecessors are preserved. Earlier source/assembly approvals and old
test contracts are historical, not a successor package or run allowance.

## Corrected Schedule

The earlier schedule probed after run_conversation returned, when pinned Hermes
had already closed its actually-used request client. The correction arms one
fixed probe after the original grant binding and BEFORE native conversation.
The M05a-only mixin intercepts _close_request_openai_client immediately before
the ORIGINAL native close, not the ordinary parent SDK factory or conversation.

Eligibility requires reason=request_complete, an armed single cleanup callback,
the passed SDK being the UNIQUE used transport's SDK, original transport-owner
thread identity, one validated/completed exchange, open SDK/HTTP/transport,
same open bound consumed adapter and original requests1. No primary-client
substitution, re-creation, rebind, reopening or private guard-state reset.
Thread ID is private observation only and is never reported as authority.

Pinned nonstreaming helper sets its response then enters _call finally, calls
_close_request_client_once("request_complete"), and delegates request-client
close on the owner thread after releasing its holder lock. Its normal outer
loop waits while t.is_alive and joins the worker. Native-shaped inert fixtures
and AST checks cover this composition; no Hermes function was executed locally.
The helper bytes are now additionally verified at product class construction
against SHA256ff17762913d3e38aefa57fa22b56048f99d09fc18d189ab6441bf9c69433a76c.
The existing three Hermes source pins/dependency bytes remain unchanged.

Coordinator order is UNCHANGED: receive original model_runtime_receipt, confirm
actual delivery with worker and receive model_runtime_ack, then send fixed
model_adapter_probe. The owner-thread cleanup hook consumes this one control
on the existing private channel. No other child reader is active: main thread
is inside native conversation, and after return no longer reads probe control.
No diagnostic lock is held across pipe I/O. An abort can mark failure concurrently;
it delegates original native abort and poisons final admission, not a retry.

The SAME still-open used HTTP client sends the explicit second fixed request.
Original request validation and consumed-budget predicate remain unchanged.
Read-only observation records the intended rejection before pipe send. The hook
always delegates original native close in finally and verifies request SDK/HTTP/
transport actually closed, including when native close swallows its own error.
Each callback delegates once; only one callback can qualify. Duplicate callbacks
remain delegated but permanently fail admission and cannot probe a second time.

Hook diagnostic failures are stored as bounded failure state, not thrown into
Hermes's model retry/fallback machinery. A successful first response is never
treated as a probe pass: after native conversation returns, the child separately
requires genuine positive conversation, an exact successful lifecycle snapshot
and probe outcome. Any earlier failure/abort/duplicate/native-close fault blocks
that admission. All original agent/all-client closure checks still follow.

## Reporting And Acceptance

Retained child JSON and successful private completion report now use
maya.offline.model.budget.child.v2. Existing13 positive fields and probe_command_id/
probe are retained; new probe_lifecycle yields16 fields total. Probe remains the
original exact9-field observation and is still UNTRUSTED child testimony.
Lifecycle exact10-field successful snapshot:

- schema=maya.model.adapter_budget.lifecycle.v1;stage=complete;failure_stage="".
- armed=true;hook_calls=1;close_delegations=1.
- owner_thread_verified,used_client_verified,native_close_verified and
  probe_before_native_close all true.

Fixed bounded failure-stage labels are listed in the companion contract. First
failure stage is retained; generic raw exception text, request/lease/output and
thread IDs are not included. Child finally saves command/lifecycle diagnostics
even if post-conversation admission fails. Pre-construction failure may retain
stage=unavailable instead; that is never accepted. Top-level host failure reporting
is unchanged: detailed diagnostics remain in the retained child report.

ModelBudgetAdmission.Child requires exact v2 report/snapshot/probe fields and
types, original positive flags/one request/two-to-eight clients and actual command/
request bindings. v1 or missing/extra/failed lifecycle reports are rejected.
Owner/guard claims are not independently trusted Windows evidence. Host still
requires no extra child frame/trailing bytes, positive fixture final text without
publication, natural child/worker exit0, exact terminal snapshot and independently
admitted FOUR positive audit records. Worker protocol/service/audit admission,
gateway2/effects(1,1,0), zero extra pipe/effects/publication remain unchanged.

## Source Delta And Tests

Against Budget1, actual runtime Python delta is ONLY model_child_entry.py,
project_maya/hermes_plugins/model_bridge.py and model_budget.py. Only C# source
changes are ModelBudgetAdmission.cs and ProtectedPython.cs (case version/consent).
No new runtime source, entry, dependency or root omission. Original worker,
service, private channel, base guard, config, earlier audit verifiers and all
deadlines/grants/security setup unchanged. The future package contract will need
its own version/report-schema/test-contract binding update during separately
approved assembly; the old frozen M05 contract has not been rewritten.

339 focused Python tests/1173 subtests pass, including15 new lifecycle tests.
Coverage includes actual-used ownership, normal call/finally close sequence,
constructor/report thread different from request owner, missing arm/wrong close
reason, invalid control, abort before/during control read without lock deadlock,
duplicate cleanup, wrong SDK/thread, closed client, native close raise/swallowed
failure, first transport failure, immutable snapshots/no rearm, pinned source
tamper and AST lifecycle/outer-wait checks. Inert ordinary/mode regressions pass.
Exception/fault paths require failure, never synthetic passes.

C# BudgetFixtures219 active assertions/ten paired earlier profiles214 each;
ten invalid compile-profile controls rejected. Prior replay409 active/nine paired
400 each also pass. Counts overlap and do not qualify native interleaving.
All C# runs used explicit INERT fixture Main methods; no product Main/setup.
Existing unknown pytest cache_dir warning remains. Full repository suite was not
claimed or rerun; focused tests avoid unrelated missing-jsonschema collection.
Local recipes/vectors and scope check:
.codex-build/maya-model-budget-lifecycle-source-20261101-1.
Budget1 ZIP/EXE pins and272 frozen source copies verified; current source delta
is intentionally different from that frozen package. No prior artifact refresh.

## Remaining Gate And Risk

Native scheduling is unverified. The hook briefly waits for the existing trusted
control in the owning thread, consuming unchanged22/30-second child budgets;
it does not add a deadline or grant. First SDK/transport response has returned
when the hook runs, but full positive conversation must still be established
AFTER native close. Unexpected subsequent native client work sees the existing
closed adapter and blocks; no fallback is enabled. The original service grant
is not renewed, and this local rejection makes no unexpired-service-grant claim.

Review source/contract before separate Budget2 offline assembly approval. Proposed
payload delta is four replacements (contract plus the three runtime Python
files), no additions/omissions, and the two reviewed launcher source replacements.
Verify ALL actual-profile members, frozen dependencies, resources and source
identities during that future assembly. Do not reuse or overwrite Budget1.
Then actual guest path/hash, separate exact-artifact one-run approval and fresh
consent remain mandatory. No M05b/later case, inference, recovery/retry,
qualification or Gate A closure; all false flags remain unchanged.

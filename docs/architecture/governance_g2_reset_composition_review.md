# G2 Reset Step 3 Acceptance Review

## Decision

2026-10-07: the initial review held Step 3 acceptance. The user then approved
targeted diagnostics and the bounded correction described below. Step 4,
production activation, a new wheel and an installer remain outside this work.
The approved sequence remains in `governance_g2_reset_transition.md`.
Earlier frozen input manifests and accepted profiles are unchanged.

## Baseline Evidence Against The Gate

The evidence is bound by `governance-g2-reset-composition.json`: 15 native
composition cases, 22 unchanged atomic cases against the combined candidate,
88 ordinary native session cases, nine preparation tests and 47 product
regressions. These are source-level tests, not installed-product qualification.

| Criterion | Assessment |
| --- | --- |
| Strict publication and independently authorized normal-exit acknowledgement | Supported for tested initial create-to-reset lineage. |
| Pending caller cannot dispatch | Supported by pending-reader denial tests. |
| Caller failure cannot dispatch | Supported for seven tested failure cases; not established for uncertain acknowledgement plus failed quarantine. |
| Old transcript preserved | Supported by native SQLite and actual conversation tests. |
| Fresh agent with no old history or prompt cache | Supported by distinct native agents and synthetic SDK request checks. |
| Independent model denial stops transport | Supported; denied case makes zero SDK transport calls. |
| No old approvals transfer | Not demonstrated: the conversation fixture excludes tools and does not seed native approval state. |
| Invalid lineage cannot route | Supported by four corruption cases within the bounded lineage. |

## Approval Boundary

The effective native gateway retains route-keyed `_pending_approvals` separately
from running agents. Its `_clear_running_agent` explicitly does not clear that
state; `_clear_session_boundary_security_state` has a separate cleanup lifecycle.
Native tool approvals also have their own store and handlers. Therefore, creating
a new AIAgent and clearing SessionStore caches does not by itself demonstrate
approval isolation. This is an evidence gap, not a demonstrated unauthorized
tool execution. Review the actual boundary caller and late approval delivery
before selecting a narrowly scoped implementation or exclusion for approval.

## Uncertain Acknowledgement

Source inspection identifies a combined-fault concern in the staged
`reset_publication.py`. `_change` commits `caller_acknowledged`; an exception
reported after a successful commit cannot be undone by its subsequent rollback.
`prepare` then attempts quarantine, but preserves the original failure if
quarantine also fails. The reader accepts a matching durable acknowledged
receipt. Consequently, a committed acknowledgement plus failed cleanup could
leave an apparently readable route despite preparation reporting failure.

This is a source-inferred failure path, not a reproduced runtime result. Existing
tests do not establish safe restart behavior for it. The candidate must not be
described as blocking every caller failure. Durable audit reconciliation remains
G3; a fix must not invent a parallel authoritative store or rely on cleanup always
succeeding.

## Recommended Next Action

Request approval for a targeted approval-boundary assessment and an isolated
uncertain-acknowledgement diagnostic before advancing to Step 4. The latter
brings one combined-fault diagnostic forward from Step 4 solely to resolve the
Step 3 gate. Then propose the smallest source-informed contract correction,
obtain approval for any contract or sequence change, implement it, rerun the
bounded evidence, and repeat Step 3 acceptance review. Do not start the complete
Step 4 crash/race matrix until that decision is made.

Repeat reset, frontend identity composition, live transports, general tools,
schema provisioning, full-fork qualification and production remain unqualified.

## Approved Targeted Diagnostics

On 2026-10-07 the user approved bringing the targeted diagnostic forward.
`tests/hermes_g2_reset_gate_diagnostic_native.py` runs against the unchanged,
inventory-verified Patch 33 source using isolated synthetic native SQLite state.
Both diagnostic cases pass by asserting the defective baseline behavior:

- A real acknowledgement commit followed by an injected reported error and
  failed quarantine leaves `caller_acknowledged`; the native bound reader
  returns the reset target although preparation raised MandatoryMiddlewareError.
- A session approval seeded through native `tools.approval.approve_session`
  remains approved through `is_approved` after normal reset preparation.

There are zero agent/model requests in these diagnostics. They demonstrate
retained approval state, not a successful unauthorized governed tool call.
The two cases passed with the cache-provider configuration warning and no skips.
Frozen source inventories passed verification; no candidate source was changed.

The gate remains open. This diagnostic does not silently authorize a different
receipt contract. Retrying quarantine alone cannot close the acknowledgement
gap when storage remains unavailable. Nor does adding another durable success
write remove uncertainty about that final write.

### Approved Bounded Correction

1. Add an exact host-bound reset security boundary for the selected route using
   the native gateway and approval stores. Clear session approvals, session YOLO,
   pending tool waits, gateway pending approvals and slash confirmations before
   acknowledgement. Mandatory errors must propagate, not become debug messages.
   Keep ordinary mode unchanged. Block unqualified late approval handlers; do
   not widen frontend authorization or treat approval as Maya tool permission.
2. Supplement, never replace, durable SQLite lineage checks with host-confirmed
   completion for this bounded reset profile. A reader may select only after
   that same bound host observed successful guarded acknowledgement completion.
   Missing confirmation, reported uncertainty and a new host/restart deny even
   if SQLite contains an acknowledged receipt. This deliberately narrows reset
   restart routing until separately authorized reconciliation is qualified;
   it is not a parallel authoritative store or automatic maintenance identity.
3. Implement a separately hashed overlay over frozen Patch 33, convert these
   defect observations into denied-route/cleared-approval regression cases,
   qualify failed cleanup and absent confirmation, and rerun composition/atomic
   and ordinary controls before reviewing Step 3 again.

Item 2 changes reader eligibility and reset restart behavior relative to the
durable-receipt-only contract. The user explicitly approved this restriction
before implementation on 2026-10-07. Full Step 4 remains deferred.

## Patch 34 Implementation

The separate five-path overlay is
`patches/hermes/0034-reset-confirmation-approval-gate.patch`, reconstructed by
`scripts/prepare_governance_g2_reset_gate.py` from verified Patch 33. Inputs,
tests and effective hashes are in `governance-g2-reset-gate.json`. Earlier
manifests, the original Hermes checkout and installed artifacts are unchanged.

The reset preparation binds the exact native GatewayRunner, database and bounded
executor factory. Its explicit native cleanup requires the currently acknowledging
reset authority. Native APIs clear session approvals, YOLO state, pending waits
and notification callbacks; blocked waits receive denial. Slash confirmations and
the exact route's gateway control state are cleared and checked. Other routes
and permanent customer configuration are not erased. Failed, malformed or no-op
cleanup cannot advance readiness. Ordinary cleanup remains unchanged.

Mandatory session/permanent approval grants, approval queue registration and
resolution, and slash confirmation registration/resolution deny at their native
entries. These are blocked unqualified paths, not a new governed approval UI.
This profile does not qualify general approval workers or frontend authentication.

The host-confirmed eligibility tuple binds target, route, database, instance,
correlation/digest, principal/binding version and projection generation/hash.
It is issued only after guarded acknowledgement and all preparation cleanup
complete without a reported failure. Every reported failure leaves it absent.
It is bound to the exact preparation/reader/runner and process, and never saved
as a credential or used in place of SQLite ownership, lineage or fresh G1 policy.
Read-only checks work within an authorized append scope without granting reset
mutation authority. A new host/process has no confirmation and must deny reset
routing even when the durable receipt says acknowledged. No automatic recovery,
reopen, adoption, schema change or maintenance credential is introduced.

## Final Gate Evidence

2026-10-07: the final independently reconstructed stage
`.codex-build/governance-g2-reset-gate-20261007-final-c` passes all 56 native
cases: 34 composition/gate cases and 22 unchanged atomic reset cases against
the same effective source. There are no skips. The one pytest `cache_dir`
warning comes from disabling its cache provider, as in earlier scoped runs.

| Previously open criterion | Final bounded evidence |
| --- | --- |
| No old approvals transfer | Real native session allowance, YOLO, pending request/wait/callback and slash-confirm fixtures are cleared; waiter receives deny; other route state is retained. |
| Cleanup must enforce readiness | Raised error, no-op cleanup and malformed gateway state deny routing and issue no confirmation. |
| Uncertain acknowledgement plus failed quarantine | SQLite remains honestly acknowledged, but both native read and authenticated conversation selection deny; no agent or transport runs. |
| All preparation cleanup must finish | Injected reported final lock-release failure leaves confirmation absent and routing denied, with fixed output rather than the private exception. |
| No restart adoption | An independent process reopens the existing native fixture with fresh owner/read permission and still denies the acknowledged reset; no repair or row change occurs. |
| Late unqualified approval paths | Seven native grant/registration/resolution entries and async slash resolution deny without notification, agent or transport effects. |
| Existing conversation behavior | Reused native fresh-agent/history/cache and independent model-denial cases pass on the final source; confirmation checks do not grant reset mutation. |

The required product regression suite and preparation suites pass all 60 cases
(47 product cases plus 13 preparation cases). Context, syntax and whitespace
checks pass. Ordinary-mode native session/approval/confirmation controls produce
322 passes and nine failures, identically on the unchanged Patch 33 parent and
the final candidate. All 88 session controls pass. The nine failures are existing
Windows absolute shell-path detection assertions in `tests/tools/test_approval.py`:
lines 375, 439, 447, 468, 482, 572, 583, 592 and 732. They are not suppressed or
repaired here; they remain relevant before shell/platform qualification.
Generated gateway guard files were removed from the parent/source inventories;
the final ordinary run places those files in a separate working directory.

The two identified Step 3 review blockers are closed for the approved bounded
source profile. This is evidence for Step 3 acceptance review, not an automatic
G2 or production acceptance decision. The input manifest keeps `pending_review`.
Full Step 4 crash/race/combined-fault qualification, repeat reset, frontend
authentication, general tools/workers, maintenance reconciliation and production
provisioning remain open in their existing order. No installer is rebuilt.

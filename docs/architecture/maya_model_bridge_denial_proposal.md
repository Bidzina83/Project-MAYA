# Offline Model Denial Test Proposal

Subsequent decision: the user approved M02 source preparation only. The source
candidate and exact protocol/audit/exit predicates are now prepared and inert
checked; see maya_model_bridge_m02_source_review.md. The proposal below records
the earlier design request; M03-M08 remain proposals and no package/run is approved.

2026-10-24. Document preparation after the bounded M01 success and scoped manual
cleanup. M02-M08 are proposed, not implemented, packaged or approved for VM runs.
Preserve the frozen M01/Document 2 archives and reports. The companion contract is
maya_model_bridge_denial_tests.json; the original M1 contract remains intact.

## Recommended Sequence

Prepare M02 alone first: a valid native Hermes/SDK request must be denied by the
existing gateway before synthetic dispatch. Review implementation/impacts before
assembly; freeze exact artifacts, then obtain separate one-run approval and fresh
product consent. Stop after its result and cleanup review before preparing M03.
M03-M08 follow in the order below, with separate approval and artifact bindings.
Do not create a VM runner, script suite, automatic retry or poison-and-continue
loop. Each native negative has its own product attempt, worker, child, profile,
host ledger and cleanup. The operator runs actual product components through RDP.

An expected denial is not enough: setup failure, timeout, process crash, unknown
exception, missing evidence or audit failure is blocked/inconclusive, never a pass.
Each case must reach its intended boundary, prove any required prior positive
effects and independently admit its exact audit schedule and actual effects.
M01 is the historical compatibility control, not proof a future artifact's
negative control reached the gateway or that a network target is reachable.

## Existing Code And Required Changes

Source assessment: model_worker.serve_model currently requires exactly two allow
rules and follows only the positive issue/dispatch/delivery/final/shutdown order.
It returns a generic exit 3 on exceptions; ModelBridgeRuntime and both audit
validators admit only the six-event positive result. Running the frozen package
cannot exercise these negatives. A timeout or generic exit must not be relabeled.

M02 preparation would add only a compile-time/frozen-case product profile:
host-owned policy retains the exact model.output rule but omits model.egress.
The worker validates that exact expected policy, then constructs the unchanged
PolicyAuthorizationGateway with it. No second policy engine, fake gateway or
replacement authorization hook. Keep the actual operator SID/attempt/channel
binding. Native Hermes emits its real unchanged request through the existing
factory/SDK/pipe path. Only a specifically caught ModelDenied with matching
zero-effect state can produce a bounded denial control response. No raw exception
or request text is released. The worker's terminal denial closes that service;
it cannot authorize another operation or reopen its RequiredAudit sink.

Coordinator reporting must distinguish expected denial, uncontrolled failure and
effect uncertainty. Independently reread the protected audit after stop, bind
actual request/response IDs and expected request hash, and check worker/child
termination and SDK closure. A controlled nonzero exit can be admitted only with
its exact fixed code plus complete intended-boundary evidence; nonzero alone is
never success. Preserve the positive profile's existing six-event validator.

Case-specific code and validators must first receive inert regression/fault tests,
including audit write/flush failure, forged denial replies, wrong/missing/extra
events, premature EOF, partial writes, misleading zero counters, token/setup
failure and unexpected exit. Source review must freeze exact denial protocol,
exit-code and audit schemas before any package. Those are remaining design-to-code
gates, not already available functionality.

## Proposed Matrix

Counters below are (synthetic dispatches, confirmed runtime deliveries, confirmed
operator publications). An earlier effect must remain counted after later denial.
One row containing alternatives means separate attempts, never a mixed fault.

| Case | Fixed proposed trigger | Required effects/evidence |
| --- | --- | --- |
| M02 | Remove only egress allow from host-owned policy | (0,0,0); actual gateway deny on valid request; one provider-destination denied event |
| M03 | Separately alter model, route, attempt identity, or body digest | (0,0,0); reject at the specified validation boundary, not asserted gateway denial |
| M04 | Separately expire an unused grant, revoke it, or replay a consumed grant | Expiry/revocation (0,0,0); replay begins with one verified dispatch/runtime delivery, then no second effect; exact denial stage recorded |
| M05 | Explicit second transport request on the same client, then on a recreated client in a separate attempt | First exchange verified (1,1,0), second denied locally or at service as specified; no extra dispatch; distinguish adapter rejection from worker denial |
| M06 | Egress allowed but output rule omitted from fixed policy | (1,0,0); successful dispatch then runtime model.output denial; three events: egress_intent, dispatch_outcome, denied |
| M07 | Separate fixed synthetic responses: malformed JSON, 4097 bytes, well-formed but nonallowlisted bytes | Dispatch attempted/count 1, runtime/operator 0; no raw response release; expected incomplete/uncertain outcome, not fabricated successful dispatch validation |
| M08 | One bounded synthetic final-text substitution after valid runtime delivery | (1,1,0); operator withheld, prior four allowed events followed by operator denied; no publication intent/commit |

M03's identity variant alters only the untrusted attempt field. An injected actor
field is a separate schema rejection, not a fake trusted Windows identity. Never
modify actual tokens or grant another SID access to simulate an attacker.
M04 expiry uses real monotonic time beyond 2 seconds but within unchanged child
budget; no native fake clock or timeout extension. Revocation requires a reviewed
fixed trusted command; none exists in the positive worker. Replay and M05 differ:
the former specifically tests the consumed service grant; the latter tests shared
budget enforcement across client ownership/recreation. Do not merge their claims.

M05 makes explicit transport-level requests, not enabled Hermes auto-retry or
fallback. Existing automatic retries remain zero/one as configured; this does
not qualify native fallback or auxiliary paths. If a case requires a new client
after normal service completion, redesign for review rather than silently reopen.
M07 needs a fixed compile-time synthetic fault seam and separate comparison to
the normal fixture. Never patch the wheel, mutate a live private member, take
caller-selected response bytes or provide a production fault switch. Its exact
uncertainty/denial schema must distinguish attempted effect from validated output.

## Audit And Output Denial Limits

M02/M03/unused M04 normally have a single denied record; they differ in trusted
boundary evidence. Post-runtime replay/M08 retain the four-event positive prefix.
M05 adapter-local denial may leave that prefix without a worker denied event;
therefore it needs coordinator transport evidence and must not satisfy a service
denial predicate. M07 denial occurs before validated dispatch_outcome and before
response assignment: preserve attempted effect count and empty validated-response
metadata; never synthesize the positive prefix. Freeze each exact schedule first.

PolicyRule matches capability/target/operation/actor, not destination. Omitting
model.output denies the first runtime release and does NOT test an operator-only
gateway denial. M08 tests final-text validation at the second destination, not
an operator-only gateway policy. A separate destination-specific denial policy
or mid-attempt policy revocation needs its own reviewed product contract; it is
deferred, not claimed as covered by these seven categories.

## Unchanged Impacts And Exclusions

No OS preconfiguration, extra capability, network permit, loopback exemption,
registry change, new dependency, Hermes patch, service, account, listener or real
provider. Preserve ordinary AppContainer, reduced tokens, six denies, both jobs,
child-process block, private pipes, protected host files, all byte bounds and
22/30-second child deadlines. Trusted worker remains outside child WFP protection.
Required audit failure is terminal; automatic recovery stays disabled.

M09 requires separate exact native probe targets, reachable controls and WFP
correlation; no internet/socket bypass test is approved here. No M2 credentials,
external inference, spending, customer document access or authoritative-state
mutation. M01 and denial results cannot close Gate A or set qualification flags.

## Decision Needed

Approve the narrow M02 source/protocol/validator preparation described above,
including its fixed gateway-denial policy and bounded denial reporting. Review
the resulting exact source behavior before package assembly. M03-M08 remain a
roadmap, not permission for further fault seams, policy changes or native runs.

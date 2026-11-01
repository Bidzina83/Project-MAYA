# M05 Adapter Request Budget Review

Subsequent decision: user approved M05a-only source preparation including bounded
diagnostic reporting. Candidate and inert results are documented in
maya_model_bridge_m05a_source_review.md. Review-stage statements below are
historical, not assembly or native-run approval. M05b remains unimplemented.

2026-11-01. Source/test-contract review only. No product source changes,
compilation, package assembly, product execution or VM/security changes.
Companion: maya_model_bridge_m05_tests.json. Preserve every frozen predecessor.
M04c outcome: maya_offline_model_replay_1_outcome.md.

## Findings

ModelChannelClient.exchange consumes _grant before sending its first request;
requests becomes one. The original guard rejects any subsequent exchange before
pipe send and marks the channel closed. bind_grant cannot reset _bound.
PipeModelTransport validates the request first and converts failures into bounded
TransportError. Transport closure alone does not close the shared pipe.
OfflineModelClientMixin creates separately owned HTTP/SDK clients but passes the
same ModelChannelClient to each transport. Its factory refuses a closed channel.
close_model_clients closes the shared adapter, so recreation AFTER that shutdown
would test a closed-session guard, not shared-budget consumption.

The current native child performs one conversation then shuts down. The worker
and coordinator continue toward final publication. They do not yet implement an
M05 schedule or independently admitted four-record terminal result. Existing inert
tests cover parts of these guards, not the proposed native sequence. No new
vulnerability or native M05 pass is established by this review.

## Separate Proposed Attempts

M05a: after one genuine positive Hermes conversation, explicitly send a second
valid transport request through the SAME still-open HTTP client/transport that
served the first request. Merely choosing agent.client is insufficient: native
construction creates multiple clients. Identify and verify the actual used
transport. Freeze how the first request bytes are observed without replacement
or mutation during source preparation; replay exactly those validated bytes.

M05b: in a fresh attempt, complete the same first positive conversation. Close
only the used SDK/HTTP client and its transport, NOT close_model_clients or the
shared ModelChannelClient. Invoke the existing parent-delegating factory with
the fixed original kwargs to create a genuinely new SDK/HTTP/transport triple.
Verify distinct ownership, same adapter identity, open shared channel, requests=1
and no rebind. Explicitly send the second valid request through the new HTTP
client. Do not create a new agent, adapter, grant, worker or attempt mid-test.

For both, use an explicit httpx transport-level request, not a second Hermes
conversation, automatic SDK retry, fallback or credential rotation. The second
request must pass normal method/URL/header/body validation and reach the original
consumed-budget guard. An already closed client, malformed request or generic
TransportError cannot satisfy that claim. Do not mutate private guard state,
monkeypatch a live method, replace a runtime dependency or widen transport rules.

Recommend M05a-only source preparation first. M05b remains a separate reviewed
design, not permission to implement or execute both together.

## Protocol And Evidence Contract

1. Normal consent/setup and pinned native construction. One unchanged 2000-ms
   grant, original request and first synthetic response. Preserve first gateway
   calls=2, dispatches=1 and confirmed runtime delivery=1. Require genuine positive
   conversation and fixture final text, retained privately without publication.
2. After original runtime confirmation, coordinator sends a bounded M05-only
   probe authorization control to the child. It is scheduling, NOT a new grant.
   No replay command goes to the service. Define exact frame fields/IDs and
   child/coordinator order during source preparation; maintain existing deadlines.
3. Child performs exactly one fixed second transport attempt. Read-only diagnostic
   observation must distinguish original budget-guard rejection BEFORE pipe send
   from earlier validation/closed-client errors. Propose a minimal case-bound
   observation hook around the ORIGINAL guard, not a replacement guard. This
   additional product-source seam requires explicit source-preparation approval
   and source review. No exception text/body/lease disclosure. Observation cannot
   turn failure into authorization or alter normal profiles.
4. Child emits bounded case/attempt-bound probe completion and positive conversation
   closure evidence on the existing channel. Child testimony remains untrusted.
   Coordinator independently rejects any extra model_request frame, response
   write or protocol deviation, and checks final counters, EOF and natural exit0.
   A child's claimed exact local guard origin is corroborative only; host pipe,
   worker and audit observations establish the narrower no-extra-effect result.
5. Add a dedicated terminal worker completion after runtime delivery. Do not call
   model_prepare_final or publish. Worker must remain healthy and stop normally;
   no reopening after normal completion or denied request. Exact terminal message
   schema and snapshot admission must be source-reviewed before assembly.
6. Independently admit EXACTLY the unchanged four positive audit records:
   egress_intent, dispatch_outcome, runtime_release_intent, runtime_delivery.
   Bind operator/attempt/request/response/delivery command and real hashes/counts.
   There is NO worker-denied fifth event for a local rejection. Do not accept a
   truncated six-event verifier or reuse M04c's five-event consumed-grant verifier.
7. Preserve effects (1,1,0), total gateway calls2, second-request pipe sends0,
   extra gateway/dispatch/response writes0 and publications0. Child request budget
   remains1; report transport attempts separately as2. Verify all clients closed,
   normal child/worker exit0, bounded empty stderr, protected files and fresh beacon.

No need to claim an unexpired service grant at the second local call: adapter
budget enforcement is independent of service TTL. Do not lengthen/reissue the
grant or reinterpret timing as M04c evidence. First runtime confirmation remains
truthful even if later diagnostics fail. Faults retain prior effects and block
acceptance; generic denial, timeout, crash, audit error or missing evidence never
passes. Retain original audit validators and ordinary profile behavior unchanged.

## Required Inert Coverage And Gates

Cover valid same-client second request; actual used-client selection; recreated
ownership/shared identity; transport-only close versus shared close; premature
shutdown; invalid headers/body; alternate adapter/new grant/rebind; unexpected
extra pipe frame; forged child result; wrong case/attempt/command/counters;
missing/extra/reordered/mutated audit records; write/flush failure; EOF/timeout;
SDK closure failure and preserved first effects. Prove both intended diagnostic
location and unchanged pre-existing guard behavior. Use inert fixtures only.

Review source and exact protocol/audit schemas before separate successor assembly
approval (including any exact inactive-root omissions). Then full payload/freeze
checks, matching guest hash, separate one-run approval and fresh product consent.
No package or native run is approved here. No new dependency, security grant,
network permit, live inference, authoritative-state mutation, retry/recovery,
M06-M09/M2 or qualification. Gate A and every false qualification flag stay open.

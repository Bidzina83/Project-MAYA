# Offline Model Bridge Integration Review

## Subsequent Approval And Source Work

The user subsequently approved the narrow non-streaming correction and continued
offline implementation. It is now implemented as a class-level flag and delegated
per-client factory in project_maya.hermes_plugins.model_bridge. No native method,
Hermes wheel or live agent is monkeypatched. The earlier approval hold below is
resolved for that exact source scope, not for VM execution or M2 inference.
See maya_model_bridge_v1_progress.md for tested scope and remaining package gates.

2026-10-24: the user approved continuation of the proposed offline M1 slice.
This review implements the design's mandatory source compatibility gate before
runtime integration. No product code, wheel, payload, package, process, credential,
network rule or VM setting was changed or executed. M2 remains unapproved.

## Evidence Source

Read the exact Document 2 payload as ZIP bytes, without importing Hermes or SDK:

- ZIP SHA256 ECD7CF55E11523DD31EABE6281B2A6F59BB0FA154A1961E04744B9C31F5F0AA1.
- Hermes b13e2fd6948a59eeb59fe618914147d97a2ee90a, packaged OpenAI 2.24.0
  and httpx 0.28.1. Frozen Document 1/2 artifacts remain unchanged.

These findings concern this pinned source, not current upstream behavior.

## Factory And Ownership Finding

hermes/run_agent.py _create_openai_client delegates to
agent.agent_runtime_helpers.create_openai_client. That helper copies kwargs,
validates proxy/base URLs, selects native provider branches, optionally creates
a per-client keepalive HTTP client, constructs the actual SDK and logs lifecycle
context. Its comment explicitly warns against storing an httpx client in
agent._client_kwargs: closing one request would otherwise poison later clients.

The originally proposed direct SDK construction would omit helper behavior.
Correct the proposal to supply a NEW per-call private-pipe httpx client in a
COPY of kwargs, force SDK retries zero, then delegate to the original factory.
Its native validation/logging stays intact and its keepalive creation is skipped
because http_client is already provided. Do not modify stored _client_kwargs.
Reject unsupported provider/mode/base URL or caller-provided http_client. Close
the newly allocated client if parent construction fails. Each returned SDK owns
only its own HTTP client/transport; transport close must not close shared pipe
handles or grant the next client another effective request.

All factory call sites, shared/recreated/per-request clients and accounted closure
still require focused inert checks before native approval. Native socket-abort
helpers cannot abort anonymous-pipe reads: coordinator hard I/O deadlines and job
termination remain authoritative. Do not claim native interruption/cancellation
compatibility from source inspection or substitute unbounded blocking reads.

## Confirmed Non-Streaming Contract Mismatch

hermes/agent/conversation_loop.py lines 1095-1143 explicitly prefer streaming,
including when there are no callbacks. The docstring describing the default as
non-streaming is not the actual implementation. _use_streaming starts True;
the native non-streaming branch is selected when agent._disable_streaming is
truthy (or excluded ACP/mock cases that are not acceptable substitutes here).

Search of all packaged Hermes Python source found _disable_streaming only in:

- conversation_loop.py:1118: the native branch predicate;
- run_agent.py:4115: prefer_stream uses the same predicate;
- chat_completion_helpers.py:1669 and :2507: setting it after streaming failures,
  with a related comment at :2527.

No public constructor/config switch for this flag was found. Triggering a
provider failure to set it would introduce an unapproved extra attempt/fallback.
Pretending the real SDK is a Mock or replacing conversation methods is forbidden.
Accepting streaming would widen the agreed protocol and output-validation scope.

Therefore the proposed factory-only subclass cannot produce the specified M1
non-streaming positive control as written. The private pipe transport must continue
rejecting stream=true, and no VM package should be assembled from that contract.
This is a proposal compatibility defect, not another Windows/AppContainer failure.

## Narrow Proposed Correction Requiring Approval

Extend the versioned Maya subclass contract, for this pin/profile only, with a
class-level _disable_streaming = True in addition to the delegated client-factory
override. This selects Hermes' existing non-streaming code path before the first
conversation. Do not patch the wheel, set attributes on a live agent, replace
conversation/serialization logic, spoof ACP/mock identity or relax stream rejection.
Assert the flag and real per-request dispatch path before admission. Source/pin
changes invalidate this contract until reviewed again.

This is an additional private Hermes interface dependency, beyond the approved
factory-only proposal. It requires an explicit scope decision before implementation.
If declined, return a different reviewed transport/integration design; do not
automatically enable streaming or use a deliberate failed first request.

Existing M1 no-network/no-key/no-inference boundaries, one-dispatch limit,
zero SDK retries, Hermes api_max_retries=1, original byte/deadline bounds, all
six child filters and separate required audit/output gates remain unchanged.
M2 provider/credential/disclosure/spend and any native run remain unapproved.
No package is ready. Native schedule and exact audit predicate are still package
gates after this integration correction is accepted and implemented.

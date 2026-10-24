# Model Authorization Bridge V1 Proposal

## Approved Correction And Source Implementation

The user subsequently approved the reviewed non-streaming integration correction.
The offline host state machine, pipe SDK adapter and pinned subclass factory are
implemented with inert fixtures; see maya_model_bridge_v1_progress.md. This resolves
the hold below for that source scope. Windows worker/coordinator integration,
host-owned exact native serialization, final audit admission and native schedule
remain package gates. No runnable M1 package or native compatibility result exists.
No M2 route, credentials, networking or inference is authorized.

## Integration Review Hold (2026-10-24)

The user approved offline continuation. Mandatory pinned-source review found
that real Hermes defaults to streaming even without callbacks; the factory-only
subclass proposed below cannot satisfy the specified non-streaming positive test.
See maya_model_bridge_v1_integration_review.md for exact source findings and a
narrow proposed additional private _disable_streaming class-level contract.
Also preserve the original factory helper by injecting a per-client pipe httpx
client into copied kwargs and delegating, rather than replacing helper behavior.
No integration code or package was created. Obtain approval for that additional
private-interface dependency before implementation; never enable streaming,
trigger a fallback attempt or substitute a Mock automatically. Earlier proposal
text remains historical design intent, not a verified compatibility claim.

## Status And Scope

2026-10-24: approved document-only design/test-contract preparation after the
bounded Document 2 success. Not implementation, packaging, credential access,
dependency acquisition, networking, inference, security provisioning or VM-run
approval. See maya_model_bridge_v1_tests.json and the Document 2 outcome.
This is A4 feasibility work, not Gate A closure or a protected conversation product.

Select private inherited pipes and the existing gateway. Preserve ordinary
AppContainer, zero capabilities, reduced tokens, both jobs, child-process block
and six child-scoped network denies. No HTTP listener, loopback exemption,
network permit, new service/account or general URL proxy. Keep Document 2 frozen.

Split evidence deliberately:

- M1 offline wire slice: real pinned Hermes conversation/model dispatch and real
  packaged OpenAI SDK serialization through private pipes to a clearly labeled
  synthetic provider response. No external networking, credentials or inference.
- M2 real-provider slice: one bounded synthetic-text inference only after M1 and
  separate route/model/credential/disclosure/spend review and artifact/run approval.
  Provider, model, endpoint, key reference and monetary ceiling are NOT selected
  or authorized here. M2 cannot be packaged as ready-to-run until these are bound.

M1 cannot be called real inference. M2 cannot be called all-model-path qualification.
Direct-route probes and auxiliaries need their own positive controls/evidence.

## Source Assessment And Compatibility Gate

Inspected Document 2's frozen payload as ZIP bytes, without executing Hermes/SDK:
Hermes b13e2fd6948a59eeb59fe618914147d97a2ee90a, distribution 0.17.0,
Python 3.13.14, OpenAI 2.24.0, httpx 0.28.1, httpcore 1.0.9.

- hermes/agent/agent_init.py initializes agent._client_kwargs and creates a
  primary OpenAI client through agent._create_openai_client.
- hermes/run_agent.py exposes _create_openai_client forwarding to
  agent.agent_runtime_helpers.create_openai_client; request-scoped clients copy
  _client_kwargs and set SDK max_retries=0. Replacing agent.client alone misses
  these clients and closed-client recreation.
- agent.api_max_retries defaults to three; fixed M1 configuration must set one
  and read it back. SDK retries must be zero for every instantiated client.
- dependencies/openai/_client.py supports http_client: httpx.Client. This SDK
  extension permits a custom httpx.BaseTransport; it is not itself an approved
  Hermes injection interface.
- agent.transports registry normalizes/builds provider requests. Registering a
  normalizer is not proof that every actual SDK request uses private pipes.
- Existing Maya governance hooks and restricted_broker(_http) remain insufficient:
  optional in-process hooks are not containment; the historical test-only broker
  handles Responses rather than this package's chat-completions path.

Proposed integration for review: a versioned Maya subclass of the real pinned
AIAgent, overriding only its client factory to construct genuine OpenAI clients
using per-client httpx clients with the product pipe transport. Never patch global
OpenAI/httpx, monkeypatch a live agent, replace conversation logic or fake the SDK.
This is an explicit NEW Hermes integration contract over a private method, not
a claim of an upstream-supported public extension. Before implementation approval,
review factory signature, initialization order, all call sites, close/abort/thread
behavior and client accounting against this exact pin. Unsupported paths block.
If this override would bypass necessary native lifecycle behavior, stop and propose
a supported interface change; do not silently fall back or edit the runtime wheel.
No subclass, factory override or SDK transport is implemented by this proposal.

## Trust, Identity And Effects

Retain the elevated coordinator and trusted medium worker outside AppContainer.
For M1 the worker remains offline. M2 would explicitly add outbound HTTPS and
provider credential use to this worker: a new trusted capability, not a property
of the child WFP rules. It must not import Hermes or execute caller-selected code.

Actual operator SID, attempt, checked process handle/PID, pipe ownership and
channel ID originate in coordinator state. Child-supplied actor, classification,
tenant, endpoint, credential reference or policy is rejected. Tenant is absent
in this single-operator scope; no multi-tenant assertion. Fixed request/response
budgets and classification internal-synthetic are bound by trusted configuration.

Use ActionRequest/PolicyAuthorizationGateway for decisions, not a second policy
engine. Match established model.egress target model:<provider>, operation infer,
and model.output target model:<provider>, operation disclose. Endpoint, model,
payload digest, route ID, byte/token limits, attempt and request IDs accompany
the trusted action metadata and required audit. The current PolicyRule matches
only capability/target/operation/actor: endpoint/digest/budget binding must be
explicit service invariants, not falsely claimed policy features. Non-ALLOW,
unhandled constraints/redactions or missing identity fail closed.

Two releases are distinct: validated provider output to restricted Hermes and
validated final assistant text to the operator. Both need model.output approval
and destination-bound audit. Child final text is untrusted even after provider
approval. For this fixed synthetic test the host may admit only an exact allowed
text/digest, not a general claim that arbitrary output is safe. No tools, document
retrieval, memory/session writes, customer content, images, attachments, URLs,
streaming, embeddings, connectors or Metabase in this slice.

## Protocol And Admission

The transport accepts exactly POST to a private .invalid logical origin plus
/v1/chat/completions, never a network URL supplied by the child. Validate serialized
UTF-8 JSON, exact allowed fields, fixed model, non-streaming text messages, bounded
max output tokens, no tools/functions, no extra headers/auth/query, duplicate keys,
NaN, unknown operations or redirects. Host policy checks the actual final serialized
bytes. For M1 the host owns an unpredictable synthetic canary and exact expected
messages; digest mismatch denies. Arbitrary runtime prompt text is not authorized.

The logical origin is only an SDK address label. Its placeholder SDK key is public
and non-secret, never a provider credential. Strip it; do not forward SDK headers.
M2 host rebuilds headers and fixed endpoint from protected route configuration.
Disable environment proxies, automatic redirects, transport/SDK retries, fallback,
automatic provider discovery and route substitution. TLS verification remains on.
No child-supplied URL, arbitrary file, bearer token or general HTTP forwarding API.

One host-issued, short-lived admission per request binds actual actor, channel,
attempt, route/model, payload digest, sequence, cancellation generation and budget.
Consume before effect, with one in flight. Retries/recreated clients/auxiliaries
receive no inherited permission; every new effective send requires fresh gateway
authorization. Initial allowance is one effective dispatch. Second send fails
without network effect; this demonstrates denial, not supported retry/auxiliary use.

Use the Document 2 frame codec and required-audit adapter without reopening poisoned
sinks. Extend message types/version explicitly; do not reinterpret document leases.
Keep 8192-byte frames and 131072-byte cumulative limit per channel direction;
strict integer protocol fields, depth/Unicode bounds and no truncation-to-accept.
Request and response JSON each <=4096 UTF-8 bytes, final text <=1024 bytes,
output token parameter <=32, one effective dispatch, no concurrent pipe users.
M1 child cooperative/hard budgets remain 22/30 seconds; worker ready 5 seconds,
per-RPC 2 seconds and incomplete frame 1 second. For M2 timeout feasibility needs
explicit review before freezing; no automatic extension to accommodate a provider.

Audit egress intent durably before any provider effect; record transport outcome,
validated-response digest/size and delivery intent before release. Coordinator
owns actual delivery confirmation, worker audits outcome, coordinator rereads the
bounded protected ledger after both processes stop. Record destination for runtime
versus operator delivery. No prompts/responses, canaries, credentials or raw provider
errors in public reports/audit; use digests/counts and allowlisted reason codes.
Exact event schedule and schema must be frozen for the approved case matrix before
package preparation; do not reuse Document 2's 21-event predicate for model events.

Audit failure poisons the attempt. Do not continue later cases using that sink.
Pre-send failure means zero provider sends. After a possible send, report
send_committed_or_uncertain; cancellation cannot retract inference or charges.
Output/audit failure withholds subsequent delivery, not a fabricated zero send.
Partial child-pipe write is delivery_uncertain; no resend or automatic recovery.

## Test And Evidence Strategy

M1 has one positive Hermes-native conversation through the actual per-request SDK
client; observe serializer request and native normalized response/final text.
Retain real class/MRO/module/pin/distribution/lifecycle checks. A direct SDK call
alone cannot satisfy the positive Hermes criterion. Synthetic response is labeled
as such, with real provider inference false and no credential use.

Inert tests first cover all malformed protocol, lease, policy, cancellation,
required-audit and framing failures with effect counters and negative controls.
Terminal fault cases use fresh service/audit instances, never poison-and-continue.
Native fault attempts must be separately approved/frozen; do not add them to one
successful-attempt ledger. Native M1 transport guards reject unauthorized model
requests before any synthetic provider dispatch or output release.

Direct socket/SDK probes must preserve all six denies and correlate WFP events
to actual child/filter identity with a reachable trusted-side positive control.
An offline socket timeout or DNS failure is inconclusive, not denial proof.
Local-service/alternate-endpoint probes need exact approved fixtures/targets and
no listener or OS change is authorized here. Earlier Screen 11 evidence is
historical, not coverage for every model route. Unsupported bypass probes stay
pending, never silently omitted or marked passed.

M2 requires exact route/model, secret backend/reference and consent path, prompt
bytes/digest, provider retention/disclosure terms, maximum output/input limits,
spend ceiling/call cap, timeout and provider-specific supported wire shape.
No provider/model recommendation or live API documentation claim is made here.
Research current official provider documentation when selecting M2. Budget caps
are conservative admission limits; do not claim a guaranteed invoice limit from
an estimated token count alone. Keys stay in approved host-local storage/process
memory; no CLI args, environment inheritance, logs, reports or child-readable file.
Secret handling that lacks a real product path blocks M2; no manual bypass.

## Impacts, Gates And Open Work

M1 would add product adapter code, protocol messages, protected route metadata,
synthetic fixtures and audit predicates; no new OS grants or dependencies selected.
M2 additionally needs reviewed host HTTPS/secret handling and explicit external
disclosure/spend permission. It does not relax child network restrictions.
Any new wheel, Hermes pin/patch, longer deadline, loopback rule, background process
or topology change requires a revised impact decision before implementation.

Before a package: approve factory integration and exact native schedule, implement
and pass inert cases, settle client ownership/closure and response validation,
freeze event schema/counts and source/EXE/payload hashes. Obtain separate artifact
VM-run approval and product-owned informed consent. Product stops both jobs before
cleanup; automatic recovery remains disabled. Preserve retained evidence and
manually check processes, links, package-SID ACEs, labels and exact WFP resources.
Profile removal remains independently unverified unless a separately reviewed
read-only check establishes it. No full cleanup/containment assertion follows.

Open: all auxiliary native routes, streaming, retries/fallback success, alternate
SDK/local-service bypasses, arbitrary-code attacks, restart/crash/concurrency,
credential lifecycle and general output-policy enforcement. Gate A, containment
and production remain unqualified even if M1 or one M2 request passes.

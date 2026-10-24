# Offline Model Bridge Source Progress

## Approved Package Preparation

2026-10-24: the user approved first-positive M01 staging and separate offline
assembly. See maya_model_bridge_m1_package.md. The earlier source-only milestones
below are historical; M02-M09 and M2 are not included in this package approval.
Exact artifact verification precedes separately approved VM execution/consent.

## Native Source Continuation

The subsequent approved continuation adds the deterministic host request oracle,
trusted worker protocol, guarded real-Hermes child/bootstrap entries, HERMES_MODEL
profile, protected host-file setup, Windows coordinator, bounded read-only UI
publication and independent C# six-record audit admission. See
maya_model_bridge_m1_native_review.md for proposed first-positive staging and
explicit limits. The older implementation/gap list below is retained as history.
Source integration is present, not native-qualified; no payload/package is ready.
Review the first-native schedule before assembly; VM execution remains separately
gated. M02-M09 and all broader adversarial/fault coverage remain pending.

Current regression result: 197 Python tests, 221 subtests. C# results: 711 prior
component checks, 154 document-bridge checks, and 178 model-profile audit/publication/
selector checks; the paired legacy-profile run passed 175 checks with model paths
rejected. These paired counts overlap and are not additive independent coverage.
The first new oracle fixture assertion compared a decoded Windows path against
escaped JSON bytes; correcting the assertion to inspect decoded content resolved
it without changing expected request bytes. A path-search wildcard was corrected
as a tooling invocation issue. No native product test failed or ran.

Local native entry tests force early non-Windows guards; they do not launch Hermes,
SDK or native security setup. C# fixtures compile/run their selected inert main,
not the product Main. Only the existing pytest cache-write warning remains.
Expected oracle sample: request 2,618 bytes; system text 2,362 UTF-8 bytes; frame
2,946 bytes. Total 4 KiB request/8 KiB frame limits are unchanged. The initial
extra 1 KiB per-message source guard was removed to admit native system text
within the already approved total request limit. Native serialization is unproven.

2026-10-24: user approved M1 offline continuation and the subsequent private
non-streaming integration correction. This is source implementation/inert checking,
not approval for M2, credential access, network traffic or VM execution.

## Implemented Source

- src/project_maya/bridge/model_service.py: host-only offline state machine using
  the existing ActionAuthorizationGateway and RequiredAudit. Exact host-supplied
  serialized request, one-use two-second admission, actor/attempt/channel/route
  binding, one synthetic dispatch, distinct runtime/operator output gates, exact
  fixed response/final text, revocation/expiry and conservative effect accounting.
  It has no live provider mode, URL proxy, path opener or networking interface.
- src/project_maya/hermes_plugins/model_bridge.py: real httpx.BaseTransport over
  the existing PrivateChannel codec, strict .invalid route/method/header/body
  checks, public non-secret placeholder auth stripped rather than forwarded,
  one inflight exchange and no second grant/request even across client recreation.
  Per-client transport close never owns/closes the shared product pipe handles.
- The same module supplies a versioned mixin with _disable_streaming=True and
  parent-factory delegation using COPIED kwargs and a fresh owned httpx client.
  trust_env=False, follow_redirects=False and zero SDK retries; native Hermes
  api_max_retries must read back as integer 1, tools and fallback chain must be
  empty. At most eight client objects may be created; this is a resource ceiling,
  never eight request permissions. Explicit client closure checks cannot silently
  report success after failure. Returned real SDK ownership remains with Hermes.
- offline_agent_class imports the real AIAgent only when explicitly invoked and
  verifies the reviewed run_agent/helper/conversation source hashes before returning
  the subclass. No import of Hermes/OpenAI or call of that constructor occurred
  during preparation. Unit tests use an explicitly labeled factory-interface
  fixture, never a substitute product runtime.

The native factory helpers and conversation implementation remain unchanged;
no global SDK/HTTP monkeypatch, fake SDK, second policy engine or registry exists.
The mixin's private interface has no implied upstream support beyond this pin.

## Semantics And Local Tests

42 new Python tests, with subtests, cover the positive offline core/HTTP framing,
egress/runtime/operator denial, exact payload/model/route/actor shape, lease
expiry/revocation/replay, second dispatch denial, constrained/redacted decisions,
pre-send and post-send audit failure, audit failure before each release, actual
delivery counts retained on confirmation-audit failure, wrong response digest,
extra/oversize response data, final output mismatch, short writes, lazy bodies,
concurrent exchange rejection, client recreation/closure and parent-factory error.

The full bridge/prior Windows regression run passed 174 tests and 65 subtests.
Only the previously disclosed pytest cache-write warning remained. Windows Temp
fixtures ran outside the sandbox under approval, not via the protected product.
No native security API, Maya/Hermes process or bundled SDK was executed. Local
httpx 0.28.1 was exercised with the non-network custom transport and memory streams.

The happy core path records six events: egress_intent, dispatch_outcome,
runtime_release_intent, runtime_delivery, operator_release_intent, operator_delivery.
These are not yet an independently qualified native audit schedule. Intent means
prepared, never delivered. Only trusted coordinator confirmation records delivery;
expiry/revocation cannot erase a write already observed. Partial/failed writes
must yield uncertainty, not a retry. Audit poisoning terminates the instance.
Fault tests use fresh service/audit state; no poisoned ledger is reopened.
Prompt/reply text is absent from audit; trusted digests/counts and destination bind
effects. The synthetic provider is explicitly not inference; token-usage zeros
are fixture wire values, not billing measurements. No real key exists.

## Remaining Native Integration Gates

No runnable package or new Windows profile is ready. Do not run Document 2 as if
it contains this source work; its EXE/ZIP/payload and evidence remain frozen.

1. Complete the product-owned worker and C# coordinator protocol/lifecycle. Actual
   runtime/operator writes, receipts and confirmations must be host-observed, not
   fabricated from prepared worker counters or child self-report.
2. Freeze host-owned exact request bytes for the actual pinned Hermes conversation
   and SDK serializer. The current core intentionally rejects every other shape;
   its inert four-field request is NOT proof of native serialization compatibility.
   Native request_overrides can explicitly select stream=false, but must be bound
   and reviewed in the fixed construction config; no body is learned/authorized
   merely by accepting the child's first request or claimed digest. Keep 4096-byte
   request and existing frame/deadline bounds; mismatch blocks, not truncates.
3. Bind real constructor options/config, no tools, max tokens 32, one attempt,
   disabled auxiliary work, all created SDKs and source/distribution identities.
   Retain true AIAgent MRO/native run_conversation and natural closure evidence.
   Partial constructor/abort/thread cleanup remains native-unqualified.
4. Freeze exact native case order/effect counters, protected audit schema and
   coordinator readback predicates. Required bypass probes and reachable controls
   remain explicitly pending; no successful core fixture can replace them.
5. Then compile/inert-check/freeze an exact artifact under the reviewed schedule
   and obtain separate VM execution approval and product-owned fresh consent.

All six child WFP denies, ordinary AppContainer, zero capabilities, token/jobs,
process block, payload/dependency pins, deadlines and disabled automatic recovery
remain unchanged. The trusted worker is not network-contained by those filters;
M1 adds no networking. M2 remains unbound and separately gated. Gate A, full
containment/cleanup, model mediation and production remain unqualified.

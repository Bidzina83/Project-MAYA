# M07c Response Allowlist Review

2026-11-02. User approved REVIEW only after bounded M07b success and scoped
manual cleanup. No product/test source edit, compilation, package assembly,
product/native/bundled-runtime/VM/security execution or inference.
Preserve Oversized1/all frozen predecessors. Companion:
maya_model_bridge_m07c_tests.json; M07b outcome documents provenance/limits.

## Current Source And Required Boundary

Original OfflineModelBridge.prepare_runtime first checks returned bytes/size
1..4096, then strict protocol.decode, then hmac.compare_digest against its
original _expected_response. Only after comparison succeeds are _response
assigned, phase changed to dispatched and dispatch_outcome written.
model.output authorization/release occur later.

Current response_failure_* observations identify JSON rejection or exact4097-byte
size rejection only. The exact-byte mismatch branch raises ModelDenied(True)
without named allowlist evidence. Relabeling M07a/M07b controls cannot prove M07c.
Recommend a narrow read-only response_allowlist stage/hash/count observation at
THAT original mismatch branch, AFTER the original decoder succeeded.
Hash at most the already admitted4096 bytes; retain no raw fault response.
Preserve original comparison, exception, failure/audit closure and uncertainty.
This observation requires separate explicit SOURCE preparation approval.

## Fixed Construction-Time Mutation

Dedicated fixed service/provider selected before issue, through existing factory.
Provider inherits original text/wire_reply unchanged; calls original dispatch
exactly once, consuming real synthetic allowance, then changes only the final
hex digit of the returned message content's host-owned fixture canary.
Proposed fixed rule: last digit becomes0 if not already0, otherwise1.
This is the final content digit, NOT the final byte of the serialized JSON.

Use structured JSON/object manipulation and canonical serialization consistent
with original generator. Require the expected original canary shape, preserve
all other envelope/model/usage fields and exact byte length. Inert controls
must prove precisely one ASCII byte differs at the intended content position.
Default native fixture response remains313 bytes, under4096. The altered bytes
must remain valid strict JSON; no type/depth/duplicate/encoding trick.

Never change provider.text, override wire_reply, assign _expected_response from
fault bytes, replace a live provider, monkeypatch SDK/wheels, or accept runtime
fault selection/body/class/URL. Dedicated root/profile/worker only.
No provider exception or parser failure may pass as allowlist rejection.

## Independent Oracle And Evidence

Host canonical normal oracle continues to derive ORIGINAL response from trusted
fixture text. Separate fixed mutation oracle derives exact altered response
independently from that trusted text/rule, NOT from child or returned fault.
Both normal and altered lengths match, digests differ, exact rule binds them.
The normal oracle remains authoritative; altered bytes are diagnostics only.

Proposed strict case evidence: exact service/provider, original request admitted,
phase admitted/provider destination, closed service/nonfailed required audit,
gateway1/dispatch1/uncertain=true, stage=response_allowlist, matching fixed-mutant
digest/count and original normal-response oracle; no gateway-denial flags.
_response must remain None, validated response hash empty/bytes0 and every
prepared/confirmed release counter0. Successful JSON parsing is evidenced by
the source observation at the post-decode branch, not child testimony.

Case-specific worker reply binds original dispatch command/attempt, carries
bounded stage/hash/count/effects only, never raw altered or canonical output.
Coordinator independently checks normal and mutated oracles and truthful
dispatch/uncertainty BEFORE control send. Separate exact M07c child denial
control, native constructor/one request/SDK closure, native_conversation=false.
Natural child/worker EOF/exit0, fresh beacon, protected-file recheck and exact
audit readback required. Freeze protocol names/key counts/report schema in
SOURCE review before assembly. Wrong case/IDs/hash/stage/count cannot pass.
Denial-control writes stay separate from zero model-response pipe writes.

## Audit And Effects

Effects(1,0,0), gateway1, uncertaintytrue. Original BOTH-rule policy.
Exact TWO records: egress_intent allow/provider/model.egress/infer/dispatches0,
then denied deny/provider/model.egress/infer/dispatches1.
Both have EMPTY validated-response hash/bytes0; original actor/attempt/service/
request/route/endpoint/model/output metadata and valid ordered UTC timestamps.
No dispatch_outcome, model.output decision, release/confirmation/operator event.
This is not gateway egress denial or validated response delivery.
Unchanged pure M07a two-record verifier may be delegated to; retain separate
strict M07c evidence and do not weaken any earlier validator.

## Required Inert Controls

- Original normal response fully passes admission; original expectation remains
  byte-identical before/after altered dispatch, inherited wire_reply unchanged.
- Fixed mutation remains strict JSON/canonical shape/model/length, one differing
  ASCII byte at final canary-content digit; both rule arms0/nonzero exercised.
- Delegating decoder spy proves the exact altered bytes reached original decode;
  named post-decode mismatch observation reached, no parallel validation engine.
- Normal return from the fault class cannot pass the negative case; wrong content
  digit/field/model/whitespace/length/encoding/malformed/oversized/type/provider
  throw cannot satisfy the exact case even when some cause original rejection.
- Wrong service/provider, changed expectation/_response/phase/destination/counters,
  missing liveness/request/egress admission or poisoned audit must block.
- Original dispatch consumed once/second dispatch rejected, no additional effects;
  no synthetic counter assignment or hidden second dispatch/client/grant.
- Mutate every control/evidence/audit field; missing/extra/reordered/unterminated
  ledger, both write/flush failures, failed/partial control sends, EOF/deadline/
  nonzero exit errors must block while preserving original prior effects.
- Preserve earlier profile admission/exclusions, reader/deadlines and cleanup.
  Inert controls are not native SDK/process/containment proof.

## Recommendation And Gates

Recommend M07c-only SOURCE preparation including fixed construction-time provider,
normal/mutant host oracles, bounded observation at ORIGINAL exact-byte mismatch,
strict evidence/controls and unchanged TWO-record semantics. No implementation
authorized by this review. No package or root omission approved here.
Actual source/payload impact review must precede separate assembly/any exact
successor-only inactive Oversized1 root omission approval. Preserve canonical
helpers and frozen artifacts, inspect full actual-profile inventory/resources.
Later matching-artifact ONE-run approval and fresh product consent remain gated.

No response4096/frame8192/channel131072/grantTTL2000/deadline/grant/security/WFP/
tokens/jobs/permissions/config/dependency revision, networking/inference,
credentials/customer content/spending, retry/fallback/recovery, M08/M09/M2 or
qualification. All flags false/Gate A open.

# M03 Request Validation Proposal

Subsequent decision: the user approved M03a-only source preparation. The source
candidate, exact event/protocol and inert evidence are now recorded in
maya_model_bridge_m03a_source_review.md. The proposal below remains design history;
other variants, package assembly and native execution are not approved.

Prepared 2026-10-31 after M02's bounded success and reported scoped cleanup.
Document-only preparation; implementation, assembly and native execution are
not authorized here. Preserve frozen Document 2, M01 and M02 artifacts/contracts.

## Objective And Sequence

Prove that a request cannot change its model, route, untrusted attempt identity
or exact body after a scoped admission. These are request-validation negatives,
not gateway-policy denials, Windows actor impersonation or socket bypass tests.
Recommend M03a wrong-model source preparation first, then review the resulting
source/protocol/impact before separate assembly. Obtain matching-artifact VM-run
approval and fresh consent before one native attempt. Stop for result/cleanup
review before another variant; no multi-case runner or automatic retries.

## Boundary Assessment

Current ModelChannelClient.exchange validates the body and admission digest
before sending. PipeModelTransport also validates model/shape. ModelBridgeRuntime
compares actual child body with its protected expected body before forwarding.
OfflineModelBridge.prepare_runtime checks route/attempt/lease/channel, then model
syntax and byte-for-byte expected request before calling the real gateway.
Its generic ModelDenied and denied audit event do not identify which validator
rejected the request. The current M02 proof expressly requires gateway denial;
it must never accept these earlier rejections as another passed M02.

Native wrong-model SDK traffic will normally fail inside the child first. To
isolate worker validation without disabling those guards, the proposed M03a
profile keeps the real child request valid and records its original exact match,
then the trusted coordinator derives one fixed negative worker request. This is
an explicit new compile-time product diagnostic seam requiring source approval,
not an implemented feature or an attacker-selected mutation API. No live patch,
wrapper test script, external supervisor or new policy authority is proposed.
The result proves worker rejection of that injected request, NOT that a hostile
child sent it past its own adapter or that all child defenses are qualified.

## Fixed Variants

Each variant needs its own approved/frozen attempt, ledger, profile and cleanup.
Do not select variants from the child, environment, editable policy or free-form
command-line input. Do not alter actual token, channel ownership or operator SID.

| Variant | Exactly one logical mutation | Required worker rejection |
| --- | --- | --- |
| M03a | Body model maya-offline-wire-v1 becomes maya-offline-wire-v0 | Fixed model validation, before gateway authorization |
| M03b | Envelope route maya.offline.model.v1 becomes maya.offline.model.v0 | Route binding, before body admission/gateway |
| M03c | Envelope attempt's first hex digit changed deterministically to another valid digit | Untrusted attempt binding; real host identity stays unchanged |
| M03d | Final hex digit of synthetic user-message canary changed to another valid digit; model/shape remain valid | Exact expected-body comparison |

All variants require zero gateway calls, zero attempted/actual synthetic dispatches,
zero prepared/confirmed runtime and operator releases. Only M03a is recommended
for next source approval. The others remain proposals. An extra actor field is
schema rejection, not an identity-spoofing proof; it is outside these variants.

For body mutations parse with the existing strict codec, edit only the named
field and serialize deterministically with the pinned SDK/httpx byte convention.
Before forwarding, independently reconstruct both expected original and exact
mutant; compare their complete structure and digests. No string-wide replacement,
fuzzy matching, learning a new allowlist or arbitrary request transform. Route
and attempt variants preserve body bytes exactly. The protected host oracle
remains the original valid request; its digest is never replaced by the mutant.

## Required Source Evidence

Use the existing real PolicyAuthorizationGateway with the ordinary positive M01
allow rules, so a policy omission cannot mask missing validation. Service-owned
bounded rejection stage and gateway-invocation observation must distinguish each
validation boundary from lease expiry, audit failure and unknown exceptions.
These observations do not decide authorization or replace the gateway. Native
clock/deadline and all existing guards remain unchanged.

A proposed denial reply must bind actual attempt, service/coordinator IDs, case,
named rejection stage, original/mutated request hashes and sizes, zero-effect and
zero-gateway observations. Child report remains untrusted. A closed service and
healthy required audit are mandatory. The protected ledger needs a separately
versioned, exact validation-rejection predicate with those bounded bindings;
the current generic denied event alone is insufficient. Define that exact schema
and Python/C# validators during approved source preparation and present them for
review before assembly. Preserve the existing M01 six-event/M02 one-event schemas.
No raw request, canary, model output or exception text in public audit/report.

The coordinator must verify protected evidence after natural child/worker exit 0,
required SDK closure, exact boundary admission and both stops. Only a fixed denial
control, not a model response, can reach the child. No operator model publication.
Generic nonzero exit, malformed protocol, timeout, absent/extra/wrong audit,
nonzero or uncertain effect, missing native valid-request baseline, or wrong
boundary is blocked/inconclusive. Never count it as expected validation rejection.
Required-audit failure is terminal; do not reopen a poisoned sink or continue.

Inert controls must prove the unmodified request still reaches normal dispatch
using a separate fresh instance, while each exact mutant reaches its named
rejection with no gateway/effect. Cover extra/missing mutation fields, a second
changed field, rebound digest/attempt/IDs, fake denial reply, audit write/flush/
sync failure, early EOF, partial write, wrong native entry, and generic exception.
No local native Hermes/SDK or Windows provisioning is needed for those fixtures.

## Unchanged Limits And Decision

Keep real pinned Hermes/SDK, factory/transport guards, config, dependencies,
ordinary AppContainer, zero capabilities, six denies, reduced tokens, jobs,
child-process block, private pipes, host ACLs/labels, 22/30-second child deadlines
and all M02 frame/channel/audit/output bounds. Worker remains trusted and outside
child WFP containment. No new grant, listener, registry/loopback exception,
network target, provider key, inference, charge, runtime wheel change or recovery.
No manually prepared Windows test environment or VM test automation.

Approval requested next: M03a-only source preparation, including the fixed trusted
wrong-model diagnostic derivation and exact validation-rejection evidence above.
No package or run follows that source approval. M03b-M03d, M04-M09 and M2 remain
gated. Qualification flags and Gate A remain unchanged even after a bounded pass.

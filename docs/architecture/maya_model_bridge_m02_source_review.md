# M02 Source Preparation Review

Subsequent decision: the user approved separate M02 offline package assembly.
See maya_model_bridge_m02_package.md. The preparation-only statements below
describe the source-review milestone; native execution remains separately gated.

2026-10-24: the user approved M02-only source preparation. This record describes
implemented source and inert checks, not an assembled product or native result.
No M02 product EXE/payload/ZIP, dependency acquisition, security setup, Hermes/SDK
execution, networking or VM run occurred. Frozen M01 and Document 2 stay intact.

## Fixed Profile

HERMES_MODEL_DENY requires HERMES_MODEL plus the existing bridge/construction/
import topology. Version 0.2.1-offline-denial.1, scope
offline-hermes-model-denial-v1. No case selector comes from command line, child,
environment, caller response bytes or a generic fault switch. The fixed native
entries are model_deny_child_entry.py and model_deny_worker_entry.py, admitted
only by the denial profile. They call the shared product entries in M02 mode.
The shared child entry checks model-contract.json cases=[M02]; positive mode
requires [M01]. The future successor payload must bind its exact new contract.

ModelHostFiles writes one host-owned allow rule: model.output/disclose for the
exact existing target/operator. Only model.egress/infer is omitted. The worker
requires this exact policy before readiness and uses the existing unmodified
PolicyAuthorizationGateway. Positive mode still requires both exact allow rules.
Neither profile accepts a policy intended for the other; no new policy engine.

The child still constructs real pinned Hermes and genuine SDK clients through
the reviewed parent-delegating factory. The host-owned expected request, native
serialization, canary, binding and per-client budget checks remain. A valid
request must pass service syntax/byte/lease/channel checks before gateway denial.

## Exact Terminal Protocol

Ready, issue and grant messages retain the positive schema. The coordinator's
model_dispatch carries the real child request and fresh request_id. Only after
ModelDenied from prepare_runtime may M02 return model_egress_denied with exactly:
v, type, attempt, request_id, effects. effects has these exact values:

```json
{"case":"M02","boundary":"gateway_egress","request_validated":true,"gateway_denied":true,"dispatches":0,"confirmed_runtime_releases":0,"confirmed_operator_releases":0,"real_inference":false}
```

Admission additionally requires the service closed, the required audit healthy,
no attempted dispatch, and zero prepared as well as confirmed releases. The
gateway observation requires actual DENY/governance.no_matching_rule and no
constraints/redactions. Generic validation denial, gateway exception, expired
grant, attempted effect or audit write/flush/fsync failure cannot qualify.
This terminal service is never reused. The worker returns 0 and closes its pipe;
there is no model_shutdown or subsequent protected operation on this attempt.

The coordinator validates that bound reply and writes only a control to the child:

```json
{"v":1,"type":"model_denied","attempt":"<actual attempt>","seq":1,"case":"M02","reason":"gateway_egress_denied"}
```

EgressDenialChannelClient observes only that exact shape, closes the transport
and raises rather than returning model content. The SDK receives a transport
failure; the product catches only its APIConnectionError after a verified denial
observation, not an arbitrary exception. Hermes may handle the SDK failure and
return its own result; no such result text is published or claimed as a model
conversation. Actual native denial/error unwinding remains to be tested.

After normal SDK/client lifecycle close, the child sends model_child_denied with
v/type/attempt/report, no text. Report uses maya.offline.model.denial.child.v1,
requires completed/native_constructor/sdk_closed/origins_verified/
distributions_verified/config_unchanged/denial_observed true, native_conversation
and real_inference false, one request, 2-8 client objects and empty reason_type.
Child report remains untrusted. Two-sided EOF, bounded stderr capture, normal
child and worker exit 0 and protected-file rechecks are mandatory; generic nonzero
exit is never admitted as expected denial. Existing deadlines are unchanged.

## Independent Evidence And Status

The protected ledger must contain exactly one newline-terminated record using
the existing AuditRecord schema: model_bridge.denied, decision deny, capability
model.egress, operation infer, fixed target/classification and actual actor.
Metadata binds attempt, service request ID, fixed route/model/logical endpoint,
provider destination, expected request digest/size, fixture output digest,
response digest empty/bytes zero, dispatches="0", real_inference="false".
Timestamp must be valid UTC. No extra, missing, rebound or duplicate event.
Python verify_denial_audit and separate C# ModelDenialAdmission.Audit implement
the predicate; C# rereads the private file after both natural exits. Positive
six-record verification stays separate and unchanged.

Only after that readback does model_denial_evidence_matches become true. The
final offline_model_egress_denied_pending_independent_cleanup status additionally
requires Python-entry/fresh-beacon evidence, both process stops and successful
product cleanup. Missing evidence, setup error, timeout, abnormal exit or audit
failure is blocked. Public counters count zero model-response writes/publications;
the bounded denial control is not a model response release. No call reaches the
operator publication callback. No raw exception, model text or canary is added
to public results or denial ledger.

## Impacts And Checks

Changed product sources: model_service boundary observations; model_worker fixed
policy and terminal response; model_bridge denial-only child endpoint; shared
child cleanup/report branch; new fixed bootstraps; ModelHostFiles policy selection;
Windows worker/child entry selection; ProductFiles profile admission;
ModelBridgeRuntime terminal path; new ModelDenialAdmission; version/consent/status.
These are intentional successor-source changes, not edits to frozen artifacts.
Dependencies, Hermes wheel/pins, config, request oracle, security provisioning,
zero capabilities, six network denies, both jobs, reduced tokens, child-process
block, 22/30-second budgets and byte limits are unchanged. No local native API
or UI provisioning/publication path was exercised. Trusted worker remains outside
child WFP containment. Automatic recovery stays disabled.

Inert results: 213 Python tests and 293 subtests pass, including 16 new M02 cases.
They use in-memory peers/audit handles and force early non-Windows bootstrap
guards; no bundled Hermes/SDK execution. One pytest unknown cache_dir warning
comes from disabling its cache plugin. C# warning-as-error source compilations
and selected inert mains pass: 117 M02 admission checks, 113 paired M01 and 113
legacy checks (overlapping coverage); prior 711 component checks, 154 document
bridge and 178 M01 model checks. No fixture invokes product Main. Fixtures cover
policy isolation, malformed request versus gateway denial, audit failures,
forged/missing/extra denial controls, exact ledger mutations, uncertain effects,
child postconditions, profile paths and byte/type/count boundaries. Existing
codec/Windows fixtures cover truncation, partial writes and startup/token failures.
Native SDK error handling, closure, exact request formation and timing remain
unproven for M02; inert success is not native acceptance or full containment.

## Next Gate

Review this exact source/protocol/impact record before approving separate M02
package assembly. No package is ready, no guest EXE/path/hash exists and no run
is approved. A future package needs unchanged dependency verification, explicit
changed-source inventory, contract/resource/source/artifact hashes and fresh
inert checks. Then obtain separate matching-artifact one-run approval and product
consent. Preserve the earlier results and stop on failure. M03-M09, M2, real
inference, Gate A and every qualification flag remain pending or false.

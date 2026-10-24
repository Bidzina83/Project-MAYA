# Maya Development And Test Sequence

## M1 Package Preparation (2026-10-24)

The user approved M01-only staging and offline package preparation. See
maya_model_bridge_m1_package.md. Next gates are exact artifact/hash review,
separate VM-run approval and fresh product consent, followed by result analysis
and scoped independent cleanup checks. No native launch or real inference is
authorized by assembly; M02-M09 and M2 remain pending.

## M1 Native Source Candidate (2026-10-24)

Guarded native entries, host-owned exact request bytes, offline worker, Windows
coordinator/UI publication and independent audit admission are now source-ready
and inert-checked. See maya_model_bridge_m1_native_review.md. Proposed first run
is one M01 positive compatibility test, not the full boundary matrix; M02-M09,
native faults and full containment remain pending. Review this first-run staging
before package assembly. No payload/archive or approved native invocation exists;
real inference, M2 permissions, Gate A and production remain blocked.

## M1 Source Milestone (2026-10-24)

The private non-streaming correction was subsequently approved. Offline model
admission and the pipe SDK/client-factory adapter now have 42 new inert checks;
174 Python regression cases pass. See maya_model_bridge_v1_progress.md for scope
and remaining native-integration/package gates. No runnable M1 package, native
Hermes conversation, inference or containment qualification is claimed. The
earlier integration hold is resolved only for that approved source dependency.

## M1 Compatibility Gate (2026-10-24)

Offline continuation was approved, but pinned-source review found a proposal
mismatch before implementation: native Hermes prefers streaming without callbacks.
The approved factory-only subclass does not select the required non-streaming
path. See maya_model_bridge_v1_integration_review.md for the proposed additional
private class flag and parent-factory delegation. Await this narrow scope decision;
no runtime code, package, native launch, network grant or inference was performed.

## Current Continuation (2026-10-24)

Document 2's bounded native bridge result and scoped manual cleanup are recorded
in maya_authorization_bridge_document_2_outcome.md. Ten cases passed: two reads,
one release and 21 verified audit events, both processes natural exit 0. Profile
removal remains product-reported; no full containment/cleanup qualification.
The historical A3 assessment below is superseded for bounded document mediation,
not for broader lifecycle/adversarial acceptance.

The user approved document-only A4 design/test preparation, now in
maya_model_bridge_v1_design.md and maya_model_bridge_v1_tests.json. Proposed M1
uses real pinned Hermes/SDK with private pipes and explicit synthetic provider
wire replies, not inference. Proposed M2 needs separate exact provider/model,
credential, disclosure, spend, artifact and execution approvals. A proposed
versioned private client-factory override needs review before implementation;
replacing only the primary SDK client is insufficient. No code/package/native
run or model call is authorized by this continuation. All child denies remain.

## Status

2026-10-22: continuation of the approved A-E order in
maya_governance_integration_plan_v2.md. This records current evidence and the
next bounded integration work, not approval to widen permissions, activate
production, run another VM test or implement an unreviewed transport.
Historical diagnostic procedures are not the current operating sequence.

## Completed Native Memory 1

The operator supplied the matching-hash 0.1.4-hermes-memory.1 result for attempt
1b64558c94ad4e8b8f80bf2540009aa3 on Windows Professional 26300.9711.
Launcher SHA256:
D05531830EEBBD15F4682EB6F1558A802C76C9642C7DB0227CEDC5E03C675647.
The report records consent, verified payload, six filters, restricted token,
matching startup beacons and natural child exit 0. The real attached MemoryStore
completed all eight synthetic mutations, exact readbacks and fresh-store reload.
Both snapshot/hash checks and two nonblocking lock probes passed. Observed peak
was 214 bytes; config unchanged, no model calls, agent/client closure verified.
UTC 18:12:27.3338272 through 18:14:46.1778566 includes host preparation/cleanup,
not just the bounded child execution.

After normal closure the operator's read-only checks found no matching processes,
recursive reparse points or package-SID ACEs across 7,395 entries, with zero
failures. State integrity was Medium. WFP export exited 0, produced 2,169,122
bytes, and complete fragment-aware traversal found none of the six exact filter
keys or sublayer. These are scoped independent checks, not a complete cleanup
attestation; profile deletion remains product-reported. The run is consumed.
No further VM command or rerun is required by this record.

## Ordered Work

| Stage | Deliverable and acceptance | Current position |
| --- | --- | --- |
| A1 Runtime compatibility | Real protected Python and pinned Hermes import, construction, closure and bounded native storage | Demonstrated for the individual frozen startup/import/construction/SQLite/memory fixtures; not all Hermes workloads |
| A2 Boundary screen | Effect-level allowed/denied controls with declared limitations | Screen 11 synthetic observations reported; ordinary AppContainer shared access and broader isolation coverage remain open |
| A3 Product authorization bridge | Restricted Hermes requests one host-owned protected operation through existing authorization, authenticated request lifetime and required audit; corresponding denied cases have no effect | Document 2 bounded document slice passed; broader security/lifecycle qualification remains open |
| A4 Effective model mediation | Real Hermes model request through trusted authorization/transport and validated delivery; direct SDK, auxiliary, fallback and alternate-route denial controls | Document-only M1/M2 proposal prepared; factory integration and exact native schedule need review; no execution approval |
| A5 Feasibility closure | Resolve coverage register, lifecycle/failure gaps and trust assumptions; qualify allowed operations and required bypass denials | Gate A remains open; earlier successes cannot substitute |
| B Minimal protected path | Authenticated input, governed SMB retrieval, real Hermes inference and validated response, with revoked identity/cancellation/policy/service/audit failure controls | Pending Gate A acceptance; no claim of protected end-to-end product readiness |
| C Useful operations | Named ingestion/search/conversion, authoritative business-memory changes, embeddings, analytics and selected governed connectors | Pending protected core; define each operation's identity, targets and outcomes before implementation |
| D Reliability | Ownership, retention, cancellation, restart, backup/recovery and accurate uncertain/committed outcomes | Native same-process persistence is partial evidence only; crashes/restart/concurrency unqualified |
| E Installed qualification | Clean customer installation, lifecycle, migration, update/rollback and adversarial installed-boundary tests, provenance/licenses/signing | Pending; development packages are not release installers |

A3 and A4 are feasibility slices, not a premature declaration that Gate B is
complete. A-E remain sequential acceptance gates. Record failures and scoped
corrections rather than repeatedly rerunning the same successful storage tests.

## Existing Code And Gaps

- src/project_maya/governance.py defines ActionRequest, AuthorizationResult,
  ActionAuthorizationGateway, PolicyAuthorizationGateway and deny-by-default
  behavior. Reuse this authority; do not introduce a second policy engine.
- src/project_maya/bootstrap.py selects the file-backed or default-deny gateway.
  That does not demonstrate its placement outside the restricted process in
  the current C# development package.
- src/project_maya/audit.py provides LocalJsonlAuditSink. Its append API alone
  does not qualify tamper isolation, durable audit semantics or failure handling.
- src/project_maya/hermes_plugins/restricted_broker.py labels itself test-only.
  It binds host identity, fixed resources, lease/budget, gateway authorization
  and audit before effect. Useful design evidence, not a ready product service.
- src/project_maya/hermes_plugins/restricted_broker_http.py is also test-only.
  Its fixed /v1/responses handling cannot be assumed compatible with the current
  construction package's chat_completions client. Do not relabel or expose it
  as a production broker or silently change the runtime/protocol.
- The current product package denies all network and uses stdin/stdout/stderr
  only for startup/output capture. These handles are not yet an authenticated
  bidirectional product authorization protocol. An IPC design needs explicit
  framing, bounds, host/session binding, cancellation and fault handling.
- Optional in-process governance/memory hooks do not independently constrain
  arbitrary runtime code. Direct MemoryStore success does not qualify those
  hooks as authority or repair the upstream memory-wrapper fail-open path.

## Next Bounded Deliverable: Authorization Bridge Contract

The requested design is now recorded in maya_authorization_bridge_v1_design.md
and maya_authorization_bridge_v1_tests.json. It proposes private inherited pipes,
one trusted medium-integrity worker reusing the Python gateway, a protected host
folder and exact document read/disclosure gates. Its 12 native cases and required
local fault/codec cases are design scope, not execution or implementation approval.

Prepare the exact product integration contract for A3 before its package:

1. Bind the trusted host's actual operator principal and attempt/request identity.
   The child cannot select actor, classification or arbitrary resources. Do not
   use a session ID, a default administrator or a prompt as authentication.
2. Use the existing gateway and an actual host-owned synthetic document outside
   the writable child state. One exact file.read target is the first allowed
   protected operation. No customer file, SMB deployment or model service yet.
   Synthetic content is an explicitly disclosed fixture, never a fake Hermes.
3. Specify a product-owned host/child transport, ownership and packaging. Compare
   a bounded inherited-handle channel with a narrowly scoped local network route
   against the real SDK/runtime requirements. Prefer preserving the current
   network denies if a compatible non-network product interface is feasible;
   no selection or permission expansion is implemented by this document.
4. Keep policy, audit and authoritative state outside the child's effective
   access. Enumerate actual host dependencies/lifecycle. A copied policy file
   inside child-writable state or an allow response from the child cannot pass.
5. Bind size/deadline/effect budgets, cancellation/revocation and replay behavior;
   reject unsupported/redacted/constrained decisions unless actually enforced.
   Required audit failure must prevent the protected effect. Final delivery
   remains separately validated; raw child output is not authorized disclosure.
6. Define fixed positive/negative controls and independently observed effects.
   Missing/wrong identity, wrong target/action, stale or replayed admission,
   revoked/cancelled request, policy/audit/transport failure, malformed/oversized
   messages and direct access must not release protected data. Test uncertain
   outcomes honestly rather than invent rollback.
7. Return exact protocol, source interfaces, dependency/permission impacts,
   allowed/denied matrix and package bounds for review. If safe operation needs
   a new capability, loopback exemption, ACL, runtime patch or process topology,
   stop and disclose it before implementation. No test-only broker substitution.

Then implement the approved product bridge, run local inert/unit checks, freeze
the package and obtain exact-artifact VM approval. Only after A3 evidence should
A4 introduce a bounded effective model request. A fixture provider may validate
framing but cannot be reported as real inference. Real provider use requires
separate credential, disclosure and spend approval; no key goes to the child.

## Repeated Test Method

For every slice: identify actual product component and criteria; disclose impact;
implement/verify within approved scope; freeze hashes; operator copies/installs
through RDP; verify artifact; obtain run approval and product consent; collect
result; independently check scoped cleanup; record outcome before expansion.
Keep ordinary Windows 11 Pro configuration. No manual ACL/WFP/registry tuning,
extra supervisor or compulsory snapshot restoration between tests. Failed
enforcement blocks the operation; no unrestricted fallback or automatic retry.

This is a dependency/acceptance sequence, not a delivery-date estimate. Later
stages require their own work packages. No unrelated connector/UI/Metabase or
installer work is started to bypass the unresolved protection boundary.

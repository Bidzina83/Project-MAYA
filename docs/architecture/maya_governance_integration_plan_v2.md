# Maya Governance Integration Plan - Revision 2

## Decision And Status

Approved document-level direction on 2026-10-14: reduce internal enforcement
scope without reducing customer protection. This supersedes the remaining G0-G7
implementation sequence, not its historical evidence. Current step: Gate A
definition and feasibility. No implementation or isolation technology is approved
by this document. Production activation remains blocked.

One Hermes execution core, one existing local authorization gateway, and separate
Hermes operational, Maya SMB and Metabase stores remain required. The boundary
contract is [restricted execution](restricted_hermes_execution_contract.md).
No fake runtime, duplicate policy engine or new agent loop is introduced.

## Ordered Gates

### A. Architecture Feasibility

Step 1's approved profile, acceptance matrix, bounded budget and stop conditions
are in [the evaluation contract](governance_v2_gate_a_evaluation_contract.md).
The user accepted Step 1 and subsequently approved Step 2's architecture on
2026-10-14. Step 3's bounded prototype is next; privileged provisioning requires
separate permission. Step 1 acceptance alone did not authorize implementation.

Step 2's [architecture assessment](governance_v2_gate_a_architecture_assessment.md)
compares two candidates and recommends LPAC plus scoped WFP with the existing
Maya gateway on the user-created `Maya-Governance-Integration-V2` branch.
The user approved that architecture and test map on 2026-10-14, closing Step 2.
No containment tests or privileged provisioning have run; Gate A remains open.

The user commenced Step 3 on 2026-10-14. Its
[progress record](governance_v2_gate_a_step3_progress.md) distinguishes host-broker
and read-only prerequisite evidence from the unimplemented native LPAC/WFP slice.
Step 3 remains open; no A01-A20 acceptance or security provisioning is inferred.

The subsequent native continuation provisioned and cleaned up isolated test
security resources with separate permission. The child was not resumed because
the assumed class-46 LPAC query failed. The user approved the bounded
[verification-method correction](governance_v2_lpac_verification_review.md) on
2026-10-14. Qualify its AccessCheck suspended-token positive/negative controls
before resuming Step 3's native slice. No runtime patch, isolation downgrade,
broader capability or product acceptance follows compilation or this correction.
The paired native token controls passed. The subsequent resumed LPAC Python child
returned 0xC0000022 with no worker frame; its exact denied startup resource remains
unidentified. Step 3 stops here for review. Do not extend the fixed budget, widen
grants or introduce another correction without specific approval. No Hermes-loop
or effect-level containment acceptance follows token behavior verification.
The user's subsequent diagnostic request produced unchanged-input startup traces:
OS registry reads deny, ending at SideBySide after Python DLL mapping. The existing
profile lacks that key's read grant; no registry permission was changed. Consult
the verification review for the narrow proposed experiment and obtain an explicit
correction-budget/impact decision before implementing it. Diagnosis is not another
approved correction, expanded evaluation sequence or Gate A acceptance.
The user subsequently approved one explicit budget exception: the reversible
SideBySide-only, non-inheriting package-SID ReadKey experiment, with descriptor
capture/rollback and unchanged-input comparison. This does not authorize another
permission sequence, broad registry capability, runtime patch or Gate A acceptance.
That verified grant changed the child exit to 0xC0150002, still without a worker
frame; exact descriptor restoration returned 0xC0000022. Stop at the unlocalized
activation-context failure. Review complete Windows startup requirements before
proposing another correction; do not automatically resume a key-by-key sequence.
The user approved that assessment; its completed bounded evidence and proposed
fixed startup-and-integration contract are in
`governance_v2_windows_startup_assessment.md`. It is not authorization to apply
the proposal. No new grant/capability, source correction, runtime pin, wheel,
installer or Gate A acceptance follows. Keep the unresolved activation root and
both Maya-owned native-contract mismatches visible before another execution.
The user subsequently approved bounded loader-level diagnosis on 2026-10-15.
Its [result](governance_v2_loader_diagnosis.md) retains the initial diagnostic
setup failure and one separately permissioned corrected inert capture. Windows
loader snaps confirm python313.dll activation failure during static-import
initialization, but no inner failing resource or safe minimum grant. Original
permissions and test resources are restored/removed. The diagnostic allowance
is consumed: stop for an explicit strategic decision rather than automatically
adding captures, capabilities, runtime patches or an alternative architecture.
No useful Hermes execution or Gate A acceptance follows.
On 2026-10-16 the user approved the immediate next deliverable: a Python-only
reproduction and exact four-case comparison contract. Preparation is in
[the reference comparison runbook](governance_v2_python_comparison.md) and its
JSON contract. The derived bundle does not change the original stage/helper or
run application code. VM impact/provisioning, VM-only capability additions and
external publication require separate permission; reference build/token-observer
and execution-manifest evidence remain prerequisites. No comparison run or
renewed workstation diagnostic allowance follows this preparation approval.
The user subsequently approved document preparation for a 26H2 baseline revision
on 2026-10-16. The active environment addendum is
[the 26H2 comparison contract](governance_v2_python_comparison_26h2.md), with a
separate successor JSON. Preserve the historical 25H2 inputs/bundle unchanged.
One four-case matrix remains the entire proposed budget, not one per OS version.
Guest/media/resource verification and explicit provisioning/security permissions
remain open. No download, preparation-tool implementation, reference build,
observer implementation or comparison execution follows this approval.
On 2026-10-17 the user reported visible credit and an Azure guest whose winver
matches 26300.9711, then requested continuation. The proposed bounded Azure
procedure is [the Azure preparation/execution proposal](governance_v2_python_azure_procedure.md).
It defines serial control while guest adapters are disabled, baseline restoration,
minimal transfer and the existing local-tool prerequisites. It does not authorize
them: approve the procedure/local preparation before implementation and disclose
exact VM impacts before separate cloud/security/rehearsal/execution permission.
No input relabelling, additional A-D attempt or product qualification follows.
The user subsequently approved the Azure procedure and Step 1 local preparation.
Its explicit 26H2 binding and 30 inert fixture/probe tests pass; the new ignored
bundle is hash-verified and the historical bundle remains unchanged. The pinned
Microsoft reference source is verified but Release/x64 build stops at MSB4019,
missing C++ build targets. Resolve the specific toolchain prerequisite with impact
approval before installing system tools. Do not retarget upstream source or reorder
past the build; observer implementation remains pending. No guest/security changes,
external upload or A-D execution has occurred. Step 1 remains incomplete.
The user subsequently authorized suitable local build-tool download/installation.
Use verified Microsoft Build Tools 2022 v143/Windows SDK with required dependencies,
native package verification and automatic restart disabled. Record installation and
unmodified reference-build outcomes in the Azure procedure. This does not authorize
VM/security changes, reference execution or another A-D attempt; Step 1 stays ordered.
Installation completed with exit 0/no reboot required; the unchanged pinned reference
passed a clean Release/x64 build with zero warnings/errors. Hashes/tool versions are
recorded in the Azure procedure. Next is the approved Step 1 observer preparation;
no launcher execution, VM/security change or Gate A acceptance occurred.
The user approved observer implementation and the common outer-job design for A-D.
The unarmed evidence library passes 57 inert checks; its fixed sequence and limits
are in [the observer preparation review](governance_v2_observer_review.md). Step 1
launcher supervision adapters/joint review remain next. No native token/job test,
launcher/managed-Python execution, VM/security action or Gate A acceptance follows.
The next observer stage now has source-candidate A-D adapters, supervision and a
native backend, with inert coverage and the documented joint review. Stage 3's
freeze/manifest/invocation review is next, still inside Step 1 local preparation.
No native backend was executed; VM/security read-backs, execution permission and
Gate A acceptance remain open. Follow the same observer review before advancing.
The subsequent local review package records unarmed candidate fingerprints and
proposed guest library placement in `governance-v2-observer-review-package.json`.
It is not the final execution manifest: the trusted executable host, exact guest
binding, durable attempt tracking and approved invocation remain stage 3/Step 1
obligations. Do not close Step 1, begin VM changes or run native tests from it.
The subsequent user-authorized host continuation is recorded in
`governance_v2_observer_host_review.md`: a compiled, fixture-tested candidate and
proposed invocation against the frozen library, not an executed host or a ready
manifest. Review it before the existing VM preparation-impact gate. Its local
claim covers process restarts, not snapshot rollback; preserve the external
ordered attempt reservation. No extra startup matrix, VM action, Gate A acceptance
or product activation follows this preparation; final execution approval stays open.
On 2026-10-17 the user explicitly accepted the host candidate. The dated decision
in its review closes Azure procedure Step 1 local preparation and observer Stage 3
candidate review for the source/fixture scope, not Gate A or native operation.
Frozen records are unchanged. Next is the existing Step 2 actual VM inventory and
exact preparation-impact disclosure for separate permission; no deployment,
guest/security change or startup follows this candidate acceptance.

### Current Test Method - Customer-Like Windows, 2026-10-18

After the earlier manual diagnostic preparation and successful restoration/NIC
rehearsal, the user directed and clarified
[customer-like Windows testing](governance_v2_customer_windows_testing.md).
This is the active test workflow: preserve the existing representative Windows
11 Pro configuration, copy/install the selected component, run through Remote
Desktop and analyze the result. Do not prepare special file/registry permissions,
integrity labels, WFP rules or loopback exemptions manually for test success.
Maya must request consent and provision required permissions through its actual
setup/runtime component. Missing product setup must be addressed as a product
gap, not implemented as more test infrastructure. Refusal or failed enforcement
still blocks the affected operation; ordinary-mode bypass is not authorized.

The pending A-D security/execution request was not approved. Its offline/SAC
requirements and per-case disk resets are superseded, not silently converted into
new runs. Preserve frozen contracts, artifacts, reviews, baseline and rehearsal
evidence; none is relabelled as installed-product qualification. No additional
matrix, observer, transfer tool or automatic recovery loop is introduced.

Follow this order within Gate A: identify the bounded product artifact and its
real setup/start entry; prepare that product component within approved scope;
copy/install and run it through RDP with product-owned consent; collect and
analyze the result against its declared criteria. Report gaps before proposing
an implementation change or additional sequence. A particular security change,
artifact rebuild or startup retains its applicable approval. Gates A-E and the
customer-protection requirements remain unchanged; production stays blocked.

Before coding, propose a fixed Windows profile, specific isolation mechanism,
supported capabilities, trust assumptions, exact allowed/denied tests, evaluation
budget and stop conditions; obtain user approval. Demonstrate real pinned Hermes
inside the proposed restriction boundary, not an inert replacement. Prove mediated
model, service, storage and delivery paths and attempts to bypass each. Identify
auxiliary calls, subprocesses, SDKs, plugins and failure/restart paths.

Acceptance requires independently enforced boundaries, legitimate allowed
controls, denial before protected effects and honest failure/readiness reporting.
If containment cannot be demonstrated within the approved scope, stop for a
strategic decision. Do not automatically extend the patch sequence or weaken
customer protection. No production/platform claim follows Gate A.

### B. Minimal Protected Product Path

Authenticated input -> governed SMB retrieval -> native Hermes -> authorized
effective model request -> validated response. Test wrong/revoked identity,
cancellation, service/policy/audit failure and alternate access/disclosure routes.
Pass only when both useful allowed execution and denied counterparts work through
the actual product path. Authority cannot originate in prompts or saved sessions.

### C. Useful SMB Operations

Qualify approved document ingestion/search/conversion, business-memory writes,
embedding rebuild, analytics and selected consented connector workflows. Each
operation binds identity, target, classification, limits and outcome semantics.
Unknown capabilities stay denied. Name the supported workloads and exclusions;
do not substitute a safe chatbot for the Info Manager product.

### D. Operational Reliability

Hermes retains conversation and preference memory in its private local area.
Qualify ownership, reset/switch/rotation functionality, retention, cancellation,
restart, backup and recovery without automatically demanding authorization for
each database mutation. No cross-customer/session disclosure or authority reuse.
Preserve accurate committed/failed/uncertain outcomes; no fabricated rollback.
Background jobs need explicit identity, lifetime and capabilities before enabling.

### E. Installed Qualification

From built artifacts only, qualify clean Windows setup, enforced restrictions,
lifecycle, health, migration, backup/restore, update/rollback and adversarial
boundary tests. Keep curated pinned dependencies, licenses/hashes/provenance,
secret-safe packaging and default Authenticode signing requirements. Manual
development-machine restrictions do not prove installed readiness.

## Change Control And Evidence

Before each gate, define its exact work packages, acceptance matrix and exclusions.
Scope changes require specific approval. No time/effort estimate is established
by this direction. Runtime pin changes and internal patches require separate
compatibility review and approval; do not delete prior patches or tests now.
Retain frozen reports/hashes and accepted bounded G0-G2 results as historical
evidence. They cannot silently satisfy these new gates. Existing installers and
wheels remain unqualified for this contract. Update release coverage and threat
assumptions before enabling any new capability.

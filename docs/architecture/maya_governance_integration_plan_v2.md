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

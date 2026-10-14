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
The user accepted Step 1 on 2026-10-14. Step 2 architecture assessment is next;
its recommendation requires approval before implementation. No isolation
mechanism or prototype is authorized by Step 1 acceptance.

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

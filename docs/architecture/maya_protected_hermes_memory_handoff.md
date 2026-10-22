# Protected Hermes Native Memory 1 Handoff

## Approval And Scope

The user approved preparation under maya_protected_hermes_memory_proposal.md.
Version 0.1.4-hermes-memory.1, scope offline-hermes-native-memory-v1, targets
customer-like Windows 11 Pro x64 26300.9711 through Remote Desktop. This is an
unsigned product-owned development component, not a test supervisor or full
installer. No local native Hermes run or VM execution is included in preparation.
Review exact artifact hashes before separate VM-run approval and fresh consent.
All previous packages, source freezes and receipts remain preserved.

## Native Workflow

Use the same unmodified Hermes commit b13e2fd6948a59eeb59fe618914147d97a2ee90a,
Python 3.13.14 and 63 dependency versions. All 6,689 Session State 1 payload
members are unchanged. Add only the memory entry, config and immutable contract:
6,692 files total. No download, substitute memory backend or runtime patch.

Before importing Hermes, require no state/memories path. Hermes' normal config
bootstrap may create the empty directory; require it to be regular/non-reparse
and empty before construction. Set skip_memory=False, native memory/user flags
True, provider empty and native limits 2200/1375. Construct one real AIAgent
with no SessionDB. Verify the actual attached MemoryStore, flags, limits, paths,
external manager absence, empty tools and unchanged offline configuration.
Explicit load_from_disk must expose initialization failures hidden by the agent.
Require empty initial lists and prompt snapshots, not a constructor-only success.

For each target memory/user, native add creates first and scratch entries,
replace revises the first, and remove deletes the scratch: eight mutations.
Every returned success/done/target/count must match, followed by independent
readable regular-file and live-list checks. No checker code writes memory files.
Fixtures are benign ASCII, below 256 bytes each, in these forms:

- MAYA synthetic fixture memory first <nonce>
- MAYA synthetic fixture memory scratch <nonce>
- MAYA synthetic fixture memory revision <nonce>
- The same forms with user replacing memory for USER.md.

A fresh real MemoryStore in the same process loads the exact final revision
entry in each file. Original agent prompt snapshots must remain initially empty;
fresh snapshots must match native formatting with expected content and without
a blocked placeholder. No snapshot is sent to a model. Compare file hashes
before/after reload; host admission independently derives expected final hashes
from the fixed ASCII revision and nonce. This prevents empty read fallbacks from
passing. Normal Windows newline decoding is accepted during multi-entry checks.

Require Windows msvcrt locking support and no fcntl substitution. After native
calls, open each existing lock file and perform one nonblocking byte acquire and
release. Failure stops; there is no retry or lock suppression. These two probes
do not establish cross-process/concurrent-writer correctness. Do not claim
atomic replacement, crash safety or which native fallback branch ran from final
file success. Native scanning remains unchanged; this is not a malicious-content
or complete injection-protection assessment.

Call context shutdown and close; require the real SDK is_closed() method True,
detached client and zero model-call counter. Constructor failures never create
a fake agent for cleanup. Host-confirmed job stop remains the outer boundary.

## Private Paths And Limits

state/memories holds MEMORY.md, USER.md and each .md.lock file. Native writes
temporarily create .mem_*.tmp files; unexpected temp/backup residue blocks
admission and is retained, not automatically repaired or deleted. The memory
report is state/hermes-memory.json. Existing config/cache/logs/sessions remain.
All are synthetic non-authoritative operational storage, not Maya's trusted
memory, governance, secrets or business state. No customer profile is imported.

Regular non-reparse memory paths and aggregate sizes are checked at bounded
stages. The observed peak must be positive and no more than 65,536 bytes. This
is an acceptance ceiling, not an OS quota or in-call growth guarantee. File reads
are size-checked first. At most four expected stable memory/lock files remain;
unexpected directory entries fail. Native locks/temp/atomic-replace behavior is
not patched, instrumented or weakened.

The HERMES_MEMORY compile profile requires HERMES_CONSTRUCTION/HERMES_IMPORT
and excludes HERMES_STATE. Only its selected entry executes; previous checkers
remain immutable payload members. Setup selects its own config rather than the
memory-disabled construction config. JSON report admission uses its own memory
predicates, not a fabricated memory_disabled field or construction success.

## Unchanged Boundaries

Ordinary AppContainer, zero capabilities, reduced same-user token, one-process
job, child-process block, three inherited pipes, Python -I -S -B and six
package-scoped WFP network denies remain. All network including localhost,
metadata and model endpoints is denied. Existing All Application Packages access
is a limitation, not complete customer-data isolation. Product-owned informed
administrator consent and setup/cleanup remain; no manual Windows conditioning,
ACL expansion, registry grant, loopback exemption, policy change or supervisor.

The same public non-secret SDK placeholder, synthetic model and .invalid URL
initialize the real client. No request, conversation, tool dispatch, connector,
credential or customer-data operation is invoked. External memory providers,
context files, checkpoints, compression, environment probing, tool search and
lazy installs remain disabled. SQLite is not exercised by this profile.

Payload caps stay 8192 files/4 MiB index, 32 MiB per file/256 MiB expanded.
Budgets stay 22 seconds cooperative/30 seconds host, stdout 4096 bytes and
captured text/report 65536 bytes. No deadline expansion or unrestricted fallback.

## Evidence And Stop Rule

Require exact immutable identities, attempt nonce, all 64 distribution versions,
class/origin/config checks, all eight operation predicates, final entry counts
1/1, both exact hashes, fresh-load/snapshot agreement, positive bounded peak,
residue absence, two lock probes and closure. Untrusted child evidence is not
an independent security attestation. Only natural exit 0, matching beacons,
complete admission and reported security cleanup yield
memory_completed_pending_independent_cleanup. Missing or failed checks block.
Keep containment, production and independent-cleanup flags False.

Copy/extract the complete package on the VM and return its EXE path/hash before
the separately approved run. The product requests its own consent. After one
result, stop for review and scoped independent cleanup; no automatic retry,
permission correction, alternate runtime or recovery experiment. Files/reports
remain for review. Profile removal and journal-less recovery remain unqualified.

Direct internal MemoryStore compatibility does not qualify the tool-facing
approval wrapper or its upstream fail-open import path. No hook bypass or waiver
of mandatory authorization for customer ingestion, authoritative writes,
disclosure, models or business effects follows. Governed full Hermes operation,
connectors, Metabase, Gate A and production activation remain blocked.

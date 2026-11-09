# M08 Eager Import Source Review

Source preparation approved/completed2026-11-04; candidate0.2.1-offline-final.3,
file0.2.1.21. No package assembled, product/native/bundled-runtime/VM run or retry.
See maya_model_bridge_m08_lease_lifecycle_review.md and eager_import_contract.json
(full filename maya_model_bridge_m08_eager_import_contract.json).

## Exact Change

model_worker.py relocates the identical M08-only import of final_text_evidence /
final_guard_evidence before service construction, worker readiness and issue.
No fallback or caught import failure: failure prevents readiness/grant issuance.
Other profiles do not execute that import. Existing service final diagnostics
remain enabled before issue. Helpers themselves and their transitive imports are
unchanged. ProtectedPython.cs changes only candidate/file version identifiers.
No product addition/deletion; no child/coordinator/service/helper/audit change.

An AST comparison against pinned frozen Final2 worker proves relocation is its
only logic change. Source scope receipt compares all167 product files against
Final2, with only these two replacements. Guard/issue, original26-field effects,
five-record operator-destination audit, child-positive/postcondition ordering,
diagnostics and failure behavior remain unchanged. No extra clock reads, TTL2000ms
or deadline change, grant reissue, security/WFP/token/job/permission/dependency
change, retry, inference, publication, M09/M2 or qualification.

Final2 observed expiry at2230ms, not import cost. Removing deferred setup from the
live lease interval is a narrow scheduling/setup correction, NOT proof of a
native fix or enough recovered time. Instrumentation remains capable of affecting
timing. Further expiry must remain blocked, never count as M08 operator_text pass.

## Inert Evidence

Recipes/receipts: .codex-build/maya-model-final-eager-source-20261104-1.
503 focused Python tests/1796 subtests pass. Four new test cases cover exact helper
import before construction/issue, import failure with no ready/grant/audit output,
non-M08 no-import behavior and original-worker AST equivalence after relocation.
Existing diagnostic differential tests preserve original operand trace/clock calls,
before/exact/after expiry boundaries, state/clock/audit failure and blocked evidence.
Existing positive M08 worker retains exact effects/five audit records.

515 active C# assertions;16 earlier profiles (fourteen500 each,M06/M02 profiles496
each);20 intentional invalid compile profiles rejected. Reader163assertions/13cases;
shared154bridge/874startup/231protected-Python/178audit checks pass. New successor
C# fixture differs only in version expectations; older fixtures retained.
Existing pytest cache_dir warning only. No full-repository collection claim.
Only inert fixture entry points ran, not product entry points/bundled SDK/native
execution. No performance measurement or cold native import experiment claimed.

The initial new ordering fixture used a service subclass and correctly failed
the original exact-type evidence guard. Changed the TEST to observe the original
class methods instead; no product predicate relaxed. Full final checks passed.

Final2 ZIP/EXE and all391 frozen source entries verified intact. Original source
hashes/recipe receipts and all predecessors preserved. No commit/revert.

## Next Gate

Separate OFFLINE ASSEMBLY approval required. Planned payload: only contract and
project_maya/bridge/model_worker.py replacements, no additions/omissions,6788members.
Both M08 roots/canonical helpers retained. Full actual-profile inventory/index/
resources/source-freeze admission required, then guest path/hash and separate
matching-artifact ONE-run approval/fresh consent. No VM run authorized here.
Original blocked outcome and false qualification flags remain; Gate A open.

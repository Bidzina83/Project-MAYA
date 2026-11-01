# Budget3 Build Record

Sealed 2026-11-01 after separate offline assembly approval. Version
0.2.1-offline-budget.3/file0.2.1.13, M05a same-client local budget case only.
No product, bundled runtime, Hermes/SDK or VM execution was performed.

Build folder: .codex-build/maya-offline-model-budget-20261101-3.
ZIP: Maya-Offline-Model-Budget-3.zip, 53000024 bytes.
SHA256: 99E58492B0F43671AF3FA70326BAC5BC501A9A1670971E13F6A6A119AD869173.
EXE: MayaProtectedPython.exe, 54534656 bytes.
SHA256: 132038698BA8AA67D6E5B627F1FA5314A52AF3F93CEDC186C8D64F3FE463BE66.

## Verification

6781 payload members, 144070710 expanded bytes, 965202 index bytes.
Exactly one replacement against Budget2: model-contract.json. No additions or
omissions; 6780 members byte-identical. All runtime/dependency/config bytes,
64 distributions and four native source pins preserved. Three launcher changes:
BridgeChannel.cs, ModelBridgeRuntime.cs, ProtectedPython.cs.

Actual HERMES_MODEL_BUDGET ReadIndex admission passed for both Budget3 and
Budget2 inventories, with inactive replay entries rejected. The inherited
fixture's printed Budget2/Budget1 labels are stale; admit.ps1 binds the actual
Budget3/Budget2 index paths. Content hashes are checked independently.

90 archive entries, 89 manifest-listed files plus the manifest; 87 inherited
notice/support files unchanged. 298 source/recipe/evidence files frozen.
x64 GUI PE headers and exact embedded payload/index verified without loading
the executable. Sealed verify.py rehashed the package, payload, source copies,
current matching sources and deliverable checksums successfully.
Recursive predecessor verification preserved all frozen artifacts.

Fresh assembly checks: 339 Python tests/1173 subtests, 219 active C# budget
assertions, ten paired profiles214 each, ten invalid profile combinations
compile-rejected. Existing pytest cache_dir warning only. Source-bound reader
evidence rechecked: 163 assertions/13 cases, no native product execution.
Context validation and git diff whitespace check passed; line-ending warnings
do not represent content failures. Dirty cumulative source tree is explicitly
recorded; no commit was made or user changes reverted.

## Handoff Gate

Copy/extract into a fresh guest folder; do not launch yet. Obtain actual guest
executable path and matching SHA256, then separate exact-artifact one-run VM
approval and fresh product consent. See maya_channel_reader_package.md.
No automatic retry, recovery, inference, credentials/spending or later case.
No VM-root-cause/fix claim. M05a native evidence is still pending.
production_qualified, containment_qualified and independent_cleanup_verified
remain false; Gate A remains open. Previous Budget2 attempt remains blocked.

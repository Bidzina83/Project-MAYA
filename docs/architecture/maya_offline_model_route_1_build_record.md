# Offline Model Route 1 Build Record

2026-10-31: approved M03b offline assembly completed. Written after sealing,
outside the frozen source set; this record does not change the package or any
predecessor. No product/native process, bundled Python/Hermes/SDK, VM/security
setup, network, credentials or real inference was executed. Separate matching-
artifact one-run VM approval and fresh product consent remain required.

## Exact Artifacts

Directory: .codex-build/maya-offline-model-route-20261031-1.
Version 0.2.1-offline-route.1, scope offline-hermes-route-validation-v1, case M03b.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Maya-Offline-Model-Route-1.zip | 52965882 | 643CB04074E6DCDA7A9C0E3CDA1B4943B473696A5718945CBA62C3F11B91205C |
| MayaProtectedPython.exe | 54476800 | E99997A7E3FA413648EB586B9B21814FB810031BC44AE81C7513794C2617FF13 |

Optimized x64 GUI compilation passed with warnings as errors, using
HERMES_MODEL_ROUTE,HERMES_MODEL_VALIDATION,HERMES_MODEL,HERMES_BRIDGE,
HERMES_CONSTRUCTION,HERMES_IMPORT. Product assembly was not loaded or executed.
PE x64/GUI headers, resource names and exact embedded payload/index bytes passed
inspection. The package manifest and 184-file source snapshot bind the actual
dirty working-tree candidate, not the recorded HEAD alone.

## Verified Changes

6774 payload files, 144000244 expanded bytes, 964193-byte index. Exactly 6765
Validation 2 members remain unchanged; six replacements and three additions,
no removals. Every Python/Hermes/dependency member and private configuration
byte is unchanged, as are all 64 distribution pins and native-source guards.
assembly-receipt.json enumerates old/new hashes and sizes of every replacement,
addition and reviewed launcher source. Exact payload replacements:

- model-contract.json.
- model_child_entry.py.
- model_validation_worker_entry.py.
- project_maya/bridge/model_service.py.
- project_maya/bridge/model_worker.py.
- project_maya/hermes_plugins/model_bridge.py.

Additions: model_route_child_entry.py, model_route_worker_entry.py,
project_maya/bridge/model_route_validation.py. Shared M03a worker support is
import-safe but default direct execution remains M03a. Existing M03a bootstrap
members remain; inactive M02 bootstrap admission was not broadened.

Before sealing, metadata review caught inherited M03a expected-stage and schema
labels. Only the assembly recipe metadata was corrected to request_route and
maya.model.route_validation.v1; unsealed intermediate payload/EXE were regenerated.
No product source or security/deadline/acceptance predicate changed. Final
payload contract and package manifest both carry M03b labels; finalizer checks
them explicitly. The obsolete intermediates were never run or frozen.

All payload member hashes/index entries and all 90 final archive members match
staging. All 87 inherited notice/support files are byte-identical. Existing sealed
predecessor verifier sources were checked against pinned manifests before reuse;
only their read-only archive verifiers ran, not payload imports. Validation 2,
Validation 1, M02, M01 and Document 2 artifact identities remain preserved.
checksums.json, assembly-receipt.json, verification-receipt.json and inert-checks.json
retain detailed local evidence. No new dependency or external acquisition.

## Verification And Limits

Fresh results: 258 Python tests/447 subtests; 177 active C# route assertions,
four paired profiles 168 each; startup reporting 874; M03a 108 with paired 101;
M02 117 with paired 113; earlier components 711, document bridge 154, model audit
178. Coverage overlaps and is not native-run evidence. Only inert fixture mains
ran. Python used normal temporary-folder access; one existing unknown-cache_dir
warning remains. Product-context validation and tracked whitespace checks pass.

The exact wrong-route diagnostic preserves the native request body and actual
host grant/identity. It requires a named pre-gateway route rejection, zero gateway
calls/dispatches/model-response releases/publications, exact one-record audit,
case-bound denial/SDK closure and normal child/worker exit 0. Body digests stay
equal; versioned projections bind the distinct envelope routes without publishing
the lease. Generic failure is not a passed negative. This does not establish
hostile-child bypass coverage or full containment.

Same ordinary AppContainer, zero capabilities, six WFP denies, reduced tokens,
jobs, child-process block, pipes, host ACLs/labels and all bounds. Trusted worker
is outside child containment. Profile deletion remains product-reported unless
separately checked. Qualification flags stay false; Gate A, later variants/cases,
M2, real inference and production remain pending/open. Validation 1's earlier
startup cause remains unexplained.

## Next Gate

Transfer the ZIP and extract into a separate VM folder. Return the full guest
MayaProtectedPython.exe path and its complete SHA256, then obtain separate
matching-artifact one-run approval and fresh product consent before launch.
No additional test automation or manual OS preconfiguration. After an approved
RDP run, return complete JSON and whether output stayed blank. Stop on failure;
no retry, recovery or permission adjustment. Scoped cleanup checks must bind
that attempt's exact process/root/SID/filter inventory.

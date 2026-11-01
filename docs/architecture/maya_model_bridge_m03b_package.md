# Maya Offline Model Route 1 Handoff

Preparation checks: 6774 payload files, 144000244 expanded bytes, 964193-byte
index. Exactly 6765 Validation 2 members unchanged, six reviewed replacements,
three additions and no removals. Runtime/dependency/config bytes are unchanged.
Fresh inert checks: 258 Python tests/447 subtests; 177 active C# route assertions,
paired profiles 168 each; 874 reporting assertions; prior M03a/M02/component
checks pass. Counts overlap and are not native cases. One existing pytest
unknown-cache_dir warning remains. Optimized x64 GUI compilation passed with
warnings as errors. The product and bundled runtime were not executed.

Approved 2026-10-31 for separate offline M03b assembly after
maya_model_bridge_m03b_source_review.md. Version 0.2.1-offline-route.1, scope
offline-hermes-route-validation-v1. This approval does not authorize native
execution, VM/security changes, a retry or real inference.

## Purpose

Real pinned Hermes/SDK sends its valid synthetic request. The trusted coordinator
verifies native envelope/body against the actual host grant, then changes only
route maya.offline.model.v1 to maya.offline.model.v0. Body bytes, model, attempt,
lease, SID and channel are unchanged. Existing child guards remain enabled.
Expected: named worker request_route rejection BEFORE body admission or any
gateway call/dispatch; zero model-response releases or operator publications.
The output field should remain blank. This is a trusted-coordinator worker
diagnostic, not hostile-child bypass or full containment coverage.

One exact route-rejection audit record must bind the original body, unchanged
mutant body, actual service/command IDs and original/mutant versioned envelope
projections. A projection is explicitly not a raw pipe-JSON hash. Raw lease/body
is not published. Require native constructor/SDK closure/config/origins checks,
normal child and worker exit 0, EOF, healthy audit and host evidence. Generic
failure, timeout, missing evidence or wrong boundary is NOT a passed negative.
Expected status: offline_model_route_rejected_pending_independent_cleanup.
All qualification flags remain false.

## Exact Preparation Scope

Against frozen Validation 2: replace model-contract.json, model_child_entry.py,
model_validation_worker_entry.py, project_maya/bridge/model_service.py,
project_maya/bridge/model_worker.py and project_maya/hermes_plugins/model_bridge.py.
Add model_route_child_entry.py, model_route_worker_entry.py and
project_maya/bridge/model_route_validation.py. Preserve all other payload members.
Shared M03a worker support is now import-safe; default direct execution stays M03a.
The fixed route wrapper selects M03b, not a child/environment/CLI selector.

Launcher changes are confined to reviewed ModelRouteAdmission.cs,
ModelValidationAdmission.cs, ModelBridgeRuntime.cs, ProtectedPython.cs,
ProductFiles.cs, WindowsBridgeProcess.cs and WindowsIsolation.cs. Compile
HERMES_MODEL_ROUTE,HERMES_MODEL_VALIDATION,HERMES_MODEL,HERMES_BRIDGE,
HERMES_CONSTRUCTION,HERMES_IMPORT; no MODEL_DENY. Read-only checks enumerate all
member/source changes and verify embedded resources, x64 GUI PE and archive bytes.
Source snapshots/check receipts bind the dirty working-tree candidate, not HEAD
alone. Assembly never loads the product assembly or bundled Python/Hermes/SDK.

Same embedded Python 3.13.14, pinned Hermes and 64 distributions; same private
config, native-source guards and notices. No acquisition or Python installation.
Product-owned consent/setup retains ordinary AppContainer, zero capabilities,
six child-scoped WFP denies, reduced tokens, one-process jobs, child-process block,
inherited pipes and four protected host files with existing ACLs/labels. Trusted
medium worker remains OUTSIDE child containment and implements no networking.
Shared All Application Packages access and profile deletion remain limitations.
No new registry/loopback grant, listener, service, account, credential or charge.

Ready/RPC/partial-frame limits 5000/2000/1000 ms, child 22/30 seconds; frame
8192 bytes, cumulative channel/audit 131072, request/response/stderr 4096,
report 65536, output 1024, diagnostic parser 256. Existing failure-only startup
reporting and zero-wait process snapshots are retained, not acceptance evidence.
No timeout extension, fallback, automatic recovery or retry.

## Transfer And Run Gates

Build directory: .codex-build/maya-offline-model-route-20261031-1.
Archive: Maya-Offline-Model-Route-1.zip. Extract to its own separate VM folder;
do not overwrite Validation 2 or prior evidence. Use the normal RDP workflow on
the customer-like Windows 11 Pro x64 26300.9711 baseline. Do not manually alter
OS permissions, labels, filters or registry to make the test pass.

Return the full guest MayaProtectedPython.exe path and full SHA256. Do not launch
before separate matching-artifact one-run approval and fresh product consent.
Then return complete JSON even on failure and whether model output stayed blank.
Stop on failure; no retry. Scoped manual cleanup will bind that attempt's exact
PIDs/root/SID/sublayer/filter keys. No additional VM test automation is included.
M03c/d, M04-M09, M2, real inference, Gate A, containment and production remain
pending/open. Validation 1's underlying startup cause remains unexplained.

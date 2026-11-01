# Offline Model Denial 1 Build Record

2026-10-24. Approved separate M02 offline assembly completed. This post-assembly
record is outside the source freeze and does not modify the package or handoff.
No product, bundled Hermes/SDK, VM provisioning, security change, network call
or inference was executed. Separate matching-artifact VM-run approval and fresh
product consent remain required.

## Exact Artifacts

Directory: .codex-build/maya-offline-model-denial-20261024-1.
Version 0.2.1-offline-denial.1; scope offline-hermes-model-denial-v1; M02 only.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Maya-Offline-Model-Denial-1.zip | 52951471 | 2E49D89DE23CCC30E30C95E5BB82D4D490DE8E9B97F3CF53FC6538333CEA9BD1 |
| MayaProtectedPython.exe | 54450688 | 2FDF51F2A67FA4A4E5019C880DED3200323EBEAB454AEF355C0E5808F2576FC7 |

Build defines HERMES_MODEL_DENY,HERMES_MODEL,HERMES_BRIDGE,HERMES_CONSTRUCTION,
HERMES_IMPORT. Optimized x64 GUI compilation passed with warnings as errors.
No compiled product entry point was invoked. Byte inspection verified x64 GUI
PE headers and both exact embedded payload/index resources without assembly load.

## Assembly Verification

6770 payload members, 143979363 expanded bytes, 963643-byte index. Exactly 6762
M01 payload members unchanged. Five replacements: model-contract.json,
model_child_entry.py, canonical model_service.py/model_worker.py/model_bridge.py.
Three additions: model_deny_child_entry.py, model_deny_worker_entry.py and
canonical model_denial.py. assembly-receipt.json binds every changed member's
old/new hashes and size. Python/Hermes/dependency bytes and all 64 distribution
versions are unchanged; no dependency acquisition or wheel patch.

Every payload member and final archive member passed byte/hash readback. All
90 final package files match staging, including 87 inherited notices/support
files. source-freeze contains 149 source/context/test/build files. Manifest
binds those files, source commit/dirty-tree status, configuration, dependencies,
payload/index, EXE and unchanged security/budget limits. Local checksums.json and
verification-receipt.json preserve exact output identity and verification counts.
Frozen M01 and Document 2 EXE/archive identities were checked and remain intact.

Fresh inert tests: 213 Python tests/293 subtests, 117 M02 C# checks and paired
M01/legacy checks of 113 each (overlap, not independent additive coverage).
One harmless unknown cache_dir pytest configuration warning follows disabling
the cache plugin. Context validator and tracked whitespace check passed.
The historical earlier C# component/positive regressions remain documented in
maya_model_bridge_m02_source_review.md; no native compatibility claim follows.

## Next Gate

Transfer/extract to a separate guest folder and return the exact EXE path and
full SHA256. Do not launch before separate one-run approval and fresh consent.
Expected bounded result is offline_model_egress_denied_pending_independent_cleanup:
the valid request reaches the real gateway, which denies before dispatch, with
zero model response releases/publications, exact denial audit and natural exits.
Blank model output is expected, not evidence by itself. Setup/timeout/crash/audit
failures remain blocked. Stop for review on failure; no retry or OS adjustment.

Qualification flags stay false; scoped independent cleanup follows a future
approved run. M03-M09, M2, real inference, Gate A and production remain pending.

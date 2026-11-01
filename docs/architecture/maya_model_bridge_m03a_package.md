# Maya Offline Model Validation 1 Handoff

Preparation checks: 6771 payload files, 143986827 expanded bytes, 963795-byte
index; exactly 6763 M02 members unchanged, five replacements, three additions
and the two reviewed inactive-bootstrap omissions. Runtime/dependency bytes and
configuration are unchanged. Fresh inert regressions pass: 232 Python tests/
352 subtests, 108 M03a C# checks and 101 in each paired M02/M01/legacy profile
(overlapping coverage). One harmless pytest cache_dir warning follows disabling
its cache plugin. Optimized x64 GUI compilation passes with warnings as errors;
neither the product nor the bundled runtime was executed.

Version 0.2.1-offline-validation.1; scope offline-hermes-model-validation-v1;
M03a only. Offline assembly was approved on 2026-10-31 after the exact source/
protocol review in maya_model_bridge_m03a_source_review.md. VM execution requires
separate exact-artifact one-run approval and fresh product-owned consent.

## Expected Test

Real pinned Hermes/SDK emits its original valid synthetic request. The trusted
coordinator verifies the body against the protected oracle, then derives a
separate worker request changing ONLY maya-offline-wire-v1 to maya-offline-wire-v0.
Child guards remain active and the original grant/oracle stay unchanged. Worker
must reject the fixed model before any gateway call or dispatch. Expected effects:
zero gateway calls, synthetic dispatches, runtime responses and operator model
publications, one exact validation audit record, verified SDK closure and natural
child/worker exit 0. The model-output field should stay blank.

Expected status: offline_model_validation_rejected_pending_independent_cleanup.
This is a trusted worker diagnostic, NOT hostile-child adapter bypass proof or
a successful model conversation. Generic denial, timeout, setup failure, crash,
audit failure or wrong rejection stage is blocked/inconclusive, never a pass.
No provider, credential, external model traffic, inference, customer data or charge.

## Preserved Setup And Bounds

The real product requests consent and owns the fresh private ProgramData setup,
ordinary AppContainer, zero capabilities, reduced tokens, child-process block,
one-process jobs, six child-scoped WFP deny-all filters and cleanup. The trusted
medium worker remains outside child network containment and implements no
networking. Shared All Application Packages access remains an isolation limit.
Do not manually adjust OS permissions, registry, WFP or loopback settings.
Keep the VM's customer-like Windows 11 Pro x64 build 26300.9711 configuration.

Embedded Python 3.13.14, pinned Hermes and existing dependencies are included;
no Python installation or new wheel is needed. Runtime/dependency bytes stay
unchanged. The manifest/receipt enumerate product replacements/additions and
the reviewed omission of model_deny_child_entry.py/model_deny_worker_entry.py
from this successor payload. No predecessor artifact or guest evidence is deleted.

Protected host request.json, policy.json, worker.json and audit.jsonl remain for
evidence. Private UTC config does not change Windows timezone. Preserve 22/30s
child budgets, 8192-byte frames, 131072-byte cumulative channel/audit bounds,
4096-byte request/response/stderr, 65536-byte report and 1024-byte model-output
bounds. Both jobs stop before security cleanup. Required audit failure is terminal;
no poisoned sink reopening, automatic recovery, retry or later case follows.

## Artifact And Run Gates

Build directory: .codex-build/maya-offline-model-validation-20261031-1.
Archive: Maya-Offline-Model-Validation-1.zip, with one same-named folder holding
MayaProtectedPython.exe, README.md, package-manifest.json and unchanged notices.
The build's checksums.json and verification-receipt.json record final identity
and archive/resource byte checks; source-freeze and manifest bind exact sources,
configuration, contracts, dependencies and payload. No product or bundled runtime
is executed by assembly/verification.

Copy/extract to a separate VM directory; return its full guest EXE path and SHA256.
Do not launch before separate exact-artifact approval. After approval and fresh
consent, run the actual component once through RDP, not an added VM test wrapper.
Return complete JSON and whether output stayed blank. Stop for review on failure.
Bind subsequent cleanup checks to that attempt's PIDs/root/package SID/filter IDs.

Qualification flags stay false. AppContainer profile removal remains independently
unverified unless separately evidenced. M03b-M03d, later cases, M2, Gate A, full
containment and production are not qualified or approved by this package.

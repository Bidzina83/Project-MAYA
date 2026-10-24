# Maya Offline Model 1 Package Handoff

Version: 0.2.1-offline-model.1. Scope: offline-hermes-model-wire-v1.
Prepared under the user's 2026-10-24 M01 staging/package approval. This is one
positive compatibility case, not the full M01-M09 matrix or real inference.

Preparation checks: 6,767 payload files, 143,971,886 expanded bytes, 963,259-byte
index; all 6,757 Document 2 members unchanged, ten added model-specific members.
All 64 distribution versions and three pinned native source guards match.
Optimized x64 GUI compilation passes with warnings as errors. Regression checks
pass: 197 Python tests/221 subtests and 178 inert C# model-profile checks.
Disabling pytest's cache plugin produced one harmless unknown cache_dir setting
warning; no test failed. These are not native product execution results.

## Purpose

Exercise a real pinned Hermes conversation and OpenAI SDK serialization through
the existing authorization gateway/private-pipe bridge. The trusted worker is an
explicit synthetic wire peer, not an external model. Expected effects are one
synthetic dispatch, one verified runtime delivery, one separately authorized
synthetic UI publication, six exact audit records and natural child/worker exit 0.
M02-M09 remain pending. No provider credentials, internet model call or spending.

## Preserved Boundaries

Ordinary AppContainer, zero capabilities, six package-scoped WFP deny-all filters,
reduced tokens, child-process block and one-process jobs remain. The trusted
medium worker remains outside child network containment and has no real-provider
implementation. The elevated product coordinator requests informed consent and
owns setup/cleanup. Do not manually change Windows permissions, WFP, registry or
loopback settings. The VM keeps its customer-like Windows 11 Pro configuration.
No Python installation is needed: the pinned embedded Python/runtime/dependencies
are included. No new wheel, dependency, service or account is introduced.

Protected host request.json, policy.json, worker.json and audit.jsonl are retained
for evidence. Private config uses UTC without changing Windows timezone. The
read-only output control publishes only exact authorized synthetic text.
Automatic bridge recovery and retries remain disabled. Child cooperative/host
budgets remain 22/30 seconds, frame 8192 bytes, request/response 4096, final output
1024, cumulative channel/audit 131072. See maya_model_bridge_m1_native_review.md
for complete disclosure, native oracle assumptions and timing limitations.

## Artifact And Execution Gates

The separate build directory is .codex-build/maya-offline-model-20261024-1.
The archive is Maya-Offline-Model-1.zip and contains one Maya-Offline-Model-1
folder with MayaProtectedPython.exe, README.md, package-manifest.json and the
unchanged third-party notices/licenses. Local checksums.json records final EXE
and ZIP identity; the manifest binds sources, dependencies, payload and resources.
Frozen Document 2 remains unchanged. Assembly never starts the product or bundled
Hermes/SDK. Successful byte checks are not a native compatibility result.

Copy/extract the package to a separate VM folder. Return the exact guest EXE path
and full SHA256 for review. Do not run it until separate exact-artifact VM-run
approval; fresh product-owned consent is also required. After approval, use RDP
to run this actual product component once, not a test automation wrapper. Return
the complete result and whether the synthetic output appeared. Stop on failure;
no automatic retry, OS adjustment or correction follows.

Expected success status is offline_model_wire_completed_pending_independent_cleanup.
production_qualified, containment_qualified and independent_cleanup_verified remain
false. Independent follow-up checks bind the actual attempt's process IDs, root,
package SID, six filter keys/sublayer and permissions/labels. Profile deletion
remains a separate evidence gap. M01 does not establish full containment, M2,
real inference, Gate A acceptance or production readiness.

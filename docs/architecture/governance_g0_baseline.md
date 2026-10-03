# G0 Reproducible Governance Baseline

## Current Gate

The user approved the revised G0-G7 integration plan on 2026-10-03. This is G0,
not another governance patch or a new installer. G0 acceptance is not yet complete:
native ordinary-mode regressions must satisfy the acceptance gate, including the
upstream POSIX-only control. The model/API target is now selected and documented;
runtime routing and live operation remain later qualification, not G0 evidence.

## Change Set Retention Review

The 108 pending files were reviewed against the approved G0-G7 plan on
2026-10-03. No file was identified as unrelated or safely redundant, so none was
deleted. This is a relevance disposition, not production or merge qualification.

| Group | Files | Reason To Retain |
| --- | ---: | --- |
| Product context, contracts, assessment, plan and baseline | 10 | Preserve agreed boundaries, historical scope and current acceptance criteria |
| Maya runtime and candidate binding code | 11 | Existing gateway integration and source candidates for G1-G4; not production activation |
| Regression test modules | 31 | Protect candidate behavior, ordinary controls and artifact separation |
| Ordered native patches and their README | 24 | Frozen G0 input; consolidation belongs to G6 after equivalence review |
| Native source fixtures, README and license | 25 | Referenced regression inputs with upstream provenance and license; not product runtime copies |
| Build, verification and baseline tooling | 4 | Historical test-artifact verification plus current G0 reconstruction and native controls |
| Manual native regression workflow | 1 | Linux control needed for the unresolved POSIX acceptance dependency |
| Line-ending rules and machine-readable baseline register | 2 | Stable patch/snapshot bytes and explicit coverage/provenance accounting |

All native Python fixtures have test references. Python files were parsed for
syntax; pending paths contain no generated distribution, build environment or
customer-data directories. Product package discovery is limited to
`src/project_maya`, so the tests, native snapshots and patch series are not
installed as product packages. Historical four-boundary/twelve-patch test-host
code is retained as evidence, not upgraded to the five-boundary source candidate.
Future replacement does not authorize deleting its regression controls now.

No native patch bytes, runtime pin, production gate, wheel or installer were
changed by this review. G0 acceptance remains open as recorded below.

Review verification: the 31 changed test modules ran 453 tests, with 441 passing
and 12 explicitly skipped in the development environment. Nine skipped Telegram
SDK tests passed when rerun in the isolated pinned environment; its Telegram
intake/provider fixture selection passed all 24 tests. Three artifact-dependent
checks remain skipped because candidate wheel/runtime or installed-payload inputs
were not supplied. The required Phase 6/update/setup/closure selection passed all
47 tests. Context validation, release-script compilation and tracked diff
whitespace checks passed. None of these results closes the native Linux control
or installed-product qualification gates.

The [machine-readable register](governance-g0-baseline.json) fixes the exact pin,
23 ordered patch hashes, source/dependency inputs, qualification profile, 21
lifecycle/root groups, evidence level, observed sinks, test suites and next gates.
Intended support is separate from current status. An unresolved exclusion is not
claimed blocked merely because it is absent from a tool catalogue.

Unknown/dynamically discovered roots block profile acceptance. The register must
be extended when a new root is found; it is not an exhaustive Python I/O sandbox.

## Reconstructed Evidence

Two final independent stages, `governance-g0-20261003-final-a` and `-final-b`, were reconstructed
under ignored `.codex-build/` from Git objects at
`b13e2fd6948a59eeb59fe618914147d97a2ee90a`.

- 5,463 native tracked files in each stage; 24 changed files after all 23 patches.
- Identical deterministic manifest SHA256:
  `e4b6a60dd6dfbe0552d546c3927a5ece0276a11129d5216025eca69f940fd062`.
- Original Git blob IDs and SHA256 plus effective patched hashes recorded per file.
- `pyproject.toml`, `uv.lock`, `setup.py` and `MANIFEST.in` pinned and unchanged;
  225 dependency package records with hashed registry artifacts checked.
- No packaging transformations, wheel builds, runtime-pin changes or activation.

The final manifests also hash both G0 tooling scripts and the current register.
Earlier preliminary stages used the initial register/tooling revision. Their
tested native source inventories match the final stages byte-for-byte, as does
the clean ordinary control. A preliminary direct-test attempt wrote a native
gateway cache into its stage; that stage is not reused as a clean input. Current
jobs run on disposable copies and preserve the final evidence trees.

The exporter does not read dirty/untracked source files, execute checkout filters,
copy host credentials/configuration, resolve new dependencies or fetch Git refs.
It rejects non-file tree entries, unsafe paths, unreviewed dependency sources,
changed patch bytes/order, missing native tests and undeclared source modifications.
This is an assessment tree, including native tests/docs; it is not a distributable
product payload. Pinned upstream example files are not host credential inputs.

The historical installed artifact remains the twelve-patch/four-boundary wheel.
Its evidence is explicitly separate from this 23-patch/five-boundary source stage.

## Fixed Provider Fixture

The offline fixture is explicitly OpenAI-compatible Chat Completions at
`/v1/chat/completions`, with `synthetic-model`, no live network and zero SDK
retries. Existing transport tests validate response and SSE formats and reject
unexpected paths/models. This is not evidence that a customer model supports
Chat Completions, nor approval to substitute it for Responses.

The target preserves the user's earlier GPT-6 Luna choice: provider `openai`,
model `gpt-6-luna`, endpoint `https://api.openai.com/v1/responses`, reasoning
`medium`, `store=false`, no hosted tools and zero SDK retries. This is a qualification
target, not a modification to customer configuration or native product routing.

[Official GPT-6 Luna documentation](https://developers.openai.com/api/docs/models/gpt-6-luna)
was fetched on 2026-10-03: Responses supports reasoning/function calling; Chat
Completions function calling requires reasoning disabled. The existing synthetic
Chat fixture must not be mistaken for this selected route.

`tests.test_governance_provider_profile` adds two real-SDK/MockTransport Responses
fixtures for text and a bounded function-call proposal. Both pass using the
isolated pinned OpenAI SDK 2.24.0, with no sockets or customer credentials. These
tests validate serialization/parsing only, not a native AIAgent loop or inference.

Pinned Hermes `AIAgent._model_requires_responses_api` recognizes only `gpt-5`
prefixes. GPT-6 automatic selection therefore requires explicit qualification
under G4; G0 does not patch the routing heuristic or silently disable reasoning.
Never inherit a fixture route, ambient key, saved profile or fallback model.

## Repeatable Reconstruction

Use an existing clone containing the pinned Git objects. Each output directory
must be new; failed stages are not reused. No cleanup of customer data is required.

```text
python scripts/prepare_governance_baseline.py --source-repo <Hermes-clone> --output .codex-build/g0-a
python scripts/prepare_governance_baseline.py --source-repo <Hermes-clone> --output .codex-build/g0-b
python scripts/prepare_governance_baseline.py --source-repo <Hermes-clone> --output .codex-build/g0-ordinary --ordinary-baseline
```

Compare the two candidate `baseline-manifest.json` files byte-for-byte. The
ordinary stage contains the exact unpatched source for controls. Manifest patch
records describe the reviewed series; `patches_applied` distinguishes control
from candidate. Reports contain no host paths or timestamps that affect identity.

## Dependency Preparation And Native Job

The normal Maya development environment failed the strict preflight: it is not
the native fork's pinned test environment. This is an environmental blocker, not
a native regression result. Do not repair it by mutating the development venv,
loosening pins or importing from an older installed runtime.

Prepare a separate environment using the pinned `uv.lock`: core plus `dev`,
`messaging` and `anthropic` extras. Preparation is a release/test operation, not
installer behavior. Downloads require explicit approval; use the lock without
upgrading or modifying it, disallow Python downloads and source builds, and keep
the environment/cache outside exported source. The assessment obtained approval
for lock-pinned dependency downloads into ignored G0-only directories.

Offline preparation first failed because setuptools 81.0.0 was not cached. An
isolated locked preparation subsequently installed 100 packages; no customer
runtime or development venv was changed. Optional packages required by collection must also come
from this reviewed lock, not arbitrary on-demand installs.

The native job is defined by `scripts/run_governance_native_regressions.py`:

```text
python scripts/run_governance_native_regressions.py --stage .codex-build/g0-ordinary --python <prepared-python> --mode bounded
python scripts/run_governance_native_regressions.py --stage .codex-build/g0-a --python <prepared-python> --mode bounded
python scripts/run_governance_native_regressions.py --stage .codex-build/g0-a --python <prepared-python> --mode full
```

The bounded native suite covers dispatch/plugins, SQLite/locks, context,
compression, finalization, memory, auxiliary/provider/transport, tool registry,
executor, Telegram, gateway sessions and CLI. Full mode runs the native fork's
non-integration suite. Live tests require separate explicit consent.

The runner checks stage bytes and actual installed versions, strips ambient keys,
native profiles and plugin settings, uses a temporary Hermes home, disables
external pytest plugin autoload and blocks external socket connections. Windows
asyncio's native socket-pair IPC is allowed only inside the actual socketpair
call; ordinary socket connections remain denied. Tests run on disposable source
copies, in a fresh process per file as required by native `tests/conftest.py`.
It runs complete native tests, not replacement AIAgent/session modules. Its sole pytest
plugin reports counts and enforces network/skip rules. Any required skip, missing
dependency, collection failure or failed test prevents a passing job. The job
stops on the first failing file and explicitly lists unexecuted required files.
Fixture
dependencies are prepared, never silently installed by the runner.

Keep environmental collection errors and native behavioral failures visible and
separate. A successful non-integration fork job is still not a live provider,
governed full-loop, installed-product or Windows lifecycle qualification.

## Acceptance Ledger

| G0 Item | Evidence | Status |
| --- | --- | --- |
| Independent reproducible source/patch stages | Identical full manifests and 24 changed files | Passed |
| Source and dependency input provenance | Git blob/SHA256 inventory and hashed 225-package lock | Passed |
| Maintained coverage and historical artifact separation | Machine-readable register and validation tests | Implemented; runtime roots remain unqualified |
| Explicit offline route | Six transport tests pass, no installed-payload skip included | Passed for fixture only |
| Customer model/API selection | Official model documentation and two pinned-SDK Responses fixtures | Selected; native/live route remains unqualified |
| Native ordinary-mode control and candidate parity | 1,271 passed and one POSIX-only skip on each tree; all 16 files covered through full and explicit subset runs | Gate open; no skip waived |
| Product activation/wheel/installer | Not authorized by G0 | Unchanged |

G1 must not start merely because the tooling exists. Record remaining G0 evidence
and blockers here before changing the current milestone. If a discovered dependency
requires reordering or modifying the plan, recommend it and obtain approval.

## Remaining Acceptance Dependency

### First Committed Linux Run

The bounded [G0 run for commit 6bba261](https://github.com/Bidzina83/Project-MAYA/actions/runs/37128902786)
failed in preparation, before native test execution. It does not establish a
native behavioral regression or pass the Linux acceptance gate.

- Candidate reconstruction inherited the enclosing Maya Git repository's path
  prefix. Linux reproduced the failure at Patch 15 in a nested repository; the
  same pin and patches reconstructed correctly outside that repository.
- The runner resolved the prepared venv's Python symlink to the base executable,
  discarding virtual-environment package selection. Its sanitized environment also
  removed the hosted interpreter's shared-library search path.

The local G0 tooling correction stops enclosing-repository discovery during patch
application, preserves the selected venv executable path, and derives a loader
directory only from that executable's resolved interpreter. Ambient loader paths,
credentials and native profiles remain excluded. No patch bytes, pins, dependency
locks, production gate or installer were modified.

Two corrected nested Ubuntu reconstructions produced identical diagnostic
manifests, SHA256 `8e79475c0d02e0d18fb53fc3e514d38fb9ca40606cb19692d65732e8ecca9122`.
A temporary Linux venv retained its own `sys.prefix` under the sanitized launcher.
These probes used locally available Python 3.14.4 for tooling diagnosis only;
they are not the pinned Python 3.13 native regression job. Fifteen Windows G0
tooling tests passed, including nested-repository isolation, venv-path selection
and rejection of ambient loader paths. All three new regression tests also passed
on Ubuntu. The 47 required product tests, context guard and script compilation
passed. These corrections still require a new
committed/pushed bounded Linux run and review of both result artifacts. G0 stays
open; G1 is not authorized by these diagnostics.

Both Windows control runs hit the same native
`TestWriteClaudeCodeCredentials.test_credentials_file_created_with_0o600` skip
in `tests/agent/test_anthropic_adapter.py:558`: POSIX mode bits do not apply on
Windows. No behavioral failure was observed. The three remaining files were
executed separately, 312 passed on each tree, with explicitly partial reports.
That supplements evidence; it does not convert a failed gate into success.

The manual `Governance Native Regression Qualification` workflow defines Linux
ordinary/candidate jobs over the exact pin with independent reconstruction and
lock-pinned preparation. `bounded` runs the registered controls; `full` runs the
fork's non-integration files. Runtime testing is offline, no customer credentials
are used, and required skips fail the jobs. No installer or capability marker is
created. The first committed dispatch and preparation blockers are recorded above.

After the tooling corrections are committed/pushed, rerun the bounded Linux job and review
both artifacts before accepting G0. A full-fork job is defined, not yet executed.
If Linux reveals new environmental or native failures, retain them as blockers;
do not weaken pins, delete tests, waive skips or reorder milestones automatically.

Local G0 verification also passed 14 provenance/provider/workflow tests, six historical
Chat fixture tests, the required 47 Phase 6/update/setup/closure tests, context
validation and compilation. The two Responses fixtures additionally passed in
the exact isolated SDK 2.24.0 environment. Generated stages/dependencies remain
ignored; no distribution artifact or customer state was committed or modified.

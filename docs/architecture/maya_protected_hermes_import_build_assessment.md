# Protected Hermes Import Build Assessment

## Status

The user approved the import-only proposal and requested a build. Read-only
source, archive and dependency assessment found packaging requirements outside
the current loader's bounds. No runnable package was produced, and no product
source, loader guard, dependency pin or Windows setting was changed. No Hermes
or native dependency was imported, executed or installed. No network acquisition
or VM action occurred. The preparation approval does not authorize a native run.

## Inputs Inspected

- Product pin in setup.py: Bidzina83/hermes-agent at
  b13e2fd6948a59eeb59fe618914147d97a2ee90a. The existing local Git checkout's
  HEAD matches, using a command-scoped safe.directory override, not a global
  Git configuration change.
- Cached Hermes wheel: hermes_agent-0.17.0-py3-none-any.whl, SHA256
  ee806be8b2f81359e36b114d03c4681da756150df522b30ebc45a29c2dbb04f2.
  It contains 827 files and 23,015,898 uncompressed bytes. Its run_agent.py
  matches the pinned Git blob 63050980934b2fe6421018b09fda950f708c5609.
  This entry-point comparison alone does not authenticate every wheel member;
  full source/archive provenance remains pending.
- Existing CPython 3.13 dependency tree in the historical LPAC preparation was
  inspected only as candidate data. It is not approved as a release wheelhouse.
  Older CPython 3.12 bundles were not substituted.

## Dependency Assessment

Distribution METADATA, WHEEL and RECORD files were parsed without importing
Hermes or dependency code. Windows/CPython 3.13.14 markers and requested extras
were evaluated explicitly, including socks, crypto and uvicorn standard extras.

The existing installed candidates resolve 63 core dependency distributions with
no detected requirement/version conflict. All their declared wheel tags intersect
the target's CPython 3.13/compatible-ABI Windows x64 tags. This is metadata
compatibility, not proof that native extensions load in AppContainer.

Their records identify 5,057 existing in-root files totaling 83,039,985 bytes,
excluding bytecode. There are also 116 absent recorded files and 17 records
outside the dependency root. These were not silently copied, restored or ignored
as proof of completeness. Some outside records may be installer-generated
commands; their identity and relevance require review. Freeze and authenticate
the original wheels before deciding what belongs in a product layout.

The private machine-readable assessment is retained under
`.codex-build/maya-protected-hermes-import-assessment-20261021/dependency-assessment.json`.

## Packaging Constraint

ProductFiles.ReadIndex currently rejects more than 2,000 payload files, limits
the index JSON to 1 MiB, limits each file to 32 MiB and caps total expanded bytes
at 256 MiB. ExtractPayload also requires exact archive/index count and hashes.

The 806 existing payload files plus the 827-file Hermes wheel and its required
1,059-file OpenAI SDK already exceed the file-count guard. The complete candidate
flat layout estimates 6,690 files before final import-check/manifest additions.
This estimate is not a finished payload inventory or an index-size measurement.

Do not silently raise guards, omit declared dependencies, use a patched candidate,
change Python, zip away filesystem-dependent Hermes modules or bypass per-file
inventory checks just to obtain an executable. A build that the current extractor
must reject is not a useful ready-to-test package.

## Import Side Effects

The pinned run_agent.py imports hermes_bootstrap, initializes Hermes-home and
dotenv loading, and imports model_tools. Tool discovery imports modules from a
real filesystem directory and catches some import exceptions. Therefore merely
resolving AIAgent is not proof that every optional tool loaded. Preserve this
limit in any eventual success report; no mocks or runtime patch may hide it.

Before assembly, finish the transitive import review and bind the fresh private
home/cache/temp paths and any supported opt-out configuration. Do not reuse an
operator home or .env, run lazy installers, introduce ambient credentials or
relax the existing network/process restrictions. The historical worker and
patched governance candidate are not approved substitutes.

## Recommended Bounded Revision For Approval

Permit an import-package-specific payload envelope of at most 8,192 files and
4 MiB of index JSON, with negative boundary tests. Preserve the existing
2,000-file/1-MiB defaults for earlier profiles. Keep the 32-MiB per-file and
256-MiB expanded-byte caps, exact archive/index membership, path checks, hashes,
read-only runtime, permissions, six filters and launch/output/deadline restrictions.
Measure the final inventory first; stop if it exceeds this proposed envelope.
Larger inventories add extraction, hashing and permission-cleanup work; native
timing is unproven, and the child deadline must not be increased automatically.

Also permit acquisition of the exact selected prebuilt Windows/Python-compatible
dependency wheels if absent locally, with publisher-index hash verification,
frozen versions, complete dependency metadata validation and licenses. This is
archive acquisition only: no machine installation, source/native compilation,
unreviewed version substitution or workstation payload import. Return any
unavailable wheel or additional requirement for decision.

These are proposed changes, not implemented ones. After approval, prepare the
product-owned import package and inert tests, then review its actual path/setup
impact and artifact hashes before separate approval of one RDP VM attempt.

## Subsequent Approved Preparation

The user approved this bounded revision. The product now has a compile-time
HERMES_IMPORT profile with the separate payload envelope and root allowlist;
legacy defaults remain unchanged. Exact prebuilt wheels were acquired, verified
against PyPI hashes and their internal RECORDs, and assembled without executing
Hermes or native dependencies. The resulting payload is 6,684 files, 143,209,647
expanded bytes and 952,392 index bytes; it does not use the incomplete installed
tree. See `maya_protected_hermes_import_handoff.md` for exact configuration and
limits. Native-run approval is still separate. This section supersedes the
earlier preparation stop only for the explicitly approved revision.

## Import 1 Build Receipt

- Prepared separately in `.codex-build/maya-protected-hermes-import-20261021-1/`.
- ZIP `Maya-Protected-Hermes-Import-1.zip`: 52,721,540 bytes;
  SHA256 `5B13F407F8C6AB161044CB22944CA8267C82A398D42E24C69AEEB0D2139CDEBF`.
- EXE `MayaProtectedPython.exe`: 54,178,304 bytes;
  SHA256 `20A34D3A16AC5ABC82309946F2E386B5D5BB0E88F69956F8787494F23EAB7842`.
- Warnings-as-errors optimized x64 Framework builds pass. All 40 Python
  unit/static checks and 440 inert C# checks pass: 411 prior checks in the legacy
  profile plus 29 import admission/envelope checks. Tests include old/new count
  limits, index limits, per-file/expanded caps, missing/wrong report fields,
  wrong origins/versions and cleanup gating. No bundled native dependency or
  Hermes import runs during these checks.
- An inert fixture extracts all 6,684 files; a separate pass verifies every size
  and SHA256 and the exact file count. All 806 prior Python payload entries
  retain their hashes. The final x64 GUI PE and both embedded resource lengths/
  digests verify through file-byte inspection without product assembly loading.
  Packaged files, 90 archive entries and frozen source hashes are checked.
- The 63 dependency archives match published PyPI hashes/sizes and their
  internal RECORDs; closure/ABI checks pass with no version substitutions.
  Windows-separator RECORD paths are normalized for matching, never used as
  extraction authority. All 821 Hermes source/data members match the pinned
  baseline; its pin/tree matches the local Git object. All original wheel
  licenses/notices are retained, including LICENCE-spelled notices.
- Screen 11's frozen ZIP and EXE retain their previous hashes. No privileged
  security provisioning, workstation payload launch/import or VM action occurred.

Preparation is complete for this artifact scope only. Native import support,
timing, optional modules and independent cleanup remain unqualified. The package
requires separate one-run approval and its own informed consent before use on
the Windows VM. A failed attempt stops for review, not another automatic repair.

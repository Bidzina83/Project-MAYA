# Offline Model 1 Build Record

2026-10-24. Approved M01-only offline package assembly is complete. No product,
bundled Hermes/SDK, VM security setup, network traffic or inference was executed.
Matching-artifact VM-run approval and fresh product consent are still required.
This post-assembly receipt is outside the frozen source set; it does not modify
the package, its handoff, source freeze or earlier artifacts.

## Artifacts

Build directory: .codex-build/maya-offline-model-20261024-1.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Maya-Offline-Model-1.zip | 52,943,845 | 7DF735195D52936B6AE3713A42021E62CC2D9099021FCD096A7CA90962D3A526 |
| MayaProtectedPython.exe | 54,446,080 | BDC50E29228E85566B75527899870F88925C1FD66D45C95AF4F0694FABF2BE64 |

Version 0.2.1-offline-model.1; scope offline-hermes-model-wire-v1. Compilation
used HERMES_MODEL,HERMES_BRIDGE,HERMES_CONSTRUCTION,HERMES_IMPORT, optimized
x64 Windows GUI, warnings as errors. The build recipe is compile.ps1; archive,
AST and PE-byte verification recipe is assemble.py in the build directory.
Neither recipe starts the product. Final EXE bytes occur identically in the ZIP.

The package manifest binds the source commit plus dirty-tree source hashes,
64 pinned distributions, configuration, payload/index and EXE. source-freeze
contains 135 files, including recipes and the inert-check receipt. Local
checksums.json and verification-receipt.json retain assembly evidence.

## Verification

- All 6,757 Document 2 payload members are unchanged; ten model-specific files
  produce 6,767 members and 143,971,886 expanded bytes. Index is 963,259 bytes.
- Every payload member/index hash and both embedded resource byte sequences
  match; PE headers identify x64 GUI. No assembly loading was used for inspection.
- All 90 final ZIP members match their staged bytes. The 87 inherited license/
  notice/support files match the frozen package exactly.
- All 64 distribution pins, three native source guards and canonical native
  literals hash match. No new dependency acquisition or wheel modification.
- Document 2 EXE, ZIP, payload and index hashes remain unchanged.
- 197 Python tests/221 subtests and 178 inert C# model-profile checks pass.
  One pytest unknown cache_dir setting warning follows disabling the cache
  plugin; no test failed. Context validation and tracked whitespace checks pass.

## Next Gate

Transfer/extract to a separate VM folder and return the exact guest EXE path and
full hash. Do not launch before separate approval. Only M01 positive synthetic
wire compatibility is staged; M02-M09 remain pending. M2/credentials/networked
inference/spending are not approved. Production, containment and independent
cleanup flags stay false; Gate A remains open. Stop after a failed result for
review, with no automatic retry or OS permission adjustment.

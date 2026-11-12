# Maya Journal Access 2 Offline Assembly Review

Review only. Proposed artifact: `Maya-Journal-Access-2`, version
`0.2.2-journal-access.2`, file version `0.2.2.2`. Keep scope
`offline-journal-access-matrix-v1`. No assembly or execution has been approved
by this review.

## Exact Inputs

Use sealed `Maya-Journal-Access-1` as the predecessor. Its ZIP and EXE match the
[build record](maya_journal_access_1_build_record.md), its manifest SHA-256 is
`4ca51d22855217de1e490dfc1447a87611870622bd5e90438d683c697e308f3b`, and
all 52 frozen inputs match. Preserve that build and its blocked result.

Reuse both embedded resources byte for byte. No payload additions,
replacements, or omissions. All 892 indexed members and 37,359,018 expanded
bytes were reverified:

| Resource | SHA-256 |
| --- | --- |
| Payload ZIP | `3a96765a0cdc077907a96870bca536a21dfabecec34a701b956ad996188c11d0` |
| Payload index | `62340398b3c9776384de448b05464256aa65b68fb9903e5963498a42a22a7455` |

Keep the same 44 compile paths, x64 GUI target, compiler/reference set, and
exact defines `HERMES_JOURNAL_ACCESS,HERMES_BRIDGE,HERMES_CONSTRUCTION,HERMES_IMPORT`.
Replace these three launcher inputs with the reviewed source:

| Input | SHA-256 |
| --- | --- |
| `JournalAccessRuntime.cs` | `f3d02d9671e04d070259bd59334f5d4f551f3ee974cb7541be4d30f4f30faacd` |
| `JournalTokenAccessFixture.cs` | `5ead3dbb09c8b866d18604d9c1e761517e6b1617266a30bb62e38364f04991cc` |
| `JournalTokenAccessNativeFixture.cs` | `48183d3b1c7a454abb480063e8c5ef5ac1ba57d44ca14238c77dc17c3a83f7c4` |

For the fourth replacement, stage the pinned predecessor
`ProtectedPython.cs` with only the access-profile file version,
informational version, and reported version updated. Verify the staged
delta is exactly those three literals. The other 40 compile inputs must
match the predecessor. Do not change the working-tree product sources
as part of assembly.

Diagnostics use only existing admitted reply fields. They are emitted
for incomplete rows, after the existing lifecycle and readback checks.
No raw identity, payload data, ACL or access mask change. The wire schema,
authorization, token checks, deadlines, cleanup, and verdict predicates
stay unchanged. This records why a row is incomplete, not a fix or
qualification for that row.

## Assembly Acceptance

After separate approval, use fresh staging and refuse overwrite. Reverify
the predecessor ZIP, EXE, manifest, resource bytes and source freeze before
and after assembly. Compile only; inspect the x64 GUI executable, versions,
fixed selectors, excluded types, and exact resources without executing
the product. Run the actual-profile index reader and inert profile,
native-status and lifecycle regressions. Freeze the exact recipes, sources
and fixtures, including the reviewed updated
`tests/windows_journal_access_profile_fixtures.cs` SHA-256
`4f7abfa509d063efd56b02b4e12a84b6c6aa09bfa0e178dd4fabbb8601e184e0`.
Seal ZIP and EXE and record their sizes and SHA-256 values only after
verification passes.

No product or bundled-runtime execution, real role probes, VM run,
permissions changes or retry is included. After sealing, a matching
test-machine EXE hash, separate one-run approval and fresh consent are
required. M08 remains blocked, M09 pending, and all qualification flags false.

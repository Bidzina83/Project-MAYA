# Maya Journal Access 2 Build Record

The approved offline diagnostic successor was sealed in
`.codex-build/maya-journal-access-20261110-2`. Launcher version
`0.2.2-journal-access.2`, file version `0.2.2.2`, scope
`offline-journal-access-matrix-v1`.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `Maya-Journal-Access-2.zip` | 14969191 | `b889a78290d155373b0850494810e9106ea3ac0a2baafe5112666843b3d2b75d` |
| `MayaProtectedPython.exe` | 15274496 | `94a6ff79c85c5210b684f0ebc613b3a59eadde5a94fcb034c80723acf1ec2694` |

All 892 payload members, the ZIP resource and the index resource are
byte-identical to the first build. The 44 compile paths are unchanged:
three reviewed diagnostics inputs and the staged launcher version
literals are the only compile-input changes. The source freeze records
the actual staged files. Working-tree product sources were not edited
during assembly. Both sealed predecessors were reverified.

Actual-profile index, x64 GUI header, version, scope, fixed entry names,
type exclusions and exact embedded-resource checks passed. The fixture
compiled with the actual 44 staged inputs passed 136 assertions. The
profile suite also passed 136 active assertions, eight each in both
legacy profiles, 25 compile exclusions and the cleanup order check.
The injected native-status and coordinator journal checks passed 692
and 833 assertions, respectively. The sealed ZIP contents were read
back and compared to the manifest and executable.

No product, bundled runtime, native role, or VM run occurred. The first
attempt remains blocked, its incomplete rows are unchanged, and all
qualification flags remain false. Verify the exact guest EXE hash
before separate one-run approval and fresh consent.

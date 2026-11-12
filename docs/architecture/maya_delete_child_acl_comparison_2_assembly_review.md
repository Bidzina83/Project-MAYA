# Standalone ACL Comparison 2 Assembly Review

Review only. Assemble a separate successor only after approval. Keep the
same 56 runtime compile paths, defines, compiler and references, x64
console subsystem, explicit native and inert mains, and zero embedded
resources. No product launcher or native execution during assembly.

Use the first sealed standalone build as the byte source. Its EXE and
all 62 frozen inputs rehashed successfully. Receipt SHA-256:
`207eb8391d890aed6f2304139e88dc8c8af648182ae323e981ad1e51568d27fc`.

Replace only these reviewed inputs:

| Input | SHA-256 |
| --- | --- |
| `DeleteChildAclCollector.cs` | `deb6b97aa55b337d306156e5f924ff0ed95bb819faf5c77a7da329283c8a45c4` |
| `DeleteChildAclComparison.cs` | `3ef3de3e3c371c0db85de90d089322786eeb4b9249b5204ed9df5c299d835aaa` |
| `DeleteChildAclExpectedPolicy.cs` | `69999cc85a90a9344f9322c87421386320d04f5287740f9319da1499735a9ef5` |
| `windows_delete_child_acl_comparison_fixtures.cs` | `7e5407c90d22b89fa8d26421959139ac2edaa8dfa3a22b35fac38f1c9aea17a9` |

The native entry source, scratch creation, access masks, and cleanup
boundaries remain unchanged. The additional field comparisons do not
waive an unknown group, control-flag difference or failed parent policy.
Do not modify the product validator or reinterpret either earlier result.

Use fresh staging; freeze exact inputs and recipes; run the 27 inert
assertions; verify the x64 console header, standalone main and zero
resources without running the native main. Recheck the predecessor and
seal the new executable with its actual SHA-256 and size. A matching
guest hash and separate one-run approval remain required.

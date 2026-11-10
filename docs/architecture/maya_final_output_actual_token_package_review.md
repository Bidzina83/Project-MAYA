# Journal Access Offline Assembly Review

Review only. Proposed new artifact: `Maya-Journal-Access-1`,
`0.2.2-journal-access.1` (file version `0.2.2.1`), scope
`offline-journal-access-matrix-v1`. No assembly, source implementation,
product execution, role opens or VM run is authorized by this review.

## Exact Payload

Use the sealed Final3 payload index and ZIP as byte sources. The index
SHA-256 is `17cbc9ae19fe42dd4c96ca9f963c4b08152874e7676e28485eaff603d3e328a3`
and payload ZIP SHA-256 is
`eb41614596be929c3ba1ed71622d8b983c308056a9cce26701f5668aaf13913f`.
This review verified all 6,788 indexed ZIP members by path, length and digest.
Final3 package manifest SHA-256 is
`afc0f2a1c854812ccfbb9dccfe4c5b89d112746573ae2df149fbdc482c5e8d22`.

Retain **889** members verbatim: all 796 `python/` files, all eight
`notices/` files, all 84 `project_maya/` files and `startup_check.py`
(required by the index reader, not executed here). Add exactly these three
source-pinned root members:

| Root | Bytes | SHA-256 |
| --- | ---: | --- |
| `journal_access_child_entry.py` | 1153 | `7c4e261c8baf75904efa7e48b3bbce629fd5436614630d173016b95a6775417b` |
| `journal_access_role.py` | 8666 | `f7e5f8a8d10cdb7783e4188fc2d5e0e848248ae30315df555633c04156e0d570` |
| `journal_access_worker_entry.py` | 1155 | `980433a82a3a0bfbd6303c5e2c8f593df0a4fd1a9bc4428619349de76c6a76af` |

The **5,899 successor-only omissions** are all 5,049 `dependencies/`
members, all 827 `hermes/` members and these 23 old roots:

```text
bridge-contract.json
bridge_child_entry.py
bridge_worker_entry.py
containment_check.py
hermes-construction-config.json
hermes-construction-contract.json
hermes-import-contract.json
hermes-memory-config.json
hermes-memory-contract.json
hermes-state-contract.json
hermes_construction_check.py
hermes_import_check.py
hermes_memory_check.py
hermes_state_check.py
model-config.json
model-contract.json
model-native-literals.json
model_child_entry.py
model_final_child_entry.py
model_final_worker_entry.py
model_validation_child_entry.py
model_validation_worker_entry.py
model_worker_entry.py
```

Result: **892 members, 37,359,018 expanded bytes, zero replacements**.
Nothing is removed from Final3 or the source tree. The sealed index resolves
each membership rule to exact names and hashes; reject any count, path or
digest drift. The existing broad bridge path rules are not an assembly
allowlist.

Both role entries add only their fixed runtime directory to the isolated
interpreter search path and use the same fixed role helper. The helper
imports `project_maya.bridge.protocol` and `transport`; importing the
package also runs its existing initializer. Static traversal of the sealed
modules found 43 reachable modules through eager import statements. The
non-stdlib names found were optional `cryptography` imports: the broker
handles absence at import, and release type imports are under
`TYPE_CHECKING`. Broker and release operations are not called. Preserve
the full canonical package and Python tree instead of trimming individual
modules. The Python tree includes `ctypes`, `_ctypes.pyd` and
`libffi-8.dll`; no bundled site-packages, path hooks, or venv config were
found. This is static dependency evidence, not a Windows startup result.

## Exact Compile Inputs

Compile x64 WinExe, warnings as errors, using the existing .NET Framework
compiler/reference set and main `ProjectMaya.WindowsRuntime.ProtectedPython`.
Use exactly `HERMES_JOURNAL_ACCESS,HERMES_BRIDGE,HERMES_CONSTRUCTION,HERMES_IMPORT`.
Use the sealed Final3 manifest's 38 C# paths, substituting the four reviewed
hashes below, plus the six reviewed journal C# paths. The other 34 C# files
must match Final3. Do not glob new files into the 44-source compile; leave
`CoordinatorJournalScratchTarget.cs`, `FinalOutputInertAdapter.cs` and
`FinalOutputInertHandles.cs` out of the product compile. Keep their source
and use fixtures only in separate inert test executables.

| C# input | Reviewed SHA-256 |
| --- | --- |
| `ProductFiles.cs` | `a504f7a762fccc53464b4c7b0b9a552adc2f7ee2ac55a5ac77b571447d4273b0` |
| `ProtectedPython.cs` | `229c62b3cd397cd9a11b219de7cffde014baaf75d6ad08139e527e0bdfeb9a56` |
| `WindowsBridgeProcess.cs` | `1468d7dff88afbb10329ff006a2b89eff0d5cfa13858efb5412f698f8b70515d` |
| `WindowsIsolation.cs` | `26b97c9ad9044bb37d447f0baa546102b84bf6b6cf5072db837453e341d4a0d5` |
| `CoordinatorJournalCandidate.cs` | `99d6d2648c1c5b6e7036c23e904ff1dc0a60205d322ad6889900de4922f85469` |
| `CoordinatorJournalDescriptor.cs` | `c163a41125f7868447c90ee5d3774687e669ffe98d8d9956a4c131aec6509dbf` |
| `CoordinatorJournalNativeTransport.cs` | `c1181529648e1f40e23dce1995c4a6fd4436bf1c7cf0823938b46e1be3ba0ea3` |
| `JournalAccessRuntime.cs` | `46a9d34375d3e59c6b08e0b19cb83985a110801b5a0387cd446fe94a46d5e12b` |
| `JournalTokenAccessFixture.cs` | `2f3efe03256164fa5426af5a2cb5ca866ab0e415024689ac27e4f17de24ef028` |
| `JournalTokenAccessNativeFixture.cs` | `44eb35a6f663fdd72150569b18712f18b0239fcf04c5d6d1ac2c64d63c6ec6e9` |

## Assembly Acceptance

1. After separate approval, create a fresh build directory and refuse
   overwrite. Reverify the Final3 package, EXE, manifest, payload, index,
   all 401 frozen source entries and the reviewed inputs. Freeze the exact
   sources, recipe, review and tests used in the new build.
2. Check archive/index equality, canonical path spelling, case-insensitive
   uniqueness, bounded sizes and all 892 per-member hashes. Run the real
   access-profile index reader against the new index in an inert fixture,
   including missing-root, alias and legacy rejection checks. Validate
   static import paths against the actual retained bytes.
3. Compile without running the product. Embed only
   `MayaPython.payload.zip` and `MayaPython.payload-index.json`.
   Inspect the PE and resource bytes without invoking the launcher, and
   confirm x64, version, scope, fixed selectors, excluded fixture/native
   role runner types and equality with the verified payload and index.
   Run only the inert fixture mains and existing inert regressions.
4. Seal the ZIP and EXE and record their actual SHA-256 and sizes, the full
   source and payload inventories, and verification results. Recheck the
   predecessor pins and keep execution and qualification flags false.

Assembly cannot prove actual-token access or post-run cleanup. In particular,
the child state grant has no explicit package `WRITE_DAC` or `WRITE_OWNER`
grant. If an exact same-right control cannot open, the corresponding denial
row remains incomplete. A forbidden open remains significant even if the
control fails. Do not widen permissions to make the matrix pass. A later
exact-artifact one-run approval and fresh consent are required to test it.
M08 remains blocked, M09 remains pending, and Gate A stays open.

# Standalone ACL Comparison Assembly Review

Review only. Proposed executable: `MayaDeleteChildAclComparison.exe`.
Compile x64 console with explicit main `DeleteChildAclComparisonNative`.
No product launcher, embedded payload, or product resources. Compile the
separate inert main `DeleteChildAclComparisonFixtures` and run only that
main during assembly.

Use the 53 C# runtime paths from the sealed Delete-Child-3 source freeze,
substituting only the reviewed `DeleteChildControlCreate.cs` and adding
the three comparison sources. Use one explicit main source per compile.
Defines: `MAYA_DELETE_CHILD_ACL_COMPARISON_INERT`,
`HERMES_JOURNAL_DELETE_CHILD_SOURCE`, `HERMES_BRIDGE`,
`HERMES_CONSTRUCTION`, `HERMES_IMPORT`. Use the predecessor's compiler
and reference set. Do not add any other fixture or Access 2 flags.

The sealed predecessor manifest SHA-256 is
`9c184a6109535db79a440f60ba987994d9cfbc5ee3c3f279d07cb2a46d3ddfe6`.
The ZIP, EXE, and all 64 frozen inputs matched at review.

| Reviewed input | SHA-256 |
| --- | --- |
| `DeleteChildAclCollector.cs` | `8706dcb5df044c438d83256c59f4343be4f9523b171b1e69302d01bed7217c37` |
| `DeleteChildAclComparison.cs` | `167b807165af7e0c769cc42472446e5b22c66ae1d840084da697a39ad8b9e633` |
| `DeleteChildAclExpectedPolicy.cs` | `0d477f106f6eaf30cfb24066e99675310608b5e9e06908e349f0e35225d31f19` |
| `DeleteChildControlCreate.cs` | `912d4340728fcb82ce7625dbf2b418b641f2ce83c366b818b6ccef77a6f450ce` |
| `windows_delete_child_acl_comparison_fixtures.cs` | `dbfaceaad05a4a9079fb1cd76e0245afa8ddab6851e456d17848c9d337b53fe9` |
| `windows_delete_child_acl_comparison_native.cs` | `f4e4b94c89f3d345de30b8a99e50f2b5a39de5b9cd6e07bdd68e1a7c56cd4bb4` |

The synthetic state parent now uses the profile's StateSecurity and
separate Low label sequence. The exclusive child create uses the same
requested access as the sealed profile; the collector does not exercise
that handle's DACL write right. No temporary grant, AppContainer launch,
or ACL update after child creation. The outer scratch descriptor and
synthetic package SID remain experimental differences. Exact ordering and
descriptor control flags remain conservative comparison requirements: a
normalization difference can make the result inconclusive, not a pass.

After separate assembly approval, freeze the exact inputs, compile with
warnings as errors, verify x64 console PE, standalone entry point and
absence of embedded resources, and rerun the 24 inert assertions. Reverify
predecessors and seal the standalone EXE with its hash and size. Do not
invoke the native main. A matching guest hash and separate one-run
approval are required. Delete-Child-3 remains blocked and inconclusive.

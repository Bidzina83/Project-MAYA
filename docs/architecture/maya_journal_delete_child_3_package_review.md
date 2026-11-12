# Delete-Child Rejected ACE Assembly Review

Review only. Proposed artifact: `Maya-Journal-Delete-Child-3`, launcher
version `0.2.3-journal-delete-child.3`, file version `0.2.3.3`. Keep the
scope and all 53 compile paths and four defines from Delete-Child-2.

The predecessor ZIP, EXE, 64 frozen inputs and both resources rehashed
successfully. Its sealed manifest SHA-256 is
`c3bd218b3b6cafa7c542d8a58d4372253cd7dbce05b67a61a695ddcd2a7fcd28`.
Reuse the 891-member payload ZIP and index byte for byte, with no
additions, replacements or omissions:

- ZIP: `f57cea986ca3b0814e73ccc7bcb8f912a05ed0fb225ac53f0af5c8a52f73326f`.
- Index: `d8f8ea595da9907aef21727eb7078181044a2fc2cbafb13ac7ac8fc4baabe036`.

| Reviewed source | SHA-256 |
| --- | --- |
| `DeleteChildControlDescriptor.cs` | `80070024b0c7ee08c1bc92c9697d749c32c1961715e918a7b50c7476f55c6124` |
| `DeleteChildControlProvision.cs` | `dd74a57416b1e77ae24d0d5f9607a2df111ebe85b99a5b1826d86cd0e3bef08a` |
| `ProtectedPython.cs` | `bae0e708f7029464b04efe3f5f924b61baab5322bbe541b4a489afbf2acd3f54` |

Stage only the three profile version literals on top of the pinned
launcher source. Other compile inputs must match Delete-Child-2.
The reviewed `windows_delete_child_control_descriptor_fixtures.cs`
SHA-256 is `25bb444aa6344e00e9455d12cd62dbf3dc4dd2c451796daca349a764d94b9f4f`.

The bounded report identifies the first rejected entry's ordinal, type,
flags and failed predicate. No SID or raw ACL is reported; the rejection
predicates, permissions, and cleanup rules are unchanged. The observed
Delete-Child-2 result stays blocked and inconclusive.

After separate assembly approval, verify the full actual index and
resource bytes, x64 GUI metadata, fixed selector and excluded profiles.
Rerun the 97-assertion diagnostic fixture, Python entry tests and legacy
profile checks. Freeze inputs and seal only after all checks pass.
No product execution or live permissions change. A matching guest hash,
separate one-run approval and fresh consent remain required.

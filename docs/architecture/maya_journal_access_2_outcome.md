# Maya Journal Access 2 Outcome

Attempt `a7400cad73ea4c5e89a471bbb861aef4` on Windows build
`26300.9711` reported the SHA-256 recorded in the sealed
[build record](maya_journal_access_2_build_record.md). Both roles exited
naturally and the launcher verified journal readback.

- Reduced worker: eight verified target-specific denials.
- AppContainer child: five verified target-specific denials. For
  `write_dacl`, `write_owner`, and `delete_child`, both the target and
  the matching control open returned Windows error 5. These rows remain
  incomplete under the same-right positive-control requirement.
- No forbidden open was observed. `delete_child` tested an open on the
  attempt directory, not a deletion or an open on the journal file.

The sealed state policy explains the pattern: neither side explicitly
grants the first two rights, and the operator's Modify grant lacks the
directory delete-child bit even though the package-side grant includes it.
This is a source-level explanation, not a captured live access decision.
Do not generalize the observation to other objects or tokens.

Operator checks found no matching processes, no package SID grants across
965 entries, the expected retained ACLs and integrity labels, all seven
recorded WFP IDs absent, and a matching journal SHA-256. The independent
reparse-point result and journal byte count were not confirmed. Profile
deletion remains launcher-reported.

Preserve the original `blocked` verdict, the same-right acceptance
requirement and all false qualification flags. No rerun or ACL change.
Only design a separate test if a release requirement calls for
target-specific proof for the three remaining rights. M08 remains blocked,
M09 pending, and Gate A open.

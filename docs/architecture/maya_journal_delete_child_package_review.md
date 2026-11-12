# Delete-Child Offline Assembly Re-Review

Proposed artifact: `Maya-Journal-Delete-Child-1`, version
`0.2.3-journal-delete-child.1`, scope `offline-journal-delete-child-control-v1`.
Review only; no assembly or native run.

Use the sealed Access 2 payload as the byte source. Retain 890 members
unchanged, including `journal_access_role.py`. Omit only
`journal_access_child_entry.py` and `journal_access_worker_entry.py`
from the successor. Add only `journal_delete_child_entry.py` (SHA-256
`c416ddd8009e385f9b8e3666992f0ebb1b1a6e98aeee533a353caf6bd71d4f72`).
Expected inventory: 891 members and 37,359,038 expanded bytes. No replacements.
The Access 2 ZIP, EXE and frozen sources were independently rehashed.

Compile x64 GUI with the existing compiler/reference set and only
`HERMES_JOURNAL_DELETE_CHILD_SOURCE,HERMES_BRIDGE,HERMES_CONSTRUCTION,HERMES_IMPORT`.
Use the predecessor's 44 C# paths plus the nine `DeleteChild*.cs` sources
present at this review: ControlCreate, ControlDescriptor, ControlLease,
ControlOwner, ControlProvision, ControlWindowsHandle, Exchange, Probe,
and Reply (all with the `DeleteChild` prefix). Do not glob new files into
the approved compile. The seven changed predecessor paths are
`CoordinatorJournalCandidate.cs`, `CoordinatorJournalDescriptor.cs`,
`CoordinatorJournalNativeTransport.cs`, `ProductFiles.cs`,
`ProtectedPython.cs`, `WindowsBridgeProcess.cs`, and `WindowsIsolation.cs`.
Other predecessor compile inputs must match the sealed manifest.

The previous create-then-reopen blocker is addressed in source: an exclusive
create relative to the verified state directory returns the retained handle;
collision, unexpected disposition, wrong object or invalid handle prevent
the grant write. The new profile's 87 inert assertions cover the admission
checks. Native creation, descriptor normalization and same-handle identity
are not verified.

After separate assembly approval, pin all reviewed input bytes, check the
actual profile index and fixed selector, verify the exact ZIP and index
resources and x64 GUI metadata, and rerun the inert suites. Freeze sources
and verify both artifacts before sealing. Do not enable fixture or Access 2
profile flags. Preserve all predecessors. A matching guest hash, separate
one-run approval and fresh consent remain required. Access 2 stays blocked;
no qualification or other case follows.

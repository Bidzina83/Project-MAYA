# Coordinator Journal Native Transport Source Review

Approved compile-gated native source and injected checks completed 2026-11-09.
`CoordinatorJournalNativeTransport.cs` is excluded without
`MAYA_FINAL_OUTPUT_INERT_FIXTURE`. No launcher, product profile, worker command,
real sink, native execution harness or runnable package was added.

The transport takes a trusted attempt and expected parent/volume IDs and accepts
only the existing fixed journal leaf and exact creation descriptor. It opens
and retains the ancestor chain with no delete sharing, verifies opened paths,
IDs, disk/directory flags and reparse status, and compares the attempt parent
to its trusted identity. The leaf is requested with CREATE_NEW, share zero,
noninheritance and the fixed descriptor. There is no path or ACL fallback.
The transport assumes trusted prior attempt admission and does not replace
that admission's ancestor descriptor checks.

The backend uses retained SafeFileHandle instances for native file metadata,
scoped descriptor, positional reads/writes and FlushFileBuffers. The transport
rechecks ancestor/leaf identity and descriptor around I/O, bounds transfers,
rejects short counts and poisons on ambiguity. The coordinator candidate adds
exact prefix comparison and journal record ordering. Owned handles close in
reverse order; no recovery writer or deletion is provided.

833 combined candidate/injected transport assertions passed. They check exact
open requests, fixed target and descriptor, local-volume admission, handle
identity and retention, substitution, wrong descriptors, short transfers,
flush failure, poisoned state, bounds and reverse-order close. The legacy
compile excludes the candidate. Prior 219 C# assertions and 108 focused Python
tests passed (existing pytest cache_dir warning). Only fixture entry points
ran; the Windows backend was compiled but not invoked. Final3, 401 frozen
files, 167 original product files and V2 probe hash remain unchanged.

Native handle behavior, descriptor round-trip with the actual coordinator,
actual worker/child token exclusion, native restart reader, and live seal
verification are not established. Scratch probe results do not cover this
descriptor or transport. Next: approve a separately bounded native-positive
harness design for this exact descriptor and transport before any execution.
No ACL change, VM run, package or qualification occurred; Final3 stays blocked.

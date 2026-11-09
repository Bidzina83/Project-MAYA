# Windows Handle And Worker Inert Contract

Approved fixture-only source step, 2026-11-09. No Win32 implementation,
real worker, production profile, package, or VM execution is authorized.

## Worker Handoff

Keep the exact finish/seal wire shapes in
`maya_final_output_windows_inert_contract.md`. The fixture validates a returned
seal only after a single finish on the retained process and private pipe
identities. Required ordered observations are finish sent, exact correlated
seal read, clean EOF with no trailing data, and natural exit zero on the
original process handle with clean stderr, all within the existing budget and
before any forced stop. The seal is checked against the four-record prefix by
the existing inert adapter. The fixture models the worker hashing its original
writer, then closing it successfully before responding; a mismatched writer
identity or a response before close is rejected. Never reopen by PID or accept
a child-originated reply. A failed handoff is terminal for this fixture owner.

## Opened Objects

Injected observations carry a retained handle token, opened parent identity,
volume/file identity, descriptor fingerprint, byte length, link count and
regular/local/non-reparse and parent-pinned flags. The independent provisioning
expectation supplies parent, file and normalized descriptor identities. The
descriptor fingerprint represents owner, group, exact protected DACL and label;
the fixture does not compute those from Windows. No supported native volume or
new rights/label is selected here. Identity fields are opaque fixture values.

The journal must start empty, exclusively created and non-inheritable, with no
read/write/delete sharing. Keep the same handle token from creation through
append, flush and readback. Verify identity before and after each operation;
enforce a 16 KiB maximum and exact transferred counts. Poison on failure and
do not recover a poisoned writer. The separate worker audit read uses a pinned
opened object matching the provisioned and sealed writer identity, with a
131072-byte maximum. It cannot mutate the worker journal.

## Restart Evidence

The classifier is read-only and uses independently trusted canonical bindings
for the expected records. Exact intent plus exact confirmation or pre-effect
stop is classified as recorded. Intent alone, torn, extra, stale, unreadable or
invalid data cannot prove nonpublication. Missing evidence is distinguished
from confirmation and never grants authority. There is no restore, retry or
publish API on the classifier. A native reader would still need opened-object
provenance and independently trustworthy expected bindings after restart.

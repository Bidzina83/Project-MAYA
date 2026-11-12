# Disposable Delete-Child Control

Design only. Evaluate whether a synthetic positive control can establish
target-specific denial of the directory `delete_child` right. This is a
separate experiment, not a revision of the
[Access 2 outcome](maya_journal_access_2_outcome.md).

## Boundary

Use a fresh synthetic attempt. Keep the existing AppContainer child token,
launch checks, jobs, network policy, state grants and target attempt-directory
descriptor unchanged. The coordinator provisions one fixed, empty, disposable
directory inside the attempt's isolated test area. Its test-only permissions
may differ only on that directory and only as needed for the single requested
right. No inheritable new grants, broader principals, changes to parent
permissions, privileges, real state or journal permissions. If those limits
cannot be met with the same child token, stop the design.

## Proposed Placement And Permissions

Use exactly `<fresh-attempt>/state/delete-child-control`, a new empty
directory, distinct from the protected target `<fresh-attempt>`. Admit
it only in the separate synthetic profile. Keep the existing state
inheritance and Low integrity label. Verify the inherited package-side
directory right before launch; if absent, stop rather than grant it.
The only proposed descriptor delta from an ordinary state subdirectory
is an allow entry for the already-bound operator SID for the directory
`delete_child` right, applying to that directory only. No new package
entry and no inheritance flags on the test entry. Review the resulting
descriptor and reject any effective-right or inheritance drift beyond
the approved delta. Confirm fixed placement, no reparse points, distinct
identities, and an unchanged target descriptor; a missing, replaced,
or nonempty control cannot support a pass.

The child requests only the existing exact `delete_child` mask, using the
same open-existing, no-follow directory open and sharing settings on both
objects. The coordinator fixes both paths and verifies their distinct opened
identities, descriptors and expected placement before launch. No delete,
rename, content write, or permission change by the child. Do not add rights
to the probe handle to make identity lookup work.

## Evidence And Verdict

Bind the reply to the verified child token, retained process and pipe,
attempt and single challenge. Require the original lifecycle checks:
closed input, one valid reply, output EOF and natural exit. Recheck the
objects and retained journal before cleanup. Use existing stop-before-
revocation ordering and independently check removal of test-only access.

After the owned jobs are confirmed stopped, remove the explicit test-only
operator entry from the verified control object before ordinary state grant
revocation. Do not assume the existing package-SID cleanup removes this
operator entry. Apply that requirement on partial setup failures too,
including a failure before child creation. If job stop, identity binding,
or grant removal is uncertain, record cleanup as pending; do not apply
permission changes to an unverified path or count the result as passing.
Verify absence of the explicit test grant separately from package SID
removal. Do not require deleting the retained empty directory to prove
revocation.

| Observed result | Verdict |
| --- | --- |
| Control opens, same-handle identity matches, handle closes, and target returns access denied | Target-specific denial for this test only, subject to lifecycle, readback and cleanup checks |
| Target opens | Forbidden open; never a pass even if the control fails or the target handle cannot be identified |
| Control fails, cannot be identified on the same handle, or fails to close; target returns another error; or evidence is incomplete | Inconclusive; no retry or extra rights |

Before source preparation, review the exact directory placement, descriptor
delta and cleanup path, including failure before child launch. Inert tests
must reject changed target permissions, inherited test grants, wrong or
aliased objects, unbound replies and failed lifecycle or cleanup. A valid
result would cover a requested directory open, not actual deletion, rename
or substitution.

This design does not authorize code, assembly or execution. Leave
`write_dacl` and `write_owner` out. Access 2 remains blocked; M08, M09,
Gate A and all qualification flags are unchanged.

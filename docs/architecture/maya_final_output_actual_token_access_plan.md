# Coordinator Journal Actual-Token Access Plan

Design review, 2026-11-10. The coordinator baseline passed on local NTFS under
the elevated test token. It did not exercise either restricted token. This
review authorizes no source change, process launch, package, ACL change, or VM
test. Final3 remains blocked.

## Test Boundary

Use a distinct synthetic access-only profile and fresh attempt. Launch fixed
probe entry points through the existing worker and AppContainer child launch
paths, retaining their process handles, token checks, private pipes and job
ownership. The worker must be the actual reduced non-AppContainer worker;
the child must be the actual final AppContainer process, not its pre-launch
token or an impersonated approximation. Confirm the PID/attempt/role against
the original process and private channel before accepting results. Preserve
existing isolation; any required provisioning and cleanup must be specified
and separately approved before execution. No generic filesystem command,
model invocation, output consent/permit, seal protocol, or real sink.

Use one new synthetic journal in the candidate's attempt-relative location,
outside the legacy worker inventory. Create it with the exact reviewed
Administrators/SYSTEM descriptor and write fixed non-sensitive bytes. Verify
the opened volume/file identity, descriptor and digest, close the exclusive
writer and leave no coordinator handle to the journal open for the test.
Do not reuse the baseline or interruption folders. Never pass a journal or
parent handle to either process; admit only the existing explicit pipe-handle
allowlist and verify the journal handle was non-inheritable before close.
This verifies the intended launch boundary, not arbitrary process handle
enumeration or protection from an already compromised coordinator.

## Open/Close Matrix

Both processes run the same fixed rights matrix on role-specific fixed targets.
Every test open uses OPEN_EXISTING, no backup/restore intent or privilege
changes, and no mutation. Close any obtained handle immediately, without
reading or writing content, changing metadata, renaming or deleting objects.

| Group | Separate requested rights | Expected journal result |
| --- | --- | --- |
| Data | Read data, write data, append data | Denied individually |
| Control | Delete, write DACL, write owner | Denied individually |
| Parent | Delete-child, add-file on the journal parent | Denied individually; distinct from leaf result |

For each role and requested right, use a paired positive control with the same
access mask and applicable flags on a fixed synthetic file/directory under
that role's already permitted access pattern. Worker controls belong to its
private host area; child controls belong to its scoped state area, subject to
existing inventory contracts. Do not change either role's token or widen its
access to make a control pass. For a specialized right without a legitimate
positive control, mark the result incomplete, even if the negative returned
access denied. Source prep must pin exact masks, share/flag choices, control
paths and inventory handling before probe code can be reviewed.

## Evidence Admission

Use a strict versioned reply from each private channel. Bind attempt, role,
process identity and command ID; report one bounded row per fixed right with
control and target open status, native error and successful-handle-close
status. No child-selected paths or arbitrary error strings. The coordinator
owns expected case IDs, order, masks and target identities. Require exact
shape, complete matrix, no duplicates or extra frames, EOF and natural exit.
Do not treat child testimony alone as proof of the target or token.

- A successful forbidden open is a failure, even if no bytes were touched.
- A negative is admitted only with a successful same-token positive control
  and target access denied. Sharing conflict, missing target, wrong object,
  unsupported rights, malformed reply or timeout is blocked/incomplete.
- After both processes exit, reopen the journal read-only as coordinator and
  verify the same descriptor, opened file identity, size and digest. Keep the
  journal and scoped cleanup evidence. Do not repair or retry a failed attempt.
- Parent-rights negatives are not an actual rename/hard-link/reparse test.
  Those would require distinct disposable objects and explicit approval.

Report per-right coverage. Do not qualify a role whose required controls or
rows are incomplete. A pass establishes only the tested rights on the tested
objects under these actual tokens, build and volume. It does not establish
production containment, worker seal, crash durability or M08 completion.

## Next Approval

Recommend **source-only contract and compile-gated inert fixtures** for the
fixed access matrix, strict result admission and launch binding. Keep probe
opens injected in that step; do not enable runnable worker/child entries or
assemble a package. Review the exact controls and fixtures before considering
native source wiring, assembly, and separately approved guest execution.

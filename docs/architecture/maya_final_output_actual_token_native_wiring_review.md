# Actual-Token Access Native Wiring Review

Review only, 2026-11-10. No new source, test execution, profile, package, token,
ACL, or VM changes. Final3 remains blocked. The 399-assertion result is inert;
the positive native baseline exercised only the elevated test token.

## Which Controls Are Plausible

| Role | Existing provision | Expected same-mask controls | Limit |
| --- | --- | --- | --- |
| Reduced worker | `BridgeHostFiles.DirectoryAcl` and `FileAcl` grant the operator SID Full Control on private host objects | All eight opens are plausible, including DACL/owner rights | Successful open is not proof the token can perform every metadata change; do not perform one |
| AppContainer child | `ProductFiles.StateSecurity` grants package read, write, delete, synchronize and directory delete-child, with low-integrity state | Six data/delete/parent opens are plausible using the matching file or directory | No explicit package `WRITE_DAC` or `WRITE_OWNER` grant; expect incomplete if the exact controls fail |

These are source inferences, not permission observations. The launch-time
checks in `WindowsBridgeProcess.StartWorkerEntry` and `WindowsIsolation.TokenCheck`
must still establish the actual worker and final child tokens. The worker's
operator SID remains relevant to its private controls; Administrators deny-only
is not equivalent to losing the operator SID. The child controls must inherit
the existing state grants and integrity handling. Do not change ownership,
inheritance, labels, grants or privileges to force a control to pass.

Use the existing role-specific ACL patterns for disposable controls, not the
coordinator's journal ACL. Admit a distinct synthetic inventory for the new
profile: the fixed control directory and file only in each allowed area, with
legacy host/state inventory checks unchanged in every older profile. Provision
before role resume and independently verify the exact object type, identity,
descriptor and label. Validate that the target journal and attempt directory
are distinct from all controls. No content reads or writes by the probe roles.

The [Windows access-right definitions](https://learn.microsoft.com/windows/win32/wmisdk/file-and-directory-access-rights-constants)
distinguish leaf data rights from directory rights, even when numeric bits
coincide. Keep the reviewed exact desired-access masks. In particular do not
add `FILE_READ_ATTRIBUTES` or `READ_CONTROL` to help obtain evidence: denial
of the combined mask would not prove denial of the original right. Open-only
parent tests do not prove rename, deletion, or hard-link behavior.

## Preserve Successful-Open Evidence

The inert status format currently requires a file identity whenever `opened`
is true. Native wiring must handle a successful open whose identity query
fails. Use [GetFileInformationByHandle](https://learn.microsoft.com/windows/win32/api/fileapi/nf-fileapi-getfileinformationbyhandle)
on the same exact-mask handle, and always attempt close. Do not turn a later
query or close failure into an open failure. Propose a separate versioned
native status with `opened`, `closed`, `open_error`, `identity`, and
`identity_error`. A valid target open is forbidden even when identity is
unavailable or close fails. A positive control requires the expected identity
and successful close. If the identity query is not available for a control's
exact mask, mark it incomplete. Never reopen with more rights to fabricate a
matching same-handle control. Keep the prior inert reply format unchanged.

Capture a failed open's native error immediately. Require the target to return
access denied with the writer closed and object identity verified before and
after. Sharing conflict, missing file, invalid mask/flags, metadata failure,
wrong identity or unreadable evidence is not a verified denial. A worker pass
cannot substitute for incomplete child rows; report per-right coverage rather
than rolling partial results into a role-wide exclusion claim.

## Wiring And Gates

Use fixed synthetic worker/child entry points, exact compile/profile gates and
the original retained process handles, token verification, private pipes and
natural-exit admission. Do not route commands into legacy roles. No caller-
selected path, role, mask or disposition. Seal the synthetic journal before
resuming probes and close its writer; do not pass any journal handle. After
both roles exit, independently reopen as coordinator and verify unchanged
identity, descriptor and bytes. Keep standard scoped cleanup evidence.

Recommend the next approval be **native open/close adapter source and injected
tests**, including the versioned status and identity/close fault cases. Keep
the adapter disconnected from both launcher paths in that step. Review
synthetic inventory/launch wiring separately before implementing it. No actual
token probe, ACL widening, worker seal, package assembly or VM run is approved.

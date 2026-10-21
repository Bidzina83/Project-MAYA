# Screen 10 Read-Only Cleanup Review

## Boundary

This is an operator-guided inspection, not a cleanup script or new test runner.
Use the same Windows account through RDP. Close Maya normally before checking.
Do not terminate stale PIDs, invoke recovery, delete files, recreate a profile,
rerun Maya or modify permissions/rules. Any unexpected resource stops for review.

Bind checks to the exact attempt inventory in the operator's original report.
Keep private identifiers and exported machine policy on the VM; share only
relevant output. Record check time, errors and coverage separately. Never rewrite
the original report's independent-cleanup flag from these instructions alone.

## Ordered Checks

1. Inspect the reported host/child PIDs and current Maya processes, including
   creation time and executable path. PID reuse is possible; a matching number
   alone is not a leftover process. Missing access is unknown, not absence.
2. Check the two exact owned alias objects and their reparse attributes before
   considering recursive file inspection. Test-Path alone is insufficient for
   dangling links. Unexpected links require review, not traversal or deletion.
3. Inspect the retained attempt tree's permissions for the exact package SID,
   including descendants and the public-control grant. Check the state integrity
   label separately. Top-directory ACL output cannot prove descendant cleanup;
   incomplete enumeration or unreadable objects leaves this check incomplete.
4. Export current WFP state with the built-in read-only show-state operation to
   a new private evidence file. Confirm command success and a valid nonempty
   export before structured inspection for all six exact filter GUIDs and the
   sublayer GUID. Do not assume an XML layout before inspecting it. Absence in
   an unsuccessful export or a layer-filtered listing is not proof of cleanup.
5. Inspect the four reported listener ports, correlating any owner with current
   process identity and creation time. Ports may legitimately have been reused.
   A query error is not evidence that no endpoint exists.
6. Assess remaining profile and named-mapping coverage explicitly. Built-in
   package listings are not proof that an unpackaged AppContainer profile is
   absent. Do not introduce a native helper merely to manufacture verification.
   If independent inspection is unavailable, record that residual gap.

The runtime, synthetic canaries, result files and lifecycle.lock may remain by
design. Their presence alone is not a security-cleanup failure. Historical WFP
events may also remain after rules are deleted; current resource existence and
past event retention are different questions.

Microsoft documents that profile deletion can return success for a nonexistent
profile, and open handles can impede removal of profile storage. API success
alone is not independent proof of complete removal. See
[DeleteAppContainerProfile](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-deleteappcontainerprofile).
For read-only WFP commands see
[netsh wfp](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/netsh-wfp).

## Reporting

Report each category as observed absent, retained by design, unexpected,
inaccessible or not independently checked. Do not collapse partial observations
into complete independent cleanup or whole-machine containment. No such review
has yet been performed on the VM under this proposal.

## Operator Readback

The subsequent operator-led inspection found no matching host/child processes,
no remaining route links or reparse points, and no exact package-SID grant across
886 entries (zero inspection failures). The state root showed Medium integrity.
A successful nonempty WFP export, parsed as an XML fragment because it contains
multiple top-level elements, contained none of the six exact filter GUIDs or
the sublayer GUID. The four recorded TCP/UDP ports had no endpoints.
The earlier null-variable search and single-root XML parse failure provide no
absence evidence; only the corrected successful inspection is used.

These are bounded current-state observations, not complete independent cleanup.
AppContainer profile and named-mapping removal remain product-reported only.
No deletion, policy change, recovery operation or test rerun was performed.

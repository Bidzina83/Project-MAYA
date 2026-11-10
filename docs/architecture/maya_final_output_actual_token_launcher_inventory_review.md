# Actual-Token Launcher And Inventory Review

Review only, 2026-11-10. No source wiring, package, process launch, ACL change,
or VM action. Final3 remains blocked.

## Run Under The Actual Role

`WindowsBridgeProcess.cs:StartWorkerEntry` and `WindowsIsolation.cs:Start`
launch the verified bundled Python executable with fixed entry files and
`-I -S -B`. They do not host the C# fixture inside either restricted role.
Calling the C# Windows backend from the elevated launcher would probe the
wrong token. Starting a second native executable from Python would change
the process/job boundary and is not proposed.

Use a narrow Python `ctypes` role adapter for the same v2 contract. The C#
adapter remains a reference and its v2 admission code can be reused later
under a separately reviewed production-profile compile gate. Both role-side
opens run in their actual processes, not a broker, helper, or impersonated
approximation. First build the disconnected Python role module and parity
fixtures. Preserve the exact-mask, no-follow, open-existing and once-close
rules; capture native errors immediately and preserve a successful open
when identity or close fails. Use the existing bounded private framing after
reviewing parity with `bridge/transport.py` and `BridgeChannel.cs`.

The eventual fixed root entry files should bind their roles in source and
validate the bundled version, isolated flags, expected argument count and
32-hex attempt, and role-specific working directory. Derive fixed paths from
the sealed entry/attempt layout and expected host or state directory, not from
commands, environment overrides, or an arbitrary path supplied by a role.
Avoid making access to a protected target or parent metadata a bootstrap
precondition for a negative probe. The coordinator independently binds the
provisioned paths and opened identities before and after the test.

## Candidate Inventory

| Location | New synthetic-profile-only requirement |
| --- | --- |
| Sealed runtime root | Proposed `journal_access_worker_entry.py`, `journal_access_child_entry.py`, `journal_access_role.py` |
| `host/journal-access-control` | Exactly one fixed `control.bin`, using the existing worker host ACL/label pattern |
| `state/journal-access-control` | Exactly one fixed `control.bin`, inheriting the existing scoped child state ACL/label pattern |
| Attempt directory | One `final-output-journal.v1.jsonl` with the exact reviewed Administrators/SYSTEM descriptor, outside `host` |

These names are proposed, not admitted or packaged. Use exact new root-path
allowlisting in `ProductFiles.PayloadPath`; a broad `project_maya/` rule is
not a profile exclusion. Test all three root paths rejected in older profiles.
Later assembly must specify the full member set, replacements and any
explicitly approved omissions; do not infer member totals or remove frozen
roots. No new interpreter, dependency, native child image or external tool.

Keep the legacy four-file model-host inventory and state checks unchanged in
older profiles. The access-only profile must define its own exact inventory
without repurposing model host files or adding a configurable fixture tree.
Review inherited control descriptors, labels and expected actual-token rights;
do not widen grants or manufacture successful specialized controls.

## Future Coordinator Order

Use a separate access-only profile symbol and coordinator path, requiring
the bridge launch primitives but excluding model dispatch and all existing
fixed cases. Freeze the exact compile combination and startup/status schema
before source wiring; don't infer that enabling an existing model profile
will supply the right prerequisites. Use new dedicated selectors for the
fixed worker and child entries; do not add this command to legacy workers.

Provision the usual restricted attempt, bind a fresh journal and controls,
validate their descriptors and opened IDs, and close all coordinator journal
handles before either probe resumes. Preserve existing reduced-worker and
AppContainer token checks, private pipe inheritance, jobs and cleanup. Keep
the existing isolation/WFP policy and limits; any provisioning changes require
explicit review and execution approval. No publication callback, model
startup, lease, final-output permit or worker seal protocol in this profile.

Use the retained process/pipe pair for each role, a single challenge per role,
and the exact v2 matrix and bounded reply. Require EOF and natural exit before
job cleanup. A well-formed provisional forbidden-open observation should be
retained if later EOF or exit admission fails, but cannot become verified
denial or a successful run. Missing or inconsistent evidence blocks. Reopen
the journal read-only after both roles exit, verify identity/descriptor/bytes
and perform scoped independent cleanup checks. No retry, repair or permission
widening on failure. Report per-right coverage; do not regrade M08.

## Next Approval

Recommend **disconnected Python role adapter source and inert parity tests
only**. Keep real opens injected; compile/run fixture entry points only. Check
Python v2 bytes against C# admission, both fixed roles, exact masks, error
capture, once-close, and forbidden-open preservation. Do not add runnable
root wrappers, launcher selectors, synthetic provisioning, package, or VM
execution until separately reviewed and approved. Final3 remains blocked and
all qualification flags stay unchanged.

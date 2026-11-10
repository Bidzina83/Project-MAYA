# Access-Only Launcher Profile Contract

Design review, 2026-11-10. No launcher source or payload changed. No product,
native or VM run is authorized. Final3 remains blocked.

## Exact Compile And Root Admission

Proposed profile symbol `HERMES_JOURNAL_ACCESS`. The normal candidate compile
defines exactly `HERMES_JOURNAL_ACCESS`, `HERMES_BRIDGE`,
`HERMES_CONSTRUCTION`, `HERMES_IMPORT`. The latter three are prerequisites
of the existing retained-process/private-bridge launch topology, not permission
to start Hermes or run construction checks. The profile must reject all
`HERMES_MODEL*` cases, `HERMES_STATE`, `HERMES_MEMORY`, and all
`MAYA_*_FIXTURE`/scratch-baseline symbols. Reject omission of any prerequisite.
Inert test Main may compile separately with its own fixture configuration.

Under this profile only, admit these three exact runtime-root paths:

- `journal_access_worker_entry.py`
- `journal_access_child_entry.py`
- `journal_access_role.py`

Test positive actual-profile index admission, required membership and rejection
of each path in older profiles. Require the sealed source bytes and prohibit
path aliases/case-fold duplicates under the existing index rules. Do not admit
a prefix or use the generic `project_maya/` rule for these three roots.
No payload baseline, member count or omissions approved here. A later assembly
review must pin the full inventory, interpreter/import dependencies and exact
member delta without altering frozen predecessors.

## Code Ownership

Separate `JournalAccessRuntime` coordinator; no `ModelBridgeRuntime`, legacy
`BridgeRuntime`, Hermes preparation, startup beacon, model lease, worker
seal, inference, publication callback or output permit. Access-only branch
must come before the broader bridge/import branches at setup, resume, evidence,
status and cleanup dispatch points. New worker/child selectors name only the
two fixed role roots. Reuse the verified reduced worker and final AppContainer
child launch mechanisms, private pipe allowlist, process handles, jobs, time
budgets, isolation and cleanup. Do not start any new helper or process type.

Expose only the journal candidate/descriptor/native transport and v2 matrix/
admission logic needed by this profile. Do not enable fixture symbols in its
compile: the scratch constructor, fake sink, C# role runner and C# open-call
test backend must stay excluded. Reuse the bounded verifier from the C# source;
the actual role opens run only in the fixed Python entries. The journal's
synthetic destination is metadata only, not a callback or effect. If a shared
constant needs extraction to avoid importing a fake sink, keep its value and
all existing fixture and legacy behavior unchanged.

## Inventory And Lifecycle

Use the existing fresh attempt and isolation provisioning. Define an exact
new host/state inventory independent of the old four-file host contract:
`host/journal-access-control/control.bin` and
`state/journal-access-control/control.bin`, each with its one fixed parent.
The host uses existing host ACL/label patterns; the state control inherits
the approved package/user access and low integrity from the scoped state.
No new grants, descriptor relaxations, specialized-control workaround or
extra model/config/audit files. Create `final-output-journal.v1.jsonl` as the
single extra attempt-level leaf with the exact candidate descriptor. Use the
validated attempt's opened parent/volume identity for the native transport.
Write fixed synthetic intent and pre-effect stop, verify and close. Retain
identity, exact descriptor and digest for post-test read-only validation.

Verify exact object inventory and identities before resume; never inherit
journal or control handles. Start the actual worker and child suspended with
their ordinary token checks and verified role-specific working directories.
Probe worker then child. Send each one bound v2 challenge, close its stdin,
read one reply and require EOF and natural exit before any job stop.
Reuse the reviewed v2 shape and original process/pipe/PID/attempt/challenge
bindings. If an admitted reply shows a forbidden open, stop further probes;
if later lifecycle evidence fails after a bound forbidden-open frame, retain
the observation only as provisional. Never treat a provisional row as denial.

After the role sequence, reopen the journal read-only and recheck identity,
descriptor, length and digest. Require validated before/after target and
control identities and verified role lifecycles for admitted rows. Missing
control, specialized right unsupported by its control, sharing conflict or
wrong identity remains incomplete. Preserve per-right evidence; do not use a
worker pass to fill child gaps. Stop owned jobs before revoking grants/removing
profile and filters. Preserve existing cleanup failure behavior; no recovery
path or retry. Retain the synthetic files for scoped independent checks.

## Report And Gates

Use a distinct access-only scope and version in later source review. Report
both roles' bounded rows, trusted lifecycle, immutable journal readback and
cleanup fields. Suggested final outcomes: `access_matrix_denied_pending_independent_cleanup`
only with both complete denied matrices, verified readback and successful
product cleanup; `blocked` otherwise, with distinct forbidden/incomplete/
provisional reasons. Cleanup cannot convert forbidden or incomplete to pass.
No `python_started` beacon inference, M08/model success, containment or
production qualification. Independent cleanup remains a later operator check.

Next approval: **profile source preparation, compile-only and inert integration
tests**, not assembly. Cover each missing prerequisite and invalid combination,
root admission and legacy exclusion, exact inventory, ordered role lifecycle,
wrong token/pipe/EOF/exit and stale replies, forbidden/incomplete outcomes,
journal identity change and stop-before-grant-removal. Run only fixture Mains.
Review all source deltas before separate assembly, actual index/resource/freeze
verification and one exact guest run with fresh consent. No ACL, WFP, timeout,
grant or production behavior change is approved by this design review.

# Final-Output Product Adapter Readiness Review

Review only, 2026-11-09. Final3 remains blocked. The V2 baseline and
`fake-accepted` interruption allowances are consumed. No probe, product,
package, VM, permission or scratch change was made in this review.

## What Carries Forward

| Boundary | Evidence | Product implication |
| --- | --- | --- |
| Opened identity and descriptor | V2 reported a successful check and matched reopen on the approved local NTFS scratch volume | Reuse exact semantic comparison and same-handle I/O design; do not copy the scratch ACL into product |
| Normal completion | 160 exact bytes and confirmed-as-recorded after natural helper exit | Use exact bounded readback; this was not a real output sink |
| Interrupted completion | 78 intent-only bytes after the controlled helper stop, unknown-or-invalid | Preserve uncertainty and no replay; not a power-loss or all-checkpoint claim |
| Worker seal | Inert handoff fixtures only | Bind to the original private channel and process handle and test actual worker close/EOF/exit later |
| Policy, consent and sink | Inert owner and fake effect only | Keep real disclosure disabled; live revocation ordering and consent remain separate work |

See the V2 baseline and interruption outcome records for full reported
identities and limitations. V2's descriptor validator is for a user/SYSTEM
scratch descriptor. `ProductFiles.CreateAttempt` and `BridgeHostFiles.FileAcl`
use different principals and rights. An elevated scratch success does not
show that the actual worker or child cannot open a product journal. Matching
file IDs and digests also do not authenticate arbitrary replacement evidence
if its source or opened-object provenance is not trusted.

## Recommended Source Slice

Prepare the coordinator journal adapter first, in a compile-gated fixture
path. Keep it outside the existing four-file worker host inventory. Define a
separate, coordinator-owned location beneath the validated attempt directory,
and a distinct descriptor expectation. The desired access is coordinator
read/write, no worker or child write, no handle inheritance, no sharing, and
read-only inspection under a verified identity after close. A candidate is
an Administrators/SYSTEM-only journal used by the verified elevated coordinator;
validate exact owner, group, DACL, label and parent traversal before adopting
it. Do not add rights to the worker or modify the legacy attempt or worker ACLs.
Actual access with the reduced worker and AppContainer child tokens must be
tested later; do not assume exclusion from an ACL listing alone.

Extract only the mechanics needed: pin verified ancestors or use a reviewed
parent-relative open; create exclusively; verify the exact opened object and
descriptor; keep one non-inherited handle through bounded append, flush and
readback. No descriptor-string equality, path recheck as a substitute for
opened-object proof, or reopen-to-append. Poison on any ambiguous I/O; there is
no recovery writer. Bind immutable intent and terminal records to the reviewed
versioned fields and an independently admitted attempt. Recovery inspection is
read-only and returns evidence classification, never a permit or callback.
The candidate source remains disconnected from the launcher and real sink.

In the next source slice, reuse the verified worker-launch and natural-exit
primitives rather than constructing a new process lookup. A future seal must
come from the original worker pipe after flush/hash/close of the provisioned
writer. Require exact correlated reply, EOF without extras, and natural zero
exit before job cleanup. Read the sealed four-record prefix under opened-object
identity and match the trusted request, response, delivery and child evidence.
This work is separate from the first journal adapter: no new live worker
command is needed to exercise the handle contract. Legacy M08 stays unchanged.

## Evidence Required Before Packaging

- Compile-only and injected I/O tests for actual adapter boundaries, including
  substitution, ancestor identity, reparse/hard-link, malformed descriptor,
  short transfer, flush and reopen mismatch; legacy build exclusion.
- Separately approved native probes for the chosen product descriptor under
  actual tokens, unauthorized open/rename/substitution negatives, and journal
  identity on reopen. Keep scratch and product evidence distinct.
- Separately approved synthetic worker/seal validation with actual bound pipe,
  original process handle, close/EOF/exit and strict prefix; require negative
  tests for stale/replayed seal, forced exit and extra frames.
- A later fake-sink-only integration contract for revocation, consent and
  uncertainty. No real sink, inference, policy widening, timing change, or
  historical M08 regrading. More crash checkpoints or power-loss testing need
  explicit scope and are not implied by the successful one-stop probe.

Recommended next approval: **coordinator journal adapter source preparation,
compile-only and inert tests**, with a frozen descriptor and I/O contract first.
No worker integration, runnable profile, product package, native execution or
permission change under that approval. Gate A and qualification flags remain
unchanged.

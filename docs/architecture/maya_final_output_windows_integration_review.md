# Final-Output Windows Integration Review

Review only, 2026-11-09. The inert Python reference is not a Windows adapter.
This review does not approve source changes, assembly, publication, or a VM run.
Final3 remains blocked under its original M08 contract.

## Existing Boundaries

- `ModelBridgeRuntime.cs` validates the response, writes it on the bound child
  channel, checks the child's receipt for exact attempt, digest and length, then
  sends a fresh coordinator command to the worker and checks its correlated ack.
  The child receipt is untrusted testimony; the coordinator's write and the
  worker's correlated record are the trusted observations. None is consent.
- `model_service.py:confirm_runtime_delivery` records a prior effect, even if the
  original lease expired afterward. It checks the response and command ID and
  appends the delivery record before entering `runtime_delivered`.
  `model_worker.py` replies only after confirmation returns. `RequiredAudit`
  requires full write, flush and fsync; errors poison that audit instance.
- `ModelHostFiles.cs` provisions four exact private host files, rechecks their
  descriptors and reads with `FileShare.None`. Existing audit readback is after
  worker completion, not a live pre-publication admission gate. Its inventory
  and ownership cannot silently absorb another journal or concurrent reader.
- `ProtectedPython.cs:Execute` holds the exclusive lifecycle lock. Fresh runs use
  a new attempt ID; pending cleanup blocks new runs, and bridge recovery is
  rejected. These are useful admission controls, not an output replay registry.
  The current `Action<string,int>` publication callback has no protocol for
  atomic acceptance, epoch checks, or distinguishing lost acknowledgement.

## Recommended Integration Shape

Keep original dispatch and runtime controls unchanged. Use a new explicit
synthetic-only profile with strict version routing. A Windows coordinator owner
implements the reviewed state transitions; do not route a real publisher through
the Python `FakeSink` or promote the existing generic callback into authority.
The only sink in the first integration is a synchronous in-memory fake effect.

The coordinator derives the immutable receipt from its own validated request and
response, exact write/child receipt, matched worker command and acknowledgement,
attempt, actor and verified process/channel bindings. It also checks the positive
child final frame against the trusted fixture and all existing postconditions.
No raw child frame, echoed digest, boolean or caller-constructed Python `Receipt`
is an independent proof. Admit once; a mismatch or duplicate cannot grant output.

Before evaluating output policy, require a versioned, evidence-only worker finish
command after delivery. It closes the worker's audit handle and produces no
operator output or new authority. Require natural worker completion and verify
the strict delivery prefix from the bounded protected file. Do not add this
command to legacy routes. If the worker cannot seal, exits abnormally, or the
prefix cannot be read and correlated, reject before issuing any permit. Preserve
truthful earlier effect observations even if full admission fails.

Use a separate coordinator-owned release journal, not a second writer in the
worker log. Design its versioned layout explicitly and keep the legacy four-file
inventory unchanged. Create exclusively under the attempt's protected storage;
verify the opened handle's object, ACL, label and non-reparse identity before use.
Hold ownership through append and readback; do not substitute a path-only recheck
or add a write-open by the worker or child. Specify maximum file/record sizes,
exact field sets and allowed event order before implementing the reader.

The local coordinator owns policy and consent revisions, cancellation, monotonic
time and sink acceptance. Require separate explicit disclosure consent for exact
bytes and destination; launch consent is not enough. The permit binds the prior
receipt, actor, attempt, output hash and length, exact destination, consent ID,
epochs, deadline and one-use identity. It never leaves the owner. Consume once,
durably append intent, then recheck time and authority at synchronous fake-sink
acceptance. No queued acceptance or remote policy freshness assumption. Policy
or revocation changes ordered before acceptance win; an already accepted effect
cannot be recalled. Durability on Windows is a later validation claim, not a
property demonstrated by a mocked flush or by the existing worker fsync alone.

## Failure And Restart Contract

Pre-effect failure is terminal with zero fake publications. A durable intent
alone never authorizes publishing or proves it happened. After invocation, no
positive auditable confirmation means delivery unknown, with no replay. When
intent exists without a valid terminal record after a crash, read it only as
unknown evidence; a missing record is not permission. Malformed or truncated
journals must never be used to reconstruct authority. A positively recorded
pre-effect stop is distinct from unknown; never infer it from a partial log.

Use fresh attempt and channel identities at every admission, under the lifecycle
lock and exclusive attempt creation. Keep permits and pending candidates only in
memory. A restarted owner may inspect prior evidence read-only, but cannot admit
its receipts, reload permits, or continue its pending outputs. No new recovery
or cleanup path is proposed. A collision or unresolved prior cleanup blocks.
Test stale messages against a fresh owner, not just release with an empty owner.

## Source Gate And Acceptance

Recommended next approval: source preparation and inert tests for a distinct
Windows coordinator adapter and exact versioned evidence contracts. Freeze
command/reply/journal schemas before integration. No profile enablement in a
runnable package, real consent UI, real sink, or native execution in that step.
Keep production limits unset; use explicit fake-clock and capacity parameters.

Require inert negative tests for cross-attempt/channel receipt or ack, duplicate
delivery, bad child final, missing worker seal, wrong audit identity or ordering,
flush/readback failure, expiry on both boundaries, consent or policy change before
acceptance, duplicate consume, wrong bytes/destination, torn intent/confirmation,
lost acknowledgement, restart and stale receipt replay. Include one fake success
and verify exact intent/confirmation binding and one effect. Assert the legacy
dispatch guard rejects replay even when separate output would be eligible.
Retain legacy profile and audit regression coverage; no historical M08 regrading.

Open before packaging: Windows handle and persistence semantics, exact evidence
schemas, measured bounds, and consent ownership. Any assembly and native run
require separate approvals after source review. No implementation or execution
occurred in this integration review; qualification flags remain unchanged.

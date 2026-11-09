# Coordinator Journal Native Transport And Token Review

Review only, 2026-11-09. No implementation, native or VM run, ACL change,
profile enablement, or package. Final3 remains blocked.

## What The Current Tokens Establish

`WindowsBridgeProcess.cs:StartWorkerEntry` checks the actual process token after
launch. `WindowsIsolation.cs:CreateReducedLaunchToken` constructs a distinct
reduced token. `VerifyReducedLaunchToken` requires the expected operator SID
and session, Medium integrity, non-elevated primary token, Administrators
deny-only (not enabled), and at most the checked traverse privilege. The child
launch applies its AppContainer attributes and verifies the resulting process
token with `TokenCheck`. The reduced launch token alone is not the child's final
token. Keep these checks and the private handle list unchanged.

The candidate journal gives access only to Administrators and SYSTEM. We expect
neither restricted process to gain access; this is a source inference, not an
observed file access result. The existing attempt directory grants the operator
read/execute; the legacy worker host files explicitly grant that user access.
Neither descriptor can be copied to the journal. Medium no-write-up is not the
reason a Medium worker should be denied: the DACL is essential. This design
does not protect against the elevated coordinator, SYSTEM, administrators, or
another principal that can control those processes.

## Native Transport Source Boundary

Implement a compile-gated `ICoordinatorJournalHandle` transport candidate only.
The trusted caller supplies the validated attempt and expected parent/volume
identity. Keep the fixed leaf outside `host`, no arbitrary path input. Pin and
verify the required ancestor chain without delete sharing, or use a separately
reviewed parent-relative open. Fail on unsupported volume, ancestor substitution,
unexpected reparse or unverified parent identity. Do not infer parent identity
from a leaf no-follow flag or a string comparison alone.

Create a new journal with the exact candidate descriptor, read/write plus
required metadata-query rights, share zero, no inheritance and no fallback.
Validate opened identity, attributes, link count and scoped descriptor on that
handle before returning the observation. Share mode and create-new provenance
are facts from the owned open call, not flags learned from untrusted data.
Read/write/flush/readback must all use that retained handle and pinned parents.
Use bounded positional reads and exact byte counts; a short transfer, failed
flush, or changed identity poisons the candidate. Dispose in reverse ownership
order on failure, and do not reopen, truncate, delete or retry evidence.

Make native calls injectable for source tests. Tests must assert exact open flags,
rights, creation descriptor, no inheritance, ownership and cleanup, ordered
I/O, bounds, and fail-closed mapping of failed calls. Do not assert that injected
observations prove Windows behavior. No real backend invocation in that source
step. A read-only native restart reader is a separate follow-up; the current
candidate neither restores permissions nor handles old attempts for writing.

## Token-Access Validation Plan

First establish separately approved native positive create/flush/readback using
the exact candidate descriptor and an approved synthetic object. The earlier
scratch probe used a different descriptor and cannot fill this gate.

For a later isolated synthetic token test, use the actual launched worker and
actual AppContainer child, each tied to its retained process and private channel,
with original token checks. Have each process attempt fixed `OPEN_EXISTING`
rights probes in its own final token context. Do not substitute the operator's
token, merely impersonate a lookalike token, or pass a coordinator-opened handle.
No inference, output publication, worker seal command or token mutation is
needed for this access test. A separate profile/command contract and approval
must precede implementation or execution of these probes.

1. Verify and close the coordinator's exclusive journal handle before the ACL
   negatives. Use a dedicated synthetic journal that is not participating in a
   release. Record its opened volume/file ID and descriptor before closing it.
   Otherwise a share violation could mask an ACL that would allow access.
2. For each process, verify a same-token positive control on a fixed,
   non-sensitive object provisioned through its existing access pattern.
   Check the requested rights separately: read, data write, append, delete,
   change DACL and change owner. For parent replacement risk, probe the relevant
   parent delete-child/create rights separately; leaf denial alone is not proof.
   Access checks are open/close only, never write, delete, rename or relabel.
3. Require the journal negative to return access denied, not file-not-found,
   sharing violation, unsupported rights mapping, bad target, timeout or a
   failed positive control. A successful forbidden open fails the case even
   if the process immediately closes it. No interpreting an inconclusive result
   as denial. For specialized rights where no safe positive control can be
   supplied without widening permissions, report that check as incomplete.
4. Check the coordinator can reopen read-only, verify the same identity,
   descriptor and bytes, and prove neither process inherited a journal handle.
   Preserve output and independent cleanup evidence. Controlled negative rename,
   hard-link and reparse tests, if needed, use disposable objects only and need
   explicit approval; a metadata-only open test is not proof of those outcomes.

Retain token, build, volume, requested-access mask, error and object-identity
evidence without dumping secrets or journal content. Live access tests on one
build/volume are not production containment or a same-principal attack claim.

## Next Approval

Recommend **compile-gated native transport source and injected tests only**.
No live handle access, new process launch, actual token probes, security setting
change, worker integration, package or VM run under that approval. Review the
exact source and new artifact identities before any separately approved native
test. Keep Final3, frozen artifacts and qualification flags unchanged.

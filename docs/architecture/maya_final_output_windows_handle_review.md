# Windows Worker, Journal, And Crash Review

Read-only product review, 2026-11-09. No native execution, package, profile
enablement or source implementation. Final3 stays blocked; Gate A stays open.

## Worker Identity And Seal

`WindowsBridgeProcess.cs:StartWorkerEntry` launches the fixed bundled executable
and entry point under a verified reduced token, one-process job, and explicit
three-handle inheritance list. `ModelBridgeRuntime.cs:PrepareWorker` reads the
private stdout pipe and checks the ready PID against the launched worker.
`Reply` validates exact message shape, attempt and command correlation.
`WaitBridge` waits on the original process handle and requires exit zero and
clean stderr capture. These are useful primitives. A matching PID in JSON or
an exit after forced job stop is not evidence of a naturally sealed worker.

For a future separate synthetic profile, bind the coordinator's seal verifier
to the same launched worker instance, original handles, token check, fixed
payload entry, and fresh attempt/channel identity. Use a new exact finish
command after the bound runtime ack; no child-originated finish or seal. Keep
existing time budgets: a failure to finish within them is a blocked result.
Require the correlated seal reply, EOF with no surplus frame, and verified
natural exit before job cleanup. Never replace the retained process handle with
a PID lookup, or infer success from cleanup. Treat malformed, missing, replayed,
wrong-channel or wrong-process evidence as no authority.

Generate the seal digest from the worker's existing audit handle after the final
required flush, with no subsequent write. Close the writer successfully before
sending the seal reply. The coordinator then reads the worker audit once using a
verified handle, compares provisioned file identity and the sealed digest, and
checks the exact four-record delivery prefix. Confirm worker-side identity on
the handle used for writing; a path reopened only to obtain the seal is not the
same proof. This requires a new command/close ordering; today `model_worker.py`
keeps the audit stream inside the serving scope, and ordinary M08 never performs
this proposed evidence-only finish. Keep original delivery/dispatch validation,
positive child postconditions, and earlier effects unchanged.

## Protected Handles

`bridge/host_files.py:open_private` already checks the opened worker-side object
for final path, size, reparse/directory attributes and a single hard link. It
explicitly depends on coordinator verification of ancestors and ACLs.
`BridgeHostFiles.cs:Write` closes the created stream before labeling and checking
by path; `ModelHostFiles.cs:ReadBounded` likewise performs a path reparse check
then opens the file. Neither sequence alone supplies the proposed continuous
handle ownership and opened-object validation. Existing host ACLs grant the
operator, Administrators and SYSTEM full control. This review does not claim
protection against those principals or a compromised coordinator.

Use a distinct coordinator-owned journal in a fixed, protected attempt location
outside the legacy worker four-file inventory. Validate the ancestor chain and
prevent replacement across the open, or use a reviewed parent-handle-relative
open. Do not treat a leaf no-follow flag as proof of ancestor identity. Require
exclusive create, no inheritance, no sharing for read/write/delete, and an
expected protected descriptor at creation. Verify the opened object's volume
and file ID, regular file attributes, no reparse tag, single link, owner/group,
DACL and integrity label; fail closed on unsupported file system or unavailable
metadata. Keep the same handle for append, flush and readback; never replace it
with a path lookup. Do not pass it to the worker or child. Define the allowed
local volume and exact rights/label in the next source contract rather than
adding privileges to make a failing check pass.

Primary API references: [CreateFileW sharing and flags](https://learn.microsoft.com/windows/win32/api/fileapi/nf-fileapi-createfilew),
[opened-object attributes](https://learn.microsoft.com/windows/win32/api/winbase/nf-winbase-getfileinformationbyhandleex),
[handle-based security descriptor](https://learn.microsoft.com/windows/win32/api/aclapi/nf-aclapi-getsecurityinfo).
These APIs are candidates for implementation, not evidence that the current
code has verified journal ownership on Windows.

## Persistence And Restart Classification

Use bounded exact writes, flush to storage, and read back the same handle before
permitting the fake acceptance. Existing `FileStream.Flush(true)` and worker
`fsync` calls are useful precedents, not a crash-recovery test. Windows exposes
[FlushFileBuffers](https://learn.microsoft.com/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)
for flushing buffered data; successful readback is not proof of power-loss
survival or atomicity with an external publication. Keep process-crash and
power-loss claims separate. The first validation should be process interruption
on the supported local volume with a fake sink, not real operator disclosure.

| Evidence after interruption | Read-only classification | Authority |
| --- | --- | --- |
| No intent, missing journal, or uncertain completeness | No confirmed delivery; absence alone proves nothing | None |
| Valid intent and matching complete pre-effect stop | No publication recorded by the trusted owner | None |
| Valid intent and matching complete confirmation | Confirmed as recorded, subject to journal provenance | None |
| Intent only, torn record, bad binding, unreadable or substituted file | Unknown or invalid evidence; never infer clean denial | None |

Restart never reopens an old attempt for writing, restores a permit, resumes a
worker, or retries an unknown disclosure. Use a fresh attempt/channel under the
existing lifecycle admission rules. Preserve the current pending-cleanup block
and do not add a recovery exception. An old journal may be inspected read-only
only after revalidating its opened identity and provenance. No missing, stale or
ambiguous evidence grants permission, even when the prior effect did not occur.

## Next Approval

Recommend a staged source-only step: first freeze exact finish/seal/EOF/exit and
opened-handle contracts, then build inert adapters with injected native-call
results. Cover handle substitution and ancestor rename, reparse/hard-link and
ACL/label mismatch, share violation, wrong worker/pipe and forced exit, stale
reply, short write, flush failure, torn and extra records, and faults at every
edge between intent, effect and confirmation. Preserve legacy regressions and
explicitly test that the proposed profile and command cannot run in a normal
build. Windows behavior itself must be validated later under separate approval;
do not count an injected result as native evidence. No lease, deadline, policy,
security settings, production limits, or qualification changes are approved.

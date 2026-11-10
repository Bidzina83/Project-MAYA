# Coordinator Journal Native Baseline Plan

Design review, 2026-11-10. No implementation, compilation, run, product root
access, or VM/ACL change is authorized by this review. Final3 remains blocked.

## Decision

Test the actual `CoordinatorJournalCandidate` and `CoordinatorJournalWindowsCalls`
with the exact Administrators/SYSTEM descriptor on a fresh synthetic object.
The earlier V2 probe used a different descriptor and its own I/O code. It
cannot substitute for this baseline. Do not launch MAYA, Python, a helper,
or a worker. Do not stop any process or invoke a publisher.

## Isolate The Target

Both the candidate and native transport currently derive their leaf from
`ProductFiles.Root`. A harness must not call those constructors unchanged
against that root or use a junction to redirect them. Approve a narrowly
gated scratch-only entry to the same implementations, with shared internal
logic and unchanged normal constructors. A second compile symbol dedicated
to this baseline must exclude the scratch entry from ordinary and injected
fixture builds. No environment override or general path parameter reaches
the normal product entry. Test both compile exclusions before sealing.

Use an explicitly approved, existing dedicated local NTFS scratch root, not
the product root or its descendants. Retain and verify the root and ancestors
by opened handles, rejecting reparse or identity mismatches. Exclusively
create one fresh GUID attempt directory beneath it; never reuse the V1/V2
folders. Use the fixed journal leaf and exact candidate descriptor
`O:BAG:BAD:P(A;;FA;;;BA)(A;;FA;;;SY)S:(ML;;NW;;;ME)` without fallback. Provision
and verify a protected scratch parent for this test without modifying any
existing folder's ACL or label. Verify the new parent's opened volume/file
identity and pass it to the transport. Do not accept a caller-supplied leaf.

## Single Positive Case

1. Require an already-elevated test operator with the expected SID and an
   enabled Administrators group. Record the observed build, volume and token
   facts, including elevation and integrity. No self-elevation, privilege
   adjustment or token substitution. This is a coordinator-equivalent test
   context, not a live MAYA coordinator process.
2. Construct the journal candidate with deterministic synthetic bindings for
   the new attempt. Use the real Windows transport for exclusive create,
   descriptor checks, exact append, flush and complete same-handle readback.
   Write intent followed by `pre_effect_stop`; no fake or real effect is
   required to validate I/O. Check the exact two records and order against
   an independently constructed expected fixture. No output text or secrets.
3. Close the writer normally. Open separately, read-only, under the retained
   parent identity. Reverify the same volume/file ID, descriptor, size and
   exact bytes. This is a separate read handle in the harness, not a restart
   or a recovery writer. Preserve the attempt directory on both pass and
   block; do not delete or repair evidence.

Pass only after every check succeeds. Report the build, token summary, attempt
path, journal identity, byte count, digest and bounded result. Any create,
descriptor, handle, flush, close or reopen failure blocks; report its stage
and numeric native error where available. No retry, rights relaxation or
alternate target. A pass establishes behavior only for that token, volume,
descriptor, transport and normal-close case. It does not establish worker or
child exclusion, crash or power-loss durability, live seal, or qualification.

## Approval Gates

Next: **standalone harness source preparation, compile-only and injected
checks**. No call to the Windows backend in that step. Verify the normal
constructors still reject scratch paths, product roots cannot be targeted by
the harness, ordinary builds exclude the harness entry, and injected failures
block without writes beyond the scratch fixture. Review and hash the exact
standalone binary. Only then request one explicit baseline approval for the
verified guest executable, target machine and exact existing scratch root.
No token-negative, interruption, worker integration or product package is
included. Preserve frozen artifacts and qualification flags.

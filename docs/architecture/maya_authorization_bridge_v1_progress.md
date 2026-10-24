# Authorization Bridge V1 Implementation Progress

## Approved Continuation

The user approved the ten-case correction. Its active successor is
maya_authorization_bridge_v1_tests_10.json; the original contract remains intact.
Windows token/job/handle launch, protected host files, bounded coordinator channels,
trusted worker, real Hermes extension and fixed native entry are now implemented
as a preparation candidate. See maya_authorization_bridge_v1_handoff.md.
This supersedes the earlier pause/pending-source statements below, not their
history or any native qualification. Native execution remains separately gated.

## Scope And Current State

2026-10-23: the user approved proceeding with bridge implementation/package
preparation after the design and disclosed process/ACL/framing impacts. Native
execution, workstation security provisioning and VM runs remain separately gated.

Implemented product source, not another test supervisor:
- bridge/protocol.py: strict UTF-8 JSON, duplicate/nonfinite/depth rejection,
  four-byte framing, incremental reads, terminal invalid/partial frames, 8192-byte
  frame and 128-KiB channel limits, one-second incomplete-frame checks.
- bridge/audit.py: existing AuditRecord serialization over an already verified
  private host handle; bounded append, short-write checks, flush and fsync;
  permanently poisoned on any failure. Existing LocalJsonlAuditSink is unchanged.
- bridge/service.py: actual existing authorization gateway, trusted bound identity,
  random single-use leases, channel/sequence checks, read/disclosure authorization,
  mandatory intent audit, bounded content, revocation and serialized release
  commitment. Partial sends are uncertain and never retried. Failed reads record
  an attempted read, not a fabricated zero-effect result.

The internal reader/writer callables are dependency-injected trusted host adapters,
never runtime-provided callbacks or generic RPC actions. Windows verified file
opening, process/token/channel ownership and hard deadlines are NOT implemented
by these core APIs. They must not be used as standalone proof of isolation.

Thirty inert core tests passed: fragmented/multiple frames, malformed JSON and
lengths, truncated EOF, trickle timeouts, depth/size/channel caps, real audit record
serialization with mocked write/flush/fsync faults, exact existing-policy permits,
non-ALLOW/constraint rejection, identity/target/action/sequence/channel denial,
expiry/cancellation/replay, pre-read/release audit faults, disclosure denial,
uncertain sends, oversized content and sanitized errors. Tests use synthetic
bytes, existing gateway code and I/O doubles, not Hermes/SDK/native security.
This is not all twelve L-family coverage or any N-case native qualification.

The six existing audit regression cases also passed after an explicitly approved
out-of-sandbox rerun resolved sandbox Temp permissions. The new thirty core
cases passed in the sandbox. Coupled-context and whitespace validation passed.
No original authorization/audit module or frozen runtime package was changed.

Final preparation adds 37 core and 12 worker/client/handle/transport cases,
with 83 previous Windows Python cases and six existing audit cases: 138 passing
Python checks. Windows fixture builds exercise 711 previous cases and 134 new
codec/descriptor/audit cases: 845 passing inert C# checks. The new native slice
requires exact 21-event persisted-audit readback after process closure; this
is not substituted by a child Boolean or worker preparation counter. Native
fault, process, timing and containment qualification remain open until VM evidence.

## Discovered Test-Contract Conflict

The frozen proposed native schedule uses one audit file and worker but orders
N09 (audit failure before read), then N10, N11 (second audit failure) and N12.
RequiredAudit correctly becomes unusable after an audit write/flush/fsync fault;
DocumentBridge refuses a later lease on that failed required audit. Therefore
the original schedule cannot complete all twelve cases as specified without
reopening/replacing a failed ledger or weakening fail-closed behavior. Neither
automatic recovery nor a per-case ledger replacement was designed/approved.
This is a design error found during implementation, not a Windows/Python failure.

Do not silently clear audit.failed, reopen the sink, convert uncertain writes
into success, replace audit with a no-op, skip cases or claim the existing
12-case contract passed. The original design/JSON remain unchanged as evidence.

## Recommended Narrow Correction For Review

For the first native bridge package use ten native cases, preserving IDs/order:
N01,N02,N03,N04,N05,N06,N07,N08,N10,N12. Keep N09/N11 as mandatory local real-code
fault tests in this package, explicitly not native audit-fault qualification.
Expected native totals become two completed document reads and one release.
No extra process, sink recovery, permission, timeout, dependency or VM run budget
is introduced. Future native audit-fault tests would terminate their attempt and
need separate scope/approval. This reduces first-run coverage; it must be an
explicit reviewed contract revision, not a quiet omission or Gate A shortcut.

Alternative: retain twelve native cases but specify separate audit lifetimes and
their protected creation, audit aggregation, evidence and worker restart/recovery
semantics. That is a larger design and is not recommended for the first package.

Pause before Windows integration/package assembly for this correction decision.
No runnable bridge EXE/package, worker entry, Hermes extension or verified native
transport is delivered yet. Existing startup/memory packages remain untouched.
Pending work includes host import/dependency closure, protected file handle/DACL
setup, separate worker token/job, pipe ownership/read/write deadlines, real Hermes
registration/closure, complete L-family coverage, revised schedule, evidence
admission, offline package/freeze and separately approved VM execution/cleanup.
Production, containment, independent cleanup and Gate A remain unqualified.

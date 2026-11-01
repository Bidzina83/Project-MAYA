# Channel Scheduling Inert Result

2026-11-01. User approved LOCAL inert-only reproduction after the Budget2 startup
review. No product-source edit, product Main/setup, bundled runtime/Hermes/SDK,
VM/security configuration, dependency/deadline change or new product package.
Budget2's actual guest root cause remains unproven. Its M05a child was not resumed.

## Reproduction

Compiled tests/windows_channel_scheduling_fixtures.cs with explicit fixture Main
ChannelSchedulingFixtures and the30 frozen C# sources from Budget2, not current
editable product source. Every compiled frozen source hash matches the manifest
in the independently pinned Budget2 ZIP. BridgeChannel.cs SHA256:
cbf5359ef6d6bba1dff2758738b5ae377f0e929acd1a481a58d345074f4df661.
Product Main was not selected, no product assembly was loaded and no native
process/handle-based channel constructor was used. All framing streams are local
in-memory fixtures. Existing ready5000/partial1000-ms limits remain unchanged.

38 assertions passed across9 cases:

| Case | Local observed result |
| --- | --- |
| Complete frame, default scheduler |79 bytes prebuffered, accepted,32ms; no remainder/error |
| Complete frame, delayed nested reader |79 bytes prebuffered; only first byte read;78 bytes still present; tail reads0; nested reader not started; bridge_incomplete_frame_timeout at1008ms |
| Actually delayed header |Only1 byte available, reader waiting for missing bytes; same category at1003ms |
| Actually delayed payload |Only5 bytes available, reader waiting for missing bytes; same category at1010ms |
| No first byte |No bytes available; bridge_channel_timeout at5000ms |
| Early EOF |eof |
| Invalid zero length |bridge_frame_size |
| Invalid JSON |bridge_json_invalid |
| Oversize8193 length |bridge_frame_size |

Elapsed values describe this ONE local experiment, not native timing guarantees
or a new performance threshold. Synthetic frame type fixture_ready tests generic
framing, not actual model-worker readiness/admission.

The private scheduler has two dedicated fixture workers. Caller occupies one,
outer channel reader the other. The third queued task is the nested reader; the
fixture also explicitly gates it until the caller records failure. This deliberate
delay makes the counterexample deterministic even after the outer task finishes.
It does NOT show that the VM used a custom scheduler, had two available ThreadPool
workers, or suffered actual ThreadPool starvation. No ThreadPool/global OS/VM
configuration was changed.

Late-data and delayed-reader gates were released for teardown. Failed channels
reject subsequent read/write/EOF calls instead of recovering. Pending reads were
joined through original channel Dispose; private scheduler tasks and both worker
threads were explicitly drained/joined. No fixture reader was abandoned. The
late complete frame is NOT counted as a recovered/accepted operation.

## Established And Unestablished

Established: the unchanged code can emit bridge_incomplete_frame_timeout with
a COMPLETE prebuffered frame when its nested reader is not scheduled. Actual
missing header/payload bytes produce that SAME category. The category alone
cannot distinguish receiver scheduling delay from incomplete producer data.
The extra queued hop introduces avoidable scheduling dependence.

Not established: actual cause of Budget2's VM failure, normal-scheduler starvation
on that VM, whether its stdout byte belonged to a valid readiness frame, or
whether a scheduling correction alone would let M05a pass. Conservative timeout
rejection is fail-closed, not evidence of unauthorized output or weakened security.
The experiment does not justify extending deadlines or accepting late frames.

## Artifacts And Next Gate

Local build .codex-build/maya-channel-scheduling-inert-20261101-1 contains
check.ps1,ChannelScheduling-InertChecks.exe,results.json,source-binding.json and
independent verify.py. The verifier binds fixture source/EXE/result hashes to the
30 frozen sources and known Budget2 ZIP/EXE pins; current product source hashes
are also compared to the frozen manifest. No prior source-freeze copy was changed.

Recommended next approval: SOURCE-ONLY correction/review of receiver scheduling
and bounded read-progress diagnostics. Remove implicit nested task-scheduler
coupling, preserve ready/RPC/partial/byte budgets and terminal failure, retain
tracking/joining of all pending readers after job stop, and report bounded
reader-start/header/payload/parse progress without raw message data. Verify the
complete-frame scheduling case AND true partial/error/cleanup controls plus
all shared-channel consumer regressions before source acceptance.

That source work is NOT authorized by this experiment's approval. No product
fix/package/native retry follows automatically. A correction would remove the
demonstrated scheduling dependence, not prove or promise a native root-cause fix.
Preserve all frozen artifacts, M05a/M05b case boundaries, grant/authorization/audit
semantics, false qualification flags and open Gate A. Native execution and any
successor assembly remain separately gated.

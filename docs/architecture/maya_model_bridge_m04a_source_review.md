# M04a Expiry Source Review

2026-10-31: user approved M04a-only source preparation after maya_model_bridge_m04_review.md.
Candidate 0.2.1-offline-expiry.1, scope offline-hermes-lease-expiry-v1. No package,
native product/Hermes/SDK execution, actual native clock wait, VM/security setup,
network, credentials or inference. Existing frozen Body 1 ZIP/EXE hashes verified
unchanged. M04b revocation and M04c replay remain unimplemented and unapproved.
The companion source contract is maya_model_bridge_m04a_tests.json.

## Native Schedule

HERMES_MODEL_EXPIRY requires HERMES_MODEL_VALIDATION and excludes BODY/ROUTE/
ATTEMPT (and existing MODEL_DENY/STATE/MEMORY guards). MODEL/BRIDGE/CONSTRUCTION/
IMPORT remain required. Fixed model_expiry_child_entry.py and
model_expiry_worker_entry.py select only M04a; future package cases=[M04a].
No child/environment/CLI-selected delay, fake clock, revocation or replay command.
Both exact positive M01 rules stay present in the existing real gateway.

After genuine child constructor/readiness, coordinator requests one ordinary
2000-ms grant and verifies its complete identity/route/sequence/TTL/body hash/lease
shape. No grant fields are changed. After the complete reply and validation,
ModelExpiryAdmission.WaitBeforeBegin starts a REAL Stopwatch and waits >=2100 ms
before sending model_begin. This start is later than receipt, so its duration is
a conservative lower bound on time since receipt, not a cross-process timestamp.
No worker RPC or partial frame is in flight during the wait. Child is waiting
for model_begin, not inside a model exchange. A separately testable WaitCore uses
bounded <=25-ms sleeps; native entry always supplies Stopwatch/Thread.Sleep.

Every step reserves >2000 ms within the smaller of original remaining host time
and a conservative 22000-ms-from-child-resume budget; no timer is restarted or
extended. Backward/invalid/oversized/stalled timing, oversleep or exhausted budget
throws a blocking failure before model_begin. Stalled-loop ceiling 512. These
checks do not guarantee Windows scheduling or qualify native timing. Native
child's own 22-second cooperation/30-second host deadlines remain unchanged.

Then normal model_begin sends the ORIGINAL grant/canary. Pinned Hermes/SDK emits
its original valid request with all guards enabled. Coordinator verifies exact
body and full envelope against original host grant/oracle. No mutation. The
ordinary next 2000-ms worker RPC dispatches that unchanged request. No fallback,
retry, grant reissue, TTL edit or VM testing wrapper.

## Actual Guard And Unused-Grant Predicate

New ExpiredGrantBridge subclasses OfflineModelBridge; the ORIGINAL base service
and _live accepted set are unchanged. issue() delegates once under the existing
lock, retaining issued lease/expiry and deriving issue time as expiry minus the
existing two-second TTL. No state replacement, live patch or expiry assignment.

Under the lock, exact read-only request preflight independently reconstructs
every v/type/attempt/route/lease/seq/method/path/body field and channel from host
state, verifies integer types and one bound actual coordinator command ID. Uses
the existing structured route_request helper and original body parser. This is
NOT completed admission: request_validated remains false; the original guard
still runs before its normal envelope/body admission steps.

The subclass MUST call super()._live("issued") and observe its exact ModelDenied
with uncertain=false. If it returns, the fixed negative profile blocks before
any gateway/effect; only a separate normal-service fixture is the fresh positive
control. Other exception types/uncertain failures are not expiry. Coherent
observations after rejection require phase issued, open, unrevoked, healthy audit,
original captured lease/expiry unchanged, preflight verified, actual finite
monotonic now >= actual expiry, zero gateway calls/denials/dispatch attempts/
dispatches/prepared or confirmed releases. No reason inferred from error text.
Retimed/replaced grant, unissued/closed/revoked/wrong phase, malformed request,
wrong channel, missing binding, generic failure or early request cannot pass.

Elapsed floor((observed_now-issued_at)*1000) must be canonical decimal string
2000..30000. The event verifies the clock did not move behind the observation.
It audits this expired DIAGNOSTIC without authorizing an operation after expiry;
M03's pre-expiry event predicates were not relaxed or reused. Service closes
normally after the denial, and RequiredAudit short/write/flush/fsync failure
poisons acceptance; no reopen or continuation. Evidence requires closed service,
healthy audit, the recorded exact expiry and zero-effect boundary.

## Exact Protocol And Audit

Worker mode expire_grant is exclusive with all older negative modes. The normal
issue/dispatch command IDs remain fresh and outer attempt binding unchanged.
On accepted expiry it sends exactly v=1,type=model_lease_expired, actual attempt,
actual coordinator request_id,evidence; then returns naturally and closes.
No model response or second command. Child receives only v=1,type=model_denied,
actual attempt,seq=1,case=M04a,reason=lease_expired. ExpiredGrantChannelClient
accepts only that exact case/reason; it raises instead of returning model content.

Explicitly untrusted report maya.offline.model.expiry.child.v1 requires
constructor/completed/denial/SDK closure/config/origins/distributions true,
native_conversation/real_inference false, one request, 2-8 clients and empty
reason_type. Only the expected SDK error after exact control, or Hermes' own
returned error result, counts as native negative handling; arbitrary failure does not.

One newline-terminated existing AuditRecord envelope, integer schema_version=1,
valid UTC timestamp, event_type=model_bridge.lease_expired, decision=deny,
reason_code=model_bridge.lease_expired, actual windows:<operator SID>,
capability=model.egress,target=model:maya-offline-fixture,operation=infer,
data_classification=internal-synthetic,idempotency_key=null. Exact metadata:

- validation_schema=maya.model.lease_expiry.v1,case=M04a,stage=lease_expired.
- Actual attempt,request_id,coordinator_request_id; route=maya.offline.model.v1,
  endpoint=https://maya-offline-model.invalid/v1/chat/completions,
  model=maya-offline-wire-v1,destination=provider.
- request_sha256/request_bytes and observed_request_sha256/observed_request_bytes
  equal original host body; lease_sha256 hashes actual issued lease, not raw token.
- grant_ttl_ms="2000",worker_elapsed_ms as above,phase_before="issued",
  closed_before="false",revoked_before="false",expiry_observed="true",
  request_preflight_verified="true",request_validated="false".
- gateway_calls="0",dispatch_attempted="false",response_sha256="",response_bytes="0",
  output_sha256 of fixed synthetic fixture,dispatches/runtime_prepared/runtime_released/
  operator_prepared/operator_released all "0",real_inference="false".

All metadata strings, SHA256 lowercase, sizes/counters canonical decimal. No
raw body/canary/lease/output/exception text. Python verify_expiry_audit and C#
ModelExpiryAdmission/ModelValidationAdmission independently enforce exact keys,
types/values and UTC time. C# range-checks the reply's dynamic elapsed value,
reconstructs every other expected field from host state and requires protected
audit to match that EXACT elapsed value; no metadata wildcard or different-clock
subtraction. Mutually selected audit cases throw; older audit defaults unchanged.

Coordinator requires normal child/worker exit 0, EOF, bounded empty stderr,
host-file recheck and exact independent audit readback before
model_expiry_evidence_matches/model_evidence_matches. Fresh beacon/worker stop/
product cleanup remain mandatory for
offline_model_lease_expired_pending_independent_cleanup. Shared startup_status
is offline_model_validation_child_completed; M04a/lease_expired/final status
identify the case. Generic timeout/EOF/crash/setup error is blocked, not a pass.
No model response write or publication callback. False qualification flags remain.

## Source And Future Package Scope

New Python model_lease_expiry.py and C# ModelExpiryAdmission.cs implement the
predicate, exact evidence and real pre-begin timing. Shared model_worker,
model_bridge, native child/worker support, coordinator, profile selectors/
allowlists, consent/version/status and common audit admission are extended.
Existing four protected host files, policy authority, framing and startup
diagnostics remain. Worker native constructor accepts NO clock from config/CLI;
fake clocks appear only in inert fixtures. No base liveness/TTL change.

Read-only Body 1 comparison finds four changed payload sources plus the future
model-contract.json replacement (five total), three additions (canonical expiry
module and two fixed root entries). Future assembly approval must explicitly
include omitting model_body_child_entry.py and model_body_worker_entry.py from
the NEW M04a payload only. Keep all canonical helpers, M03a shared support and
unrelated bytes. Actual-profile ReadIndex must verify every future member before
sealing. Do not broaden admission or delete prior/source/workstation/guest files.
No package or artifact hashes for M04a exist yet.

Same Python 3.13.14, pinned Hermes/64 distributions/config/native guards;
no acquisition. Same AppContainer/zero capabilities/six denies/reduced tokens/
one-process jobs/child-process block/pipes/host ACLs/labels. Trusted worker remains
outside child containment; shared All Application Packages and profile deletion
limitations remain. No listener/service/account/registry/loopback grant, credentials,
customer data, inference, spend, recovery or extra VM test automation. Ready/RPC/
partial-frame 5000/2000/1000 ms; child 22/30 seconds; frames 8192, direction/audit
131072, request/response/stderr 4096, report 65536, output 1024, diagnostic parser
256. The extra 2100-ms wait consumes these budgets, not a new allowance.

## Inert Evidence And Next Decision

325 Python tests/709 subtests pass, including 19 expiry tests and two mocked
startup-main checks. Fake boundary clocks only in ordinary-host fixtures; no
native expiry or product clock wait ran. Existing unknown-cache_dir warning
remains. C# M04a 225 assertions; seven paired profiles 216 each. Earlier M03d
136/paired127, M03c195/186, M03b177/168, M03a108/101, M02 117/113, startup874,
earlier components711, bridge154 and model-audit178 pass. Counts overlap, not
native cases. Cross-language metadata/audit and fake-clock WaitCore budget/stall/
backward/oversleep checks pass; native WaitBeforeBegin is source-bound to
Stopwatch/Thread.Sleep and is not executed by the fixture main.

Coverage includes before/at/after expiry, fresh base positive, actual guard
required, uncertain/generic failures, revoked/closed/audit/wrong phase, grant
retiming/token replacement, wrong request/channel/command, malformed elapsed,
required-audit faults, exact dynamic ledger matching, spoofed child controls,
native-entry guards and pre-begin/outside-RPC placement. Existing framing fixtures
cover partial IO/EOF; no native timing or cleanup qualification follows.

Source preparation complete. Next: review/approve separate assembly INCLUDING
the two exact inactive Body 1 root omissions, then matching-artifact one-run VM
approval/fresh consent. No M04a native run, M04b/c implementation, later case,
inference or qualification is authorized. Preserve all frozen artifacts and
original reports; Gate A and all qualification flags remain open/false.

# Maya Authorization Bridge Document 1 Handoff

## Scope

2026-10-23: user-approved implementation preparation and ten-case correction.
Version 0.2.0-bridge-document.1, scope offline-authorized-document-bridge-v1.
Use the same customer-like Windows 11 Pro x64 26300.9711 VM through RDP.
This unsigned development component is not a release installer. No local native
product/Hermes run or VM execution is included in preparation. Separate matching-
artifact VM-run approval and fresh product-owned informed consent are required.

The active schedule is maya_authorization_bridge_v1_tests_10.json. The original
twelve-case contract is preserved as history. Native N09/N11 are deliberately
not claimed: mandatory local audit-fault tests prove that a failed sink is not
reopened. No audit recovery, new grant or deadline expansion was introduced.

## Product Components

One trusted elevated C# coordinator owns product setup and cleanup. It launches:
- One trusted same-user medium-integrity gateway worker outside AppContainer,
  with its own one-process kill-on-close job and checked reduced token.
- One real pinned Hermes runtime in the existing ordinary AppContainer with
  zero capabilities, reduced token, one-process job and child-process block.

The child's six package-scoped WFP network denies remain. The trusted worker is
NOT network-contained by those filters. It exposes no network/model/URL/shell
operation, imports no Hermes or OpenAI SDK, and serves only the fixed document
operation. Its canonical project_maya imports also load existing cryptography
46.0.7 support (with existing cffi 2.0.0/pycparser 3.0). These exact packages were
already in the frozen payload: no wheel/pin/download or runtime patch changed.
Worker startup rejects missing crypto support or wrong package origins/versions.

Private anonymous inherited pipes carry framed requests; no listening socket,
HTTP server, loopback exemption, named reconnect endpoint or bearer file exists.
Each process inherits exactly its own stdin/stdout/stderr endpoints, not the
other process's handles, host files, policy, audit, process tokens or jobs.
Both suspended process tokens are checked before their respective resumes;
worker ready PID must match the actual coordinator-owned process handle.

The existing ActionAuthorizationGateway/PolicyAuthorizationGateway decides
file.read and file.disclose. No second policy engine or C# policy port is used.
The historical test-only broker/HTTP adapters are not promoted or launched.
Canonical Python modules remain ordinary packaged modules, not import-loader stubs.

## Private State And Permissions

Existing runtime/state and temporary package grants remain. The new host sibling
is outside those recursive grants and contains exactly document.txt, policy.json,
audit.jsonl and worker.json. Product setup creates explicit protected descriptors
at creation, permitting only SYSTEM/Administrators/the actual operator. Medium
labels are verified; no customer, ancestor or machine policy ACL is modified.
Host ACLs remain intentionally after cleanup to protect retained evidence.

The synthetic document contains a fresh unpredictable 256-bit canary. Its content
is not preseeded in the child or printed in reports. The worker uses exclusive,
open-existing handles, rejects directories/reparse objects/multiple hard links,
checks handle-final path and size, and verifies document bytes against the private
expected digest. This is not general customer-file mediation or isolation proof.

Policy is exactly two rules for windows:<actual operator SID>, the fixed resource
and fixed runtime recipient. The child cannot supply actor, classification, path,
approval or URL. Fresh private single-use leases are bound to attempt/channel,
monotonic expiry and next sequence. Replay, unknown fields and unhandled policy
outcomes fail closed. No inherited process ID or a saved session is authentication.

Required audit reuses AuditRecord, appending through a private host handle with
short-write checks, flush and fsync before read and before disclosure. Failed
required audit poisons the sink permanently. Durable release intent does not claim
delivery: the coordinator validates actual channel/result evidence and confirms
delivery/withholding back to the worker for an additional outcome record. A lost
confirmation or post-release audit error blocks with an uncertain/committed
outcome, not fabricated rollback. Tokens/content/raw exceptions are not public.

## Fixed Test

Hermes commit b13e2fd6948a59eeb59fe618914147d97a2ee90a and Python 3.13.14 remain.
Register one maya_document_read extension in the native tools.registry singleton,
enable only maya_bridge, construct the real agent/client and verify actual schema,
tool names, class/origins/config and all 64 distribution identities. Invoke the
native registry dispatcher for the positive case; direct protocol denials verify
that skipping the wrapper does not grant authority. No fake agent/client, model
selection/conversation, native-memory retest or provider operation is included.

Run exactly one schedule in one child/worker:
N01 allow; N02 direct protected-file read/write opens; N03 policy deny;
N04 wrong resource; N05 claimed actor; N06 consumed-token replay with current
sequence; N07 expired lease; N08 pre-admission cancellation; N10 disclosure deny
after authorized read; N12 unsupported operation.

Require two actual completed document reads and exactly one document release.
N10 may read, but releases zero bytes. Pre-read denials open/read/release nothing.
Worker preparation counters and child observations do not alone prove delivery;
the coordinator validates worker request IDs, exact effects, document digest,
case ordinals, final schemas, successful pipe writes and child receipts. It rejects
trailing bytes, partial frames, unknown fields or any inconclusive case. Both real
processes must exit 0, with agent/SDK closure and zero model-call counter verified.

After both exits, the coordinator reads the protected audit file and admits the
exact 21-event schedule: actor/attempt, per-case request binding, read/release
targets, disclosure digests, UTC timestamp shape and outcome confirmations must
match. Missing, partial, extra or misbound records block success. Persisted
intent order is evidence, not independent proof of power-loss durability.

## Budgets And Cleanup

No change to 8192-file/4-MiB index, 32-MiB single-file/256-MiB expanded caps.
Each frame is at most 8192 bytes and each channel direction 128 KiB; document
1024 bytes, audit 128 KiB, stderr 4096 bytes, report/captured text 65536 bytes.
JSON scalars used by this protocol are strings, Booleans, null and signed 32-bit
integers; fractional/nonfinite numbers are not accepted by the Windows codec.
Messages use one increasing document-request sequence and a single in-flight
request. Fixed control frames do not grant effects or reset budgets.

Keep 22-second cooperative and 30-second host child budgets. Worker readiness
is capped at 5 seconds, calls at 2 seconds, incomplete frames at 1 second. Channel
I/O is owned by separate bounded coordinator tasks; stop jobs before joining
blocked readers. Stderr overflow terminates its job. No deadline increase,
resend, unrestricted fallback or automatic retry is permitted.

Maya stops/confirms both jobs and channel tasks before revoking child grants,
profile and filters. State returns to Medium; host evidence stays protected.
Uncertainty blocks cleanup success. Bridge automatic recovery is intentionally
disabled rather than reusing legacy single-job recovery without qualification.
Forced closure requires review. Profile removal still lacks independent proof.

## Operator Handoff And Verdict

Copy/extract the complete frozen ZIP, return the EXE path and verify its hash.
Do not run until separately approved. Use Maya's own consent/setup through RDP;
do not manually adjust ACLs, WFP, labels, registry, antivirus, Python or Windows.
No VM/Docker product dependency or additional test supervisor is added.

Only complete host evidence, child/worker natural exit 0, startup beacon and
reported security cleanup produce
bridge_document_completed_pending_independent_cleanup. Production, containment
and independent-cleanup flags remain False. A failed/unexpected case stops the
schedule, with no retry or correction. Return the full bounded JSON for review.

This is a first native product-bridge feasibility test, not SDK/model mediation,
complete L-family native fault coverage, concurrent users, crash recovery,
authoritative state, connectors, Metabase, Gate A acceptance or production readiness.

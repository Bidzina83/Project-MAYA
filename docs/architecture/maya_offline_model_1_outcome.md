# Offline Model 1 Outcome

Recorded 2026-10-24 from operator-supplied VM results and manual readbacks.
These are reported guest observations, not a local rerun or independent scan.

## Artifact And Run

Version 0.2.1-offline-model.1; scope offline-hermes-model-wire-v1; case M01.
Guest EXE D:\Maya-Offline-Model-1\MayaProtectedPython.exe matched prepared SHA256
BDC50E29228E85566B75527899870F88925C1FD66D45C95AF4F0694FABF2BE64.
After the one-run approval question, the operator explicitly said "I will run it";
the returned report records informed_consent=true. That allowance is consumed.
Windows 11 Pro build 26300.9711. Attempt 918d68470879409fbfb7dbfee71acb3e.
Host PID 11136, trusted worker 11096, child 10448.
Reported UTC interval 2026-10-24T12:55:05.1136411Z to
2026-10-24T12:57:25.0353812Z includes setup/cleanup, not just child execution.

## Bounded Result

Status offline_model_wire_completed_pending_independent_cleanup; model_stage
complete. Payload, six filters, reduced child token, worker token/readiness and
protected Python entry verified in the coordinator report.

Expected and observed serialized request were both 2618 bytes, SHA256
86aa185f8c4497956a14ed7380707518b4ffb66bf8afc0e0405d69ae0f66453a.
One synthetic dispatch, one runtime pipe write with the admitted receipt, and
one operator publication were recorded. Six audit events verified, SHA256
5629503a048ebdeb7ef6499f2a037ff512bd4721beb6819eb056505e8214c7aa.
The coordinator admitted matching model evidence and natural child/worker exit 0;
fresh state beacon observed, worker stopped and evidence collected.

The explicitly untrusted child report says native construction/conversation,
SDK closure, unchanged config, verified origins/distributions, one request and
two client objects. These assertions are corroborated within the coordinator's
bounded predicates, not elevated into independently trusted child testimony.
The operator separately confirmed the expected MAYA_OFFLINE_MODEL_OK synthetic
text appeared in the Maya output field. No external model inference occurred.

## Scoped Manual Cleanup

Following normal window closure, the operator reported:

- No matches for the specified host/worker/child PIDs or MayaProtectedPython name.
- No reparse points under the instructed attempt root. This was confirmed in
  prose, not pasted output; later ACL results explicitly identify that same root.
- No package-SID ACE across 7477 entries, zero processing failures.
- State permissions SYSTEM/Admin full control, operator modify, Medium OI/CI/NW.
- Retained host directory plus audit.jsonl, policy.json, request.json, worker.json
  have SYSTEM/Admin/operator full control, Medium labels; directory OI/CI/NW,
  files NW, five entries and zero failures. Display does not attest all owner,
  group or descriptor protection bits independently.
- WFP export exit 0. The instructed fragment-aware reader returned all seven
  exact IDs absent, with no parsing error reported:
  sublayer 16f36c0d-e795-2394-3f0e-011e245146fd;
  filters b0c09eb1-52e0-b3cd-40ea-29fc8039536b,
  ac370ed6-a526-cd3f-0b8b-a2f4cc4cff7e,
  4e195a29-1c05-4bc7-bcf7-91cf5fea08a2,
  b12a91c5-928b-f0c0-07db-c846a026fd53,
  40772b32-6a00-3cbc-2ff6-e9925278af68,
  d5d197e7-d807-03cb-8362-f44b98d1fec7.

Package SID:
S-1-15-2-3686397461-2348232480-2841884560-957529618-2992371765-792582922-2913225516.
The WFP XML itself and export filename were not returned. No native listener
was introduced in this slice, so no invented test-listener ports are checked.

Scoped manual checks pass as reported; profile removal remains product-reported.
Do not alter the original report's independent_cleanup_verified=false,
production_qualified=false, containment_qualified=false or pending-cleanup status.

## Next Work

M01 establishes bounded offline native compatibility, not a real provider call,
all-route mediation, arbitrary output validation, full cleanup or containment.
Gate A remains open. The operator authorized continuation to record this outcome
and prepare M02-M08 denial proposals. See maya_model_bridge_denial_proposal.md
and maya_model_bridge_denial_tests.json. No further native run, package change,
new grant, provider credential/network access, automatic recovery or retry follows.

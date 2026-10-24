# Authorization Bridge Document 2 Outcome

Recorded 2026-10-24 from operator-supplied VM report and read-only cleanup outputs.
These are reported guest observations, not a local rerun or new qualification.

## Artifact And Approval

The operator verified EXE SHA256
6D4F22DC0CAA1EE83502B51B9FCB24890EA701A17B2819C5B4AA246F4444D21D,
then explicitly authorized one RDP run with fresh product consent after Document
1 scoped cleanup checks. Version 0.2.0-bridge-document.2; scope
offline-authorized-document-bridge-v1; Windows Professional 26300.9711.
Attempt 4ddae15a3c1b4cb2b7c5a56111718464. Host 9860, worker 6772, child 1832.
Reported UTC interval 2026-10-23T18:37:03.2721572Z through
2026-10-23T18:39:32.3724680Z includes preparation and cleanup, not merely the
bounded child deadline. The one-run allowance is consumed.

## Bounded Native Result

Status bridge_document_completed_pending_independent_cleanup. Payload, six
filters, reduced child token and trusted worker token/readiness verified.
Protected Python entry and fresh state beacon observed. All ten cases report
host_effects_match and child_observation_matches:

| Cases | Observed document effects |
| --- | --- |
| N01 authorized registry operation | One read, one release |
| N02 direct host-file access | No bridge read/release; expected child denial observations |
| N03-N08 policy/resource/actor/replay/expiry/revocation negatives | No reads or releases |
| N10 read permitted, disclosure denied | One read, zero releases |
| N12 unsupported operation | No reads or releases |

Totals: two reads, one release, 21 coordinator-verified audit events.
Audit SHA256 b99d086b516af447c8b75c3d98e7e627dd590d4c9b71db60c68656475384cdee.
Worker and child natural exit 0; worker stopped; bridge evidence matched.
Child report (explicitly untrusted) says real construction, SDK closure,
unchanged configuration, checked origins/distributions and zero model calls.
It is corroborated only within the coordinator's bounded admission predicates;
do not treat child self-report as independent authority.

The label correction passed this setup path. No broader Windows compatibility,
model mediation, customer-document access or authoritative-state operation follows.

## Scoped Independent Manual Checks

After normal window closure the operator reported:

- No matching host/worker/child PID or MayaProtectedPython process.
- No recursive reparse entries in the checked attempt folder. The pasted
  reparse command omitted the earlier root assignment; its attribution assumes
  the previously instructed Document 2 root remained in that PowerShell session.
  Later ACL commands explicitly rebound that root to this attempt.
- No matching package-SID ACE across 7,467 entries; zero processing failures.
- State restored to Medium OI/CI/NW, SYSTEM/Admin full control and operator modify.
- Retained host folder and document.txt, policy.json, worker.json, audit.jsonl
  show only SYSTEM/Admin/operator full control, Medium labels, correct directory
  versus file inheritance flags; five entries, zero failures. This display does
  not independently attest owner/group or every descriptor protection bit.
- WFP export succeeded, exit 0; complete fragment-aware text/CDATA traversal
  reported all seven exact resource IDs absent:
  sublayer 9700f8d2-86ff-78ad-cacd-6b5aee3b643c;
  filters 42918d83-8590-d2d2-9f0e-a1096236fd3c,
  e7fa5187-199f-759d-d864-61da2cfd8cb2,
  53fdd1cb-6ec8-5457-849e-38f70bf4ad4f,
  832cc6d8-ef26-58b7-cb7b-9553d6a6e628,
  365b2aba-1734-01e0-b1c0-8e4d4ebf01fb,
  ba4c21c9-6702-2ae7-7e8f-ffda5ab33d31.

Package SID:
S-1-15-2-1234064436-1933187102-1645998646-277386704-621143316-399112551-1943476646.
Export: Maya-BridgeDocument2-cleanup-e8f27038cf614354b8326f6c1cbda07f.xml
in the operator's guest Temp folder. The export itself was not transferred here.

Scoped checks passed as reported, with the provenance limitation above.
AppContainer profile removal remains product-reported only; no full independent
cleanup attestation. Do not rewrite the original report's false flags or status.
No further VM command or rerun is required by this outcome record.

## Acceptance Boundary

Bounded A3 document mediation is demonstrated, not complete A3 security/lifecycle
qualification. N09/N11 native audit faults, forced closure/recovery, concurrency,
profile removal, broader bypass coverage and shared AppContainer access remain
open. The trusted medium worker is not covered by the child's network filters.
Gate A, production_qualified and containment_qualified remain open/false.
The user approved recording this outcome and document-only A4 design/test
preparation, not implementation, a package, credentials, inference or another run.

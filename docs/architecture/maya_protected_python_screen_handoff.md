# Maya Protected Python - Containment Screen 10

Version: 0.1.0-screen.10. Baseline: Windows 11 Pro x64 26300.9711.

This is an unsigned development candidate for a fixed synthetic containment
screen, not the complete Maya product. Preparation and inert checks do not prove
native compatibility, cleanup or containment. Production activation is blocked.

## Approval Boundary

Do not run this package until its exact artifact and native-impact review has
been separately approved. No execution command is included in this handoff.
The existing Package 7, Screen 8 and Screen 9 artifacts and reports are preserved;
do not replace or relaunch them.
Do not use this candidate to recover a pending record from another version.

After a separately approved run, Maya itself requests informed consent and the
administrator elevation required for its scoped setup. Do not manually modify
ACLs, registry permissions, WFP/firewall defaults, loopback exemptions, antivirus,
encryption or boot settings. Refusal or setup failure blocks the run.

## Change From Screen 9

Screen 9 completed setup, ran Python and returned all 47 child observations. The
aggregate failure was its own-token query returning error 24, not an observed
escape. Four UDP observations and the subprocess denial remained inconclusive;
cleanup was reported complete, not independently verified.

Screen 10 fixes the Python diagnostic to query elevation and AppContainer status
with exact four-byte buffers and verify their returned lengths. The variable-size
capability query first obtains the required size, admits only 4..4096 bytes, then
performs one bounded data query. Non-elevated, AppContainer and zero-capability
predicates remain unchanged. Failures and unexpected lengths still block success.

Only C06.spawn may now accept error 367 (ERROR_CHILD_PROCESS_BLOCKED) in addition
to access denied. Other cases and unknown errors retain their original admission.
The bundled CPython files, other probe operations, 48 case IDs/expected outcomes,
native token admission, ACLs/labels, six WFP denies, endpoint/IPC scope, deadlines
and cleanup remain unchanged. No permissions are relaxed. The synthetic-stream
handle correction and stage reporting from Screen 9 remain in place.

UDP remains inconclusive. Even if the corrected token and subprocess checks work,
the aggregate screen must remain blocked until the UDP evidence gap is resolved
through a separately reviewed design. Do not reinterpret blocked as a new Python
startup failure or a demonstrated escape; do not relax rules to obtain a pass.

## What The Candidate Does

- Retains ordinary AppContainer, zero capabilities, a reduced same-user token,
  six profile-scoped WFP network denies, one-process job and child-process policy.
- Uses the same embedded Python 3.13.14 files as Package 7; adds one fixed probe
  module. Python is not installed into Windows or added to the machine PATH.
- Creates a new attempt under ProgramData/MayaProtectedPython-Startup1, with
  synthetic document, memory, business, policy, audit and dummy-secret canaries.
  No real customer file, credential, model, connector or business service is used.
- Grants temporary read-only All Application Packages access to one explicitly
  public synthetic control, not to protected targets or existing Windows objects.
- Creates two owned path aliases, one protected named shared-memory object and
  four loopback-only TCP/UDP targets (IPv4/IPv6). Host endpoint controls use private
  random challenges that are not included in the child plan or report.
- Runs one fixed Python child for at most 30 seconds, with a 22-second internal
  probe budget, a 4096-byte stdout limit and 65536-byte detailed-report limit.
- Attempts 47 fixed child observations plus product cleanup (48 frozen cases).
  Direct file/path/process/token/IPC and network operations use synthetic targets.
  No shell or arbitrary command is offered. A possible forbidden subprocess is
  only the bundled Python with the fixed inert command `pass`.
- Stops on an observed unauthorized effect, confirms job stop, removes only
  verified owned links, closes endpoints/shared memory and revokes fixture grants
  before the existing profile/filter cleanup. Inert canaries and reports remain.

## Interpretation And Limits

The frozen case inventory is in `screen-contract.json`. A denial needs an explicit
admitted native error and controls; silence or timeout is never a pass. Successful
UDP send/bind without demonstrated transport denial remains inconclusive. A bind
denial does not independently exercise a later listen/receive API; those deeper
inbound paths remain unqualified. A mapping namespace miss is inconclusive, not
proof of access rejection. Child-process error 367 is admitted only for C06.spawn;
other unrecognized child-policy errors remain inconclusive.

The child report is untrusted; host controls and effect readbacks are separate.
Unexpected traffic may contaminate a target and fail the screen without proving
Python caused it. Existing AAP-readable customer resources are not made private
by WFP; the public positive control is not a customer-privacy success.

`python_entry_observed` records the exact startup beacons independently of the
probe exit. The historical `python_started` predicate still requires natural exit
zero as well as both beacons; a false value alone does not mean Python never ran.
All-expected observations can at most yield
`observations_completed_pending_independent_cleanup`. The report always keeps
containment/production qualification false and independent cleanup unverified.

Normal cleanup and version-bound recovery remain product-owned. The known
journal-less recovery gap is not fixed; no forced-crash test or automatic retry is
approved. A cleanup uncertainty retains security denies/grants for review. Do not
force-close Maya or disable Windows protections to get a different result.

Hermes, real gateway authorization, secrets services, model routes, connectors,
Metabase, indirect brokers, path races and crash/restart qualification are not
included. The Azure VM is a laboratory, never a product prerequisite.

Preserve the result window/report after any future approved attempt and stop for
review. Exact resource identifiers are retained in the attempt report for a
separate read-only cleanup check. No rerun or corrective grant follows failure.

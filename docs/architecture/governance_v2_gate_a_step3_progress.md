# Governance V2 Gate A - Step 3 Progress

## Status

Step 3 commenced on `Maya-Governance-Integration-V2`, 2026-10-14.
Incomplete. This is the approved prototype work, not a new gate, correction batch
or acceptance. No A01-A20 family is qualified by the unit tests below. No policy
weakened, Hermes patch applied, installed artifact rebuilt or production gate changed.

## Implemented And Observed

The initial observations below predate the native continuation recorded later.

- Reconstructed unchanged Hermes pin into ignored
  `.codex-build/governance-v2-gate-a-baseline` using the existing ordinary exporter.
  Manifest SHA256: `c554f5dc0d2fdccbfa1b578de22e07077e6043c1e820e72c0150d3ec0a8b1d72`.
  The source inventory has 5,463 files, with bytes verified against recorded SHA256
  and Git blob identities. No packaging changes or patches were applied.
- Implemented a test-only host broker core using the existing Maya gateway/audit
  interfaces. Host-held identity/classification, bounded targets/budgets/TTL,
  revocation without waiting for a running service, audit-before-effect, strict JSON,
  fixed public errors and separate final-disclosure validation. Denials revoke the
  remainder of the request. Service implementations are injected host-owned handlers;
  unit handlers are synthetic, not qualified document/SMB/model services.
- Implemented a dedicated loopback HTTP transport with no arbitrary forwarding,
  bounded body/timeouts, strict admission/Host checks and suppressed raw diagnostics.
  This is not network isolation or a production endpoint.
- Added baseline verification and read-only Windows/WFP preflight. Observed native
  Windows version 10.0 build 26200 and presence of required APIs. WFP engine open
  returned access denied (5) inside the Codex sandbox, then success (0) outside it.
  Engine session was closed; no filters were installed. This is not proof of
  permission to provision filters or of valid isolation policy.
- Existing isolated native dependency environment reports Python 3.13.14 and
  OpenAI SDK 2.24.0. This is a tooling observation, not the prepared LPAC runtime
  artifact or dependency-lock qualification.

## Evidence Level And Remaining Approved Work

Broker/preflight tests exercise host controls and one real temporary loopback
server; they do not execute AIAgent. Existing Local API regressions remain controls,
not evidence that its current ingress can be adopted unchanged under V2.
The new source/preflight tools remain separate from production launchers.

The native continuation implements launcher/helper and slice code as described
below, superseding the initial missing-component inventory. The native product
slice has not executed successfully. The full Steps 4-5 matrix remains unrun.

Before executing security provisioning, disclose exact profile/SID, workspace
paths, ACL grants, WFP filter conditions, permitted loopback capability/exemption,
privileges and cleanup procedure, then obtain separate permission. Changes must
be confined to evaluation resources and SID-scoped policy, not default host policy.
Do not provision an unreviewed helper merely because architecture was approved.

The original single-prototype and one specifically approved correction budget
remain unchanged. No additional implementation sequence is introduced here.

## Native Continuation And Stop (2026-10-14)

Implemented `scripts/native/governance_v2_windows.cs`, compiled with the existing
Windows .NET Framework compiler into ignored test tooling. It creates a suspended
AppContainer process with the SDK LPAC opt-out attribute, explicit handle list,
private environment and kill-on-close/no-breakaway job. It refuses thread resume
unless AppContainer/LPAC/SID checks pass. No normal-process fallback exists.

The WFP helper transaction installs eight persistent complementary BLOCK rules
scoped to the unique evaluation SID: non-TCP, non-127.0.0.1 and non-broker-port IPv4
connects, all IPv6 connects, and IPv4/IPv6 listen/receive. It installs no PERMIT rule.
Read-back compares layer, action, SID, conditions and persistent/enabled flags;
Windows's documented INDEXED bit is accepted without permitting DISABLED or
unknown flags. Administrators/System own the test rules; the host user receives
READ_CONTROL and FWPM_ACTRL_READ only. Effect-level network tests are still unrun.

Prepared managed copies of CPython 3.13 and existing native test dependencies,
unchanged Hermes sources and a test worker: 16,138 runtime files hashed. These are
assessment artifacts, not a license/dependency-qualified release payload. The
worker uses -I/-S and explicit staged paths, refuses an ordinary token, checks
`run_agent` origin and uses native registration/memory/session APIs. New runner
code binds the host broker and synthetic document/Maya SQLite store to real SDK
Responses fixtures. No installed wheel, legacy candidate startup guard or
production plugin activation is selected.

Provisioning was separately permitted through tool approval and Windows UAC.
Initial non-elevated transaction returned error 5. Elevated read-back found flags
65 (PERSISTENT + INDEXED), then native helper path enumeration exposed long-path
handling defects. These were corrected in the helper without broadening grants
or changing Hermes. Scoped filters, ACLs and exemption were then provisioned and
read back. The prototype never reached effective network/agent qualification.

The suspended child passed TokenIsAppContainer, but GetTokenInformation class 46
(TokenIsLessPrivilegedAppContainer) returned error 87. Inspection also found an
incorrect startup attribute constant in the first implementation: SDK value
0x2000F, not child-process-policy 0x2000E. It was corrected, and class 46 still
returned 87. The child was terminated before ResumeThread on both attempts.
Hermes import, construction, loop, tool execution and native memory have NOT run.
Error 87 alone does not prove LPAC unsupported or identify the query's cause.

Cleanup was separately permitted and completed: removed the exemption, eight
filters/sublayer, directory SID grants and test profile, restoring private state
to medium integrity. Read-only checks found the filter key absent (FWP_E_FILTER_NOT_FOUND)
and no target SID in the exemption list. Prepared artifacts and failed evidence
remain ignored; no installed Maya/Hermes home was changed. Capture files are
`host/lpac-query-failure.json` and `host/initial-filter-verification-failure.json`
inside the ignored stage, not acceptance artifacts.

Previous stop: Step 3's LPAC verification contract needed specific approval before
changing it. The proposed bounded correction is in
[the verification review](governance_v2_lpac_verification_review.md). No downgrade,
new isolation architecture, Hermes patch, runtime pin or acceptance is proposed.

## Approved Correction And New Stop (2026-10-14)

The user approved the bounded AccessCheck correction. Paired real suspended-token
controls now pass: selected-package access allowed, LPAC AAP-only access denied,
ordinary-AppContainer AAP access allowed, and wrong-package/no-grant access denied.
The ordinary control never resumed. The verification-only LPAC child also never
resumed. Input hashes and the startup-attribute implementation correction are in
the verification review.

Only after those controls passed did the synthetic slice resume the LPAC Python
child. It exited with `0xC0000022` and no worker frame. No Hermes loop, native memory
or mediated model/tool effect is qualified. The runner now reports that fixed
protocol failure plus numeric exit status. The exact denied startup resource is
unidentified; explicit executable RX alone does not qualify dependency access.

All 51 portable broker/preflight/worker-guard/Local API tests pass. Compilation
passes, but this does not close Step 3 or any A01-A20 family. No native-source
patch, broader capability, normal-token fallback, runtime pin, wheel or installer
change was made. Stop for startup-failure review within the fixed evaluation
budget, not an automatically expanded patch/task sequence.

The evaluation security resources were subsequently cleaned up and read back:
test filter absent, no matching loopback exemption and no package-SID executable
ACL grant. No installed Maya/default Hermes state was touched. Input hashes and
cleanup evidence are recorded in the verification review; ignored artifacts stay
out of the commit. Context validation, Python compilation and diff checks pass.

## Startup Diagnosis (2026-10-14)

The user requested diagnosis only. Separately permitted, unchanged-input capture
shows Windows registry read denials and terminal SideBySide denial immediately
before 0xC0000022 exit. Staged python313.dll mapped successfully. The SideBySide
DACL permits AAP/registryRead, neither usable in the current selected LPAC profile;
the launcher omitted OS-registry compatibility reads. Full evidence, confidence
limits and hashes are in the verification review. No registry grant, capability,
Hermes code or production artifact changed. A further correction requires an
explicit budget/impact decision; Step 3 remains blocked.

## Approved SideBySide Experiment (2026-10-14)

The user approved one additional exact-key read experiment. The independent
host script preserves the existing launcher/runtime, captures rollback metadata,
applies only non-inheriting ReadKey to the test SID and restores original
owner/group/DACL bytes. Its initial .NET handle-mode and auto-inheritance defects
were stopped and retained; final grant/restore uses RegSetKeySecurity.
The 35,078 descendant keys have no test-SID grants.

Verified exact grant: child exit 0xC0150002, no worker frame. Exact restoration:
original 0xC0000022 returns. Access-denial correction is effective but startup
remains blocked by application activation-context generation. No matching staged
SideBySide event identifies its exact cause. Consult the verification review;
do not add another key/capability automatically or claim Hermes/Gate A readiness.
Original owner/group/DACL bytes and control flags are verified restored. Test
profile/WFP/exemption/directory grants are removed and read back absent. All 51
portable regressions and PowerShell syntax/context/diff checks pass. This remains
an unsuccessful startup qualification, not a production fix or installer change.

## Whole-Startup Assessment (2026-10-14)

The user approved holistic assessment, not another correction. See
[the completed assessment](governance_v2_windows_startup_assessment.md) for the
160-image/104-distribution inventory, matching 28 direct requirements and 58
transitive edges, actual DLL-activation trace, registry-capability boundary review,
and two deterministic Maya-owned memory/SSE wiring mismatches. These are not
proof of native import/loop readiness. Broad registryRead is not a safe default;
the exact restricted activation root remains unresolved.

Only the previously approved exact-key grant/profile was repeated with separate
permission for diagnostics, then restored/removed. No new key/capability, runtime
or fixture correction was applied. Native artifacts/pins are unchanged. All 55
diagnostic/parser/broker/token/Local API tests, context validation, Python compile
and diff checks pass. Raw/generated evidence is ignored. Review a fixed complete
startup-and-integration compatibility contract before another correction, not a
new automatically expanded grant sequence. Step 3 and Gate A remain open.

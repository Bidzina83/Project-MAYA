# Governance V2 Gate A - Step 3 Progress

## Status

Step 3 commenced on `Maya-Governance-Integration-V2`, 2026-10-14.
Incomplete. This is the approved prototype work, not a new gate, correction batch
or acceptance. No A01-A20 family is qualified by the unit tests below. No policy
weakened, Hermes patch applied, installed artifact rebuilt or production gate changed.

## Implemented And Observed

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

Step 3 still requires the concrete LPAC launcher and WFP provisioning/verification
helper, curated runtime grants, exact variant inventory, process adapter/native
tool-memory integration and native product slice. No launcher or WFP helper is
reported as implemented. The full Steps 4-5 bypass/failure matrix remains unrun.

Before executing security provisioning, disclose exact profile/SID, workspace
paths, ACL grants, WFP filter conditions, permitted loopback capability/exemption,
privileges and cleanup procedure, then obtain separate permission. Changes must
be confined to evaluation resources and SID-scoped policy, not default host policy.
Do not provision an unreviewed helper merely because architecture was approved.

The original single-prototype and one specifically approved correction budget
remain unchanged. No additional implementation sequence is introduced here.

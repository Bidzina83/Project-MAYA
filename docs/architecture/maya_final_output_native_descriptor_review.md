# Native Probe Descriptor Comparison Review

Review only, 2026-11-09. The one baseline allowance for the original probe is
consumed. It blocked with exit 2 at `descriptor_mismatch` on Windows
26300.9711, local NTFS. Original EXE SHA-256
`37669A3F955F2F18A3F2D339FBBCB6EEA0A6BE415A9BD17FBAFD9EEFF701D2B5` and
source SHA-256 `78DA86E1EC7A312DE0F2199D738E14DAC1D433436B36026003E1A1349126F431`
were rechecked locally. Preserve the original artifact and scratch evidence.

## Observed And Inferred

The operator's read-only output for scratch attempt
`4112b2c3528c4e949a25853e20530440` reports owner and group MyVM\Bidzina, a
protected DACL, SYSTEM and local-user Full Control entries, and a Medium
no-write-up label. `Get-Acl` returned `O:LAG:LAD:P(A;;FA;;;SY)(A;;FA;;;LA)`;
the label was observed separately through `icacls`. No journal leaf exists.
The supervisor checks the new directory before helper launch. This was not a
journal write, flush, crash or recovery test.

`tests/windows_final_output_native_probe.cs:Descriptor` constructs the two
allow entries user-first, and `VerifyDescriptor` requires literal equality of
the converted descriptors. The reported DACL is SYSTEM-first. That is a
credible formatting mismatch, not proof that the actual comparison failed
only for that reason. The operator commands did not capture both descriptors
from the probe's same opened handle and conversion path. No descriptor
weakening is justified.

## Proposed Exact Semantic Check

Keep the same-handle descriptor query and the same creation descriptor. Replace
only text equality with a bounded structured comparison of the returned object.
Normalize SID representation to binary SID identity. Allow either order only
after verifying that there are exactly two explicit, noninheriting, ordinary
allow ACEs. Require one current-user SID and one SYSTEM SID, each with the exact
file full-access mask from the existing contract. A duplicate SID, missing ACE,
deny/object/callback ACE, extra ACE, changed mask or any ACE flags fails. Do not
sort arbitrary ACLs or compare effective access: reordering mixed allow/deny
entries is outside this exception.

Require owner and group to match the current test-user SID, protected and
present non-null DACL, and an explicit, single queried Medium mandatory-label
ACE with exact no-write-up mask and zero ACE flags. Treat label information as
the label returned by the scoped query, not a claim that the whole audit SACL
was inspected. Missing, malformed, unparseable or unsupported structures fail
closed. Validate sizes/counts before decoding; free the returned descriptor
exactly once. Do not reopen by path, query a different object, add privileges or
silently fall back to an unprotected descriptor. Use bounded reason codes for
owner/group, DACL, allow-entry and label mismatch; do not log raw descriptors.

## Acceptance And Approval Boundary

Require inert comparisons for both known ACE orders and binary-equivalent SID
spellings, plus rejection of every wrong owner/group, unprotected/null/empty
DACL, duplicate/extra/deny/inherited ACE, wrong mask, missing/extra/wrong label,
and malformed/truncated descriptor. Keep original handle identity, scratch
provisioning, no-inheritance/sharing, journal, checkpoint, timing and restart
checks unchanged. Compile a separate successor, preserve the original EXE and
hash, and record the successor identity. No native descriptor compatibility is
established by inert inputs or compilation.

Recommend separate approval for **successor source, inert tests and compile-only
checks**. A later baseline needs a matching hash and explicit one-run approval.
No source implementation, rebuild, retry, interruption, scratch mutation or
product configuration change occurred in this review. Final3 remains blocked.

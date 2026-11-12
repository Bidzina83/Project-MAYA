# Standalone Delete-Child ACL Comparison

Design approved. No implementation or execution approval follows.

## Question

Delete-Child-3 rejected the first allow entry because flags 0x03 lacked
the 0x10 inherited marker. Determine whether fresh native creation
reproduces that observation and whether the discrepancy is limited to
inheritance metadata or includes a principal, access mask, entry type,
or other policy difference.

## Experiment

- Use a fresh, isolated NTFS scratch tree on Windows build 26300.9711.
  Do not reuse the retained attempt or touch product state, journal,
  firewall, AppContainer profiles, or tokens. No AppContainer child.
- Reconstruct the sealed state parent policy on the synthetic parent.
  Use a validated synthetic stand-in for the package principal, with
  the original distinct directory and file inheritance entries. Verify
  the parent policy and label before creation. Record the stand-in and
  scratch ancestry as limitations, not exact native-attempt equivalence.
- Create the empty control using the sealed profile's exclusive,
  parent-handle-relative directory creation path. Verify the returned
  handle is the created object, and verify its path, volume, type and
  distinct identity. Read parent and child descriptors by handle
  before any cleanup. No ACL updates after control creation, no
  temporary delete-child grant, and no probe opens as another token.
- Report bounded, ordered ACE summaries: type, flags, exact access mask
  and role (SYSTEM, Administrators, operator, synthetic package or
  unknown). Report owner/group roles, descriptor control flags and
  integrity label. Do not emit raw SIDs or descriptor bytes. Compare
  against the complete expected ACL, preserving the distinction between
  inherit-only and effective entries. An unknown role is never a match.
- Close all owned handles and verify scratch cleanup separately. On
  uncertainty, retain the exact scratch location for review; do not
  retry or change product permissions.

## Decision

| Observation | Next step |
| --- | --- |
| Missing marker reproduced; exact policy matches apart from identified inheritance metadata | Review a narrow full-policy validator for the disposable control. Do not ignore the marker globally. |
| Principal, mask, type, effective rights, owner or label differs | Keep rejecting. Diagnose the specific difference before proposing another control design. |
| Missing marker not reproduced, evidence incomplete, or stand-in prevents comparison | Inconclusive. Do not infer the original ACL or modify the launcher. |

No outcome reclassifies Delete-Child-3 or establishes AppContainer
access, grant restoration, or containment. Next approval: standalone
source preparation and inert tests only. Assembly and native execution
remain separate decisions.

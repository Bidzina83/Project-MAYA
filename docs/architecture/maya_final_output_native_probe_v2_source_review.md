# Native Journal Probe V2 Source Review

Approved successor source, inert checks and compile-only step completed
2026-11-09. No baseline, interruption, MAYA worker, product executable, or VM
run occurred. Original probe and scratch evidence were preserved.

Successor: `.codex-build/maya-final-output-native-probe-v2-20261109/FinalOutputNativeProbeV2.exe`.
Size: 19968 bytes. SHA-256:
`C5C903C4DD8DCFB36EFA6DE67585BDFEACAFE359A4B0A0A7CF9FA2A33C813079`.
Original source and executable still match their recorded hashes.

The successor replaces the same-handle descriptor string comparison with a
bounded structured check. It accepts either order for the same two exact
allow ACEs and compares binary SID identity. The DACL must be present,
non-null and protected, with exactly two ordinary noninheriting allow entries,
current user and SYSTEM, exact mask 0x001f01ff and zero ACE flags. Owner and
group must be the test-user SID. The scoped label must be exactly one Medium
mandatory-label ACE with mask 1 and zero flags. No claim about the full audit
SACL. The native query and creation descriptor remain unchanged. No fallback,
descriptor logging or new rights. Opened-handle, journal, checkpoint, timing
and restart logic are unchanged. The probe's entry type is versioned so it
spawns its own successor image, not the frozen original.

202 inert assertions passed. Cases cover both ACE orders, equivalent binary
SID, owner/group and DACL control, missing/extra/duplicate ACEs, deny/object/
callback/inherited entries, wrong rights or label, invalid offsets, and every
truncated prefix of the valid fixture. Warnings-as-errors compilation passed.
The inert runner does not call the probe or native descriptor query. Native
serialization and descriptor compatibility remain unverified; the original
blocking comparison's exact cause is not proven.

Next gate: matching guest EXE path/hash, same approved scratch root, and a
separate explicit one-baseline approval. The successor creates a fresh attempt
folder; do not reuse or alter the blocked attempt. No interruption is approved.
Final3 remains blocked and no product qualification changes.

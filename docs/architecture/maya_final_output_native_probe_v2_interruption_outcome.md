# Native Journal Probe V2 Interruption Outcome

Operator-reported VM result for the separately approved single `fake-accepted`
case of the previously hash-verified V2 executable. Windows 26300.9711, local
NTFS, `admin_role=True`. Scratch attempt
`MayaJournalProbe-798d6ba8b5b3406cb187b06c6761af7a` under the approved root.
Reported reopened identity `7a12254e0009000000004753`, 78 bytes,
`classification=unknown_or_invalid`, exit code 0.

The probe reported success for its controlled checkpoint after fake acceptance
and before confirmation. Under the verified source path, exit zero requires a
matched checkpoint, termination of only the launched helper, expected exit
status, and independent read-only reopen with matching identity and exact
intent-only bytes. This is the expected conservative result: the intent survived
the tested process stop, but the journal cannot establish delivery and grants
no authority. The probe has no replay path; no real output was published.

The result covers this checkpoint, token, build and volume only. It does not
establish power-loss durability, all interruption or adversarial handle cases,
production worker/seal provenance, real sink semantics or product qualification.
See `maya_final_output_native_probe_v2_baseline_outcome.md` for the separate
normal-close result. Keep all scratch evidence. This run allowance is consumed;
no retry, additional interruption, cleanup mutation or product execution is
authorized. Final3 remains blocked. Next recommendation: review which journal
checks can carry into a product adapter and which need further native evidence
before source or packaging approval.

# Native Journal Probe V2 Baseline Outcome

Operator-reported 2026-11-09, under the approved single baseline allowance.
The guest path was `D:\FinalOutputNativeProbeV2.exe` and the reported hash
matched `C5C903C4DD8DCFB36EFA6DE67585BDFEACAFE359A4B0A0A7CF9FA2A33C813079`.
The probe reported build 26300.9711, local NTFS, and `admin_role=True`.
Scratch attempt: `MayaJournalProbe-a1cc5d015b674a72808ab7f34b4675da` under the
approved `C:\Users\Bidzina\AppData\Local\MayaJournalProbeScratch` root.

Reported opened identity `7a12254e00040000000056fd`, 160 bytes,
`classification=confirmed_as_recorded`, exit code 0. The normal-close path
passed the probe's descriptor, same-handle append/flush/readback, natural
helper exit, and independent read-only reopen identity/byte checks as reported.
The effect was synthetic. This does not prove the exact V1 mismatch cause,
negative handle tests, process-interruption persistence, power-loss durability,
worker integration, or production qualification. Final3 remains blocked.

Preserve both scratch attempts. The baseline allowance is consumed. Recommend
separate exact-artifact approval for one `fake-accepted` interruption: stop only
the launched probe helper after its matched checkpoint, with flushed intent and
before confirmation. Expect a fresh attempt, intent-only journal, and
`unknown_or_invalid` classification with no replay. No interruption or retry
is authorized by this record.

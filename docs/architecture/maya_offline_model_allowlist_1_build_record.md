# M07c Allowlist 1 Build Record

Sealed 2026-11-03 after offline assembly approval. Candidate
0.2.1-offline-allowlist.1, file version 0.2.1.18, HERMES_MODEL_ALLOWLIST.
No product, bundled runtime, or VM execution.

Build: .codex-build/maya-offline-model-allowlist-20261103-1.
ZIP: Maya-Offline-Model-Allowlist-1.zip, 53017240 bytes.
SHA256: 99633849593C29ABC879F6970ADDCF020CE77445885AC10AAEA3A017772034DA.
EXE: MayaProtectedPython.exe, 54562304 bytes.
SHA256: EFB3F5CAB3BF4E0E0511C8575CAC6E0EA9D239E32F3EEAAA50B7F56D0ABFCEB9.

Actual-profile admission verified all 6786 payload entries. Six replacements,
three additions and two omissions; 6777 immediate predecessor entries remained
byte-identical. Only model_oversized_child_entry.py and
model_oversized_worker_entry.py were omitted from the new payload.
Canonical helpers, runtime dependencies and frozen predecessors were retained.
Independent verification checked 90 archive entries, 361 frozen source entries,
and the embedded payload and index.

429 Python tests and 1796 subtests passed, with the existing pytest cache_dir
warning. C# fixtures passed for M07c and 15 prior profiles; 19 invalid profile
combinations were excluded. Reader checks passed: 163 assertions in 13 cases.

Extract into a fresh guest directory and report the executable path and SHA256.
Do not launch until separate exact-artifact one-run approval and fresh consent.
Expected status: offline_model_response_allowlist_rejected_pending_independent_cleanup.
No qualification is implied; Gate A remains open.

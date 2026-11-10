# Coordinator Journal Native Baseline Source Review

Source, compile-only and injected checks completed 2026-11-10. The native
harness was compiled but not launched. No product or VM run occurred.

Artifact: `.codex-build/maya-coordinator-journal-native-baseline-20261110/CoordinatorJournalNativeBaseline.exe`.
x64 console, 275456 bytes. SHA-256:
`ADBDC82A2CFC78BE9808CF4A3A9A271695DC6885B9417684577C964700DBFFEF`.

The standalone entry accepts only `--baseline` and the exact existing scratch
root `C:\Users\Bidzina\AppData\Local\MayaJournalProbeScratch`. It requires
Windows build 26300.9711, the expected operator SID, elevated High-integrity
token and enabled Administrators group; it cannot self-elevate. Scratch setup
pins the ancestor chain and uses an exclusive fresh GUID directory, exact
Administrators/SYSTEM descriptor and fixed journal leaf. It reports the planned
attempt path before creation and does not remove or repair artifacts.

Both the candidate and native transport share their existing implementation
with a scratch-only constructor gated by the second compile symbol. Normal
constructors retain the product-root binding. The scratch target cannot accept
the product root or a caller-selected journal path. The baseline writes only
synthetic intent and pre-effect stop, checks independently constructed bytes,
closes the writer, and validates the exact bytes, identity and descriptor
through a separate read-only open while retaining the parent handles. There is
no worker, subprocess, sink, interruption, restart writer, or publication.

1389 injected harness assertions and both normal/inert-only compile exclusions
passed. Previous 833 coordinator and 219 adapter C# assertions and 108 focused
Python tests passed. Only fixture entry points ran; actual token admission,
descriptor round-trip and native journal I/O remain unverified. Final3, its
401 frozen entries, 167 original product files and V2 probe were rehashed intact.

Next gate: provide the exact guest path and matching SHA-256, reconfirm the
existing scratch root, and obtain explicit approval for one baseline run on the
VM. Do not reuse the previous V2 approval or run any token-negative or
interruption case. No package, product integration or qualification occurred.
Final3 remains blocked.

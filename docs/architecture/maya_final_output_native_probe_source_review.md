# Native Journal Probe Source Review

Standalone source and compile-only step completed 2026-11-09. The probe has
not run. See `maya_final_output_native_probe_plan.md` for the approved design.

Source: `tests/windows_final_output_native_probe.cs`.
Source SHA-256: `78DA86E1EC7A312DE0F2199D738E14DAC1D433436B36026003E1A1349126F431`.
Compiled x64 console fixture: `.codex-build/maya-final-output-native-probe-20261109/FinalOutputNativeProbe.exe`, 17408 bytes.
Executable SHA-256: `37669A3F955F2F18A3F2D339FBBCB6EEA0A6BE415A9BD17FBAFD9EEFF701D2B5`.
The adjacent `compile.ps1` compiles only this source, with warnings as errors.

The source accepts a dedicated, existing local NTFS scratch root named
`MayaJournalProbeScratch`, rejects the current product root subtree, and
exclusively creates a fresh attempt folder and fixed journal leaf. It pins the
directory chain and checks opened identity, no reparse, single file link, bounds,
noninheritance and a protected descriptor. Probe-only descriptor: current user
SID as owner and group, two explicit noninheriting file/directory full-access
allow ACEs for that SID and SYSTEM, and Medium no-write-up. It requests no new
privileges. An unsupported descriptor, open or label query blocks; there is no
fallback. The implementation uses handle-based descriptor retrieval; see
[GetSecurityInfo](https://learn.microsoft.com/windows/win32/api/aclapi/nf-aclapi-getsecurityinfo)
and [security descriptor string format](https://learn.microsoft.com/windows/win32/secauthz/security-descriptor-string-format).
Whether the exact descriptor is accepted and round-trips on the target token and
volume is unverified. The experiment trusts the test principal and administrators.

The helper writes only synthetic records, flushes and verifies bytes on the
same handle, and reports the opened ID through the supervisor's private pipe.
The supervisor opens read-only after the helper exits, verifies matching ID and
descriptor, and compares the full journal against its independently derived
expected bytes. Baseline closes normally; an explicitly selected interruption
case can terminate only the launched helper's retained process handle after a
matching checkpoint. No retry or authority restoration exists. The fake effect
is a checkpoint boolean, not an external publication. Partial writes are
deliberately flushed prefixes, not evidence of spontaneous torn writes. The
probe retains its scratch evidence and performs no deletion.

Compile and static checks only. Neither a baseline nor an interruption case ran.
The probe does not yet generate competing opens, links, or malformed ACL fixtures;
those cases require separately reviewed test setup. No native assurance about
ancestor pinning, sharing, descriptor normalization, flush survival, worker
identity, production journal semantics or power loss follows from compilation.
No runtime file, VM, policy, security setting, product profile or release package
changed. Final3 remains blocked and all qualification flags are unchanged.

Next gate: exact EXE hash, explicit existing scratch-root path and approval of
one baseline execution without interruption. Do not use an interruption mode
until the baseline evidence is reviewed and that case is separately approved.

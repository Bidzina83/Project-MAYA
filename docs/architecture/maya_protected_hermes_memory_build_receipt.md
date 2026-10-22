# Protected Hermes Native Memory 1 Build Receipt

## Prepared Artifact

2026-10-22: approved offline preparation completed; no product/Hermes native
launch, VM execution or workstation security provisioning occurred. Inert
fixture executables ran without invoking native product security functions.
See maya_protected_hermes_memory_handoff.md for disclosed behavior and limits.

Build directory: .codex-build/maya-protected-hermes-memory-20261022-1.

- Maya-Protected-Hermes-Memory-1.zip: 52,741,247 bytes;
  SHA256 2B03C44212C3572051FA5E4D9361B38BC81A80E960C44CE33DDD9D9EA7A040FE.
- MayaProtectedPython.exe: 54,208,000 bytes;
  SHA256 D05531830EEBBD15F4682EB6F1558A802C76C9642C7DB0227CEDC5E03C675647.
- Version 0.1.4-hermes-memory.1; scope offline-hermes-native-memory-v1.
- Payload: 6,692 files, 143,265,179 expanded bytes, 953,406 index bytes.
- Payload ZIP SHA256
  A2D368EE3ED1A2BAB86AD4B5E102BB928DCC1272C0F62AA6C41162E82C7DCCC7.
- Payload index SHA256
  E90CC591D2EF0B1F28A6792A05AE60A7FECA4A97FE04114D3D29741530243C3F.
- Memory config SHA256
  CA42EE52EDEA728C14EA83BCF6B1CF61FDF72EE98195F762F4666DBAE4234F44.

All 6,689 Session State 1 payload members retain identical bytes. Only
hermes_memory_check.py, hermes-memory-config.json and hermes-memory-contract.json
are added. Python 3.13.14, Hermes commit
b13e2fd6948a59eeb59fe618914147d97a2ee90a, all 63 dependencies and notices remain.
The frozen State 1 ZIP/EXE and payload-index hashes were checked before reuse.
Earlier artifacts were not overwritten. No download or runtime patch occurred.

## Source Verification

Packaged tools/memory_tool.py, agent/agent_init.py, hermes_cli/config.py and
utils.py match retained baseline source bytes and baseline manifest hashes.
The memory module SHA256 is
587E73A30BE3433A3DF5B979ABB91796C91C468B68590331D91CC27F5959AC05.
AST checks bind nine used MemoryStore interfaces, native constructor defaults
2200/1375, static path resolution and context-managed lock decorators. No
Hermes, SDK or bundled native module was imported for this verification.

Static inspection also verified native snapshot semantics, Windows lock branch,
write/fsync/replace sequence, result keys and supported memory flags. Hermes
bootstrap can create an empty memories directory; freshness is checked before
imports and content absence checked before construction. This avoids treating
normal native setup as preexisting customer memory. No Windows compatibility,
lock-release behavior or persistence is inferred from these static checks.

## Verification

- All 83 Python unit/static cases passed, including 14 new memory cases.
  Fixtures use synthetic interface-shaped doubles and temporary fixture files,
  never the bundled runtime. They cover eight-mutation success, supported
  constructor arguments, empty bootstrap directory, existing-file rejection,
  missing store/flags/locking, false mutation success, empty file readback,
  snapshot/hash mismatch, lock failure, residue/size limits and cleanup calls.
  Sandbox Temp permissions blocked the first run; the explicitly approved
  out-of-sandbox inert rerun passed without changing product permissions.
- All 711 inert C# checks passed: 231 startup, 118 containment reporting,
  62 UDP, 29 import, 48 construction, 96 session-state and 127 native-memory
  admission/path/version checks. Missing predicates, wrong Boolean types,
  partial mutations, bad origins/paths, wrong nonce/hashes, size violations,
  closure failure and construction-only reports cannot satisfy memory admission.
- Optimized x64 product/fixture compilation passed with warnings as errors.
  GUI/x64 PE headers and both exact length-prefixed embedded resources were
  verified as bytes without loading or launching the product assembly.
- Every old payload member was size/hash verified before reuse. Every final
  payload and package member matches expected bytes. All 90 package files
  including manifest and 34 frozen source/document files were verified.
  The immutable package manifest and source freeze remain in this build.
- Coupled-context validation and diff whitespace checks passed. No complete
  final-tree extraction/rehash or native startup timing test is claimed.
  Unchanged extraction controls retain prior fixture coverage; this package
  received complete archive/resource/member verification instead.

## Remaining Gates

The approved next step is artifact/impact review, not an automatic VM launch.
Transfer/extract the complete package, verify EXE identity, then obtain separate
one-run approval and fresh product consent. No manual OS conditioning, model
traffic, customer data, new grant, runtime correction or retry is authorized.

Only native synthetic memory compatibility is being tested. It does not qualify
the tool-facing approval wrapper, authoritative memory, concurrent writers,
atomic/crash/restart durability, governed full Hermes operation or containment.
Independent cleanup, profile removal and journal-less recovery remain open.
All qualification flags stay False; Gate A and production activation stay blocked.

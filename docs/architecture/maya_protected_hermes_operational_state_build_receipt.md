# Protected Hermes Session State 1 Build Receipt

## Approved Scope

Prepared on 2026-10-22 after the user's explicit approval of the bounded native
session-persistence proposal. See maya_protected_hermes_operational_state_handoff.md
for exact behavior, private file impact, unchanged restrictions and stop rules.
No native Maya/Hermes payload, SDK, bundled dependency or SQLite library was
executed locally. No VM access, security provisioning or dependency installation
occurred. Preparation is not exact-artifact VM-run approval.

## Artifact Identity

Directory: .codex-build/maya-protected-hermes-state-20261022-1.

- Maya-Protected-Hermes-State-1.zip: 52,734,233 bytes;
  SHA256 A62FA17D64ACBA7D1719E884F4AB150BECDFFBB73B28D07254FA02BE94E14A37.
- MayaProtectedPython.exe: 54,195,712 bytes;
  SHA256 E508C0CBF0340683593F77FFC75A4F3BD31A1F84C83D0A6152AD11CD933A7524.
- Version 0.1.3-hermes-state.1; scope offline-hermes-session-state-v1.
- Payload: 6,689 files, 143,242,946 expanded bytes, 953,032 index bytes.
  All 6,687 Construction 2 members retain their bytes. Only
  hermes_state_check.py and hermes-state-contract.json are added.
- Fixed config SHA256 remains
  945AB88A564268203AF4ADFE4186BC48452F292FEC1DF84D45B945810ABEBB73.

Python 3.13.14, Hermes commit b13e2fd6948a59eeb59fe618914147d97a2ee90a,
all 63 dependencies and licenses/notices are unchanged. The existing payload
already includes python/DLLs/_sqlite3.pyd and python/DLLs/sqlite3.dll.
No binary download, repair, source patch or alternative store is introduced.
Construction 2's ZIP/EXE hashes were rechecked and its files were not overwritten.

## Source And Interface Verification

The actual packaged hermes/hermes_state.py matches the retained baseline source
and its pinned manifest SHA256:
2092D272D091C297E8B51429D8A635D13ED12AA2D607384119241991ADE63797.
Its SessionDB constructor and eight used methods were inspected as AST, without
runtime imports, to bind parameter names, keyword use and the read_only default.
Schema fields, message counters/order and closure behavior were inspected in
source. No hand-written schema or native-memory substitute is used.

The product creates one writer SessionDB instance and one subsequent read-only
SessionDB instance. Native schema reconciliation also creates and closes its
own transient :memory: SQLite connection to parse the pinned schema; this is
not another persistent store or a second test process. The 32 MiB acceptance
ceiling concerns the four disclosed on-disk SQLite files, not total process
memory or a filesystem quota. No memory/resource-limit qualification is implied.

## Verification Results

- Sixty-nine Python unit/static checks passed. The state tests use inert
  native-interface-shaped doubles, not a runtime substitute shipped in the
  package. They cover success, wrong path/read-only binding, pre-existing DB,
  DELETE mode, constructor/write/session-end/reopen failures, corrupt readback,
  still-open connection, size/peak limits and report bounds. A sandbox Temp
  permission failure was resolved by an explicitly approved out-of-sandbox
  unit-test run; its temporary synthetic files are ordinary fixture bytes,
  not native SQLite execution or security setup.
- All 584 inert C# checks passed: 231 startup, 118 containment reporting,
  62 UDP, 29 import, 48 construction and 96 state admission/path checks.
  Missing/wrong fields, partial construction-only reports, wrong nonce/session,
  fallback journal, bad path/origin/counts, wrong Boolean types, cleanup failure
  and size boundaries cannot satisfy state admission.
- Optimized x64 warnings-as-errors product and fixture builds passed. GUI/x64
  PE headers and both exact length-prefixed embedded resources were verified as
  bytes without loading the product assembly.
- Assembly rechecked every old payload member before reuse. Every final payload
  member and final archive member matches its expected size/hash or source
  bytes. All 90 final package files and 29 frozen source/document files match.
  The source freeze and package manifest remain inside this separate build.
- Context validation and diff whitespace checks passed. No full final-tree
  extraction/rehash, native database run or startup-timing test is claimed;
  unchanged extraction controls are covered by prior fixtures and current
  archive/resource/member checks. Native persistent state remains the VM test.

## Remaining Gates

Obtain separate approval for one matching-hash RDP VM attempt and fresh product
consent. Existing AppContainer/WFP boundaries, token/job controls, configuration,
deadlines and output limits stay unchanged. No model traffic, customer data,
MEMORY.md/USER.md or governed external action is authorized by preparation.

All production, containment and independent-cleanup flags remain False. Success
would mean only same-process native session close/reopen persistence for this
exact synthetic fixture. It would not establish restart/crash durability, full
search, full Hermes operation, governance, connectors, Metabase or Gate A.
Stop at a failed result; no new grant, timeout increase, fallback, runtime patch
or automatic retry follows.

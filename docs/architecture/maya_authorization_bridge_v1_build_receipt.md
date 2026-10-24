# Authorization Bridge Document 1 Build Receipt

## Frozen Candidate

2026-10-23: approved implementation/offline preparation and ten-case correction.
No product/Hermes process, native security setup or VM run occurred. Only inert
fixture executables and ordinary local unit tests were executed.

Build: .codex-build/maya-authorization-bridge-20261023-1.
Version 0.2.0-bridge-document.1; scope offline-authorized-document-bridge-v1.

- Maya-Authorization-Bridge-Document-1.zip: 52,921,634 bytes;
  SHA256 070266BEE1A37D0488A762C856FE846D6DEFDF28C2CF7FF9A6C85AF9ADFE8367.
- MayaProtectedPython.exe: 54,407,168 bytes;
  SHA256 1B8C850C4D99CBCB672C6B75CDBA12E4EACA4C34C929A1EFAA9F598A9A9390EC.
- Payload: 6,757 files, 143,919,092 expanded bytes, 961,973 index bytes.
- Payload ZIP SHA256
  ECD7CF55E11523DD31EABE6281B2A6F59BB0FA154A1961E04744B9C31F5F0AA1.
- Payload index SHA256
  976A585FDD419EB3ABDDE7EC31F2EB34A5441C5E783F649F49487B4538F0E52C.
- Construction config remains
  945AB88A564268203AF4ADFE4186BC48452F292FEC1DF84D45B945810ABEBB73.

The ZIP has the normal Maya-Authorization-Bridge-Document-1 root. The local
final staging directory has a -final suffix. Earlier unpublished compilation/
staging outputs are not the artifact identified above. Do not use their hashes.
The separate source-freeze and manifest bind 109 source/document/test files;
all 90 package files including manifest were verified against expected hashes.
This receipt is outside that freeze to avoid a circular artifact hash.

## Source And Dependencies

Every one of the 6,692 frozen Native Memory 1 members is unchanged and rechecked
by size/hash before reuse. Add canonical project_maya Python sources, two bridge
entries and the bridge contract. Every new canonical source member matches the
current source bytes. Native tools/registry.py, toolsets.py, model_tools.py and
agent/agent_init.py match retained unmodified baseline source/manifest hashes;
registry registration/dispatch parameters were bound using AST inspection.

Hermes pin b13e2fd6948a59eeb59fe618914147d97a2ee90a, Python 3.13.14 and all
63 dependency versions/notices remain. No wheel acquisition, pin change, system
Python installation or Hermes patch. Recursive eager-import inspection of the
canonical host package identified cryptography, already pinned at 46.0.7 with
existing cffi 2.0.0/pycparser 3.0. Worker startup verifies these origins/versions
and rejects a missing crypto implementation rather than using its optional
fallback. Host native import compatibility is still unproven until the VM run.

## Verification

- 138 Python checks passed: 37 bridge-core, 12 worker/client/transport/handle
  integration fixtures, 83 prior Windows component cases and six existing audit
  regressions. Windows temporary-file regressions used explicitly approved
  out-of-sandbox runs after sandbox Temp permission failures. New bridge fixtures
  use synthetic data, mocked native APIs/I/O and the real gateway/audit/protocol
  code, not a product substitute or bundled Hermes/SDK execution.
- 845 inert C# checks passed: 711 prior startup/containment/UDP/import/construction/
  SQLite/memory cases plus 134 bridge codec/descriptor/audit cases. The new checks
  cover strict JSON/Unicode, byte framing, truncated EOF, blocked I/O bounds,
  exact private descriptors, payload path/version selection and complete 21-event
  audit admission with missing/wrong target/actor/digest/record rejection.
- The first codec run found the platform JSON reader normalizing an unpaired
  escaped surrogate. Explicit Unicode escape-pair validation corrected it;
  invalid data is rejected, not normalized into accepted protocol text.
- The fixed ten-case worker schedule passes with inert channels, actual policy
  engine and state machine: two reads and one prepared release. Prepared worker
  counters are not presented as actual child delivery; native coordinator pipe
  writes, child digest receipts and subsequent durable outcome acknowledgments
  are separate required checks.
- Optimized x64 warnings-as-errors product and fixture compilation passed.
  GUI/x64 headers and both exact length-prefixed embedded resources were verified
  as bytes without loading or launching the product assembly.
- Every final payload member and every final package member was reverified.
  Frozen source/current-source and package-file hashes match. Coupled context
  validation and whitespace checks passed. No full final-tree extractor/rehash
  or native timing/security/process fault qualification is claimed; unchanged
  extraction retains prior fixture coverage plus current archive/resource checks.

## Native Gate

Review maya_authorization_bridge_v1_handoff.md and the exact matching artifact
before one separately approved RDP attempt and product-owned informed consent.
The approved first-run schedule is the ten-case successor, not the preserved
twelve-case design. N09/N11 remain local mandatory audit faults; native audit
failure/recovery and broader lifecycle/crash/adversarial coverage remain open.

This candidate adds one trusted medium worker/job, host-only folder/ACLs, private
duplex protocol and required audit. The worker is not covered by the child's WFP
denies. Existing child AppContainer/capabilities/network-deny/token/job restrictions
remain; no network permit, loopback exception or registry permission is added.
Do not manually condition Windows. Stop at the first failed/unexpected result;
no correction, timeout change, recovery or retry follows automatically.

Native process/handle/DACL/crypto/tool compatibility, timing and cleanup are
unproven. Independent post-run checks remain required. A successful fixture run
does not close Gate A or qualify model mediation, authoritative state, arbitrary
customer-file isolation, connectors, Metabase or production. All production,
containment and independent-cleanup qualification flags remain False.

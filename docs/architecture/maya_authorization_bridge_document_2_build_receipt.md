# Authorization Bridge Document 2 Build Receipt

2026-10-23: user approved only the narrow file/directory label correction,
inert regression checks and separate offline package preparation. Document 1
attempt 3e7ecf7926ae44a290741c01107808e5 and its frozen artifacts are preserved.
See maya_authorization_bridge_document_2_handoff.md for the result and scope.

## Exact Artifacts

Build directory: .codex-build/maya-authorization-bridge-20261023-2.
Version: 0.2.0-bridge-document.2.
Scope: offline-authorized-document-bridge-v1.

- Maya-Authorization-Bridge-Document-2.zip: 52,922,159 bytes;
  SHA256 8D57DCCB50AC584975B012BBA791E3F046B1BBC3EF79EBF75BA8A347EC2F0B37.
- MayaProtectedPython.exe: 54,407,168 bytes;
  SHA256 6D4F22DC0CAA1EE83502B51B9FCB24890EA701A17B2819C5B4AA246F4444D21D.
- Payload ZIP SHA256:
  ECD7CF55E11523DD31EABE6281B2A6F59BB0FA154A1961E04744B9C31F5F0AA1.
- Payload index SHA256:
  976A585FDD419EB3ABDDE7EC31F2EB34A5441C5E783F649F49487B4538F0E52C.

Both payload resources are identical to Document 1: 6,757 members, 143,919,092
expanded bytes and 961,973 index bytes. No Python source, dependency, Hermes
patch, policy, protocol, capability, WFP filter or deadline changed. Source
changes are the label object-type handling/readback, version and label fixtures;
context/handoff records and a separate package manifest describe the correction.

## Verification

- Optimized warnings-as-errors x64 product and inert fixture compilation passed.
- 154 inert bridge C# checks passed, including 20 new label cases. The pure
  descriptor verifier is exercised without filesystem label/security APIs.
- 132 Python cases and 37 subtests passed across bridge and prior Windows
  components. Initial sandbox Temp permission failures were resolved by the
  approved out-of-sandbox rerun; a pytest cache-write warning remained.
- Byte-only x64 GUI PE header and exact embedded resource checks passed without
  loading or executing the product assembly. Every payload/package member was
  checked by the offline packager; current canonical payload Python matches.
- Coupled context validation and git diff whitespace check passed.
- Source freeze and package manifest were generated in the separate build;
  this receipt is outside the freeze to avoid circular hashes.

No product, Hermes, SDK, native security setup or VM execution occurred during
preparation. Fixture success does not qualify actual Windows label behavior,
worker setup, containment or cleanup. Document 1 cleanup remains product-reported;
independent scoped checks are pending before another VM attempt. Document 2
requires separate exact-artifact VM-run approval and fresh product consent.
Do not manually change Windows permissions, retry automatically or broaden
the correction. Gate A and all qualification flags remain unchanged.

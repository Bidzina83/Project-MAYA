# Phase 6 Production Distribution

## Objective

Project MAYA Phase 6 turns the existing installed-package, setup, health,
backup, restore, migration, broker, and update-readiness surfaces into a
signed production distribution contract.

The first advertised platform is Windows desktop. macOS, Linux, server, and
container artifacts remain not advertised until their own installer,
lifecycle, health, backup, restore, update, rollback, and clean-install
qualification passes.

## Release Contract

Phase 6 release metadata is canonical JSON signed with Ed25519. Runtime update
verification uses trusted public keys only. Production private signing keys
must be supplied by release infrastructure and must not be committed.

Required metadata includes:

- release manifest with artifact list, SBOM reference, provenance reference,
  platform qualification, and offline Enterprise bundle metadata;
- update manifest with platform, version, artifact checksum, SBOM reference,
  provenance reference, migration compatibility, rollback reference, and
  release-manifest reference;
- rollback manifest with platform, previous artifact checksum, SBOM reference,
  provenance reference, migration compatibility, and release-manifest
  reference.

Unsigned, tampered, wrong-key, wrong-platform, incomplete, or unsupported
metadata is rejected. `maya update --check` and `maya update --rollback`
remain non-mutating and network-free.

## Tooling

Release tooling is script-level rather than runtime brain:

```text
scripts/build_phase6_release.py --version <version> --platform windows-desktop --out <dir>
scripts/verify_phase6_release.py --release-dir <dir> --platform windows-desktop
```

The builder creates a deterministic release directory containing a built wheel,
a Windows payload bundle, Standard and Enterprise Inno Setup installer sources,
an Inno installer manifest, SBOM, provenance, signed release manifest, signed
update manifest, and signed rollback manifest.

If `ISCC.exe` is supplied through `--inno-compiler`, the builder may also
compile native Inno Setup `.exe` installers. Production `.exe` installers
must be Authenticode-signed through release infrastructure by passing
`--signtool` plus exactly one certificate selector, either `--sign-cert-sha1`
or `--sign-cert-subject`. Private certificate material and passwords are never
stored in this repository.

For local smoke testing only, `--allow-unsigned-installers` permits compiled
installers to remain unsigned. That mode does not satisfy Windows desktop
release qualification and may be blocked by Smart App Control. The builder
never installs Inno Setup, Python, system dependencies, services, OAuth grants,
or customer tenant resources.

The verifier checks signatures, checksums, SBOM/provenance presence, Inno
installer products, installer-bundle boundaries, packaged launcher startup,
and that compiled Windows installers are trusted by Authenticode. Unsigned or
untrusted compiled `.exe` installers fail verification.

## Boundaries

Phase 6 does not add automatic background updates, silent installer execution,
system dependency installation, customer tenant resource creation, or platform
support claims beyond the qualified Windows desktop artifact.

The Phase 5 external independent security review remains a pre-production and
customer-readiness gate.

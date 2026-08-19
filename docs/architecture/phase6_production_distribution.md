# Phase 6 Production Distribution

## Objective

Project MAYA Phase 6 turns the existing installed-package, setup, health,
backup, restore, migration, broker, and update-readiness surfaces into a
signed production distribution contract. The current Windows work is a staged
production-installer payload, not a completed Windows desktop support claim.

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
a managed Windows payload layout, Standard and Enterprise Inno Setup installer
sources, an Inno installer manifest, SBOM, provenance, signed release manifest,
signed update manifest, and signed rollback manifest.

For production Standard qualification, the builder consumes prepared runtime
artifacts rather than silently downloading or installing system software. The
artifact inputs are a Maya-managed Python runtime directory, a pinned Hermes
Agent wheel built from the compatible commit, optional curated Maya skills
overlay source and allowlist, and a prepared heavy-dependency artifact
directory for Metabase, Java, LibreOffice, and optional Poppler. The resulting
payload records hashes, provenance-oriented manifests, and whether the build is
`production` or `local_smoke_blocked`.

The Windows Standard payload is required to contain product-level structure
rather than thin command wrappers:

```text
windows-app-payload/
  app/
  runtime/
  wheels/
  skills/
  services/
  config-templates/
  scripts/
  release/
  bin/
```

The payload includes the built `project_maya` artifact, the pinned Hermes Agent
runtime artifact when supplied, Maya-owned setup, doctor, health, backup,
restore, migration, update, broker/messaging, Metabase/document integration
code, starter Standard configuration templates, first-run setup scripts,
qualification scripts, curated skills metadata, managed-service metadata, and
release metadata. If the pinned Hermes runtime artifact or profile-specific
heavy dependency is not actually present or configured, setup and doctor must
report a blocked readiness item. They must not report the product as healthy.

Standard setup selects Maya's `local_vector` SQLite backend, installs the
Maya-owned provider through Hermes' supported local plugin directory and
selects external provider `maya` without replacing Hermes session storage,
`MEMORY.md`, or `USER.md`. Installed
qualification must prove both public Hermes provider discovery and governed
SQLite read/write. Semantic qualification additionally requires a pinned local
ONNX embedding model and native runtime wheels. A payload using `local_json`,
an unavailable Maya provider, or a non-governed memory configuration fails or
remains blocked.

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
installer products, installer-bundle boundaries, managed payload layout,
product shortcuts, installed qualification commands, secret-safe output, and
that compiled Windows installers are trusted by Authenticode. Unsigned or
untrusted compiled `.exe` installers fail verification.

Release-artifact smoke means the built payload can start and run non-mutating
qualification commands from the release directory. Production Windows desktop
qualification remains stricter: the compiled installer must be
Authenticode-signed and clean-install lifecycle, health, backup, restore,
migration, update, rollback, setup, and start checks must pass on a supported
Windows machine with the required managed runtime artifacts.

## Boundaries

Phase 6 does not add automatic background updates, silent installer execution,
system dependency installation, customer tenant resource creation, or platform
support claims beyond the qualified Windows desktop artifact.

The Phase 5 external independent security review remains a pre-production and
customer-readiness gate.

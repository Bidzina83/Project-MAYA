# Phase 6 Production Distribution Closure

## Status

Implementation complete for signed Phase 6 release metadata, Windows desktop
release-bundle generation, Standard and Enterprise Inno Setup product sources,
signed update and rollback verification, platform support boundary reporting,
package verification, and tests.

## Evidence

| Step | Evidence |
| --- | --- |
| 1. Release metadata contracts | `src/project_maya/release.py`, `tests/test_phase6_release.py` |
| 2. Signed update and rollback verification | `src/project_maya/update.py`, `tests/test_phase1_update.py` |
| 3. Windows desktop Inno release tooling | `scripts/build_phase6_release.py`, `scripts/verify_phase6_release.py` |
| 4. Platform boundary diagnostics | `src/project_maya/doctor.py`, `src/project_maya/health.py` |
| 5. Installed package surface | `scripts/verify_phase1_package.py` |
| 6. Scope and closure docs | `docs/architecture/phase6_production_distribution.md`, `docs/architecture/phase6_production_distribution_closure.md` |

## Completed Surfaces

- Release, update, and rollback manifests use canonical JSON and Ed25519
  signatures.
- Runtime verification uses public keys only; committed test signing material
  is explicitly non-production.
- The release builder emits Standard and Enterprise Inno Setup `.iss` products
  and an Inno installer manifest. Native `.exe` compilation runs only when a
  caller supplies an available `ISCC.exe`.
- `maya update --check` and `maya update --rollback` reject unsigned,
  tampered, incomplete, wrong-key, and unsupported-platform metadata without
  network use or mutation.
- Windows desktop is the only advertised Phase 6 platform.
- macOS, Linux, server, and container artifacts remain not advertised until
  full qualification passes.
- The release verifier checks SBOM, provenance, checksums, Inno Setup product
  sources, installer-bundle boundaries, and built-artifact installation.

## Known Limits

Phase 6 does not:

- execute automatic background updates;
- silently install system dependencies;
- create customer tenant resources;
- install Inno Setup or compiler toolchains;
- claim macOS, Linux, server, or container support;
- replace the deferred external independent security review gate.

# Phase 6 Production Distribution Closure

## Status

Implementation complete for signed Phase 6 release metadata, Windows
release-bundle generation, Standard and Enterprise Inno Setup product sources,
signed update and rollback verification, platform support boundary reporting,
package verification, and staged managed-payload tests.

The previous Inno Setup output was a release-artifact smoke installer: it
installed metadata, an unpacked `project_maya` payload, and thin command
launchers. That shape is not a production-quality Maya Standard installer and
does not satisfy the product specification by itself.

The current staged payload now includes a managed product layout, starter
Standard configuration template, first-run setup script, product shortcuts,
runtime and wheel metadata, curated-skills and managed-service manifests, and
installed qualification checks. The builder can now consume prepared managed
Python, Hermes, heavy dependency, and skills-overlay artifacts and records
whether the result is `production` or `local_smoke_blocked`. It still must be
run with real release-approved artifacts and pass clean-install Windows
qualification before Windows desktop support is claimed.

Windows desktop production qualification remains open until compiled Inno
Setup `.exe` installers are Authenticode-signed with release-infrastructure
certificate material and pass clean install, lifecycle, backup, restore,
update, and rollback qualification. Smart App Control blocking an unsigned
installer is treated as valid evidence that the production exit gate is not
met.

## Evidence

| Step | Evidence |
| --- | --- |
| 1. Release metadata contracts | `src/project_maya/release.py`, `tests/test_phase6_release.py` |
| 2. Signed update and rollback verification | `src/project_maya/update.py`, `tests/test_phase1_update.py` |
| 3. Windows desktop Inno release tooling and staged managed payload | `scripts/build_phase6_release.py`, `scripts/verify_phase6_release.py` |
| 4. Platform boundary diagnostics | `src/project_maya/doctor.py`, `src/project_maya/health.py` |
| 5. Installed package surface | `scripts/verify_phase1_package.py` |
| 6. Scope and closure docs | `docs/architecture/phase6_production_distribution.md`, `docs/architecture/phase6_production_distribution_closure.md` |

## Completed Surfaces

- Release, update, and rollback manifests use canonical JSON and Ed25519
  signatures.
- Runtime verification uses public keys only; committed test signing material
  is explicitly non-production.
- The release builder emits a staged Windows payload with `app/`, `runtime/`,
  `wheels/`, `skills/`, `services/`, `config-templates/`, `scripts/`,
  `release/`, and `bin/`, plus Standard and Enterprise Inno Setup `.iss`
  products and an Inno installer manifest. Native `.exe` compilation runs only
  when a caller supplies an available `ISCC.exe`.
- The builder accepts prepared artifact inputs for a managed Python runtime,
  the pinned Hermes Agent wheel, heavy dependency artifacts, and a curated Maya
  skills overlay. Missing runtime-heavy artifacts are recorded as blocked
  readiness and local-smoke status, not healthy operation.
- Windows shortcuts now target product actions: Setup Maya, Start Maya, Maya
  Doctor, installed qualification, and the Maya data folder. They are not a
  replacement for the guided desktop setup experience.
- The installed qualification script exercises setup plan/init, doctor, health
  summary, update check, rollback check, migration dry run, backup/restore dry
  run, broker status, broker conformance, and secret-safe output checks from
  the installed payload. Missing Hermes runtime or heavy profile dependencies
  are reported as blocked readiness, not healthy operation.
- Compiled Windows `.exe` installers must be Authenticode-signed with
  `signtool.exe` and a release-infrastructure certificate selector. The
  builder allows unsigned compiled installers only when
  `--allow-unsigned-installers` is explicitly supplied for local smoke testing.
- `maya update --check` and `maya update --rollback` reject unsigned,
  tampered, incomplete, wrong-key, and unsupported-platform metadata without
  network use or mutation.
- Windows desktop is the only advertised Phase 6 platform.
- macOS, Linux, server, and container artifacts remain not advertised until
  full qualification passes.
- The release verifier checks SBOM, provenance, checksums, Inno Setup product
  sources, installer-bundle boundaries, managed payload layout, product
  shortcuts, installed qualification commands, built-artifact installation,
  secret-safe output, and Authenticode trust for compiled `.exe` installers.

## Known Limits

Phase 6 does not:

- execute automatic background updates;
- silently install system dependencies;
- create customer tenant resources;
- provide release-approved managed Python and Hermes artifacts by default in
  this repository;
- install Inno Setup or compiler toolchains;
- provide or store Windows code-signing private keys, certificate passwords,
  or release-signing credentials;
- claim macOS, Linux, server, or container support;
- replace the deferred external independent security review gate.

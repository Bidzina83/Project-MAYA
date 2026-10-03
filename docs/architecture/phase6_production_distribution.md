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

The embedded Windows runtime explicitly loads the bundled pywin32 module and
DLL directories without executing arbitrary `.pth` files or registering system
components. Windows qualification exercises native file locking and a real
concurrent log write; importability alone is not logging readiness.

First-run setup requires an explicit provider model ID and blocks unattended
startup while the starter model placeholder remains. Offline qualification
uses an isolated synthetic model ID and credential, never a paid model call.
Product construction requests Hermes quiet mode to suppress credential-fragment
startup output. Provider tool injection is checked separately from Hermes'
early diagnostic tool listing.

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

### Separate Governance-Test Installer

`scripts/build_governance_test_installer.py` builds a dedicated Inno product,
not the Standard production installer. It consumes the hashed twelve-patch Hermes
candidate, builds the current Maya wheel and materializes prepared Python
dependency wheels beside managed Python. No source-tree execution, provider
credentials or system software installation is used. Metabase, documents,
browser, broker and connectors are disabled in this core qualification profile;
normal Standard still requires its included Metabase capability.

Install root: `%LOCALAPPDATA%\Programs\Maya Governance Test`.
Test state/reports: `%LOCALAPPDATA%\Maya Governance Test\run-<id>`.
It has its own AppId and selectable Start Menu/desktop shortcuts. The
`Qualify Maya Governance Test` shortcut uses managed Python to run
`project_maya.hermes_plugins.candidate_qualification` from installed artifacts.
Each run initializes new isolated state, actual SQLite memory and local policy,
starts/stops actual Maya/Hermes, verifies four native bindings before SDK
construction and audits a denied model request with zero provider calls.
The shortcut also starts two fresh processes for allowed model/output and a
denied native file-tool proposal. These use real SDK parsing and the native loop
with zero SDK retries, but synthetic HTTP/SSE fixtures rather than sockets or a
live LLM. The file tool comes from the native catalogue; its handler must not
execute on denial, and there must be no second inference. No customer credential
or data is used. This does not test live provider authorization, actual model
reasoning, allowed tool effects, complete recovery/background behavior or the
full Standard lifecycle.

The fourth `tool-allow` scenario reads exactly one synthetic document through
the native file tool, validates its result before the follow-up model request,
and verifies two separately authorized model requests and validated final
output. On Windows this native path depends on customer-managed Git Bash;
it is not bundled here and clean-install qualification remains blocked until
the shell dependency is curated/packaged or an approved alternative is qualified.

`scripts/verify_governance_test_installer.py` checks every payload file and the
six-scenario launcher. `compression-denial` exercises the installed complete
native summary consumer at its governed auxiliary-call seam: typed denial,
one attempt, zero transport/fallback and unchanged summary/cooldown state.
It does not qualify auxiliary provider selection or all compression callers.
`background-denial` triggers the native loop's finalizer review branch after
validated synthetic output and checks the readiness denial propagates, with no
background thread or additional agent. Earlier validated saves are not undone.
Other worker/recovery/persistence paths and clean installation remain open.

The verifier checks the
compiled installer against hashes. `--run-payload` runs offline qualification
using managed Python. Its result is release-payload smoke, not evidence of a
clean Inno installation. Unsigned installers require the builder's explicit
`--allow-unsigned-installers` and verifier's `--allow-unsigned-local-smoke`;
production qualification remains false even if Authenticode signing is supplied.

The current governance-test build is `0.1.0+govtest.20261002.013`, using Hermes
`0.17.0+maya.gov12.candidate.20261002` with patches 1-12. Its ignored artifact
directory is `.codex-build/maya-governance-test-20261002-013/`. All six offline
packaged scenarios pass, each also checking native persistence denial, preserved
session assignment, zero denied store calls and raw API observer suppression.
The probe opens Hermes's native session database in isolated test state; it does
not qualify allowed database writes or bypassing gateway writers. It registers
observers through the native PluginContext API. Builds 011 and 012 failed probe
development and are not delivery candidates. Build 013 is unsigned local-smoke
only, not Standard or Windows production qualification. The real-provider,
managed-shell and full lifecycle/recovery/worker gates remain open.

Governance-test build `0.1.0+govtest.20261002.010` used the eleven-patch wheel
and passed all six release-payload scenarios on the build machine. The generated
installer and evidence are under the ignored
`.codex-build/maya-governance-test-20261002-010/` directory. Build 009 is superseded
and must not be used for qualification. The test initializer observer preserves
the real AIAgent class and native routing; synthetic HTTP remains the transport.
This result is not evidence of a clean Inno installation, a live provider, a
managed shell, full recovery/worker coverage or Windows production support.

The candidate uninstaller removes only its own managed runtime tree, including
untracked caches; test data and all other Maya/Hermes homes are preserved. The
existing Standard uninstaller relies on Inno's owned-file log and has no explicit
runtime cleanup, so generated files or locked files can leave directories behind.
Do not delete customer state to remedy this. Hermes itself defaults to
`%LOCALAPPDATA%\hermes` when `HERMES_HOME` is absent and seeds a generic SOUL.md;
the candidate explicitly supplies its isolated home before importing Hermes.

Phase 6 does not add automatic background updates, silent installer execution,
system dependency installation, customer tenant resource creation, or platform
support claims beyond the qualified Windows desktop artifact.

The Phase 5 external independent security review remains a pre-production and
customer-readiness gate.

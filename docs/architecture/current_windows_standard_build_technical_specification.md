# Maya Standard 0.1.0 Current Build Technical Specification

## 1. Document Status

This document describes the actual Windows Standard production-candidate
payload built on 2026-09-26 at:

```text
.codex-build/maya-standard-production-payload-20260926-002
```

It is an as-built specification, not a statement that every Product Spec V2
capability is complete or that Windows production support is approved.

| Item | As-built value |
|---|---|
| Product | Maya the Info Manager, Standard edition |
| Release version | `0.1.0` |
| Target | Windows x64-compatible desktop, per-user installation |
| Source commit recorded by provenance | `b4a5c73f98e1e5e5c0c4a93780c1c5d4023d91b9` |
| Hermes source commit contract | `b13e2fd6948a59eeb59fe618914147d97a2ee90a` |
| Compressed release bundle | `project-maya-0.1.0-windows-desktop.zip` |
| Compressed bundle size | 1,545,794,240 bytes |
| Expanded application payload size | 2,503,752,305 bytes |
| Unsigned Standard smoke installer | 1,474,284,560 bytes; SHA256 `a8bc8db64ac703a1f2dfe0298602d3cb10f8340e1cc6af10a0f7c516bee71a64` |
| Inno Setup source | Standard and Enterprise `.iss` files generated |
| Release signature | Ed25519 non-production test key, `phase6-test-key` |
| Payload manifest mode | `production` artifact completeness |
| Product support status | Not yet Windows production-qualified |
| Project MAYA source tree | Dirty; recorded explicitly in provenance |
| Skills source | Clean commit `60c14ac87aa46db8a3182387130e9484b68c8287` |

The payload passed `scripts/verify_phase6_release.py` from installed artifacts.
That result proves payload structure and subprocess qualification, but it does
not replace a compiled, signed, clean-machine installation and lifecycle test.

## 2. Interpretation of Installation States

The current build uses three distinct dependency states:

1. **Installed by default** means the Inno `[Files]` section copies the
   component into the Maya-owned installation directory. The current installer
   has no package-selection task; it copies the complete payload.
2. **Configured or activated on demand** means code or a runtime is already
   present, but setup, credentials, customer consent, policy, data-source
   connection, process startup, or an explicit command is still required.
3. **Externally supplied on demand** means the component is not in this build.
   The customer or a later approved release/setup flow must supply it. Maya
   must report the corresponding capability as blocked until validation
   succeeds.

Presence on disk does not imply that a component is configured, authorized,
running, healthy, or supported.

## 3. Installed System Architecture

The intended execution boundary is:

```text
Channel or local client
  -> authenticated loopback Local API and identity policy
  -> governed SMB context and persistent-memory retrieval
  -> Project MAYA Agent lifecycle facade
  -> Hermes Agent runtime
  -> model-provider request
  -> proposed response or action
  -> local action authorization gateway
  -> approved local tool or external connector
  -> result validation and audit
  -> governed business-memory write decision
  -> response
```

The current `Start Maya` shortcut initializes setup if necessary and then runs
`project_maya.cli serve-local-api`. It does not currently start a Telegram,
Slack, or Google gateway process.

### 3.1 State ownership

- Maya SMB operational and business memory is stored in a customer-controlled
  SQLite database under `MAYA_DATA_DIR`.
- Hermes continues to own conversation sessions, `MEMORY.md`, and `USER.md`.
  These are not migrated into Maya business memory.
- Maya embeddings and indexes are derived, rebuildable data and are not
  authoritative records.
- Governance policy, audit records, configuration, logs, backups, update
  metadata, Metabase state, and connector state remain local.
- Raw secret values are stored through the Windows DPAPI-backed Maya secret
  store. Configuration contains only `secret://` references.

## 4. Installation Layout and Behavior

### 4.1 Program files

The Standard Inno source installs per user under:

```text
%LOCALAPPDATA%\Programs\Maya the Info Manager
```

| Directory | Purpose |
|---|---|
| `app/` | Expanded `project_maya` package and runtime bootstrap code |
| `runtime/python/` | Maya-managed CPython runtime |
| `runtime/site-packages/` | Materialized offline Python environment |
| `wheels/` | Hashed offline wheelhouse for provenance and repair |
| `services/runtime/` | Java, Metabase, LibreOffice, Poppler, and embedding model |
| `skills/` | Sanitized, allowlisted Maya skills overlay |
| `config-templates/` | Standard configuration and deny-by-default policy |
| `scripts/` | First-run and installed-qualification programs |
| `bin/` | Setup, start, doctor, CLI, and qualification launchers |
| `release/` | Release, SBOM, provenance, update, and rollback metadata |
| `assets/` | Maya application icon |

Python package tests, bytecode caches, repository tests, and generated cache
directories are excluded from the executable runtime.

### 4.2 Customer data

First-run setup creates the default local state root at:

```text
%LOCALAPPDATA%\Maya the Info Manager\maya-data
```

It creates configuration, memory, governance policy and audit, logs, backups,
documents, connectors, Local API, updates, and separate Metabase application,
provisioning, and analytics-source directories. Uninstall does not delete this
customer-controlled directory.

### 4.3 Shortcuts

Start Menu shortcuts are an optional checked-once installer task. A desktop
shortcut is an optional unchecked task. The generated Standard installer
defines:

- Maya the Info Manager / Start Maya
- Setup Maya
- Maya Doctor
- Maya Installed Qualification
- Maya Data Folder
- Release Manifest

### 4.4 Installer side effects

The installer only copies curated payload files. It does not silently install
system Python, Java, LibreOffice, Poppler, Metabase, OAuth applications,
webhooks, bots, tenant resources, services, or customer credentials. The
managed runtime copies live inside Maya-owned directories.

## 5. Components Installed by Default

All components in this section are physically copied by the generated Inno
Standard installer source.

| Component | Version or pin | Function in Maya | Activation state after file installation |
|---|---|---|---|
| `project_maya` | 0.1.0 | Canonical product package: lifecycle facade, governance, Local API, memory, connectors, setup, doctor, backup/restore, migration, update/rollback, broker contracts, Metabase and document integration | Core code installed; first-run setup required |
| Hermes Agent | Wheel `0.17.0`; commit contract `b13e2fd...` | Core agent execution, identity/skills, model interaction, tool orchestration, sessions, and Hermes-native memory | Installed and importable; model configuration required |
| Managed CPython | 3.12.0, x64 | Runs Maya, Hermes, Local API, setup, health, and qualification without system Python | Installed and used by all launchers |
| SQLite and FTS5 | CPython standard library | Authoritative local SMB record persistence, full-text search, transactions, integrity checks, and backup | Store initialized during setup/use |
| Maya SQLite/vector memory | Current `project_maya.memory` | Governed SMB ingestion, provenance/trust metadata, lexical/vector/hybrid retrieval, audit, and embedding rebuild | Configured during first run |
| Multilingual embedding model | `paraphrase-multilingual-MiniLM-L12-v2`, revision `f16484b...`, 384 dimensions | Generates local semantic vectors for SMB business information; it is not an LLM and does not generate answers | Installed; used on governed ingestion/search/rebuild |
| ONNX Runtime | 1.29.0 | Executes the local embedding model on CPU | Installed and materialized |
| Tokenizers | 0.23.1 | Converts multilingual text to model tokens | Installed and materialized |
| NumPy | 2.3.5 | Tensor preparation, vector normalization, and cosine similarity | Installed and materialized |
| Metabase | 0.62.1.6 | Local BI dashboards and governed analytics over approved data sources | JAR installed; service/configuration still required |
| Eclipse Adoptium Java | 21.0.11 | Managed JVM for Metabase | Installed; invoked only for Metabase lifecycle |
| LibreOffice portable | 26.2 | Headless Office document conversion for the documents profile | Installed; conversion invoked on demand |
| Poppler | 26.02.0 | PDF page rendering through `pdftoppm` | Installed; rendering invoked on demand |
| Windows DPAPI secret backend | Maya implementation plus Windows APIs | Protects model, Local API, and connector secret values for the current Windows user | Local API token initialized during first run |
| Default governance policy | Schema 1, deny by default | Allows core runtime, configured model egress, and governed SMB memory operations; denies undeclared consequential actions | Copied and initialized during first run |
| Standard configuration | Schema 2 | Selects Standard edition, loopback API, managed Metabase, local memory, and default profiles | Rendered during first run |
| Release metadata | Release/update/rollback manifests, SBOM, provenance | Verification, update checks, rollback checks, diagnostics, and auditability | Installed and copied into local state |

### 5.1 Default enabled profiles

The starter configuration enables:

| Profile | Included function | Immediate readiness |
|---|---|---|
| `maya-core` | Agent lifecycle, governance, Local API, secrets, memory, health, backup/restore, migration, update/rollback | Installed; model credential and first-run state required |
| `maya-metabase` | Managed local BI integration | Files present; setup, application state, and lifecycle validation required |
| `maya-documents` | PDF and Office processing | Python and native tools present; conversion validation required |
| `maya-messaging` | Google, Slack, and Telegram contracts and gateway-related code | Connector authorization and policy required |

`maya-browser` and `maya-local-models` are not enabled. The multilingual
embedding model belongs to Maya business-memory retrieval and is distinct from
the `maya-local-models` profile for local generative LLM inference.

### 5.2 Installed skills overlay

The build installs these allowlisted, hashed skills:

| Skill | Function |
|---|---|
| `maya-identity` | Maya identity and role behavior |
| `ai-information-manager` | SMB information-management workflows |
| `pdf` | PDF inspection and transformation procedures |
| `metabase-operations` | Metabase lifecycle and operational procedures |
| `metabase-free` | Metabase-based BI workflows |
| `office-functionality` | Office-document workflows |
| `google-account-mapping` | Google identity/account mapping workflow |
| `google-drive-folder-listing` | Google Drive discovery workflow |
| `microsoft-graph` | Microsoft Graph workflow knowledge; no Microsoft authorization is configured by the current setup |
| `slack-gateway-integration` | Slack gateway workflow and credential-handling guidance |

## 6. Python Packages Installed by Default

The build materializes 76 hashed wheels into `runtime/site-packages` and keeps
the original wheels in the offline wheelhouse. The wheelhouse manifest is the
authority for exact SHA256 values.

| Package | Version | Function in the system |
|---|---:|---|
| `project_maya` | 0.1.0 | Canonical Maya product implementation |
| `hermes_agent` | 0.17.0 | Agent execution runtime and factory |
| `openai` | 2.24.0 | OpenAI-compatible model API client |
| `fastapi` | 0.139.0 | Local API application framework |
| `starlette` | 1.3.1 | ASGI and web primitives beneath FastAPI |
| `uvicorn` | 0.51.0 | Loopback ASGI server for the Local API |
| `httptools` | 0.8.0 | High-performance HTTP parsing for Uvicorn |
| `h11` | 0.16.0 | HTTP/1.1 protocol implementation |
| `websockets` | 15.0.1 | WebSocket transport support |
| `watchfiles` | 1.2.0 | File-change monitoring used by runtime tooling |
| `python_multipart` | 0.0.32 | Multipart request parsing for API endpoints |
| `pydantic` | 2.13.4 | Typed validation for API and runtime data |
| `pydantic_core` | 2.46.4 | Native validation engine for Pydantic |
| `annotated_types` | 0.7.0 | Type constraints consumed by Pydantic |
| `annotated_doc` | 0.0.4 | Function annotation metadata used by FastAPI |
| `typing_extensions` | 4.16.0 | Backported typing features |
| `typing_inspection` | 0.4.2 | Runtime type inspection for validation |
| `anyio` | 4.14.1 | Structured async compatibility layer |
| `sniffio` | 1.3.1 | Detects the active async library |
| `httpx` | 0.28.1 | Async/sync HTTP client for APIs and model services |
| `httpcore` | 1.0.9 | Low-level HTTP transport for HTTPX |
| `requests` | 2.33.0 | Synchronous HTTP client used by runtime integrations |
| `urllib3` | 2.7.0 | HTTP connection pooling beneath Requests |
| `certifi` | 2026.5.20 | Trusted CA bundle for outbound TLS |
| `charset_normalizer` | 3.4.9 | HTTP text-encoding detection |
| `idna` | 3.18 | Internationalized domain-name handling |
| `socksio` | 1.0.0 | SOCKS proxy protocol support |
| `cryptography` | 49.0.0 | Signatures, encryption, broker security, and release verification |
| `cffi` | 2.1.0 | Python/native interface used by cryptography |
| `pycparser` | 3.0 | C parser used by CFFI tooling |
| `pyjwt` | 2.13.0 | JWT processing for broker and authorization flows |
| `pywin32` | 312 | Windows APIs used by platform integrations |
| `pywinpty` | 2.0.15 | Windows pseudo-terminal support for Hermes tools |
| `psutil` | 7.2.2 | Process and host health inspection |
| `onnxruntime` | 1.29.0 | Local embedding-model inference |
| `numpy` | 2.3.5 | Embedding tensors and vector math |
| `tokenizers` | 0.23.1 | Local multilingual model tokenization |
| `flatbuffers` | 25.12.19 | ONNX Runtime serialization dependency |
| `protobuf` | 7.36.0 | Structured model/runtime serialization |
| `huggingface_hub` | 1.28.0 | Model artifact metadata utilities; install-time downloading is not used |
| `hf_xet` | 1.6.0 | Hugging Face artifact transport dependency; not required for offline install |
| `fsspec` | 2026.7.0 | File-system abstraction used by model tooling |
| `filelock` | 3.32.3 | Cross-process artifact/cache locking |
| `packaging` | 26.0 | Version and package compatibility parsing |
| `tqdm` | 4.68.4 | Progress reporting for artifact operations |
| `pypdf` | 6.14.2 | PDF reading, writing, merging, and inspection |
| `reportlab` | 5.0.0 | PDF generation |
| `pillow` | 12.2.0 | Image decoding and document-image processing |
| `markdown` | 3.10.2 | Markdown-to-document processing |
| `jinja2` | 3.1.6 | Text and document templating |
| `markupsafe` | 3.0.3 | Safe escaping for Jinja templates |
| `pyyaml` | 6.0.3 | Hermes and Maya YAML configuration |
| `ruamel_yaml` | 0.18.17 | Round-trip YAML processing |
| `ruamel_yaml_clib` | 0.2.15 | Native acceleration for Ruamel YAML |
| `click` | 8.4.2 | Command-line interface framework |
| `fire` | 0.7.1 | Hermes command exposure and CLI utilities |
| `rich` | 14.3.3 | Structured terminal output |
| `markdown_it_py` | 4.2.0 | Rich Markdown parsing |
| `mdurl` | 0.1.2 | URL parsing for Markdown-It |
| `pygments` | 2.20.0 | Syntax highlighting in terminal output |
| `prompt_toolkit` | 3.0.52 | Interactive Hermes console support |
| `wcwidth` | 0.8.2 | Terminal display-width calculations |
| `colorama` | 0.4.6 | Windows terminal color compatibility |
| `termcolor` | 3.3.0 | Terminal color formatting |
| `concurrent_log_handler` | 0.9.29 | Process-safe rotating log files |
| `portalocker` | 3.2.0 | Cross-process file locks used by logging/runtime code |
| `croniter` | 6.0.0 | Cron-style schedule calculation |
| `python_dateutil` | 2.9.0.post0 | Date parsing and calendar arithmetic |
| `pytz` | 2026.2 | Time-zone compatibility data/API |
| `tzdata` | 2025.3 | IANA time-zone database |
| `six` | 1.17.0 | Compatibility dependency for older cross-version APIs |
| `python_dotenv` | 1.2.2 | Environment-file loading for compatible runtime workflows |
| `distro` | 1.9.0 | Operating-system distribution detection |
| `jiter` | 0.16.0 | Fast JSON parsing used by the OpenAI client |
| `pathspec` | 1.1.1 | Git-style path matching for tool/file selection |
| `tenacity` | 9.1.4 | Controlled retry behavior for network/runtime operations |

## 7. Configured or Activated on Demand

These components are installed, but are not fully operational merely because
installation completed.

| Capability | Installed material | Required on-demand action | Function when ready |
|---|---|---|---|
| Model inference | OpenAI client, Hermes and Maya model adapter | Run Setup Maya, provide a model API key, and complete valid provider/endpoint configuration | LLM reasoning and response/tool-call generation |
| Metabase | JAR and Java runtime | Initialize application state, validate lifecycle, start the local process, and connect only approved analytics sources | Local dashboards and business intelligence |
| Office conversion | LibreOffice portable | Invoke and validate headless conversion for an approved file | Converts Office formats into processable/output formats |
| PDF rendering | Poppler | Invoke `pdftoppm` through governed document workflows | Renders PDF pages for inspection/OCR workflows |
| Semantic memory | Model, tokenizer, ONNX Runtime, NumPy | Governed ingestion or explicit embedding rebuild | Adds semantic ranking to FTS retrieval |
| Google connector | Connector contracts and skills | Explicit broker-assisted or customer-owned OAuth authorization, scopes, identity mapping, allowlists, and governance policy | Google Drive/account operations |
| Slack connector | Connector contracts and skill | Explicit broker-assisted or customer-owned OAuth authorization, scopes, workspace/channel/user allowlists, and governance policy | Governed Slack read/write workflows |
| Telegram connector | Connector contract; starter setting disabled | Customer creates and supplies a bot token, user/chat allowlists, and enabling policy | Customer-owned Telegram command/response gateway |
| Microsoft Graph | Skill only | Customer delegated application/credential setup, connector implementation/configuration, scopes, and policy | Microsoft 365 information workflows |
| Maya OAuth Broker | Broker client and protocol code | Replace placeholder endpoint, complete approved broker threat model/deployment, and obtain explicit consent | Google/Slack OAuth assistance, licensing, updates, or optional model proxying |
| Backup/restore | CLI and local backup directory | Explicit backup command; restore is dry-run unless apply/overwrite consent is given | Recoverable local Maya state |
| Migration | Migration CLI | Dry-run, review, then explicit apply | Converts supported legacy memory/state formats |
| Update/rollback | Signed metadata and CLI | Supply production-signed update channel/artifact and explicitly initiate action | Verified product update and rollback |

The current first-run script prompts only for the configured model provider API
key. It does not run Google, Slack, Telegram, or Microsoft authorization.

## 8. Dependencies Not Included and Supplied On Demand

| Dependency or capability | Current build state | Function and readiness rule |
|---|---|---|
| Browser executable | Not included; `maya-browser` disabled | Required for browser-based workflows; must be customer-approved and detected |
| Browser automation driver/runtime | Not included | Executes governed browser actions; missing runtime blocks browser readiness |
| Browser governance policy additions | Not enabled | Must authorize specific browser targets/actions before execution |
| Local generative-model runtime | Not included; `maya-local-models` disabled | Ollama, LM Studio, vLLM, or another OpenAI-compatible local runtime may host an LLM |
| Local generative-model artifact | Not included | Customer selects and supplies an approved model; this is separate from the embedding model |
| Microsoft Office | Customer-managed and optional | May support customer-specific Office automation; LibreOffice is the managed conversion default |
| PyMuPDF | Not in the current wheelhouse | Optional enhanced PDF parsing/rendering path |
| Production OAuth applications and grants | Not included | Must be broker-assisted or customer-owned according to edition and connector policy |
| Telegram bot | Never Maya-shared or silently created | Must be customer-owned, credentialed, and allowlisted |
| Customer analytics databases | Not included | Must be explicitly connected to Metabase with least-privilege secret references |
| Production signing certificate/private key | Not included | Required to Authenticode-sign distributable installer executables |
| Production release-signing key | Not included | Required to replace the Phase 6 test signature for production update trust |
| Inno Setup compiler | Build-machine tool, not payload software | Compiles the generated `.iss`; installed locally at release-build time, never on customer machines |

## 9. First-Run Setup Contract

`Setup Maya` performs these local actions:

1. Renders the Standard schema-2 configuration with a new instance ID.
2. Creates customer-data directories.
3. Copies the deny-by-default governance policy.
4. Copies release/update/rollback/SBOM/provenance metadata to local state.
5. Copies the managed Metabase JAR into the Metabase application directory.
6. Creates a Hermes plugin shim selecting provider `maya` while preserving
   Hermes `memory_enabled` and `user_profile_enabled` settings.
7. Initializes and validates the Maya governed business-memory provider.
8. Generates a Local API bearer token and protects it with Windows DPAPI.
9. Prompts interactively for the model API key when one is not already stored.
10. Runs setup plan and setup init/apply through the managed runtime.

The `--ensure` and `--non-interactive` paths never prompt. If the model secret
is missing, they return blocked readiness and instruct the operator to run
Setup Maya interactively.

## 10. Runtime and Security Configuration

| Setting | Current default |
|---|---|
| Local API bind | `127.0.0.1:8765` |
| Remote API access | Disabled |
| Local API authentication | DPAPI-protected bearer token |
| Governance | Audit enabled, deny by default |
| Minimum memory trust | `0.7` |
| Memory registry | SQLite |
| Retriever | Local vector/hybrid retriever |
| Model provider | `openai` |
| Model mode | `maya_managed` |
| Model endpoint | Not set in starter template |
| Broker mode | `runtime` |
| Broker endpoint | Placeholder `https://broker.maya.example` |
| Metabase endpoint | `http://127.0.0.1:3030` |
| Metabase application database | Local H2 configuration with secret reference |
| Google | Enabled in template, broker credential mode, not authorized |
| Slack | Enabled in template, broker credential mode, not authorized |
| Telegram | Disabled, customer-owned credential mode |

External model requests are governed data egress. Connector mutations and
other consequential actions remain denied until explicit policy and
authorization are added. Metabase application state, approved analytics
sources, and Maya persistent memory remain separate stores.

## 11. Qualification Coverage

The installed-payload verifier exercises or checks:

- setup plan and setup init;
- Hermes import/factory and governed-memory provider discovery;
- doctor and health summary;
- Local API loopback/authentication behavior;
- update and rollback checks;
- migration dry run;
- backup creation and inspection;
- restore dry run;
- broker status and conformance;
- connector authorization readiness without creating tenant resources;
- Metabase/Java artifact readiness;
- LibreOffice artifact readiness;
- local embedding model execution;
- governed SQLite memory write/read;
- secret-safe output scanning.

The payload has also passed the Phase 6, update, setup/health, closure, and
embedding-artifact unit suites. These are artifact-level qualifications.

## 12. Current Limitations and Release Blockers

The following items prevent this build from being called the final supported
Windows Standard product:

1. The compiled Standard executable is not Authenticode signed and is therefore
   a local-smoke artifact only. It is kept outside the verified payload release
   tree so it cannot be mistaken for a signed distribution artifact.
2. Release metadata is signed with the non-production Phase 6 test key.
3. Clean Windows installation, uninstall, restart, lifecycle, connector,
   backup/restore, update/rollback, and secret-safety qualification has not yet
   passed for a compiled executable from this payload.
4. Project MAYA provenance correctly records that this candidate was built
   from a dirty working tree. A promotable release must be rebuilt from the
   reviewed, committed, clean source state.
5. The release manifest currently labels the Windows platform as qualified,
   which is broader than the product rule requiring clean installed lifecycle
   qualification. That claim must be narrowed until the gate passes.
6. `Start Maya` starts only the Local API. It does not start a supervised
   Hermes messaging gateway or managed Metabase service.
7. First-run setup collects only the model API key. It does not collect the
    customer-owned Telegram token/chat allowlist or complete Google, Slack, or
    Microsoft authorization.
8. The starter model endpoint is null. Provider/base-URL behavior must be
    validated against the pinned Hermes runtime on a clean installation.
9. The runtime retains both materialized site packages and the wheelhouse.
    This supports offline provenance/repair but contributes to disk usage and
    should be an explicit product-size decision.
10. Metabase and Java are present, but the installer does not install a Windows
    service or supervised lifecycle process.
11. Retention enforcement, contradiction resolution, and a benchmarked
    large-collection vector index remain future SMB-memory hardening work.

## 13. Next Build Acceptance Gate

The next candidate should:

1. review and commit the payload changes, then rebuild from a clean source tree;
2. implement or explicitly stage the messaging and Metabase lifecycle model;
3. complete customer-consented connector setup, including Telegram;
4. validate Hermes provider/base-URL configuration without changing the Hermes
   bridge contract without approval;
5. Authenticode-sign the Standard installer with an external production
   certificate and replace the test release-signing key;
6. install on a clean Windows environment and pass the complete installed
   qualification path;
7. preserve customer data through uninstall/reinstall and verify backup,
   restore, update, and rollback;
8. claim Windows support only after all gates pass.

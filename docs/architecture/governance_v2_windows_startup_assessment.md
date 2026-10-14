# Gate A Windows Startup Assessment

## Decision And Evidence Level

2026-10-14: the user approved assessment of the complete Windows startup
dependency/permission problem, not another correction or expanded capability.
Assessment complete for the current prepared inputs: static native/package
inventory, Windows binding diagnostics, bounded registry ACL review, and native
host-contract review. A complete **proven** permission allowlist is not available:
the restricted process still fails before Python worker entry, so imports and
native Hermes operations have not been observed inside LPAC. Gate A stays open.

This does not restart G0-G7, replace Hermes, qualify the installer or authorize
machine-security changes. References: [Gate A evaluation](governance_v2_gate_a_evaluation_contract.md),
[architecture](governance_v2_gate_a_architecture_assessment.md),
[retained failures/comparisons](governance_v2_lpac_verification_review.md).

## Executive Diagnosis

The prototype omitted a Windows startup compatibility contract and assumed two
native Hermes interfaces incorrectly. These are identifiable gaps in Maya's
prototype analysis/wiring, not evidence that new Hermes patches are needed.

1. Prepared-file RX and a network capability are insufficient for CPython's
   Windows activation-context and OS-metadata dependencies.
2. The test host configures a nonexistent external provider named `builtin` and
   then requires the memory manager that native construction deliberately clears.
3. Its completion-only SSE fixture does not implement the pinned native stream
   consumer's content/tool event contract.

Therefore another registry-key fix alone cannot deliver the allowed product
slice. Conversely, blanket registry access is not an acceptable solution to the
startup failure. The next proposal must address a whole fixed compatibility and
integration profile, not another automatically extended per-key sequence.

## Frozen Inputs And Method

Hermes pin remains `b13e2fd6948a59eeb59fe618914147d97a2ee90a`, unpatched.
Managed runtime manifest remains
`0ed977a4f7269ec86d01468e19820d616fc4e74cacd21b2919131d88457a5b32`.
Native launcher binary remains
`e72f101bea8222d14e908c2f39e7fecdca122b2f13b2abe9d5293490b7856f63`.

Read-only tool `scripts/inspect_governance_v2_startup.py` verifies the recorded
runtime hashes, maps PE images exclusively as resources (no artifact DllMain or
entrypoint), reads import/delay-import tables using Windows DbgHelp, parses
manifest XML and checks package requirements/selected extras from metadata.
It does not construct/import Hermes or execute payload code on the trusted host.
[Resource-only mapping](https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-loadlibraryexw),
[DbgHelp image directories](https://learn.microsoft.com/en-us/windows/win32/api/dbghelp/nf-dbghelp-imagedirectoryentrytodata).

Observed inventory:

| Item | Observation | What It Does Not Prove |
| --- | --- | --- |
| Native images | 160: 150 AMD64, eight x86, two ARM64 | Every image is needed/loadable in the supported x64 profile |
| Native import names | 80; each has a staged/System32 candidate or API-set classification | Actual loader search, forwarder/dynamic import resolution or LPAC access |
| Python distributions | 104 | Curated minimal release or license/provenance acceptance |
| Active direct Hermes requirements | 28, all metadata versions match | Imports, data files, extras' runtime behavior or native initialization |
| Active transitive requirement edges | 58, all metadata versions match, including selected extras | Complete execution-path dependency closure |
| ABI/profile | Core CPython is AMD64/cp313; Hermes requires Python >=3.11,<3.14 | General platform or all tool support |

Key recorded versions: OpenAI 2.24.0, httpx 0.28.1, pydantic 2.13.4,
pydantic-core 2.46.4, pywin32 311, portalocker 3.2.0,
concurrent-log-handler 0.9.29, tzdata 2025.3 and cryptography 46.0.7.
These were consumed from prepared artifacts, not downloaded/upgraded.

The copied assessment environment includes CPython test extensions, debugpy,
setuptools multi-architecture launchers and unrelated optional tooling. It also
contains tkinter binaries without the Python-root Tcl scripts directory. Do not
call this a production-curated payload or infer GUI readiness. Removing unused
files is release curation, not the enforcement mechanism for hostile code.

## Startup Layers And Required Resources

| Layer | Necessary Resources/Contract | Current Evidence |
| --- | --- | --- |
| Windows image/assembly initialization | Staged PE images, UCRT/VC runtime, OS loader/API sets, embedded manifests, assembly-binding/locale metadata | DLL mapping observed; restricted activation fails |
| CPython bootstrap | Lib/encodings, extension DLLs, explicit search paths, UTF-8/private pipes, private writable temp/home | Files/hash inventory only; worker entry not reached |
| Native library imports | sqlite3/_sqlite3; OpenSSL/_ssl/_hashlib; ctypes/libffi; SDK Rust/C extensions; pywin32 DLL discovery | Import-table candidates and metadata only |
| Hermes import | Bootstrap/config/env-loader, tool discovery, supported package/data dependencies, no uncontrolled lazy install | Static native-source inventory; no restricted import |
| Hermes construction | Private logs/locks, SessionDB schema/state, explicit model URL/admission, local native memory, real external-provider registration | Deterministic memory wiring mismatch found |
| First useful request | Native SSE consumer, approved memory/document broker methods, separate model authorization, validated final delivery | Completion-only fixture mismatch found; no restricted loop |
| Resume/shutdown | Private session/MEMORY.md/USER.md persistence, fresh admission, cancellation, cleanup | Must be qualified, not inferred from file grants |

OS DLL/API-set existence is not an authorization grant. Keep managed runtimes
read-only and separate all private Hermes state from protected SMB/policy/audit/
credential/customer roots. No shell, COM, UI, credential-service, external-network
or lazy-install permission is implied by a dependency name. Metabase/LibreOffice,
embeddings, connectors and full product lifecycle remain outside this Gate A
core slice; their later product gates are unchanged.

## Activation Failure: What Is Now Known

Resource inspection finds a Microsoft.Windows.Common-Controls 6.0.0.0 assembly
dependency in python.exe, python313.dll, python3.dll and multiple CPython
extensions, including _ssl and _sqlite3. It exists even for this headless worker.
Removing only an executable manifest would not address the DLL/extension contract
and would modify signed/runtime artifacts; no such shortcut is recommended.

With separately permitted reproduction of **only the previously approved**
SideBySide grant, Windows SxS tracing identifies failed activation of
`runtime/python/python313.dll`, not a model/agent call. The executable-name filter
initially produced no records because the event is attributed to the DLL;
unfiltered local parsing finds the staged DLL record. It reports parsing, null
manifest definition identity and activation-generation failure, without a more
specific inner error. Null identity alone is not a corruption diagnosis.
[SxS tracing](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/sxstrace).

The paired file/registry trace confirms SideBySide root open SUCCESS and an
absent optional PreferExternalManifest value, followed by 0xC0150002. No denied
SideBySide subkey or WinSxS file access appears in the selected-child trace.
Do not invent a Winners-subtree/Common-Controls-file grant from that status.
Other observed OS registry reads (NLS/CodePage, Session Manager, FileSystem,
Image File Execution Options and software-restriction policy) and HKCU opens
remain denied; their individual necessity/fatality has not been established.

Trusted-host CreateActCtx metadata-only checks succeed for both python.exe and
python313.dll; handles are released without activation/default-context changes
or artifact execution. This supports intact usable binding metadata outside the
restriction, not permission to run Hermes unrestricted. Exact failing dependency
within restricted DLL activation remains unresolved.

## Broad Registry Capability Is Not The Default Fix

Read-only ACL inspection on this host finds registryRead ReadKey grants on:

- HKCU root and Software (non-inheriting at those keys);
- HKCU Environment and Internet Settings (with inheritance);
- HKLM SOFTWARE and the examined Windows startup keys.

The examined HKCU Office key has no registryRead/AAP/ARAP ACE. This bounded review
is not a claim that all customer registry keys are readable, nor an effective
access test with the capability. It is concrete evidence that the capability's
potential scope is broader than Windows assembly binding. No customer values or
secrets were read. User environment values can contain provider credentials; a
profile intended to withhold those credentials must not silently grant that read
channel. Network blocking or later redaction would not authorize the read itself.

Reject unreviewed registryRead/lpacCom, blanket HKCU/HKLM grants and ordinary-
AppContainer fallback. Windows runtime metadata must be explicitly classified
and allowlisted separately from customer settings/credentials, with negative
registry fixtures as well as protected-file tests. New grants require an impact
decision and rollback contract; privileges cannot originate in model/tool text.

## Native Integration Mismatches

### Memory Registration

The runner writes `memory.provider: builtin`. This pin's discovery loader searches
`plugins/memory/<name>/__init__.py` and the private user-plugin directory; neither
contains builtin. agent_init.py creates a MemoryManager temporarily, then clears
it when no provider was found. MEMORY.md/USER.md use the separate MemoryStore and
do not themselves populate that external-provider registry.

The worker subsequently demands `_memory_manager is not None` before calling
add_provider, so its own assertion would block on this fixture even after loader
recovery. Correct Maya-owned provider bootstrap/lifecycle using the native
MemoryProvider/MemoryManager/discovery contract; preserve MemoryStore and native
conversation storage. Never fabricate a builtin plugin, parallel manager registry
or SMB-memory replacement for Hermes preferences. Register Maya once, initialize
it before turn context, validate governed retrieval, then prove native shutdown.
No source correction was applied during this assessment.

### SDK/SSE Fixture

restricted_broker_http.py emits only response.completed. The pinned
agent/codex_runtime.py:_consume_codex_event_stream reconstructs content/tool items
from response.output_item.done and text deltas; it intentionally never reconstructs
content from response.completed.response.output. Completion alone therefore
leaves its collected output empty in this path.

Correct the Maya-owned buffered fixture adapter to emit the required event/items
from an already host-validated response. Keep raw provider streaming away from
user delivery. Test tool-call, final-text and empty/failed/malformed/denied cases
against this actual pinned consumer/SDK in the restricted native path. Do not
change Hermes's parser, disable reasoning or replace its real loop to fit a test.

## Recommended Next Decision

Approve one **fixed startup-and-integration compatibility contract**, not another
isolated grant. Contract preparation must include:

1. An enumerated OS-metadata read profile for the observed Windows build, with
   unresolved DLL-activation access identified before proposing its ACLs. The
   current evidence is insufficient to publish a proven complete grant list.
2. Native artifact/import/data-file curation and deterministic search/temp/home
   layout; preserve runtime hashes/pins and document every packaging adaptation.
3. Maya-owned memory bootstrap and buffered SSE corrections against the verified
   native interfaces; no Hermes internal patch or fake substitute.
4. One frozen phase ladder: metadata/loader -> Python imports -> native Hermes
   construction/private memory -> real SDK/tool/follow-up -> resume/shutdown,
   each paired with protected filesystem/registry/network denial controls.

No new permission/code correction is authorized by this assessment. Once the
exact contract is reviewed, any execution allowance needs an explicit fixed
budget and stop decision: unexpected required privilege, customer-registry access
or another unresolved startup root stops the candidate, rather than automatically
expanding the list. All A01-A20 families remain required for Gate A; a startup
pass is not acceptance. If a safe complete profile cannot be defined within that
budget, reject LPAC for the frozen candidate and return to the user's architecture
decision, not an automatic alternative implementation or a Hermes patch sequence.

## Evidence And Cleanup

Generated/raw evidence stays ignored in `.codex-build/gate-a-startup-diagnostics`:

| Evidence | SHA256 |
| --- | --- |
| startup-inventory.json | `61e2118232d8b1c1c5035369043b5810510a368c027254a461a9beb1d0eb1254` |
| activation.etl | `83d80b7b7399d3619b331a4aa3880a4f5b38874cb6636286239699ce23da8b87` |
| activation-all.txt | `c5fec40f39133f3c1ed69ef47c109711db0310db40623a8244bdcd1243b18aa2` |
| activation-io.pml | `69b0543117105702ea8bdcdf40d18fd5c50e74c309432ca2e1bb866200b38150` |
| activation-io.csv | `b7ca4fe9d1ba9ee6516f31fd2f7051682dfe0461d6b2dd957d12b4b77ce3ce04` |

Raw traces may include unrelated host metadata and must not be committed/shared.
Only selected-child diagnostics inform this report. Original SideBySide
owner/group/DACL bytes and control flags are restored and verified; SACL untouched.
Test profile/filters/exemption/directory grants removed. Read-back reports missing
filter, zero exemption/diagnostic process/driver/SxS trace and no executable SID
grant. No live requests, customer/cloud resources, installer rebuild, runtime
upgrade, Hermes patch or model-route change occurred.

Validation: 55 diagnostic manifest/parser, broker, preflight/token-guard and Local
API tests pass. Context validation, Python compilation and diff checks pass;
existing Git LF/CRLF checkout warnings remain unchanged. The new script/tests are
diagnostic tooling only. The inspected dependencies directory contains no second
run_agent/agent/hermes_cli/tools/plugins namespace or project_maya package; the
trusted Maya host still uses source paths in this assessment, not an installed
product artifact. This cannot be relabeled as installed qualification.

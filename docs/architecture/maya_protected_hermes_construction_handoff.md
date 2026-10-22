# Protected Hermes Construction 1 Handoff

## Approval Boundary

The user approved preparation on 2026-10-22 after reviewing
maya_protected_hermes_construction_proposal.md. This document describes the
resulting candidate, not authorization to execute it. Separate exact-artifact
VM-run approval and fresh product consent are required. No local Hermes/native
payload execution or VM change is part of preparation. Stop after one approved
VM result; no automatic retry, grant or fallback.

Version: 0.1.2-hermes-construction.1. Scope: offline-hermes-construction-v1.
Target: the existing customer-like Windows 11 Pro x64 26300.9711 laboratory VM,
operated through Remote Desktop. No VM or Docker dependency is added to Maya.
The package is an unsigned development component, not a production installer.

## Real Runtime And Configuration

Python remains 3.13.14; Hermes remains unmodified commit
b13e2fd6948a59eeb59fe618914147d97a2ee90a (distribution 0.17.0), with exactly the
same 63 dependency versions as Import 1. All 6,684 existing import payload files
remain byte-identical. Three files are added: the construction entry, its fixed
contract and fixed configuration. No download, new dependency, source patch,
mock SDK/client or alternative agent is involved.

The entry imports the real run_agent:AIAgent and constructs exactly one instance:

- provider=custom; api_mode=chat_completions;
  base_url=https://maya-construction.invalid/v1;
  model=maya-construction-only;
  api_key=maya-public-nonsecret-construction-only.
- The key is deliberately public, unusable placeholder text, not a credential.
  The address is configuration only; no server or gateway is installed or
  authorized. No model request or conversation is invoked.
- enabled_toolsets=[]; skip_memory=True; skip_context_files=True;
  load_soul_identity=False; session_db=None; checkpoints_enabled=False;
  fallback_model=None; credential_pool=None; quiet_mode=True;
  save_trajectories=False; verbose_logging=False.
- The session ID includes the fresh attempt nonce. No existing user profile,
  .env, secrets, customer configuration, skills or files are copied.

Maya copies a verified fixed JSON-form YAML document into state/config.yaml
before launch. It sets model.context_length=131072, context.engine=compressor,
compression.enabled=False, agent.environment_probe=False, and
tools.tool_search.enabled=off. The last supported setting prevents the tool
search assembler's separate metadata lookup even for an empty tool list.
Both the exact config bytes and effective merged settings are checked before
construction. Ambient managed configuration blocks this test instead of being
overridden. Config bytes must remain unchanged afterward.

## Source Review Findings

The pinned direct helpers were inspected without importing Hermes:

- Custom-provider normalization retains the synthetic model. Explicit key and
  URL select SDK creation instead of automatic credential/provider discovery.
- Empty enabled toolsets yield an empty registry selection; availability check
  callbacks are not called for absent tool names. The child environment has no
  Kanban task variable. Tool search is explicitly off; its metadata path is not
  needed. Empty tools and valid tool names are checked after construction.
- The custom URL/provider avoid OpenRouter prewarming, local-endpoint Ollama
  probing and the LM Studio preload path. A positive context-size override
  returns before the built-in compressor's model-metadata discovery.
- Real SDK initialization validates the packaged certifi CA bundle and builds
  HTTP/TLS transport state. TLS validation is not disabled. This may expose
  compatibility failures that the earlier import-only test could not expose.
- Config loading merges defaults and reads the fresh private config; required
  effective leaves are checked. The built-in context engine is selected and
  initialized; its session-start default is a no-op and session-end clears
  summary state. No external context/memory provider is selected.
- The constructor creates a private sessions directory, in-memory todo state
  and a disabled checkpoint manager (whose Git probe is lazy). Subdirectory
  hints initially resolve only the current private working directory.
- shutdown_memory_provider([]) is called before close(). close() independently
  attempts process-registry, terminal, browser, child-agent and client cleanup;
  some errors are suppressed. Fresh session IDs and no tool calls mean no
  intended terminal/browser resources. Returning normally is not proof that
  every cleanup step succeeded. SDK is_closed and agent.client=None are checked
  in addition to the calls returning, but do not prove complete resource cleanup.

This is bounded static assessment, not an exhaustive no-I/O proof. Initializers,
native libraries, optional imports or cleanup code can attempt unsupported
operations; all remain subject to the existing restrictions. An unchanged zero
Hermes API-call counter is only an observation, not independent network evidence.

## Paths And Security Impact

The existing product-owned ProgramData/MayaProtectedPython-Startup1 location
receives a fresh attempt directory. Runtime stays read/execute only for the
package; state stays its low-integrity writable operational area. HERMES_HOME,
USERPROFILE, LOCALAPPDATA and TEMP/TMP remain bound to state. Existing cache/logs
directories remain; fixed config.yaml, Hermes sessions and bounded construction
reports are the additional disclosed private-state content. No authoritative
customer store is supplied. Reports and files remain after security cleanup.

Ordinary AppContainer, zero capabilities, reduced same-user token, one-process
job, child-process policy, three inherited pipes, isolated Python flags and
six package-scoped WFP denies are unchanged. All network access remains denied,
including provider, metadata, auxiliary and localhost traffic. No extra ACL,
registry grant, loopback exemption, machine Python/PATH setting or Windows policy
change. Ordinary AppContainer's existing All Application Packages access remains
a known limit, not complete customer-data isolation.

There are no synthetic listeners, aliases, canary files, shared-memory fixture,
external supervisor or WFP event-collection change. Explicit read-only imports
and DLL paths and HERMES_DISABLE_LAZY_INSTALLS=1 remain as in Import 1.

Limits remain 8,192 payload files, 4 MiB index, 32 MiB per file, 256 MiB expanded,
4,096 stdout bytes and 65,536 report/captured-text bytes. The cooperative Python
budget is 22 seconds; the host deadline stays 30 seconds. Profiling cannot
interrupt every native blocking call. No timing success has been established.

## Evidence And Failure

The child records Python entry, import identity, all 64 distribution versions,
constructor entry/completion, expected postconditions, context-shutdown return,
close return and SDK closure separately. The host admits the bounded untrusted
report against the immutable contract and attempt binding only after job stop.
Natural exit 0, exact Python beacons, successful admission and reported security
cleanup are all required for construction_completed_pending_independent_cleanup.

On constructor failure, no usable agent instance is obtained; no __new__ bypass
or manufactured partial agent is used. The job boundary still stops the process
and product cleanup proceeds. A later shutdown failure cannot turn a failed
constructor into success. Preserve bounded exception types, missing-module names
and operation stages; raw exception text, tracebacks and environment are not
exported. Suppressed upstream errors remain a qualification limit.

The existing journal-less recovery issue remains open. Forced closure/crash
testing is not approved. Missing evidence, output overflow, timeout, denied
resource, wrong origin/config, nonzero exit or cleanup uncertainty blocks the
test. Do not weaken protections or rerun to obtain a pass.

All containment, production and independent-cleanup qualification flags remain
false. Success would establish only offline construction/shutdown compatibility
of this exact configuration. Memory, model authorization, governed actions,
connectors, Metabase, alternate-path prevention and full Hermes operation remain
separate work under restricted_hermes_execution_contract.md.

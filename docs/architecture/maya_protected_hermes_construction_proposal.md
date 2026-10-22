# Protected Hermes Construction And Shutdown Proposal

## Status

2026-10-22: source assessment and proposal only, following the user's request
to proceed after the agent-construction explanation. No new package, Hermes
execution, VM action or permission change occurred. Package preparation and a
subsequent exact-artifact VM run are separate decisions. Gate A and production
activation remain blocked.

## Import 1 Outcome

The operator's report identifies version 0.1.1-hermes-import.1 and launcher
SHA256 20A34D3A16AC5ABC82309946F2E386B5D5BB0E88F69956F8787494F23EAB7842.
On Windows Professional 26300.9711, Python and the real pinned Hermes class
imported successfully. The report records natural exit 0, matching startup and
import evidence, all 64 distribution versions matching, no modules outside the
verified runtime, and complete product-reported cleanup. Its UTC interval is
2026-10-21T20:07:27.9411508Z through 20:09:50.0401533Z; this includes host work,
not a measured Python-only duration.

Subsequent operator checks found no matching host/child process, no recursive
reparse points, and no package-SID ACE among 7,380 checked entries (zero
failures). State retained the Medium integrity label. A successful WFP state
export and fragment-aware XML inspection found none of the exact six filter
keys or sublayer key. Profile removal remains product-reported, not independently
verified. Preserve the original report and frozen import package/handoff.
This establishes bounded import compatibility, not agent construction, governed
execution, complete independent cleanup or containment qualification.

## Source Findings

Reviewed pinned Hermes commit b13e2fd6948a59eeb59fe618914147d97a2ee90a,
using the retained baseline source; no runtime import was used for inspection.

| Source | Finding and consequence |
| --- | --- |
| run_agent.py:356 | AIAgent forwards to agent.agent_init.init_agent. Construct the real class, not an alternative runtime or mock. |
| agent/agent_init.py:401 | OpenRouter selection can start a metadata-fetch thread. Do not select OpenRouter for this offline test. |
| agent/agent_init.py:737 | Explicit nonempty api_key and base_url choose direct SDK construction instead of automatic credential/provider resolution. A deliberately unusable, public placeholder is necessary for this candidate path; it is not a customer credential. |
| agent/agent_init.py:922; agent/agent_runtime_helpers.py:1357 | The constructor creates the actual SDK/HTTP client, including TLS/transport setup. Successful import alone does not establish this compatibility. Client creation is not a successful authenticated model request. |
| agent/agent_init.py:1059 | Initialization creates its logs directory. Fresh bounded operational state is expected, not a read-only or side-effect-free constructor. |
| agent/agent_init.py:1145,1166 | skip_memory=True avoids the built-in memory load and external memory-provider initialization. This deliberately leaves memory compatibility untested. |
| agent/agent_init.py:1265 | agent.environment_probe=False is a supported configuration switch for the Python toolchain probe. |
| agent/agent_init.py:1503 | context.engine=compressor avoids selecting an external context plugin. The built-in context engine still initializes and receives session-start notification. |
| agent/model_metadata.py:1646 | A positive explicit model.context_length returns before model-metadata discovery in this function. |
| agent/agent_init.py:1686 | A local endpoint can trigger an Ollama probe. Do not use localhost as a supposedly inert provider endpoint. |
| run_agent.py:3026,3186 | Memory/context session shutdown is separate from close(). close() also attempts process, terminal, browser and client cleanup and suppresses individual errors. Neither returning normally nor client=None independently proves resource cleanup. |

These findings support a preparation candidate, not a complete proof that all
transitive constructor and shutdown code is free of attempted I/O.

## Proposed Bounded Test

1. Reuse the verified Import 1 Python, Hermes and dependency identities and the
   existing Maya product-owned consent, setup, restricted launch and cleanup.
2. Within the same zero-capability AppContainer/WFP profile, import the real
   AIAgent and construct exactly one instance. No conversation, prompt, tool
   invocation, model request, connector, customer file or authoritative store.
3. Propose explicit provider=custom, api_mode=chat_completions,
   base_url=https://maya-construction.invalid/v1, a fixed public non-secret
   placeholder key, and a clearly synthetic model identifier. This is only
   SDK initialization configuration, not a fake client, model or gateway.
   No server is started and no connection is authorized.
4. Propose enabled_toolsets=[], skip_memory=True, skip_context_files=True,
   load_soul_identity=False, session_db=None, checkpoints_enabled=False,
   fallback_model=None, credential_pool=None, quiet_mode=True,
   save_trajectories=False and verbose_logging=False. Bind session_id to this
   attempt, never a shared default. These switches are not security boundaries.
5. Maya supplies a fixed config only inside the fresh private Hermes home:
   model.context_length=131072, context.engine=compressor,
   compression.enabled=False and agent.environment_probe=False. No copied
   profile, .env, account token, customer configuration or enabled plugin.
6. After successful construction, call shutdown_memory_provider([]), then
   close() in a finally path even if session shutdown fails. Record each
   reached stage separately. Constructor failure never becomes a successful
   shutdown result; partial initialization needs a separately reviewed cleanup
   path without bypassing __init__ or fabricating a usable agent.
7. Preserve the host's confirmed job termination, revocation and bounded
   reporting. Stop on the first result; no new grant, timeout extension,
   dependency replacement, SDK substitution or automatic retry.

All networking remains denied, including DNS, metadata, auxiliary models and
localhost. Avoiding known automatic probes reduces irrelevant work; only the
existing restrictions enforce the network boundary. Do not claim zero attempted
traffic merely because the constructor completes or the WFP filters exist.

## Preparation Acceptance Requirements

Before freezing executable code, trace the candidate's remaining direct helpers
(provider normalization, tool selection, TLS/transport setup, configuration,
context initialization and shutdown) against this exact configuration. Verify
that an empty toolset really remains empty and the config is actually consumed;
do not infer those facts from argument names. Required additional files, paths,
dependencies or effects must return for review instead of broadening this scope.

Use source/static and inert fixture checks locally, never a local native Hermes
launch. No monkeypatch, stub provider/client, inherited user configuration or
alternate source pin. Preserve existing payload limits, six denies, token/job
checks, isolated Python flags, output bounds and deadlines. Disclose the new
fixed config/state files and placeholder values in the later package handoff.

Evidence must distinguish import, constructor entry/completion, context shutdown,
close entry/return, natural exit and product security cleanup. Validate admitted
reports against immutable identities and attempt binding, not just child booleans.
Inspect available postconditions such as empty tool definitions, absent memory
manager/store, unchanged zero model-call counter and closed client, while clearly
labelling these as observations, not complete cleanup or network proof. Retain
bounded redacted errors; do not export raw credentials, environment or tracebacks.

Success would mean only offline construction/shutdown compatibility of this
bounded configuration. Full Hermes operation, authoritative memory, governance,
model authorization, alternate-path prevention, connectors and Metabase remain
separate qualification work under restricted_hermes_execution_contract.md.

## Next Decision

Approve preparation of this construction-only product package, including the
fixed non-secret SDK placeholder and fresh private configuration. Review its
exact artifact and impact before separately authorizing one RDP VM run and
fresh in-product consent. No command to run on the VM is issued by this proposal.

## Subsequent Preparation Approval

The user approved package preparation on 2026-10-22. The supported private
tools.tool_search.enabled=off setting is included because its assembler can
otherwise perform a separate context lookup even with an empty tool list.
The direct helper assessment and implemented scope are documented in
maya_protected_hermes_construction_handoff.md. The approved preparation does not
authorize a native run, additional dependency, broader grant or qualification.

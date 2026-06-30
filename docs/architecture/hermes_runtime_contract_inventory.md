# Hermes Runtime Contract Inventory

## Status

Step 3 of the approved Hermes Runtime Inclusion phase.

## Sources Inspected

| Source | Role | Commit inspected |
| --- | --- | --- |
| `Bidzina83/hermes-agent` | Selected runtime integration source | `b13e2fd6948a59eeb59fe618914147d97a2ee90a` |
| `NousResearch/hermes-agent` | Upstream compatibility reference | `885e80df74f017d5e897d39928f49b0212e9bedb` |
| `Bidzina83/Hermes-Agent-Maya-Skills` | Trained Maya skill artifact source | Local synced checkout inspected for skill inventory only |

The selected fork and upstream reference are not identical at the inspected
commits. The memory provider ABC matched, but `run_agent.py`,
`agent/memory_manager.py`, `agent/prompt_builder.py`, `agent/skill_utils.py`,
and `hermes_cli/plugins.py` differed. Step 4 must therefore bind to the
selected fork's exact contract and mark fork-specific assumptions explicitly.

## Packaging Contract

The selected Hermes source declares:

- package name: `hermes-agent`;
- package version: `0.17.0`;
- Python support: `>=3.11,<3.14`;
- build backend: `setuptools.build_meta`;
- build requirement: `setuptools>=77.0,<83`;
- many core dependencies are exact-pinned in `pyproject.toml`.

This matters for Maya packaging:

- the current user smoke test used Python 3.14, but selected Hermes declares
  `<3.14`;
- Step 5 package inclusion must either select a compatible Python runtime or
  defer Hermes execution for unsupported Python versions with an honest doctor
  result;
- Maya must not depend on editable installs, local clone paths, `PYTHONPATH`,
  or `/opt/hermes`.

## Runtime Entry Point

The selected Hermes runtime exposes `run_agent:AIAgent`.

`AIAgent.__init__` is the construction seam. It accepts a large chat-oriented
configuration surface, including:

- `base_url`, `api_key`, `provider`, `api_mode`, and `model`;
- `request_overrides`, `fallback_model`, and provider ordering/filtering
  arguments;
- `enabled_toolsets` and `disabled_toolsets`;
- session, platform, user, chat, thread, and gateway identifiers;
- `skip_memory`, `load_soul_identity`, `session_db`, and parent-session
  arguments;
- callbacks for streaming, tool progress, status, notices, reasoning, and
  events.

Construction delegates to `agent.agent_init.init_agent`.

## Lifecycle Surface

`AIAgent` does not expose a first-class `start()` method.

Available lifecycle-related methods are:

- `chat(message, stream_callback=None) -> str`;
- `run_conversation(...) -> dict`;
- `release_clients() -> None`;
- `shutdown_memory_provider(messages=None) -> None`;
- `commit_memory_session(messages=None) -> None`;
- `close() -> None`.

The current Maya adapter's generic `start -> run -> stop` contract therefore
remains a Project MAYA lifecycle wrapper around a Hermes chat object. Step 4
should keep `start()` as Maya-owned lifecycle state and map shutdown to
Hermes `close()` plus memory-provider shutdown behavior where appropriate.

## Execution Surface

`chat(message, stream_callback=None)` calls `run_conversation(...)` and returns
`result["final_response"]`.

`run_conversation(...)` delegates to `agent.conversation_loop.run_conversation`
and returns the richer runtime result dictionary. Step 4 should prefer the
least lossy execution surface that still satisfies Maya's public `Agent.run`
contract. For smoke execution, `chat()` is sufficient; for future audit,
memory, and tool-result detail, `run_conversation()` may be the better adapter
target.

## Model Configuration Surface

The selected constructor accepts the fields Maya already models at its config
boundary:

- `model`;
- `provider`;
- `base_url`;
- `api_key`;
- `request_overrides`.

It also accepts advanced provider-routing fields that Maya should not expose
until governed product configuration exists:

- provider allow/ignore/order/sort fields;
- fallback model configuration;
- credential pool;
- provider data-collection and parameter requirement flags.

Step 4 should pass only the approved Maya configuration fields and keep raw
credentials behind secret resolution. External model calls remain governed
data egress.

## Memory Contract

The selected source exposes `agent.memory_provider.MemoryProvider`.

Core provider lifecycle:

- `name`;
- `is_available()`;
- `initialize(session_id, **kwargs)`;
- `system_prompt_block()`;
- `prefetch(query, session_id="")`;
- `queue_prefetch(query, session_id="")`;
- `sync_turn(user_content, assistant_content, session_id="", messages=None)`;
- `get_tool_schemas()`;
- `handle_tool_call(tool_name, arguments)`;
- `shutdown()`.

Optional hooks include:

- `on_turn_start(...)`;
- `on_session_end(messages)`;
- `on_session_switch(...)`;
- `on_pre_compress(messages)`;
- `on_memory_write(...)`;
- `on_delegation(...)`;
- `backup_paths()`.

Hermes `MemoryManager` orchestrates providers. It accepts built-in memory plus
at most one external provider, collects prompt blocks, prefetches recall
context, queues background prefetch, syncs completed turns, routes memory
tool calls, initializes providers, and shuts them down.

Important adapter finding: `AIAgent` does not expose `attach_memory()`.
Hermes memory integration is manager/provider-based. Step 4 must either use an
existing Hermes provider-loading seam or introduce a small adapter-side bridge
that registers Maya's `HermesMemoryProvider` with Hermes without creating a
second authoritative memory store.

## Skill Contract

The selected fork contains:

- `72` default `skills/**/SKILL.md` files;
- `101` optional `optional-skills/**/SKILL.md` files.

The trained Maya skills checkout contains:

- `46` `skills/**/SKILL.md` files.

Hermes skill discovery uses `SKILL.md` files and supports configured external
skill directories through `skills.external_dirs`. Relevant categories in the
selected fork include `email`, `github`, `mlops`, `note-taking`,
`productivity`, `research`, and `software-development`. The trained Maya
skills checkout includes information-management-relevant directories such as
`business`, `data-science`, `devops`, `google-account-mapping`,
`google-drive-folder-listing`, `google-web-search-workflow`, `google-workspace`,
`google_meet`, `metabase-operations`, and `mlops`.

Step 6 must define the product skill bundle boundary. Step 4 should not
directly copy or force-load skills. It may only preserve a path for the
future adapter to pass approved skill directories into Hermes.

## Plugin Contract

Hermes plugin-facing surfaces include registries for tools, memory providers,
web search providers, video providers, and host-owned plugin LLM access.

The plugin LLM facade is host-owned: provider routing, auth resolution,
timeouts, and fallback remain under Hermes host control, and plugins do not
receive raw OAuth tokens or API keys through that facade. For Maya, this still
requires local governance before any model egress or external action.

Step 4 should not expose arbitrary plugin loading from Maya config. Plugin and
skill loading must remain allowlisted and mediated by the Maya/Hermes adapter.

## Compatibility Summary

| Area | Inventory result | Step 4 implication |
| --- | --- | --- |
| Factory | `run_agent:AIAgent` exists in selected source | Current factory path remains valid. |
| Startup | No native `AIAgent.start()` | Maya owns lifecycle start state. |
| Execution | `chat()` and `run_conversation()` exist | Adapter can execute real Hermes. |
| Shutdown | `close()` exists; memory shutdown helpers exist | Adapter stop must call real cleanup. |
| Memory | Hermes uses `MemoryProvider` and `MemoryManager` | Adapter needs manager/provider bridge, not simple `attach_memory()`. |
| Skills | `SKILL.md` discovery plus external dirs | Product skill inclusion belongs to Step 6. |
| Packaging | `hermes-agent==0.17.0`, Python `<3.14` | Step 5 must handle Python compatibility explicitly. |
| Upstream | Relevant files differ from upstream at inspected commits | Fork-specific behavior must be documented. |

## Open Questions For Step 4

1. Should Maya's first real execution adapter call `chat()` for a string result
   or `run_conversation()` for richer runtime details?
2. Should Maya introduce a tiny Hermes-native wrapper object that implements
   `start/run/stop/health` around `AIAgent`, or continue normalizing inside
   `HermesRuntimeAdapter`?
3. What is the safest way to register Maya's governed memory provider with
   Hermes `MemoryManager` without bypassing Maya memory governance?
4. How should `HERMES_HOME` map to `MAYA_DATA_DIR` for packaged Maya so Hermes
   state remains local, customer-controlled, and recoverable?
5. What Python runtime should Maya use for Windows package verification while
   selected Hermes requires `<3.14`?


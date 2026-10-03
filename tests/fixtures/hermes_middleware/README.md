# Pinned Hermes Middleware Fixture

`middleware.py`, `auxiliary_client.py`, `plugin_llm.py`, and `conversation_loop.py` are unmodified source
snapshots extracted from the already built Hermes Agent 0.17.0 wheel, not
substitute implementations or fake runtimes.

- Source: https://github.com/Bidzina83/hermes-agent
- Recorded commit: `b13e2fd6948a59eeb59fe618914147d97a2ee90a`
- Wheel: `hermes_agent-0.17.0-py3-none-any.whl`
- Wheel SHA256: `ee806be8b2f81359e36b114d03c4681da756150df522b30ebc45a29c2dbb04f2`
- Source SHA256, UTF-8 with LF line endings:
  `699f514c4f437670e345277de7b105a8a7b18e052af68b1a2bbef904eef99f6c`
- Auxiliary client SHA256, UTF-8 with LF line endings:
  `317d71beee41a235171d25c441c46587d64246c1ca6efa9c9aee8c5c53475f3c`
- Plugin LLM SHA256, UTF-8 with LF line endings:
  `4158b0ed2be2140eb99f09e1a488daed04da496052fe415cb84e412e4b71fb30`
- Copyright and license: Nous Research, MIT; see `LICENSE`.
- Conversation loop SHA256, UTF-8 with LF line endings:
  `b32a7c2ef5f0f607488a92e6e513d267bd6f49f9a2564c1301c2e5dfea7ba4e8`

Tests apply the tracked candidate patch series to this exact source in a
temporary directory and import the real modules. They use inert transports,
client-resolution dependencies, and plugin-registration fixtures, while executing
real request building, error classification, retry/fallback, and dispatch logic.
They also compare selected legacy behavior against the unmodified source.
No provider credentials or network is required. Socket access is forbidden in
the auxiliary harness. These are focused contract tests, not the full agent loop.
Conversation tests execute the exact patched exception-handler sequences with
recovery probes and compare the remaining AST against the original source.

This fixture is test-only. It must not be included in a Maya wheel or installer.
It does not replace full Hermes regression tests or qualification of a new wheel.

Additional unmodified pinned snapshots for patch 4, SHA256 (UTF-8/LF):

- `tool_executor.py`: `80a138e9ff2b7abc617adc528535e0271b4efe26ee3006daeb82c9c681b5574f`
- `turn_context.py`: `09902a61baef2e0ef113ea72d8dcbdbc0f64d275020926214c7f1db6e8c70f31`
- `memory_manager.py`: `3083e30b9532ad2fdb135de1b2de3cb43466d41a119a4e7679316fcaa35318fb`

The patch-4 harness compiles complete native preflight and serial-dispatch
functions plus the memory manager's turn-start/prefetch methods from the patched
source. Dependencies are inert; this does not substitute a runtime implementation
or claim whole-loop/worker qualification.

Additional unmodified pinned snapshots for patch 5, SHA256 (UTF-8/LF):

- `model_tools.py`: `c0d96e11a5388dc66a4740859b1f9bc6efabe391c475de7a2a5fa957464faf52`
- `tool_registry.py` (upstream `tools/registry.py`): `1fff28948e5714763c26279f40a0188b657243942f8ad8e157a672c453515aef`

The patch-5 tests compile the complete native `handle_function_call` and import
the real registry module, joining them to the patched middleware and real Maya
policy gateway. Discovery, approval environment, observer hooks and tool handlers
are inert dependencies. The async registry case uses an inert coroutine bridge;
full worker-loop and result-transformation qualification are not claimed.

Patch 6 reuses these snapshots and applies after the first five patches; no
additional upstream source snapshot is needed. Its tests load the real patched
middleware and registry, execute native dispatcher/tool-helper functions, and use
Maya's actual policy and result validation. Final-result middleware is a candidate
fork extension, not a feature claimed to exist in the original upstream snapshot.

Additional unmodified pinned snapshots for patch 8, SHA256 (UTF-8/LF):

- `chat_completion_helpers.py`: `ff17762913d3e38aefa57fa22b56048f99d09fc18d189ab6441bf9c69433a76c`
- `codex_runtime.py`: `3878e102cd53dd7e4dd5d767ca5b1e0f0f2778e16e521f4e37a11a1826c1d357`
- `anthropic_adapter.py`: `c7541f69e5dd8515c6b8cf4afd93e38e66d25fbab86eef2a6b32a2249fb2b054`

Tests execute complete native summary and transport helper functions from the
patched source with inert SDK clients, real provider threads and native mandatory
middleware. Summary authorization uses Maya's real policy/audit adapter. API-mode
branch tests do not qualify full Codex/Anthropic SDKs, worker identity or output
disclosure. These are test sources, never installer or wheel dependencies.

Additional unmodified pinned snapshot for patch 9, SHA256 (UTF-8/LF):

- `run_agent.py`: `7a36be48ffdc0fe62b855263683d55c1c7138cc65acf597175920fcf86b45bd5`

Tests execute complete native AIAgent delivery methods after applying the series,
plus the five exact guarded conversation display statements. They compare normal
and mandatory publication behavior, including tails, provider-thread delivery,
the non-streaming message builder and muted-stream display fallback.
No alternate runtime or output buffer is implemented in the test harness. Final
output, observers, persistence, full-loop behavior and worker authorization are
not qualified by these focused suppression tests.

Additional unmodified pinned snapshot for patch 10, SHA256 (UTF-8/LF):

- `turn_finalizer.py`: `71ddf4e5245fe1302056290b95011aefc57909ad12485f8198a64ff46dbc709c`

The patch-10 harness applies the series and executes the complete native
finalizer and native output middleware with inert saves/hooks and Maya's actual
policy/audit adapter. It does not qualify pre-finalizer loop writes, observers,
background work, real provider transports or installed artifacts.

Additional unmodified pinned snapshots for patch 11, SHA256 (UTF-8/LF):

- `context_compressor.py`: `c83042885c66f13b9ffb3b94da763f8a4240c6bfdc81b9e5c98ff172a20d8733`
- `background_review.py`: `afb05223518c3ea945bdb40da1af133431c1eb86146dd80c43054777a131170c`
- `plugins.py`: `fb60534b86b403778232eb63842bba563448a15419b1a43c7fced2274b7601c4`

The harness applies all eleven patches, executes complete native summary and
observer methods and the complete background-review module, and tests the native
AIAgent thread wrapper and complete finalizer caller. Dependencies are inert;
one summary denial uses Maya's
actual policy callback. This does not qualify the complete compression caller,
observer callers, memory-manager workers, scheduler, delegation or artifacts.

Additional unchanged pinned snapshots for patch 13, SHA256 (UTF-8/LF):

- `cli.py`: `5b1f202b0eafe9028b79132bcac7911eb6755b74b2b335ce9f57902b22ddf728`
- `conversation_compression.py`: `956696cc13b349074eef3812902dc487af1a207c328218246c63b00c8bb9255f`

The caller harness applies patches 1-13 and executes complete native compression,
tool-progress, prompt-init and selected CLI methods with inert dependencies.
It also tests the exact native pre-tool flush catch, not the complete model loop.
One persistence denial uses Maya's actual policy and native output gate.
These fixtures are not packaged into product wheels or installers.

## Native Session Database Fixture

`hermes_state.py` is an unchanged UTF-8/LF snapshot from Hermes commit
`b13e2fd6948a59eeb59fe618914147d97a2ee90a`. SHA256:
`2092d272d091c297e8b51429d8a635d13ed12aa2d607384119241991ade63797`.
The row tests execute its complete SQLite implementation; only unrelated home
discovery and memory-read sanitization imports are replaced with inert functions.

`gateway_session.py` and `gateway_mirror.py` are unchanged UTF-8/LF snapshots of
`gateway/session.py` and `gateway/mirror.py` at that same pinned Hermes commit.
SHA256 values are respectively
`6d36c5cfdd9cf36159c8295d5b7757f26b3bbae49dc4c7fbdfbd8bc4e763fc74` and
`8c5b402386af657349f6f5ab95e1bd80dd0742fe91a02fa96d6d67cb0a749d8e`.
Complete native transcript/mirror functions run against actual native SQLite;
identity bindings and mirror lookup are synthetic host inputs, not a qualified
connector authentication flow. These fixtures are not installed product files.

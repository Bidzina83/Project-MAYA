# Project MAYA

Project MAYA is the foundation for the IM AI Employee distribution. The target
product combines a Hermes Agent execution runtime, persistent memory, curated
skills, Metabase integration, and product-specific configuration behind the
stable `project_maya` Python API.

## Current architecture

The first public API foundation is intentionally dependency-injected:

```python
from project_maya import create_agent

agent = create_agent("im-employee", runtime=hermes_runtime_adapter)
agent.attach_memory(memory_provider)
agent.load_plugin("calendar")

with agent:
    result = agent.run("Prepare today's briefing")
```

`Agent` manages lifecycle and delegates execution, memory attachment, and
plugin loading to an `AgentRuntime`. It does not provide a fake fallback for
Hermes. Until a versioned Hermes construction contract is integrated, callers
must inject a compatible runtime adapter.

Persistent-memory retrieval is exposed separately through `MemoryRetriever`,
which adapts the canonical `Retriever` contract (`upsert`, `get`, `search`,
vector queries, and provider-specific retrieval operations). Key-value
`read`/`write` methods are not the persistent-memory API.

See [docs/architecture/public_api.md](docs/architecture/public_api.md) for the
dependency and lifecycle decisions.

## Migration safety

Legacy `memory_kv` migration is dry-run by default:

```bash
python scripts/migrate.py --from legacy.sqlite --to memory.sqlite
```

Applying a migration requires explicit write consent. An existing destination
also requires a verified backup path:

```bash
python scripts/migrate.py \
  --from legacy.sqlite \
  --to memory.sqlite \
  --apply \
  --allow-modify \
  --backup memory.backup.sqlite
```

Applied migrations produce a JSON report containing counts, conflicts,
validation results, provenance samples, duration, and backup location.

## Development

Install the package and test dependencies:

```bash
python -m pip install -e ".[test]"
python -m pytest -q
```

Build the wheel with:

```bash
python -m build
```

Optional Alembic migration tooling is available through the `migration` extra.

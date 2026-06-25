# Local Doctor Checks

## Decision

Phase 1 `maya doctor` validates the local runtime boundary and selected local
state before Maya is treated as operational.

The local-state checks cover:

- `filesystem.data_dir`
- `memory.store`
- `governance.policy`
- `lifecycle.agent`
- `profiles.enabled`
- `local_api.binding`
- `secrets.backend`
- Hermes compatibility and health

First-run missing local state is reported as a warning when Maya can safely
create it later. Malformed local state is reported as a failure.

The lifecycle check is observational. `maya doctor` reports the assembled
Agent state but does not start or stop Maya as a side effect. Stable states
such as `created`, `running`, and `stopped` pass; `failed` fails; transient
startup or shutdown states warn.

The profile check reports configured component profiles only. It does not
claim Metabase, document processing, messaging, browser automation, or local
model services are installed until those component-specific lifecycle and
health checks exist.

## Privacy

Doctor output must stay redacted. It may report paths, backend names, record
counts, and state names, but it must not print memory records, policy rule
contents, secret values, prompt contents, or raw connector data.

## Limits

These checks do not replace repair, migration, backup, or restore commands.
They identify local readiness and obvious corruption without changing local
state.

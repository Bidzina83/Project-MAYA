# Phase 4 Recovery Operator Guide

## Purpose

This guide maps common local Maya setup and recovery symptoms to safe operator
commands. Commands are diagnostic or dry-run unless `--apply` is explicitly
shown.

## Common Paths

| Symptom | First command | Safe next action |
| --- | --- | --- |
| New machine or missing data directory | `maya setup plan --config maya-config.json` | `maya setup init --config maya-config.json --apply` |
| Missing Maya-owned directories | `maya repair --config maya-config.json` | `maya repair --config maya-config.json --apply` |
| Invalid governance policy | `maya doctor --config maya-config.json` | Fix the policy file; Maya does not auto-rewrite policy |
| Broken local memory store | `maya doctor --config maya-config.json` | Back up current state, then repair or migrate with explicit consent |
| Hermes compatibility failure | `maya health summary --config maya-config.json` | Install a compatible package/runtime; do not mark runtime healthy manually |
| Missing optional dependency | `maya health summary --config maya-config.json` | Install the profile extra or customer-managed dependency when needed |
| Document conversion blocked | `maya health summary --config maya-config.json` | Install LibreOffice yourself or disable `maya-documents`; Maya does not install it |
| Metabase provisioning blocked | `maya metabase plan-provision --config maya-config.json` | Configure approved analytics sources and rerun the plan |
| Packaged skill unavailable | `maya skills status --config maya-config.json` | Review packaged skill validation; do not mark the skill loaded manually |
| Backup destination exists | `maya backup --config maya-config.json --to backup.zip` | Choose a new archive path; backup does not overwrite |
| Backup contents unknown | `maya backup inspect --from backup.zip` | Review the redacted manifest before restore; inspection does not extract |
| Restore conflicts | `maya restore --from backup.zip --to maya-data` | Inspect conflicts and rerun with `--apply --allow-overwrite` only after review |
| Legacy memory migration needed | `maya migrate --from legacy.db --to registry.sqlite --dry-run` | Apply only with `--apply --allow-modify` and a verified backup when modifying existing state |
| Update metadata unavailable | `maya update --config maya-config.json --check` | Configure signed metadata later; V2 Phase 4 does not install updates |
| Rollback metadata unavailable | `maya update --config maya-config.json --rollback` | Configure signed rollback metadata later; V2 Phase 4 does not roll back files |

## Boundaries

V2 Phase 4 recovery commands do not create credentials, install system packages,
contact providers, perform OAuth, apply updates, or execute destructive repair
without explicit flags.

Phase 4 also does not claim Windows, macOS, Linux, server, or container
platform support. The Windows smoke path validates installed operator commands
only.

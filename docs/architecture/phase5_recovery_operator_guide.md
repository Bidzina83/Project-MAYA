# Phase 5 Recovery Operator Guide

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
| Backup destination exists | `maya backup --config maya-config.json --to backup.zip` | Choose a new archive path; backup does not overwrite |
| Restore conflicts | `maya restore --from backup.zip --to maya-data` | Inspect conflicts and rerun with `--apply --allow-overwrite` only after review |
| Update metadata unavailable | `maya update --config maya-config.json --check` | Configure signed metadata later; Phase 5 does not install updates |

## Boundaries

Phase 5 recovery commands do not create credentials, install system packages,
contact providers, perform OAuth, apply updates, or execute destructive repair
without explicit flags.

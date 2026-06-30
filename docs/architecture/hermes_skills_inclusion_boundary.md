# Hermes Skills Inclusion Boundary

## Status

Step 6 of the approved Hermes Runtime Inclusion phase.

## Decision

Maya skills are product artifacts, not arbitrary runtime folders.

Only two skill origins are eligible for future Maya packaging:

1. `Bidzina83/hermes-agent` default Maya-relevant skills for information and
   knowledge management.
2. `Bidzina83/Hermes-Agent-Maya-Skills` trained Maya skills developed during
   operator-guided training.

Neither source is automatically included. Every skill must pass explicit
allowlisting, versioning, sanitization, and governance review before it can be
shipped or discovered by a Maya runtime.

## Artifact Contract

An approved Maya skill artifact must declare:

- stable `skill_id`;
- approved origin: `hermes_default` or `maya_trained`;
- artifact version;
- portable relative `source_path` ending in `SKILL.md`;
- declared capabilities.

Absolute paths, drive-letter paths, parent-directory traversal,
machine-specific paths, personal account details, OAuth tokens, bot tokens,
API keys, and raw secrets are not valid skill artifacts.

## Runtime Loading Boundary

Skill discovery and loading must remain mediated by the Maya/Hermes adapter.
Future adapter work may pass approved skill directories to Hermes through its
documented skill discovery surface, such as `skills.external_dirs`, but it must
not import skills directly from product command handlers, connectors, memory
code, local API handlers, or arbitrary local checkout paths.

Skills cannot bypass:

- local action authorization;
- connector credential contracts;
- model-egress governance;
- governed memory retrieval and write decisions;
- audit logging;
- customer-defined allowlists.

## Installation Boundary

Future installation of skills must be idempotent. It must not overwrite
customer-edited state without consent and must preserve customer-controlled
configuration, secrets, logs, memory, and audit records.

## Current Step

This step defines the boundary and adds validation contracts only.

It does not:

- package any default Hermes skills;
- package trained Maya skills;
- copy skill folders into `project_maya`;
- enable Hermes skill discovery;
- configure `skills.external_dirs`;
- claim that any skill is loaded or healthy.

Those remain later approved implementation steps.

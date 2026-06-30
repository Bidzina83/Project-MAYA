# Hermes Source Strategy

## Status

Step 2 of the approved Hermes Runtime Inclusion phase.

## Decision

`Bidzina83/hermes-agent` is the selected integration source for Maya's
concrete Hermes runtime inclusion.

Project MAYA will preserve compatibility awareness with
`NousResearch/hermes-agent`, but the practical runtime, dependency, and default
skill integration work for this phase targets the Bidzina83 fork because it is
the trained Maya operating environment.
`NousResearch/hermes-agent` remains the upstream compatibility reference, not
the practical integration source for this phase.

The related `Bidzina83/Hermes-Agent-Maya-Skills` repository is a separate
skill artifact source. It contains skills developed with Maya during training
and may be curated into Maya product skill bundles after review, sanitization,
versioning, and packaging decisions.

## Source Roles

| Source | Role |
| --- | --- |
| `Bidzina83/hermes-agent` | Primary Hermes runtime integration source for this phase. Also contains default Maya-relevant skills for information and knowledge management. |
| `NousResearch/hermes-agent` | Upstream compatibility reference. Maya should avoid fork-only assumptions unless they are explicitly documented in the adapter contract. |
| `Bidzina83/Hermes-Agent-Maya-Skills` | Trained Maya skill artifact source. Skills from this repo must be curated, sanitized, versioned, and packaged through the approved skills boundary before inclusion. |

## Integration Strategy

The runtime inclusion work should proceed in this order:

1. Inspect `Bidzina83/hermes-agent` and identify the exact commit or release
   candidate used for runtime contract inventory.
2. Record the runtime surface exposed by that source, including
   `run_agent:AIAgent`, startup behavior, session execution, memory hooks,
   plugin and skill loading, model configuration, shutdown, health, and
   dependencies.
3. Compare only the relevant runtime contracts against
   `NousResearch/hermes-agent` so Maya knows which adapter expectations are
   upstream-compatible and which are fork-specific.
4. Choose a reproducible packaging mechanism for Hermes. Acceptable options
   include a pinned package dependency, a pinned Git dependency, or a reviewed
   vendored package snapshot. Runtime behavior must not depend on a local repo
   checkout, `PYTHONPATH`, `/opt/hermes`, or machine-specific paths.
5. Wire Project MAYA through `HermesRuntimeAdapter` rather than importing
   Hermes directly from product command handlers, local API handlers,
   connectors, skills, or memory code.

## Skills Strategy

Maya has two skill origins for this phase:

1. Default Maya-relevant skills already present in `Bidzina83/hermes-agent`.
2. Trained Maya skills from `Bidzina83/Hermes-Agent-Maya-Skills`.

Both origins must be treated as product artifacts before shipping:

- skills are included only after explicit allowlisting;
- skill identifiers and versions are recorded;
- personal account details, local paths, tokens, and operator-specific
  assumptions are removed;
- installation is idempotent and does not overwrite customer state without
  consent;
- skill loading remains mediated by the Maya/Hermes adapter and local
  governance boundary;
- skills cannot bypass connector credential contracts, model-egress
  governance, local authorization, or governed memory-write decisions.

The trained skills repository is not automatically part of the runtime
dependency. It becomes an input to the later Skills Inclusion Boundary step.

## Guardrails

- Do not copy arbitrary Hermes runtime folders into `project_maya`.
- Do not create a second runtime implementation in Project MAYA.
- Do not rely on local clone paths, shell activation state, or editable
  installs for product behavior.
- Do not package personal Google Workspace, Slack, Telegram, email, calendar,
  file-system, or operator-account details.
- Do not hide fork-specific behavior behind generic compatibility claims.
- Do not claim upstream compatibility when the adapter depends on fork-only
  behavior.

## Acceptance Criteria

Step 2 is complete when:

1. `Bidzina83/hermes-agent` is documented as the selected runtime integration
   source.
2. `NousResearch/hermes-agent` is documented as an upstream compatibility
   reference, not the practical integration source.
3. `Bidzina83/Hermes-Agent-Maya-Skills` is documented as a separate trained
   skill artifact source.
4. The strategy forbids path shims, machine-specific paths, and arbitrary
   folder copying.
5. The strategy states that future runtime work must go through
   `HermesRuntimeAdapter`.
6. The strategy defines how default fork skills and trained Maya skills will
   be curated before product inclusion.

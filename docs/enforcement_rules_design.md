Enforcement Rules - Design and Examples

Purpose
-------
This document explains the enforcement_rules feature introduced in GovernancePolicy and how operators can configure advisory enforcement hints that the GovernanceValidator will produce for each block.

Principles
----------
- Advisory-only: enforcement_rules DO NOT cause the system to filter or block retrievals. They produce EnforcementHint(s) that downstream components can act on.
- Per-reason mapping: rules map a canonical reason code (e.g. "low_trust") to a small rule dict that suggests actions.
- Conservative merge: when multiple rules apply to a block, the validator merges rules conservatively (e.g. score_adjust takes the minimum).

Rule schema
-----------
A rule is a JSON-like dict with any of the following keys:
- score_adjust: float (0.0 - 1.0) — suggested multiplier to apply to the block's relevance (lower -> less relevant). The validator keeps the most conservative (minimum) value when multiple rules apply.
- block_flag: bool — advisory flag recommending the block be blocked from downstream use.
- redact: List[Dict] — list of redact hints, each an object describing what to redact (e.g. {"reason":"privacy_block","note":"contains SSN"}). Redaction span indexing is deferred; the hint is advisory.
- note: str — human-readable justification or operator message to include in the EnforcementHint.note.

Example enforcement_rules (Python dict)
--------------------------------------
policy.enforcement_rules = {
    "low_trust": {"score_adjust": 0.6, "note": "reduce weight by derived_trust"},
    "privacy_block": {"block_flag": True, "redact": [{"reason": "privacy_block"}], "note": "contains privacy-sensitive pattern"},
    "provider_not_allowed": {"block_flag": True, "note": "untrusted provider"},
}

Behavior notes
--------------
- Namespaced reason codes (e.g. "missing_provenance:field1") are matched by root ("missing_provenance") when applying rules.
- If no policy rule applies, the validator falls back to legacy heuristics (e.g. privacy_block -> block_flag; low_trust -> score_adjust = derived_trust or 0.7).
- EnforcementHint merging: if multiple rules provide score_adjust, the smallest value is chosen (most conservative). Block flags are OR'd; redact lists are concatenated.

Operational guidance
--------------------
- Start with mild score_adjust rules (0.8-0.95) for informational reasons, reserve block_flag=True for legal/privacy/regulatory codes.
- Test policy changes in a staging environment: enforcement rules are advisory but downstream systems may adopt them — ensure consumers respect the advisory contract.
- Keep enforcement_rules in a centralized config (file, secrets manager, or infra config) and apply via initializing GovernancePolicy at runtime.

Future work
-----------
- Extend rule syntax with "score_adjust_mode": "multiply"|"absolute" and numeric thresholds.
- Add support for redaction spans (start/end indices) computed via a small extractor if redaction is required.
- Provide a management UI to tune enforcement_rules and audit their effects.

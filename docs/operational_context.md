OperationalContext schema for Project-MAYA

This document defines the OperationalContext produced by plugins/memory/context_builder.build_context
and attached to RetrieverService.last_operational_context.

High-level intent
-----------------
OperationalContext is a small, deterministic, structured representation of retrieval outputs tuned for
upstream consumers (LM prompts, planner, tooling). It is intentionally minimal for the V1 implementation
and is meant to evolve into a richer, token-budget-aware context package.

OperationalContext (top-level)
------------------------------
- blocks: List[ContextBlock]
- total_tokens: int  -- conservative estimate of tokens used by the included blocks
- token_budget: int  -- the budget passed to ContextBuilder
- truncated: bool     -- whether not all deduped retrievals could fit into token_budget

ContextBlock (per fact)
-----------------------
Each fact is represented as a ContextBlock dictionary with the following fields:
- chunk_id: str           -- canonical id for the chunk (prefers chunk_id then id)
- content: str            -- text content of the fact/chunk
- provider: str           -- canonical provider name (e.g. "local", "holographic")
- score: float            -- final normalized relevance score in [0,1]
- similarity: float       -- normalized similarity in [0,1] when available
- trust_score: float      -- trust multiplier computed or provided by the provider (default 1.0)
- source_path: Optional[str] -- optional path or origin identifier for provenance
- created_at: Optional[str]  -- ISO8601 timestamp when chunk was created (if available)
- meta: Dict[str, Any]    -- provider-specific metadata (tags, model, embedding_id, etc.)
- estimated_tokens: int   -- conservative token estimate used for budgeting

Representation of facts
-----------------------
- Facts are represented as ContextBlock entries under OperationalContext.blocks. Each block is
  small and self-contained: the content plus provenance and scoring metadata.
- The ContextBuilder V1 deduplicates facts by chunk_id and keeps the highest-ranked instance.

Provenance preservation
-----------------------
- Provenance fields preserved in each ContextBlock include: provider, source_path, created_at, and meta.
- The builder preserves any provider-supplied metadata under meta (embedding ids, original doc ids,
  source URLs). Callers should treat meta as the canonical place to find provider-native provenance.

Governance information attachment
--------------------------------
- Governance is passive in V1: GovernanceValidator.validate(...) returns a GovernanceReport and is stored
  on RetrieverService.last_governance_report.
- OperationalContext currently does NOT embed the full GovernanceReport per-block in V1. Instead, callers
  can consult RetrieverService.last_governance_report (the last produced GovernanceReport) alongside
  RetrieverService.last_operational_context.
- Future versions should add governance annotations per ContextBlock (flags, reason_codes, redaction hints).

Confidence representation
------------------------
- Confidence is represented across two fields:
  1) score: final normalized relevance in [0,1] after temporal decay and trust multiplication
  2) trust_score: provider-supplied or derived trust multiplier in [0,1+], applied multiplicatively to score
- Callers should treat 'score' as the primary ordering/confidence signal and may consult 'trust_score' for
  governance-aware decisions.

Notes and Next Steps
-------------------
- The schema is intentionally flat and JSON-friendly so it can be embedded into prompts easily.
- Next objective: evolve ContextBuilder into a structured OperationalContext builder that supports
  summarization hooks, per-block governance annotations, token-aware stitching, and provenance normalization.


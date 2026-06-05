Context Builder: design notes & API

Goal
- Convert a set of normalized RetrievalResult items into a single governed operational context that downstream agents or prompt templates can consume.
- The Context Builder must preserve provenance, respect governance rules and token budgets, and produce deterministic, testable outputs.

High-level responsibilities
- Input normalization & filtering: accept RetrievalResult[] and apply governance filters (min_trust, recency, allowlists/denylists) as configured by caller.
- Chunk scoring & ranking: compute a context-specific utility score per chunk combining relevance (service score), recency, uniqueness, and explicit policy signals.
- Deduplication & consolidation: remove near-duplicate chunks and optionally merge/concat or summarize them to reduce token footprint.
- Compression/summarization: where necessary, call a summarizer (configurable) to compress groups of chunks into concise summaries while retaining provenance links.
- Token budget management: select/compress chunks to fit within the provided token budget (tokens, or approximate characters/bytes), with deterministic selection rules.
- Output assembly: return a ContextPackage with ordered context blocks (chunk/summaries), plus provenance map and audit metadata.

Key concepts
- ContextBlock
  - id: str  # either chunk_id or synthetic id for a generated summary
  - type: 'chunk' | 'summary' | 'metadata'
  - content: str
  - source_chunk_ids: List[str]
  - provider: str
  - score: float  # final utility score used for ordering
  - created_at: Optional[str]
  - meta: Dict[str,Any]

- ContextPackage
  - blocks: List[ContextBlock]  # ordered by descending score
  - total_tokens: int
  - token_budget: int
  - provenance: Dict[str, Dict[str,Any]]  # chunk_id -> {provider, created_at, meta}
  - audit: {filtered_count:int, deduped_count:int, summarized_count:int}

Interfaces (Python-like)

class ContextBuilderConfig:
    min_trust: float = 0.0
    max_age_days: Optional[int] = None
    half_life_days: float = 30.0  # used for decay if configured
    dedup_similarity_threshold: float = 0.88  # threshold for near-duplicate content removal
    summarizer: Optional[Callable[[List[RetrievalResult], int], ContextBlock]] = None
    tokenizer: Callable[[str], int]  # returns token count
    token_budget_default: int = 2048
    ordering_bias: Dict[str, float] = None  # provider -> multiplier

class ContextBuilder:
    def __init__(self, config: ContextBuilderConfig):
        ...

    def build_context(self, retrievals: List[RetrievalResult], query: Optional[str]=None, token_budget: Optional[int]=None) -> ContextPackage:
        """Main entry point. Deterministic: same input yields same output.
        Steps:
        1. Filter retrievals according to min_trust and max_age_days.
        2. Apply ordering multipliers from config (provider bias).
        3. Compute pairwise similarity for deduplication (fast approximate method; trade accuracy for speed).
        4. Group near-duplicates into clusters; for each cluster choose either one canonical chunk or summarize the cluster using summarizer.
        5. Score clusters by aggregated utility (max score * cluster_size_adjustment * recency_boost).
        6. Greedily select clusters into context until token_budget exhausted. If a cluster's canonical chunk exceeds the remaining budget, call summarizer for that cluster with a smaller budget.
        7. Return ContextPackage with ordered ContextBlocks and provenance map.
        """

Deterministic selection and tie-breaking
- Sort by (cluster_score, created_at desc, provider priority, chunk_id) to ensure deterministic order.
- When greedy selection hits budget boundary, the summarizer must be deterministic given the same inputs and target token budget.

Summarization hooks
- The ContextBuilder relies on an injected summarizer function with signature:
    summarize(chunks: List[RetrievalResult], target_tokens: int, query: Optional[str]) -> ContextBlock
  - The summarizer MUST:
    - Produce a ContextBlock with source_chunk_ids populated
    - Respect the target_tokens (approximate allowed)
    - Preserve key provenance details in meta

Token accounting
- The builder uses a tokenizer (config.tokenizer) to compute token estimates. Implementations MAY accept an approximate tokenizer (BPE count or character-based heuristics) but tests must assert deterministic token estimates.

Governance integration
- ContextBuilder receives governance decisions (filters) from RetrieverService or GovernanceValidator. It must not re-implement policy logic but must apply filters verbatim.
- ContextBuilder should annotate final ContextPackage.audit with the governance rule ids that affected selection (for auditing/tracing).

Failure modes and mitigations
- Summarizer unavailable: fall back to taking first N characters of the canonical chunk plus an explicit "[TRUNCATED]" marker and include provenance.
- Token budget too small to include any chunk: return a metadata-only package indicating budget constraints and the top-N metadata entries (titles/short labels) so calling code can request an increased budget or a targeted follow-up query.

Testing guidance (unit/e2e)
- Unit tests:
  - deterministic selection: given fixed retrievals and tokenizer, build_context must return the same ContextPackage every run
  - deduplication clustering: verify near-duplicates cluster and only one canonical chunk/summarized output is present
  - token budget edge cases: very small budgets, budgets just enough for one full chunk, budgets requiring summarization

- E2E tests:
  - pipeline: ingest -> retrieve -> build_context -> ensure returned context fits token_budget and contains provenance for the top result

Integration points
- RetrieverService: provides RetrievalResult[] to ContextBuilder
- GovernanceValidator: supplies filters (min_trust, max_age_days, allowlists)
- Summarizer service: external LLM call or local summarizer library

Next steps for implementation
- Create a minimal ContextBuilder class under plugins/memory/context_builder.py implementing the API above (start with simple heuristics & string-length "tokenizer").
- Add unit tests under plugins/memory/ingest/tests/test_context_builder.py covering deterministic selection, dedup, and token budget logic.


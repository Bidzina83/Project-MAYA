Canonical retrieval provider architecture

Scope
- Defines the canonical architecture for retrieval providers used by Project-MAYA's memory subsystem.
- Declares the normalized RetrievalResult schema and how providers must present results.
- Identifies RetrieverService (plugins/memory/retriever_service.py) as the official retrieval entry point and describes registration/fallback semantics.

Principles
- Adapter pattern: each persistent store exposes a thin adapter that implements the Retriever Protocol (plugins/memory/retriever_api.py). Providers are not required to share internals; adapters translate provider responses into the normalized RetrievalResult schema.
- Deterministic initialization: provider adapters must initialize explicitly (no automatic seeding or side-effects). Holographic adapter is optional and must be registered explicitly by the caller.
- Governance at the service edge: RetrieverService centralizes governance (min_trust filtering, score normalization, temporal decay, provenance enforcement) so individual adapters can remain simple.
- Reproducible local-first provider: the primary local provider is local_vector_store (SQLite-backed LocalVectorStore). It is dependency-free and suitable for CI/local runs.

Components
- Retriever Protocol (plugins/memory/retriever_api.py)
  - RetrievalResult TypedDict
  - Retriever Protocol (query_vector, search, get, upsert, bulk_upsert, stats, probe, related, reason, contradict)
  - RetrieverError, ProviderInfo

- Provider adapters
  - local_vector_adapter -> wraps LocalVectorStore (plugins/memory/indexer.py)
  - holographic_adapter -> wraps FactRetriever (optional)
  - Adapters must:
    - Return RetrievalResult list for query/search operations
    - Normalize per-provider raw scores to a similarity value in [-1, 1] (if applicable) before handing to service
    - Set provider canonical name string (e.g. 'local_vector_store', 'holographic')

- RetrieverService (plugins/memory/retriever_service.py)
  - Single official entry point for retrieval-related operations in the system
  - Responsibilities:
    - Provider registry and routing
    - Score normalization and clamping
    - Governance filters (min_trust, recency decay)
    - Dual-write semantics (optional) and upsert orchestration
    - Provenance tagging
    - Metrics counters
  - Public surface (examples):
    - register_provider(name: str, adapter: Retriever)
    - upsert(provider: str, items: List[Document])
    - query_vector(query_vec: List[float], top_k: int, providers: Optional[List[str]]=None) -> List[RetrievalResult]
    - search(text: str, top_k: int, embedder: Callable) -> List[RetrievalResult]

Normalized RetrievalResult schema
- Canonical shape (fields and types):
  - chunk_id: str  # canonical id for the retrieved chunk (storage-level id)
  - embedding_id: Optional[str]  # id of the vector/embedding object, if distinct
  - content: str  # the text/serialized content of the chunk
  - embedding: Optional[List[float]]  # embedding vector (optional, may be omitted for efficiency)
  - vector_dim: Optional[int]
  - similarity: float  # similarity measure normalized to [-1.0, 1.0] by the adapter
  - score: float  # normalized final score in [0.0, 1.0] after RetrieverService normalization and governance multipliers
  - trust_score: float  # provider-supplied or computed trust/confidence in [0.0, 1.0]
  - provider: str  # canonical provider name (e.g. 'local_vector_store')
  - created_at: Optional[str]  # ISO-8601 UTC timestamp when chunk was created
  - updated_at: Optional[str]
  - meta: Dict[str, Any]  # free-form metadata (source_url, chunk_index, file_id, tags...)

Score normalization rules
- Adapters provide similarity in a native range where applicable (cosine in [-1,1], inner-product unbounded, euclidean negative distance, etc.). Adapters MUST map native similarity to a canonical similarity in [-1,1] before returning RetrievalResult.
- RetrieverService computes final score in [0,1]:
  - base = (similarity + 1.0) / 2.0  # maps [-1,1] -> [0,1]
  - apply trust multiplier: base *= trust_score (if provided, default 1.0)
  - apply temporal decay multiplier: base *= decay_factor where decay_factor = 2^{-age_days / half_life_days}
  - clamp: score = min(max(base, 0.0), 1.0)

Temporal decay example
- half_life_days is configurable in RetrieverService (default: 30 days)
- age_days = (now_utc - created_at).total_seconds() / 86400
- decay_factor = 2 ** (- age_days / half_life_days)

Registration and routing
- register_provider(name, adapter, priority=100)
  - name must be the canonical provider string used in RetrievalResult.provider
  - priority determines routing order when multiple providers are queried by default
- query_vector(..., providers=None)
  - if providers omitted — service queries all registered providers ordered by priority (can be limited to top-N providers)
  - per-provider top_k may be configurable
- Fallbacks
  - RetrieverService may merge results from multiple providers and re-rank using the canonical score.
  - Duplicates are deduplicated by chunk_id; for duplicate chunk_id, prefer higher score and merge meta.

Governance responsibilities (summary)
- min_trust: drop results with trust_score < configured threshold
- recency: apply decay_factor or drop results older than max_age_days
- provenance: ensure provider and source fields are present; if provenance missing, downgrade or drop depending on policy
- auditable logs: all retrieve calls should log resolver decisions (filtered results, applied multipliers) for auditing

API examples
- Register
  service.register_provider('local_vector_store', local_adapter)
  if try_init_holographic():
      service.register_provider('holographic', holographic_adapter, priority=50)

- Query
  results = service.query_vector(query_vec, top_k=10)
  # results are RetrievalResult[] with score in [0,1]

Notes
- Keep adapters small and deterministic; side-effects and automatic DB migration/seeding are disallowed unless explicitly requested and consented to.
- This document is authoritative for the retrieval architecture; code should follow the types and flows described here.

References
- Retriever API: plugins/memory/retriever_api.py
- RetrieverService implementation: plugins/memory/retriever_service.py
- Local provider: plugins/memory/indexer.py (LocalVectorStore)

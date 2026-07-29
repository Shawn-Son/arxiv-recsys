# System architecture

## Context

Aster separates product state, source metadata, retrieval indexes, and model
artifacts so each can be versioned and rolled back independently.

## Runtime components

| Component | Responsibility |
| --- | --- |
| Web application | Search, paper records, library, exports, and explanations |
| Public API | Versioned contracts, authorization, orchestration, and rate limits |
| Ingestion worker | arXiv harvesting, OpenAlex enrichment, normalization |
| Retrieval service | Lexical retrieval, FAISS search, fusion, and reranking |
| Training jobs | Embeddings, two-tower training, cross-encoder tuning |
| PostgreSQL | Canonical metadata, users, events, saved state, manifests |
| Redis | Request cache, rate limits, and short-lived job coordination |
| Object storage | Immutable model, index, evaluation, and manifest artifacts |

## Data flow

1. The ingestion worker reads from source-specific cursors.
2. Raw records are normalized into a stable paper and paper-version model.
3. Enrichment joins citations and external identifiers without replacing source
   provenance.
4. Deduplication emits candidate groups and confidence, then conservatively
   chooses a canonical record.
5. Embedding jobs write versioned vectors and build an immutable FAISS artifact.
6. The retrieval service loads a validated artifact and exposes its manifest
   with every result.
7. Ranking events record model, feature, experiment, and index versions.

## Reliability boundaries

- Upstream failures pause only the affected source cursor.
- Schema changes use forward-compatible migrations.
- Index releases use checksum validation and a blue/green pointer swap.
- API requests never synchronously call the arXiv API.
- Training jobs cannot mutate the production index directly.

## Security boundaries

- HTML from upstream metadata is never rendered unsanitized.
- User events are private by default and deletable.
- Services receive the narrowest available credentials.
- CI uses workload identity rather than long-lived cloud keys.
- Public endpoints are rate limited and emit trace identifiers.

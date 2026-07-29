# ADR 0003: Retrieve with lexical and FAISS indexes, then rerank

- Status: Accepted
- Date: 2026-07-28

## Context

Scientific queries contain exact terminology, abbreviations, and broader
conceptual intent. A lexical-only system misses paraphrases, while a dense-only
system can underweight exact terms and identifiers.

## Decision

Generate independent BM25 and dense candidate lists, combine them using
Reciprocal Rank Fusion, and reserve the top candidate set for a separately
versioned cross-encoder. Store the dense corpus in a FAISS HNSW or IVF-PQ index
selected by benchmark. Keep index files immutable and publish checksums,
encoder identity, corpus manifest, dimensions, vector count, and code revision.

The deterministic hashing encoder is only a contract and CI baseline. It is not
the production scientific embedding model.

## Consequences

- Each retrieval signal can be measured, inspected, and disabled independently.
- Exact terms and semantic neighbors both contribute candidates.
- Index construction is separated from API deployment.
- Quality and latency claims require the full-corpus artifact and frozen
  relevance judgments.

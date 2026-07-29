# ADR 0002: Preserve source records and version every derived artifact

- Status: Accepted
- Date: 2026-07-28

## Context

Paper metadata changes, arXiv publishes multiple versions of the same work, and
citation providers can revise their graph. Replacing records in place would
make ranking results and research evaluations impossible to reproduce.

## Decision

Treat an unversioned arXiv identifier as the canonical work and each `vN` as an
immutable paper version. Record source checksums and batch manifests. Derived
deduplication decisions, embeddings, indexes, and evaluations must name their
input manifest and implementation version.

## Consequences

- The system can explain which source state produced a ranking.
- Reprocessing is safe because canonical upserts are idempotent.
- Storage grows with versions and manifests.
- Retention and compaction policies must never invalidate published evaluations.

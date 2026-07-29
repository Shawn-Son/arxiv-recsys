# ADR 0004: Separate candidate retrieval from personalized ranking

- Status: Accepted
- Date: 2026-07-28

## Context

A research recommendation system needs to represent both a paper and a
reader's evolving interests. It also needs to remain useful for new readers,
avoid training leakage, and expose which model changed a result.

## Decision

Use a two-tower model to generate personalized candidates from explicit reading
history. The paper tower projects versioned scientific-text features; the reader
tower aggregates only events observed before the evaluation boundary. A
separately versioned cross-encoder may rerank a bounded candidate set.

Keep lexical and semantic query retrieval available when a reader has no
history. Train and evaluate with temporal splits, group near-duplicates before
scoring, and publish coverage and age/category slices alongside aggregate
ranking metrics. Synthetic readers are used only for correctness and load
testing, never as evidence of recommendation quality.

## Consequences

- Candidate generation remains scalable and cacheable.
- Cross-encoder cost is bounded by an explicit candidate limit.
- Model artifacts can be rolled back independently.
- Personalization requires consented event storage and deletion controls before
  it can use real reader activity.
- No quality improvement is claimed until a frozen, versioned evaluation
  reproduces it.

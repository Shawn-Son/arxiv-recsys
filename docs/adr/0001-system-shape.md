# ADR 0001: Separate online retrieval from offline research jobs

- Status: Accepted
- Date: 2026-07-28

## Context

The product must serve low-latency search while continuously ingesting papers,
building indexes, and training ranking models. Combining these workloads in one
process would make latency, failure isolation, and reproducibility difficult.

## Decision

Use a TypeScript web surface, a versioned Python API/retrieval boundary, and
separate offline workers. Store canonical product data in PostgreSQL and
immutable model/index artifacts in object storage.

The first deployed interface remains Cloudflare Worker-compatible. The
full-corpus retrieval service will run as an independently scalable container.

## Consequences

- The web product can ship and be tested before the full corpus is available.
- Model and index versions can be rolled back without redeploying the interface.
- Local development requires a composed environment once backend services land.
- Contracts and end-to-end traces become mandatory between components.

# Aster two-tower and reranking model card

## Status

Architecture and correctness baseline. No production weights or quality claims
are included in this repository revision.

## Intended use

- Retrieve papers related to a reader's explicit saved and viewed history.
- Rerank a bounded candidate set for a research query.
- Evaluate recommendation behavior with temporal splits.

The models are not intended to assess paper quality, author quality, novelty,
truth, or research impact.

## Training signals

Planned positive signals include citation pairs, saves, explicit likes, and
qualified reading events. Random and in-batch negatives are supplemented with
hard negatives from the retrieval index. All signals must be observed before
the temporal split boundary.

## Architecture

- paper tower: normalized scientific text features projected to a compact space;
- reader tower: masked mean of recent paper features followed by a projection;
- loss: symmetric in-batch contrastive objective with temperature;
- reranker: separately versioned cross-encoder over query/document pairs.

## Evaluation

Report nDCG@10, Recall@K, MRR, coverage, diversity, novelty, latency, and
category/age slices. Synthetic readers validate behavior and load only.

## Limitations and risks

- Citation-derived training can reinforce established-field and popularity bias.
- Interaction data can encode exposure bias.
- Cold-start recommendations depend heavily on onboarding choices.
- A cross-encoder score is relevance evidence, not scientific correctness.
- Near-duplicate papers can inflate ranking metrics unless grouped first.

## Release requirements

Production weights require immutable data and feature manifests, configuration,
seed, code revision, raw evaluation results, bias slices, and rollback artifact.

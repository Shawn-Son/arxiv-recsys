# Retrieval and recommendation evaluation

## Dataset split

Use a temporal boundary. Training features contain only papers, interactions,
and citation edges observed before that boundary. Validation and test queries
come from later periods.

## Retrieval metrics

- Recall@20, Recall@50, and Recall@100 for candidate generation
- nDCG@10 and MRR@10 for final ranking
- coverage across arXiv categories and publication-age buckets
- duplicate rate and near-duplicate concentration in the top 20
- p50, p95, and p99 latency with corpus size, hardware, concurrency, and cache
  state recorded

## Deduplication metrics

Report precision, recall, F1, and false-merge examples against a labeled set.
Select the automated merge threshold primarily for precision. Report the
percentage reduction separately from correctness.

## Recommendation metrics

In addition to nDCG and recall, report catalog coverage, intra-list diversity,
novelty, and exposure by category. Synthetic readers test system behavior and
load; they do not substitute for online user evidence.

## Claim policy

A result can enter the README or résumé only when its report includes:

- immutable data and index manifests;
- baseline and treatment definitions;
- exact metric implementation;
- hardware and load profile for latency;
- raw per-query or per-run results;
- code revision and random seeds.

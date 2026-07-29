# Data governance

## Source policy

| Source | Purpose | Stored data | Refresh |
| --- | --- | --- | --- |
| arXiv OAI-PMH | Canonical paper metadata and versions | Metadata and abstracts | Daily |
| arXiv API | Focused reconciliation and fixture verification | Metadata responses | On demand, cached |
| OpenAlex | Citations and external identifiers | Edges and identifiers | Snapshot plus changes |

PDFs and source archives are not redistributed. Product links resolve to the
canonical arXiv abstract page.

## Provenance

Every ingestion batch records:

- source and source window;
- upstream cursor or resumption token;
- raw payload checksum;
- accepted and rejected record counts;
- code revision;
- schema and normalizer version;
- completion time and failure state.

Raw payload retention is controlled separately from canonical metadata.

## Identity and versions

An arXiv identifier without a version identifies the work. Each `vN` record is
stored as an immutable version beneath that work. A new version never overwrites
the text or checksum of an earlier version.

## Deduplication

Deduplication evaluates exact arXiv work identity, DOI identity, title MinHash,
author overlap, and publication proximity. Probable matches remain reviewable.
The production merge threshold is selected using a labeled dataset and must
prioritize false-merge prevention.

## Research reproducibility

Published evaluation artifacts refer to immutable data-manifest IDs. Splits are
temporal, and citation edges observed after the split boundary are excluded from
training features.

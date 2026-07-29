# Product specification

## Problem

Researchers can retrieve papers by keyword, but building a current, coherent
reading trail still requires repeated searching, manual deduplication, and
opaque relevance judgments. Aster should reduce that coordination cost without
hiding why a result appeared.

## Primary users

- Researchers entering an adjacent field
- Applied scientists maintaining a current literature view
- Research engineers building a defensible reading set
- Students organizing papers for a review or thesis

## Core journeys

### Discover

A researcher submits a natural-language question, applies field and date
filters, reviews ranked abstracts, and opens the arXiv source.

### Build a reading trail

A researcher saves papers into a library. Saves and explicit feedback become
recommendation signals while remaining visible and removable.

### Stay current

A researcher saves a search or topic. A daily job identifies materially new
papers and creates an explainable brief.

### Export

A researcher exports a collection as BibTeX, CSV, or JSON with stable arXiv and
DOI identifiers.

## Non-goals for the first release

- Hosting or redistributing paper PDFs
- Generating paper summaries without citations to source text
- Claiming online-user improvements from synthetic readers
- Hiding sponsored or popularity-only ranking signals

## Release gates

- All ingestion jobs are idempotent and produce data manifests.
- Retrieval is evaluated against a frozen lexical baseline.
- Latency results state corpus size, hardware, concurrency, and warm/cold state.
- Deduplication reports precision, recall, and false-merge examples.
- The public UI meets keyboard and screen-reader acceptance checks.
- Backup restoration is tested before the production corpus is declared ready.

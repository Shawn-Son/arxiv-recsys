# Aster API

The API owns canonical paper contracts, ingestion normalization, deduplication
signals, and the boundary consumed by the web and retrieval services.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn arxiv_recsys.main:app --reload --port 8000
```

Documentation is available at `http://localhost:8000/docs`.

The development service loads a small, explicitly labeled fixture. Production
storage is introduced through the canonical migration and a repository adapter;
the API contract does not expose storage-specific fields.

Liveness is exposed at `/healthz`; readiness is exposed at `/readyz`. See the
[operations runbook](../../docs/operations.md) for private metrics, request
tracing, load testing, and incident handling.

## Retrieval benchmark

```bash
uv run python benchmarks/run_retrieval.py --repetitions 100
```

The bundled relevance judgments exist to test metric and artifact plumbing.
Their output is always labeled as a representative fixture and must not be used
as a production quality claim.

Build a fixture FAISS artifact without overwriting an existing release:

```bash
uv run --extra retrieval python scripts/build_index.py \
  --output ../../work/index-fixture \
  --artifact-id fixture-index-v1 \
  --corpus-manifest fixture-2026-07-28 \
  --code-revision "$(git rev-parse HEAD)"
```

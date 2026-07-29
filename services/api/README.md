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

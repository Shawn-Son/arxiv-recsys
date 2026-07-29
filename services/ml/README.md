# Aster ML

This package contains the recommendation and reranking contracts behind Aster:

- PyTorch two-tower paper and reader encoders
- citation-pair contrastive training
- cross-encoder reranking boundary
- leakage-resistant temporal splits
- deterministic reader simulation for behavior and load tests

The package ships a small correctness suite, not pretrained production weights.
Quality metrics require the frozen corpus and evaluation manifests described in
the repository evaluation contract.

## Local validation

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest --cov=aster_ml --cov-report=term-missing
```

The optional `reranker` extra installs Sentence Transformers. Model downloads
are never performed during import or CI.

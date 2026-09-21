# Aster

Aster is a citation-aware search and recommendation workspace for arXiv
research. It combines hybrid retrieval, transparent reranking, personalized
reading trails, and reproducible evaluation in one system. Under active development.

[API specification](services/api/README.md) ·
[Evaluation contract](docs/evaluation.md)

> **Project status:** in development, not deployed. The interface currently uses a small
> representative fixture while the ingestion and retrieval services are being
> implemented. Corpus size and quality metrics are published only after they
> are reproduced by the versioned benchmark suite.

## Product principles

- **Evidence before popularity.** Lexical, semantic, and citation signals are
  evaluated independently before they are fused.
- **Explanations by default.** Results and recommendations expose the signals
  that affected their position.
- **Research-grade reproducibility.** Data manifests, model cards, temporal
  splits, and benchmark environments are versioned with each release.
- **Responsible source use.** Paper downloads link back to arXiv and ingestion
  respects upstream access policies.

## Local development

Requirements:

- Node.js 22.13 or newer
- npm 10 or newer

```bash
npm ci
npm run dev
```

Open `http://localhost:3000`.

Run the full local quality gate:

```bash
npm run check
```

## Repository map

```text
app/                 Web product and route handlers
services/api/        Versioned metadata, ingestion, and retrieval API
services/ml/         Recommendation, reranking, and simulation contracts
docs/                Product, architecture, and decision records
tests/               Render and contract tests
worker/              Cloudflare-compatible application entrypoint
.github/workflows/   Continuous integration and security automation
```

Each service owns its dependency lock, test suite, and release contract so the
web, retrieval, and model layers can evolve without hidden environment coupling.

## Delivery roadmap

1. Production baseline, CI, and product shell
2. arXiv ingestion, canonical records, and citation enrichment
3. Hybrid FAISS retrieval and versioned REST API
4. Persistent research library and alert workflow
5. Two-tower recommendations, cross-encoder reranking, and evaluation
6. Production observability, load testing, and full-corpus deployment

See [the product specification](docs/product-spec.md) and
[system architecture](docs/architecture.md) for the acceptance criteria.

## License

Apache-2.0. See [LICENSE](LICENSE).

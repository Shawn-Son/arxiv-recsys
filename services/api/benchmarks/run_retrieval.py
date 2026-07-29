import argparse
import json
import time
from pathlib import Path

from arxiv_recsys.evaluation import ndcg_at_k, percentile, recall_at_k
from arxiv_recsys.repository import FixturePaperRepository
from arxiv_recsys.retrieval.hybrid import Bm25Index, HybridSearchEngine


def run(relevance_path: Path, repetitions: int) -> dict:
    judgments = json.loads(relevance_path.read_text())
    repository = FixturePaperRepository.from_package_data()
    papers = list(repository.all())
    documents = {
        paper.arxiv_id: f"{paper.title} {paper.abstract}"
        for paper in papers
    }
    lexical = Bm25Index(documents)
    hybrid = HybridSearchEngine(papers)

    query_results = []
    latencies_ms: list[float] = []
    for item in judgments:
        query = item["query"]
        relevance = item["relevance"]
        lexical_ids = [paper_id for paper_id, _ in lexical.search(query, limit=10)]
        hybrid_ids = [result.paper_id for result in hybrid.search(query, limit=10)]
        query_results.append(
            {
                "query": query,
                "bm25_ndcg_at_10": ndcg_at_k(lexical_ids, relevance, 10),
                "hybrid_ndcg_at_10": ndcg_at_k(hybrid_ids, relevance, 10),
                "hybrid_recall_at_10": recall_at_k(hybrid_ids, relevance, 10),
            }
        )
        for _ in range(repetitions):
            started = time.perf_counter()
            hybrid.search(query, limit=10)
            latencies_ms.append((time.perf_counter() - started) * 1000)

    mean_bm25 = sum(item["bm25_ndcg_at_10"] for item in query_results) / len(query_results)
    mean_hybrid = sum(item["hybrid_ndcg_at_10"] for item in query_results) / len(query_results)
    return {
        "scope": "representative fixture; not a production quality claim",
        "queries": len(query_results),
        "repetitions_per_query": repetitions,
        "bm25_ndcg_at_10": mean_bm25,
        "hybrid_ndcg_at_10": mean_hybrid,
        "relative_ndcg_change": (
            (mean_hybrid - mean_bm25) / mean_bm25 if mean_bm25 else None
        ),
        "latency_ms": {
            "p50": percentile(latencies_ms, 0.50),
            "p95": percentile(latencies_ms, 0.95),
            "p99": percentile(latencies_ms, 0.99),
        },
        "results": query_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--relevance",
        type=Path,
        default=Path(__file__).with_name("relevance.json"),
    )
    parser.add_argument("--repetitions", type=int, default=100)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()

    report = run(arguments.relevance, arguments.repetitions)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(payload)
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()

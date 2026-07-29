from dataclasses import dataclass
from typing import Protocol


class PairScorer(Protocol):
    model_name: str

    def predict(self, pairs: list[tuple[str, str]]) -> list[float]: ...


@dataclass(frozen=True)
class RerankedCandidate:
    paper_id: str
    text: str
    retrieval_score: float
    reranker_score: float
    final_score: float


def rerank(
    *,
    query: str,
    candidates: list[tuple[str, str, float]],
    scorer: PairScorer,
    limit: int,
    retrieval_weight: float = 0.15,
) -> list[RerankedCandidate]:
    if limit <= 0:
        raise ValueError("Reranking limit must be positive")
    if not 0 <= retrieval_weight <= 1:
        raise ValueError("Retrieval weight must be between zero and one")
    pairs = [(query, text) for _, text, _ in candidates]
    scores = scorer.predict(pairs)
    if len(scores) != len(candidates):
        raise ValueError("Reranker score count does not match candidates")

    results = [
        RerankedCandidate(
            paper_id=paper_id,
            text=text,
            retrieval_score=retrieval_score,
            reranker_score=reranker_score,
            final_score=(
                retrieval_weight * retrieval_score
                + (1 - retrieval_weight) * reranker_score
            ),
        )
        for (paper_id, text, retrieval_score), reranker_score in zip(
            candidates,
            scores,
            strict=True,
        )
    ]
    results.sort(key=lambda item: (-item.final_score, item.paper_id))
    return results[:limit]


class SentenceTransformersCrossEncoder:
    """Lazy production adapter; construction is the only model-loading point."""

    def __init__(self, model_name: str, **model_options: object) -> None:
        from sentence_transformers import CrossEncoder

        self.model_name = model_name
        self._model = CrossEncoder(model_name, **model_options)

    def predict(self, pairs: list[tuple[str, str]]) -> list[float]:
        values = self._model.predict(pairs)
        return [float(value) for value in values]

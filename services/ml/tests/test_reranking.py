from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from aster_ml.reranking import SentenceTransformersCrossEncoder, rerank


class StaticScorer:
    model_name = "static-test-scorer"

    def __init__(self, scores: list[float]) -> None:
        self.scores = scores
        self.pairs: list[tuple[str, str]] = []

    def predict(self, pairs: list[tuple[str, str]]) -> list[float]:
        self.pairs = pairs
        return self.scores


def test_rerank_blends_scores_orders_results_and_applies_limit() -> None:
    scorer = StaticScorer([0.2, 0.9, 0.4])
    candidates = [
        ("paper-a", "Alpha", 0.95),
        ("paper-b", "Beta", 0.40),
        ("paper-c", "Gamma", 0.50),
    ]

    results = rerank(
        query="graph learning",
        candidates=candidates,
        scorer=scorer,
        limit=2,
        retrieval_weight=0.25,
    )

    assert scorer.pairs == [
        ("graph learning", "Alpha"),
        ("graph learning", "Beta"),
        ("graph learning", "Gamma"),
    ]
    assert [result.paper_id for result in results] == ["paper-b", "paper-c"]
    assert results[0].final_score == pytest.approx(0.775)
    assert results[0].reranker_score == 0.9


@pytest.mark.parametrize("weight", [-0.01, 1.01])
def test_rerank_rejects_invalid_weight(weight: float) -> None:
    with pytest.raises(ValueError, match="weight"):
        rerank(
            query="query",
            candidates=[],
            scorer=StaticScorer([]),
            limit=1,
            retrieval_weight=weight,
        )


def test_rerank_rejects_invalid_limit_and_score_count() -> None:
    with pytest.raises(ValueError, match="limit"):
        rerank(
            query="query",
            candidates=[],
            scorer=StaticScorer([]),
            limit=0,
        )
    with pytest.raises(ValueError, match="score count"):
        rerank(
            query="query",
            candidates=[("id", "text", 0.5)],
            scorer=StaticScorer([]),
            limit=1,
        )


def test_sentence_transformers_adapter_loads_lazily(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeCrossEncoder:
        def __init__(self, model_name: str, **options: object) -> None:
            self.model_name = model_name
            self.options = options

        def predict(self, pairs: list[tuple[str, str]]) -> list[float]:
            return [index + 0.25 for index, _ in enumerate(pairs)]

    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(CrossEncoder=FakeCrossEncoder),
    )
    adapter = SentenceTransformersCrossEncoder("test/model", device="cpu")

    assert adapter.model_name == "test/model"
    assert adapter.predict([("q", "one"), ("q", "two")]) == [0.25, 1.25]

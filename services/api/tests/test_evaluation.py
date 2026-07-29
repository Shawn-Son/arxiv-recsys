import pytest

from arxiv_recsys.evaluation import dcg_at_k, ndcg_at_k, percentile, recall_at_k


def test_ranking_metrics_reward_the_ideal_order() -> None:
    relevance = {"best": 3, "good": 2, "related": 1}
    ideal = ["best", "good", "related", "noise"]
    reversed_order = list(reversed(ideal))

    assert ndcg_at_k(ideal, relevance, 10) == 1.0
    assert ndcg_at_k(reversed_order, relevance, 10) < 1.0
    assert dcg_at_k(ideal, relevance, 2) > dcg_at_k(reversed_order, relevance, 2)
    assert recall_at_k(ideal, relevance, 2) == pytest.approx(2 / 3)


def test_metrics_handle_empty_relevance_and_validate_percentiles() -> None:
    assert ndcg_at_k(["paper"], {}, 10) == 0.0
    assert recall_at_k(["paper"], {}, 10) == 0.0
    assert percentile([1.0, 2.0, 3.0], 0.5) == 2.0
    assert percentile([1.0, 3.0], 0.5) == 2.0

    with pytest.raises(ValueError, match="without values"):
        percentile([], 0.5)
    with pytest.raises(ValueError, match="between zero and one"):
        percentile([1.0], 1.1)

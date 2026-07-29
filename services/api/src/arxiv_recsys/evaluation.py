import math


def dcg_at_k(ranked_ids: list[str], relevance: dict[str, int], k: int) -> float:
    return sum(
        (2 ** relevance.get(paper_id, 0) - 1) / math.log2(rank + 1)
        for rank, paper_id in enumerate(ranked_ids[:k], start=1)
    )


def ndcg_at_k(ranked_ids: list[str], relevance: dict[str, int], k: int) -> float:
    ideal = sorted(relevance, key=lambda paper_id: relevance[paper_id], reverse=True)
    denominator = dcg_at_k(ideal, relevance, k)
    return dcg_at_k(ranked_ids, relevance, k) / denominator if denominator else 0.0


def recall_at_k(ranked_ids: list[str], relevance: dict[str, int], k: int) -> float:
    relevant = {paper_id for paper_id, grade in relevance.items() if grade > 0}
    if not relevant:
        return 0.0
    return len(set(ranked_ids[:k]) & relevant) / len(relevant)


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("Cannot calculate a percentile without values")
    if not 0 <= quantile <= 1:
        raise ValueError("Quantile must be between zero and one")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight

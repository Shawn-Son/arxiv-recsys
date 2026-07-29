import math


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        raise ValueError("Cannot calculate a percentile without observations")
    if not 0 <= percentile_value <= 100:
        raise ValueError("Percentile must be between zero and one hundred")
    ordered = sorted(values)
    rank = max(0, math.ceil(percentile_value / 100 * len(ordered)) - 1)
    return ordered[rank]

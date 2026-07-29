import pytest

from arxiv_recsys.load_testing import percentile


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, 1.0), (50, 2.0), (95, 4.0), (99, 4.0), (100, 4.0)],
)
def test_percentile_uses_nearest_rank(value: float, expected: float) -> None:
    assert percentile([4.0, 1.0, 3.0, 2.0], value) == expected


def test_percentile_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="observations"):
        percentile([], 50)
    with pytest.raises(ValueError, match="between"):
        percentile([1], 101)

from datetime import UTC, datetime

import pytest

from aster_ml.splits import TimedExample, temporal_split


def at(day: int) -> datetime:
    return datetime(2026, 7, day, tzinfo=UTC)


def test_temporal_split_orders_examples_and_respects_boundaries() -> None:
    examples = [
        TimedExample("test", at(20)),
        TimedExample("train-b", at(2)),
        TimedExample("validation-end", at(19)),
        TimedExample("validation-start", at(10)),
        TimedExample("train-a", at(2)),
    ]

    result = temporal_split(
        examples,
        validation_start=at(10),
        test_start=at(20),
    )

    assert [item.id for item in result.train] == ["train-a", "train-b"]
    assert [item.id for item in result.validation] == [
        "validation-start",
        "validation-end",
    ]
    assert [item.id for item in result.test] == ["test"]


@pytest.mark.parametrize(
    ("validation_start", "test_start"),
    [(at(10), at(10)), (at(20), at(10))],
)
def test_temporal_split_rejects_overlapping_periods(
    validation_start: datetime,
    test_start: datetime,
) -> None:
    with pytest.raises(ValueError, match="before"):
        temporal_split(
            [],
            validation_start=validation_start,
            test_start=test_start,
        )

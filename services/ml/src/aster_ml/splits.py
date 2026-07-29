from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TimedExample:
    id: str
    observed_at: datetime


@dataclass(frozen=True)
class TemporalSplit:
    train: tuple[TimedExample, ...]
    validation: tuple[TimedExample, ...]
    test: tuple[TimedExample, ...]


def temporal_split(
    examples: list[TimedExample],
    *,
    validation_start: datetime,
    test_start: datetime,
) -> TemporalSplit:
    if validation_start >= test_start:
        raise ValueError("Validation must begin before the test period")
    ordered = sorted(examples, key=lambda item: (item.observed_at, item.id))
    return TemporalSplit(
        train=tuple(item for item in ordered if item.observed_at < validation_start),
        validation=tuple(
            item
            for item in ordered
            if validation_start <= item.observed_at < test_start
        ),
        test=tuple(item for item in ordered if item.observed_at >= test_start),
    )

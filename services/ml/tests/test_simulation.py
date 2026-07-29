import pytest

from aster_ml.simulation import SimulationConfig, simulate_readers


def test_default_simulation_is_deterministic_and_has_expected_scale() -> None:
    first = simulate_readers(SimulationConfig())
    second = simulate_readers(SimulationConfig())

    assert first == second
    assert first.reader_count == 10_000
    assert first.topic_count == 40
    assert first.session_count >= first.reader_count
    assert first.event_count >= first.session_count
    assert 0 < first.saved_event_count < first.event_count
    assert len(first.topic_exposure) == 40
    assert sum(first.topic_exposure) == first.event_count
    assert first.mean_profile_entropy > 0


def test_seed_changes_simulation() -> None:
    baseline = simulate_readers(SimulationConfig(reader_count=50, seed=1))
    changed = simulate_readers(SimulationConfig(reader_count=50, seed=2))

    assert baseline != changed


@pytest.mark.parametrize(
    "overrides",
    [
        {"reader_count": 0},
        {"topic_count": -1},
        {"mean_sessions_per_reader": 0},
        {"mean_events_per_session": -1},
    ],
)
def test_simulation_config_rejects_invalid_values(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        SimulationConfig(**overrides)

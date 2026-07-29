from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class SimulationConfig:
    reader_count: int = 10_000
    topic_count: int = 40
    mean_sessions_per_reader: float = 6.0
    mean_events_per_session: float = 4.0
    seed: int = 20260728

    def __post_init__(self) -> None:
        if min(self.reader_count, self.topic_count) <= 0:
            raise ValueError("Reader and topic counts must be positive")
        if min(self.mean_sessions_per_reader, self.mean_events_per_session) <= 0:
            raise ValueError("Simulation rates must be positive")


@dataclass(frozen=True)
class SimulationReport:
    reader_count: int
    topic_count: int
    session_count: int
    event_count: int
    saved_event_count: int
    topic_exposure: tuple[int, ...]
    mean_profile_entropy: float


def _entropy(profiles: NDArray[np.float64]) -> float:
    safe = np.clip(profiles, 1e-12, 1)
    return float(np.mean(-np.sum(safe * np.log(safe), axis=1)))


def simulate_readers(config: SimulationConfig) -> SimulationReport:
    rng = np.random.default_rng(config.seed)
    concentration = np.full(config.topic_count, 0.35)
    profiles = rng.dirichlet(concentration, size=config.reader_count)
    sessions = rng.poisson(
        config.mean_sessions_per_reader,
        size=config.reader_count,
    )
    sessions = np.maximum(sessions, 1)
    event_count_by_reader = rng.poisson(
        sessions * config.mean_events_per_session,
    )
    event_count_by_reader = np.maximum(event_count_by_reader, sessions)
    event_count = int(event_count_by_reader.sum())

    weighted_topics = profiles * event_count_by_reader[:, None]
    expected_exposure = weighted_topics.sum(axis=0)
    topic_exposure = rng.multinomial(
        event_count,
        expected_exposure / expected_exposure.sum(),
    )
    save_probabilities = np.clip(0.08 + profiles.max(axis=1) * 0.12, 0, 0.35)
    saved_event_count = int(
        rng.binomial(event_count_by_reader, save_probabilities).sum()
    )

    return SimulationReport(
        reader_count=config.reader_count,
        topic_count=config.topic_count,
        session_count=int(sessions.sum()),
        event_count=event_count,
        saved_event_count=saved_event_count,
        topic_exposure=tuple(int(value) for value in topic_exposure),
        mean_profile_entropy=_entropy(profiles),
    )

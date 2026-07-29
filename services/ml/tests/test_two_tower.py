from __future__ import annotations

import random

import numpy as np
import pytest
import torch

from aster_ml.training import set_reproducible_seed, train_step
from aster_ml.two_tower import TwoTowerConfig, TwoTowerModel


def small_config(**overrides: object) -> TwoTowerConfig:
    values = {
        "input_dimensions": 6,
        "hidden_dimensions": 8,
        "embedding_dimensions": 4,
        "temperature": 0.2,
        "dropout": 0.0,
    }
    values.update(overrides)
    return TwoTowerConfig(**values)


@pytest.mark.parametrize(
    "overrides",
    [
        {"input_dimensions": 0},
        {"hidden_dimensions": -1},
        {"embedding_dimensions": 0},
        {"temperature": 0},
        {"dropout": -0.1},
        {"dropout": 1.0},
    ],
)
def test_config_rejects_invalid_values(overrides: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        small_config(**overrides)


def test_model_returns_normalized_embeddings_and_pairwise_logits() -> None:
    model = TwoTowerModel(small_config())
    history = torch.randn(3, 4, 6)
    mask = torch.tensor(
        [[True, True, False, False], [True, True, True, False], [True, False, False, False]]
    )
    papers = torch.randn(3, 6)

    readers = model.reader_tower(history, mask)
    paper_embeddings = model.paper_tower(papers)
    logits = model(history, mask, papers)
    loss = model.contrastive_loss(history, mask, papers)

    assert logits.shape == (3, 3)
    assert torch.allclose(torch.linalg.vector_norm(readers, dim=1), torch.ones(3))
    assert torch.allclose(torch.linalg.vector_norm(paper_embeddings, dim=1), torch.ones(3))
    assert torch.isfinite(loss)


def test_towers_validate_feature_and_history_shapes() -> None:
    model = TwoTowerModel(small_config())

    with pytest.raises(ValueError, match="dimensions"):
        model.paper_tower(torch.randn(2, 5))
    with pytest.raises(ValueError, match="history must"):
        model.reader_tower(torch.randn(2, 6), torch.ones(2, dtype=torch.bool))
    with pytest.raises(ValueError, match="wrong shape"):
        model.reader_tower(torch.randn(2, 3, 6), torch.ones(2, 2, dtype=torch.bool))
    with pytest.raises(ValueError, match="at least one"):
        model.reader_tower(torch.randn(2, 3, 6), torch.zeros(2, 3, dtype=torch.bool))


def test_seed_controls_python_numpy_and_torch() -> None:
    set_reproducible_seed(17)
    first = (random.random(), np.random.random(), torch.rand(1))
    set_reproducible_seed(17)
    second = (random.random(), np.random.random(), torch.rand(1))

    assert first[0] == second[0]
    assert first[1] == second[1]
    assert torch.equal(first[2], second[2])


def test_train_step_updates_parameters_and_reports_finite_metrics() -> None:
    set_reproducible_seed(23)
    model = TwoTowerModel(small_config())
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.01)
    history = torch.randn(4, 3, 6)
    mask = torch.ones(4, 3, dtype=torch.bool)
    positives = torch.randn(4, 6)
    before = [parameter.detach().clone() for parameter in model.parameters()]

    result = train_step(
        model=model,
        optimizer=optimizer,
        history_features=history,
        history_mask=mask,
        positive_features=positives,
    )

    assert np.isfinite(result.loss)
    assert np.isfinite(result.gradient_norm)
    assert any(
        not torch.equal(previous, current)
        for previous, current in zip(before, model.parameters(), strict=True)
    )


def test_train_step_validates_gradient_limit_and_non_finite_loss() -> None:
    class NonFiniteModel(TwoTowerModel):
        def contrastive_loss(
            self,
            history_features: torch.Tensor,
            history_mask: torch.Tensor,
            positive_features: torch.Tensor,
        ) -> torch.Tensor:
            return torch.tensor(float("inf"), requires_grad=True)

    model = NonFiniteModel(small_config())
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    features = torch.randn(2, 2, 6)
    mask = torch.ones(2, 2, dtype=torch.bool)
    positives = torch.randn(2, 6)

    with pytest.raises(ValueError, match="positive"):
        train_step(
            model=model,
            optimizer=optimizer,
            history_features=features,
            history_mask=mask,
            positive_features=positives,
            max_gradient_norm=0,
        )
    with pytest.raises(FloatingPointError, match="not finite"):
        train_step(
            model=model,
            optimizer=optimizer,
            history_features=features,
            history_mask=mask,
            positive_features=positives,
        )

import random
from dataclasses import dataclass

import numpy as np
import torch
from torch import Tensor

from aster_ml.two_tower import TwoTowerModel


def set_reproducible_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


@dataclass(frozen=True)
class TrainingStepResult:
    loss: float
    gradient_norm: float


def train_step(
    *,
    model: TwoTowerModel,
    optimizer: torch.optim.Optimizer,
    history_features: Tensor,
    history_mask: Tensor,
    positive_features: Tensor,
    max_gradient_norm: float = 1.0,
) -> TrainingStepResult:
    if max_gradient_norm <= 0:
        raise ValueError("Maximum gradient norm must be positive")
    model.train()
    optimizer.zero_grad(set_to_none=True)
    loss = model.contrastive_loss(
        history_features,
        history_mask,
        positive_features,
    )
    if not torch.isfinite(loss):
        raise FloatingPointError("Training loss is not finite")
    loss.backward()
    gradient_norm = torch.nn.utils.clip_grad_norm_(
        model.parameters(),
        max_gradient_norm,
    )
    optimizer.step()
    return TrainingStepResult(
        loss=float(loss.detach()),
        gradient_norm=float(gradient_norm),
    )

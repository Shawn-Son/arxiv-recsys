from dataclasses import dataclass

import torch
from torch import Tensor, nn
from torch.nn import functional as F


@dataclass(frozen=True)
class TwoTowerConfig:
    input_dimensions: int = 384
    hidden_dimensions: int = 256
    embedding_dimensions: int = 128
    temperature: float = 0.07
    dropout: float = 0.1

    def __post_init__(self) -> None:
        if min(
            self.input_dimensions,
            self.hidden_dimensions,
            self.embedding_dimensions,
        ) <= 0:
            raise ValueError("Tower dimensions must be positive")
        if self.temperature <= 0:
            raise ValueError("Temperature must be positive")
        if not 0 <= self.dropout < 1:
            raise ValueError("Dropout must be between zero (inclusive) and one")


class ProjectionTower(nn.Module):
    def __init__(self, config: TwoTowerConfig) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.LayerNorm(config.input_dimensions),
            nn.Linear(config.input_dimensions, config.hidden_dimensions),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dimensions, config.embedding_dimensions),
        )

    def forward(self, features: Tensor) -> Tensor:
        if features.shape[-1] != self.network[0].normalized_shape[0]:
            raise ValueError("Feature dimensions do not match the tower configuration")
        return F.normalize(self.network(features), dim=-1)


class ReaderTower(nn.Module):
    def __init__(self, config: TwoTowerConfig) -> None:
        super().__init__()
        self.projection = ProjectionTower(config)

    def forward(self, history_features: Tensor, history_mask: Tensor) -> Tensor:
        if history_features.ndim != 3:
            raise ValueError("Reader history must be [batch, history, features]")
        if history_mask.shape != history_features.shape[:2]:
            raise ValueError("Reader history mask has the wrong shape")
        if not torch.any(history_mask, dim=1).all():
            raise ValueError("Every reader must have at least one history item")
        weights = history_mask.to(history_features.dtype).unsqueeze(-1)
        denominator = weights.sum(dim=1).clamp_min(1)
        pooled = (history_features * weights).sum(dim=1) / denominator
        return self.projection(pooled)


class PaperTower(ProjectionTower):
    pass


class TwoTowerModel(nn.Module):
    def __init__(self, config: TwoTowerConfig) -> None:
        super().__init__()
        self.config = config
        self.reader_tower = ReaderTower(config)
        self.paper_tower = PaperTower(config)

    def forward(
        self,
        history_features: Tensor,
        history_mask: Tensor,
        candidate_features: Tensor,
    ) -> Tensor:
        readers = self.reader_tower(history_features, history_mask)
        papers = self.paper_tower(candidate_features)
        return readers @ papers.T / self.config.temperature

    def contrastive_loss(
        self,
        history_features: Tensor,
        history_mask: Tensor,
        positive_features: Tensor,
    ) -> Tensor:
        logits = self(history_features, history_mask, positive_features)
        labels = torch.arange(logits.shape[0], device=logits.device)
        return F.cross_entropy(logits, labels)

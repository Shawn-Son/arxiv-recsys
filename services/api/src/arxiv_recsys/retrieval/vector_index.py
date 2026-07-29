from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray


class VectorIndex(Protocol):
    dimensions: int

    def add(self, ids: list[str], vectors: NDArray[np.float32]) -> None: ...

    def search(
        self,
        query: NDArray[np.float32],
        limit: int,
    ) -> list[tuple[str, float]]: ...


class ExactVectorIndex:
    """Deterministic reference implementation used for correctness tests."""

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions
        self._ids: list[str] = []
        self._vectors = np.empty((0, dimensions), dtype=np.float32)

    def add(self, ids: list[str], vectors: NDArray[np.float32]) -> None:
        if vectors.shape != (len(ids), self.dimensions):
            raise ValueError("Vector matrix shape does not match IDs and dimensions")
        self._ids.extend(ids)
        self._vectors = np.concatenate([self._vectors, vectors.astype(np.float32)])

    def search(
        self,
        query: NDArray[np.float32],
        limit: int,
    ) -> list[tuple[str, float]]:
        if query.shape != (self.dimensions,):
            raise ValueError("Query vector has the wrong dimensions")
        if not self._ids:
            return []
        scores = self._vectors @ query
        order = np.argsort(-scores, stable=True)[:limit]
        return [(self._ids[index], float(scores[index])) for index in order]


class FaissVectorIndex:
    """FAISS HNSW cosine index with explicit external-ID persistence."""

    def __init__(self, dimensions: int, hnsw_connections: int = 32) -> None:
        import faiss

        self.dimensions = dimensions
        self._faiss = faiss
        self._index = faiss.IndexHNSWFlat(
            dimensions,
            hnsw_connections,
            faiss.METRIC_INNER_PRODUCT,
        )
        self._ids: list[str] = []

    def add(self, ids: list[str], vectors: NDArray[np.float32]) -> None:
        if vectors.shape != (len(ids), self.dimensions):
            raise ValueError("Vector matrix shape does not match IDs and dimensions")
        normalized = np.ascontiguousarray(vectors.astype(np.float32))
        self._faiss.normalize_L2(normalized)
        self._index.add(normalized)
        self._ids.extend(ids)

    def search(
        self,
        query: NDArray[np.float32],
        limit: int,
    ) -> list[tuple[str, float]]:
        normalized = np.ascontiguousarray(query.astype(np.float32).reshape(1, -1))
        self._faiss.normalize_L2(normalized)
        scores, positions = self._index.search(normalized, min(limit, len(self._ids)))
        return [
            (self._ids[int(position)], float(score))
            for score, position in zip(scores[0], positions[0], strict=True)
            if position >= 0
        ]

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        self._faiss.write_index(self._index, str(directory / "vectors.faiss"))
        (directory / "ids.txt").write_text("\n".join(self._ids) + "\n")

    @classmethod
    def load(cls, directory: Path) -> "FaissVectorIndex":
        import faiss

        index = faiss.read_index(str(directory / "vectors.faiss"))
        instance = cls.__new__(cls)
        instance.dimensions = index.d
        instance._faiss = faiss
        instance._index = index
        instance._ids = (directory / "ids.txt").read_text().splitlines()
        if index.ntotal != len(instance._ids):
            raise ValueError("FAISS index and external ID manifest disagree")
        return instance

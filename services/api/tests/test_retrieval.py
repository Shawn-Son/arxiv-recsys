from pathlib import Path

import numpy as np
import pytest

from arxiv_recsys.repository import FixturePaperRepository
from arxiv_recsys.retrieval.artifact import (
    create_manifest,
    validate_artifact,
)
from arxiv_recsys.retrieval.encoder import HashingTextEncoder
from arxiv_recsys.retrieval.hybrid import Bm25Index, HybridSearchEngine
from arxiv_recsys.retrieval.vector_index import ExactVectorIndex, FaissVectorIndex


def test_hashing_encoder_is_normalized_and_deterministic() -> None:
    encoder = HashingTextEncoder(dimensions=64)
    values = encoder.encode(["scientific discovery", "scientific discovery"])

    assert values.shape == (2, 64)
    assert np.allclose(values[0], values[1])
    assert np.isclose(np.linalg.norm(values[0]), 1.0)


def test_exact_vector_index_orders_cosine_scores() -> None:
    index = ExactVectorIndex(dimensions=3)
    index.add(
        ["best", "second", "last"],
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.8, 0.2, 0.0],
                [0.0, 1.0, 0.0],
            ],
            dtype=np.float32,
        ),
    )

    result = index.search(np.array([1.0, 0.0, 0.0], dtype=np.float32), limit=2)

    assert [item[0] for item in result] == ["best", "second"]


def test_bm25_prefers_exact_scientific_terms() -> None:
    index = Bm25Index(
        {
            "matching": "large language models for automated scientific discovery",
            "other": "graph networks for climate forecasting",
        }
    )

    results = index.search("language models scientific discovery", limit=2)

    assert results[0][0] == "matching"
    assert results[0][1] > results[1][1]


def test_hybrid_retrieval_is_stable_and_filterable() -> None:
    repository = FixturePaperRepository.from_package_data()
    papers = list(repository.all())
    engine = HybridSearchEngine(papers)

    first = engine.search("language models for scientific discovery", limit=3)
    second = engine.search("language models for scientific discovery", limit=3)
    filtered = engine.search(
        "language models for scientific discovery",
        category="stat.ML",
        limit=3,
    )

    assert first == second
    assert first[0].score == 1.0
    assert all(result.explanation for result in first)
    assert [result.paper_id for result in filtered] == ["2304.05376"]


def test_faiss_index_round_trip(tmp_path: Path) -> None:
    index = FaissVectorIndex(dimensions=3)
    vectors = np.array(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        dtype=np.float32,
    )
    index.add(["paper-a", "paper-b"], vectors)
    index.save(tmp_path)
    manifest = create_manifest(
        directory=tmp_path,
        artifact_id="test-index",
        corpus_manifest="fixture",
        encoder="test",
        dimensions=3,
        vector_count=2,
        index_kind="faiss-hnsw",
        code_revision="test",
    )
    manifest.write(tmp_path)

    restored = FaissVectorIndex.load(tmp_path)
    result = restored.search(np.array([1.0, 0.0, 0.0], dtype=np.float32), limit=1)

    assert result[0][0] == "paper-a"
    assert validate_artifact(tmp_path).id == "test-index"


def test_artifact_validation_rejects_mutation(tmp_path: Path) -> None:
    data = tmp_path / "ids.txt"
    data.write_text("paper-a\n")
    manifest = create_manifest(
        directory=tmp_path,
        artifact_id="test-index",
        corpus_manifest="fixture",
        encoder="test",
        dimensions=3,
        vector_count=1,
        index_kind="test",
        code_revision="test",
    )
    manifest.write(tmp_path)
    data.write_text("tampered\n")

    with pytest.raises(ValueError, match="checksum mismatch"):
        validate_artifact(tmp_path)

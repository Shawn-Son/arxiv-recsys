import json
from collections.abc import Iterable
from datetime import UTC, datetime
from importlib.resources import files
from time import perf_counter

from arxiv_recsys.models import (
    Author,
    IndexManifest,
    Paper,
    RankingEvidence,
    SearchHit,
    SearchResponse,
)
from arxiv_recsys.retrieval import HybridSearchEngine


class FixturePaperRepository:
    """Deterministic contract repository used until PostgreSQL is configured."""

    ranking_version = "metadata-baseline-v1"
    manifest_id = "fixture-2026-07-28"

    def __init__(self, papers: Iterable[Paper]) -> None:
        self._papers = {paper.arxiv_id: paper for paper in papers}
        self._retriever = HybridSearchEngine(list(self._papers.values()))

    @classmethod
    def from_package_data(cls) -> "FixturePaperRepository":
        payload = json.loads(
            files("arxiv_recsys.data").joinpath("sample_papers.json").read_text()
        )
        return cls(
            Paper(
                **{
                    **item,
                    "authors": tuple(Author(**author) for author in item["authors"]),
                }
            )
            for item in payload
        )

    def get(self, arxiv_id: str) -> Paper | None:
        return self._papers.get(arxiv_id)

    def all(self) -> tuple[Paper, ...]:
        return tuple(self._papers.values())

    def manifest(self) -> IndexManifest:
        return IndexManifest(
            id=self.manifest_id,
            source_mode="fixture",
            paper_count=len(self._papers),
            generated_at=datetime(2026, 7, 28, tzinfo=UTC),
            sources=("arXiv representative fixture",),
            notes="Contract fixture; not a production corpus or benchmark.",
        )

    def search(
        self,
        *,
        query: str,
        category: str | None,
        limit: int,
    ) -> SearchResponse:
        started = perf_counter()
        candidates = self._retriever.search(query, category=category, limit=limit)
        results = [
            SearchHit(
                paper=self._papers[result.paper_id],
                rank=rank,
                score=round(result.score, 6),
                evidence=RankingEvidence(
                    semantic=result.dense_score,
                    lexical=result.lexical_score,
                    citation=0.0,
                    explanation=result.explanation,
                ),
            )
            for rank, result in enumerate(candidates, start=1)
        ]
        return SearchResponse(
            query=query,
            total=len(results),
            limit=limit,
            results=results,
            ranking_version=self._retriever.version,
            index_manifest=self.manifest_id,
            source_mode="fixture",
            took_ms=round((perf_counter() - started) * 1000, 3),
        )

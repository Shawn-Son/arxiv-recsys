import json
import math
import re
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

TOKEN_PATTERN = re.compile(r"\w+")


def _tokens(value: str) -> set[str]:
    return {token for token in TOKEN_PATTERN.findall(value.casefold()) if len(token) > 2}


class FixturePaperRepository:
    """Deterministic contract repository used until PostgreSQL is configured."""

    ranking_version = "metadata-baseline-v1"
    manifest_id = "fixture-2026-07-28"

    def __init__(self, papers: Iterable[Paper]) -> None:
        self._papers = {paper.arxiv_id: paper for paper in papers}

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
        query_tokens = _tokens(query)
        candidates: list[tuple[Paper, float, RankingEvidence]] = []

        for paper in self._papers.values():
            if category and category not in paper.categories:
                continue
            title_tokens = _tokens(paper.title)
            abstract_tokens = _tokens(paper.abstract)
            matched = query_tokens & (title_tokens | abstract_tokens)
            lexical = len(matched) / max(1, len(query_tokens))
            title_match = len(query_tokens & title_tokens) / max(1, len(query_tokens))
            semantic = min(1.0, 0.35 + 0.45 * lexical + 0.2 * title_match)
            citation = min(1.0, math.log1p(paper.citation_count) / math.log(5000))
            score = min(1.0, 0.7 * semantic + 0.25 * lexical + 0.05 * citation)
            candidates.append(
                (
                    paper,
                    score,
                    RankingEvidence(
                        semantic=semantic,
                        lexical=lexical,
                        citation=citation,
                        explanation=(
                            f"{len(matched)} query concepts matched; citation is a capped "
                            "secondary signal."
                        ),
                    ),
                )
            )

        candidates.sort(key=lambda item: (-item[1], item[0].arxiv_id))
        results = [
            SearchHit(
                paper=paper,
                rank=rank,
                score=round(score, 6),
                evidence=evidence,
            )
            for rank, (paper, score, evidence) in enumerate(candidates[:limit], start=1)
        ]
        return SearchResponse(
            query=query,
            total=len(candidates),
            limit=limit,
            results=results,
            ranking_version=self.ranking_version,
            index_manifest=self.manifest_id,
            source_mode="fixture",
            took_ms=round((perf_counter() - started) * 1000, 3),
        )

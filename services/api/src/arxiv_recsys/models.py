from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Author(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1, max_length=300)
    orcid: str | None = None


class Paper(BaseModel):
    model_config = ConfigDict(frozen=True)

    arxiv_id: str = Field(pattern=r"^[a-zA-Z.-]+/\d{7}$|^\d{4}\.\d{4,5}$")
    version: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=1000)
    abstract: str = Field(min_length=1, max_length=20_000)
    authors: tuple[Author, ...]
    categories: tuple[str, ...]
    primary_category: str
    published_at: datetime
    updated_at: datetime
    doi: str | None = None
    journal_reference: str | None = None
    citation_count: int = Field(default=0, ge=0)
    source_url: HttpUrl


class RankingEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    semantic: float = Field(ge=0, le=1)
    lexical: float = Field(ge=0, le=1)
    citation: float = Field(ge=0, le=1)
    explanation: str


class SearchHit(BaseModel):
    paper: Paper
    rank: int = Field(ge=1)
    score: float = Field(ge=0, le=1)
    evidence: RankingEvidence


class SearchResponse(BaseModel):
    query: str
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    results: list[SearchHit]
    ranking_version: str
    index_manifest: str
    source_mode: Literal["fixture", "production"]
    took_ms: float = Field(ge=0)


class IndexManifest(BaseModel):
    id: str
    source_mode: Literal["fixture", "production"]
    paper_count: int = Field(ge=0)
    generated_at: datetime
    sources: tuple[str, ...]
    notes: str


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
    version: str
    timestamp: datetime


class DateRange(BaseModel):
    start: date | None = None
    end: date | None = None

    def contains(self, value: date) -> bool:
        return (self.start is None or value >= self.start) and (
            self.end is None or value <= self.end
        )

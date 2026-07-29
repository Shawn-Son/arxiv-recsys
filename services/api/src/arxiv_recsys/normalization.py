import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime

from arxiv_recsys.models import Author, Paper

ARXIV_ID_PATTERN = re.compile(
    r"(?:arxiv:)?(?P<identifier>[a-zA-Z.-]+/\d{7}|\d{4}\.\d{4,5})(?:v(?P<version>\d+))?",
    re.IGNORECASE,
)


def normalize_whitespace(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).split())


def normalize_title(value: str) -> str:
    normalized = normalize_whitespace(value).casefold()
    return re.sub(r"[^\w\s]", "", normalized)


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().casefold()
    cleaned = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", cleaned)
    return cleaned or None


@dataclass(frozen=True)
class ArxivIdentifier:
    canonical_id: str
    version: int


def parse_arxiv_identifier(value: str) -> ArxivIdentifier:
    match = ARXIV_ID_PATTERN.search(value.strip())
    if not match:
        raise ValueError(f"Invalid arXiv identifier: {value!r}")
    return ArxivIdentifier(
        canonical_id=match.group("identifier"),
        version=int(match.group("version") or 1),
    )


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def canonicalize_paper(
    *,
    identifier: str,
    title: str,
    abstract: str,
    authors: list[str],
    categories: list[str],
    primary_category: str,
    published_at: datetime,
    updated_at: datetime,
    doi: str | None = None,
    journal_reference: str | None = None,
    citation_count: int = 0,
) -> Paper:
    parsed = parse_arxiv_identifier(identifier)
    clean_categories = tuple(dict.fromkeys(item.strip() for item in categories if item.strip()))
    if not clean_categories:
        raise ValueError("At least one arXiv category is required")

    return Paper(
        arxiv_id=parsed.canonical_id,
        version=parsed.version,
        title=normalize_whitespace(title),
        abstract=normalize_whitespace(abstract),
        authors=tuple(
            Author(name=normalize_whitespace(author)) for author in authors if author.strip()
        ),
        categories=clean_categories,
        primary_category=primary_category.strip(),
        published_at=ensure_utc(published_at),
        updated_at=ensure_utc(updated_at),
        doi=normalize_doi(doi),
        journal_reference=(
            normalize_whitespace(journal_reference) if journal_reference else None
        ),
        citation_count=citation_count,
        source_url=f"https://arxiv.org/abs/{parsed.canonical_id}",
    )

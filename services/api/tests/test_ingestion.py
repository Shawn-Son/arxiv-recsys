from datetime import UTC, datetime
from pathlib import Path

import pytest

from arxiv_recsys.deduplication import (
    DuplicateReason,
    compare_papers,
    estimated_jaccard,
    minhash_signature,
)
from arxiv_recsys.ingestion.arxiv_atom import parse_arxiv_atom
from arxiv_recsys.ingestion.pipeline import BatchResult, process_batch
from arxiv_recsys.normalization import (
    canonicalize_paper,
    normalize_doi,
    normalize_title,
    parse_arxiv_identifier,
)

FIXTURES = Path(__file__).parent / "fixtures"


def make_paper(
    *,
    identifier: str,
    title: str,
    authors: list[str],
    doi: str | None = None,
):
    return canonicalize_paper(
        identifier=identifier,
        title=title,
        abstract="A sufficiently detailed scientific abstract for this test.",
        authors=authors,
        categories=["cs.LG"],
        primary_category="cs.LG",
        published_at=datetime(2024, 1, 1, tzinfo=UTC),
        updated_at=datetime(2024, 1, 2, tzinfo=UTC),
        doi=doi,
    )


def test_normalizes_identifiers_titles_and_dois() -> None:
    assert parse_arxiv_identifier("https://arxiv.org/abs/2402.19427v3").canonical_id == (
        "2402.19427"
    )
    assert parse_arxiv_identifier("arXiv:hep-th/9901001v2").version == 2
    assert normalize_title("  A  Paper:  With—Punctuation ") == "a paper withpunctuation"
    assert normalize_doi("https://doi.org/10.1000/ABC") == "10.1000/abc"


def test_rejects_invalid_identifier() -> None:
    with pytest.raises(ValueError, match="Invalid arXiv identifier"):
        parse_arxiv_identifier("not-an-arxiv-id")


def test_parses_atom_feed_into_canonical_paper() -> None:
    payload = (FIXTURES / "arxiv-feed.xml").read_text()
    papers = parse_arxiv_atom(payload)

    assert len(papers) == 1
    paper = papers[0]
    assert paper.arxiv_id == "2402.19427"
    assert paper.version == 2
    assert paper.primary_category == "cs.AI"
    assert paper.categories == ("cs.AI", "cs.LG")
    assert paper.authors[0].name == "Chris Lu"
    assert paper.doi == "10.5555/example.1"
    assert "\n" not in paper.title


def test_minhash_is_stable_and_estimates_identity() -> None:
    title = "Retrieval augmented generation for scientific discovery"
    left = minhash_signature(title)
    right = minhash_signature(title)

    assert left == right
    assert estimated_jaccard(left, right) == 1.0


def test_deduplicates_versions_and_dois_before_fuzzy_matching() -> None:
    original = make_paper(
        identifier="2402.19427v1",
        title="A Scientific Paper",
        authors=["A. Researcher"],
        doi="10.1000/paper",
    )
    version = make_paper(
        identifier="2402.19427v2",
        title="A Scientific Paper Revised",
        authors=["A. Researcher"],
    )
    published = make_paper(
        identifier="2403.00001",
        title="A Scientific Paper",
        authors=["A. Researcher"],
        doi="https://doi.org/10.1000/PAPER",
    )

    version_decision = compare_papers(original, version)
    doi_decision = compare_papers(original, published)

    assert version_decision.duplicate is True
    assert version_decision.reason == DuplicateReason.SAME_ARXIV_WORK
    assert doi_decision.duplicate is True
    assert doi_decision.reason == DuplicateReason.SAME_DOI


def test_keeps_different_work_distinct() -> None:
    left = make_paper(
        identifier="2401.00001",
        title="Transformers for Molecular Property Prediction",
        authors=["Ada Lovelace"],
    )
    right = make_paper(
        identifier="2401.00002",
        title="Graph Networks for Climate Forecasting",
        authors=["Grace Hopper"],
    )

    decision = compare_papers(left, right)

    assert decision.duplicate is False
    assert decision.reason == DuplicateReason.DISTINCT


class RecordingStore:
    def __init__(self, *, fail_upsert: bool = False) -> None:
        self.fail_upsert = fail_upsert
        self.events: list[str] = []
        self.result: BatchResult | None = None

    async def upsert_papers(self, papers, payload_sha256: str) -> None:
        self.events.append(f"upsert:{len(papers)}:{payload_sha256[:8]}")
        if self.fail_upsert:
            raise RuntimeError("database unavailable")

    async def save_cursor(self, source: str, cursor: str, result: BatchResult) -> None:
        self.events.append(f"cursor:{source}:{cursor}")
        self.result = result


@pytest.mark.anyio
async def test_advances_cursor_only_after_persisting_batch() -> None:
    payload = (FIXTURES / "arxiv-feed.xml").read_text()
    store = RecordingStore()

    result = await process_batch(
        source="arxiv",
        cursor="page-002",
        payload=payload,
        parser=parse_arxiv_atom,
        store=store,
    )

    assert store.events[0].startswith("upsert:1:")
    assert store.events[1] == "cursor:arxiv:page-002"
    assert result.payload_sha256 == store.result.payload_sha256


@pytest.mark.anyio
async def test_does_not_advance_cursor_when_persistence_fails() -> None:
    payload = (FIXTURES / "arxiv-feed.xml").read_text()
    store = RecordingStore(fail_upsert=True)

    with pytest.raises(RuntimeError, match="database unavailable"):
        await process_batch(
            source="arxiv",
            cursor="page-002",
            payload=payload,
            parser=parse_arxiv_atom,
            store=store,
        )

    assert len(store.events) == 1
    assert store.events[0].startswith("upsert:")

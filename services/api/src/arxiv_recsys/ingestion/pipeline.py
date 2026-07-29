import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from arxiv_recsys.models import Paper


@dataclass(frozen=True)
class BatchResult:
    source: str
    cursor: str
    payload_sha256: str
    accepted: int
    rejected: int


class IngestionStore(Protocol):
    async def upsert_papers(self, papers: list[Paper], payload_sha256: str) -> None: ...

    async def save_cursor(self, source: str, cursor: str, result: BatchResult) -> None: ...


async def process_batch(
    *,
    source: str,
    cursor: str,
    payload: str,
    parser: Callable[[str], list[Paper]],
    store: IngestionStore,
) -> BatchResult:
    """Persist a source page before advancing its cursor.

    Replaying a page is safe when the store upserts by arXiv work/version and
    payload checksum. A failed upsert never advances the source cursor.
    """

    payload_sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    papers = parser(payload)
    result = BatchResult(
        source=source,
        cursor=cursor,
        payload_sha256=payload_sha256,
        accepted=len(papers),
        rejected=0,
    )
    await store.upsert_papers(papers, payload_sha256)
    await store.save_cursor(source, cursor, result)
    return result

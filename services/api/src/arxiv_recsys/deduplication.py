import hashlib
import re
from dataclasses import dataclass
from enum import StrEnum

from arxiv_recsys.models import Paper
from arxiv_recsys.normalization import normalize_title


class DuplicateReason(StrEnum):
    SAME_ARXIV_WORK = "same_arxiv_work"
    SAME_DOI = "same_doi"
    NEAR_DUPLICATE = "near_duplicate"
    DISTINCT = "distinct"


@dataclass(frozen=True)
class DuplicateDecision:
    duplicate: bool
    reason: DuplicateReason
    confidence: float
    title_similarity: float
    author_overlap: float


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"\w+", normalize_title(value)))


def _shingles(value: str, size: int = 3) -> set[str]:
    tokens = list(re.findall(r"\w+", normalize_title(value)))
    if len(tokens) < size:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[index : index + size]) for index in range(len(tokens) - size + 1)}


def minhash_signature(value: str, permutations: int = 64) -> tuple[int, ...]:
    shingles = _shingles(value)
    if not shingles:
        return tuple(0 for _ in range(permutations))

    signature: list[int] = []
    for permutation in range(permutations):
        salt = permutation.to_bytes(4, byteorder="big")
        signature.append(
            min(
                int.from_bytes(
                    hashlib.blake2b(
                        shingle.encode("utf-8"),
                        digest_size=8,
                        key=salt,
                    ).digest(),
                    byteorder="big",
                )
                for shingle in shingles
            )
        )
    return tuple(signature)


def estimated_jaccard(left: tuple[int, ...], right: tuple[int, ...]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("MinHash signatures must have the same non-zero length")
    return sum(a == b for a, b in zip(left, right, strict=True)) / len(left)


def _author_tokens(paper: Paper) -> set[str]:
    return {
        token
        for author in paper.authors
        for token in _tokens(author.name)
        if len(token) > 1
    }


def _overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / min(len(left), len(right))


def compare_papers(left: Paper, right: Paper) -> DuplicateDecision:
    if left.arxiv_id == right.arxiv_id:
        return DuplicateDecision(True, DuplicateReason.SAME_ARXIV_WORK, 1.0, 1.0, 1.0)

    author_overlap = _overlap(_author_tokens(left), _author_tokens(right))
    title_similarity = estimated_jaccard(
        minhash_signature(left.title),
        minhash_signature(right.title),
    )

    if left.doi and right.doi and left.doi == right.doi:
        return DuplicateDecision(
            True,
            DuplicateReason.SAME_DOI,
            0.995,
            title_similarity,
            author_overlap,
        )

    years_close = abs(left.published_at.year - right.published_at.year) <= 1
    duplicate = title_similarity >= 0.82 and author_overlap >= 0.6 and years_close
    confidence = min(0.99, 0.55 * title_similarity + 0.35 * author_overlap + 0.1)
    return DuplicateDecision(
        duplicate,
        DuplicateReason.NEAR_DUPLICATE if duplicate else DuplicateReason.DISTINCT,
        confidence if duplicate else 1 - confidence,
        title_similarity,
        author_overlap,
    )

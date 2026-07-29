import math
import re
from collections import Counter
from dataclasses import dataclass

from arxiv_recsys.models import Paper
from arxiv_recsys.retrieval.encoder import HashingTextEncoder
from arxiv_recsys.retrieval.vector_index import ExactVectorIndex, VectorIndex

TOKEN_PATTERN = re.compile(r"\w+")


def tokenize(value: str) -> list[str]:
    return [
        token
        for token in TOKEN_PATTERN.findall(value.casefold())
        if len(token) > 2
    ]


@dataclass(frozen=True)
class RetrievalResult:
    paper_id: str
    score: float
    dense_score: float
    lexical_score: float
    explanation: str


class Bm25Index:
    def __init__(self, documents: dict[str, str], *, k1: float = 1.5, b: float = 0.75) -> None:
        self._k1 = k1
        self._b = b
        self._tokens = {document_id: tokenize(text) for document_id, text in documents.items()}
        self._term_frequencies = {
            document_id: Counter(tokens)
            for document_id, tokens in self._tokens.items()
        }
        self._average_length = sum(map(len, self._tokens.values())) / max(1, len(self._tokens))
        document_frequency = Counter(
            term for tokens in self._tokens.values() for term in set(tokens)
        )
        document_count = len(documents)
        self._idf = {
            term: math.log(1 + (document_count - count + 0.5) / (count + 0.5))
            for term, count in document_frequency.items()
        }

    def search(self, query: str, limit: int) -> list[tuple[str, float]]:
        query_terms = tokenize(query)
        scores: list[tuple[str, float]] = []
        for document_id, frequencies in self._term_frequencies.items():
            document_length = len(self._tokens[document_id])
            score = 0.0
            for term in query_terms:
                frequency = frequencies[term]
                if not frequency:
                    continue
                denominator = frequency + self._k1 * (
                    1 - self._b
                    + self._b * document_length / max(1.0, self._average_length)
                )
                score += self._idf.get(term, 0.0) * frequency * (self._k1 + 1) / denominator
            scores.append((document_id, score))
        scores.sort(key=lambda item: (-item[1], item[0]))
        return scores[:limit]


class HybridSearchEngine:
    version = "hybrid-rrf-v1"

    def __init__(
        self,
        papers: list[Paper],
        *,
        encoder: HashingTextEncoder | None = None,
        vector_index: VectorIndex | None = None,
        rrf_constant: int = 60,
    ) -> None:
        self._papers = {paper.arxiv_id: paper for paper in papers}
        self._encoder = encoder or HashingTextEncoder()
        self._vector_index = vector_index or ExactVectorIndex(self._encoder.dimensions)
        self._rrf_constant = rrf_constant

        documents = {
            paper.arxiv_id: f"{paper.title} {paper.abstract}"
            for paper in papers
        }
        self._lexical = Bm25Index(documents)
        vectors = self._encoder.encode(list(documents.values()))
        self._vector_index.add(list(documents), vectors)

    def search(
        self,
        query: str,
        *,
        category: str | None = None,
        limit: int = 20,
    ) -> list[RetrievalResult]:
        candidate_limit = min(len(self._papers), max(limit * 5, 50))
        dense = self._vector_index.search(
            self._encoder.encode([query])[0],
            candidate_limit,
        )
        lexical = self._lexical.search(query, candidate_limit)
        dense_rank = {paper_id: rank for rank, (paper_id, _) in enumerate(dense, start=1)}
        lexical_rank = {
            paper_id: rank for rank, (paper_id, _) in enumerate(lexical, start=1)
        }
        dense_scores = dict(dense)
        lexical_scores = dict(lexical)

        allowed = {
            paper.arxiv_id
            for paper in self._papers.values()
            if category is None or category in paper.categories
        }
        candidates = (set(dense_rank) | set(lexical_rank)) & allowed
        fused: list[RetrievalResult] = []
        max_lexical = max(lexical_scores.values(), default=1.0) or 1.0

        for paper_id in candidates:
            score = 0.0
            signals: list[str] = []
            if paper_id in dense_rank:
                score += 1 / (self._rrf_constant + dense_rank[paper_id])
                signals.append(f"dense rank {dense_rank[paper_id]}")
            if paper_id in lexical_rank:
                score += 1 / (self._rrf_constant + lexical_rank[paper_id])
                signals.append(f"lexical rank {lexical_rank[paper_id]}")
            fused.append(
                RetrievalResult(
                    paper_id=paper_id,
                    score=score,
                    dense_score=max(0.0, min(1.0, dense_scores.get(paper_id, 0.0))),
                    lexical_score=max(
                        0.0,
                        min(1.0, lexical_scores.get(paper_id, 0.0) / max_lexical),
                    ),
                    explanation=", ".join(signals),
                )
            )

        fused.sort(key=lambda item: (-item.score, item.paper_id))
        max_fused = fused[0].score if fused else 1.0
        return [
            RetrievalResult(
                paper_id=item.paper_id,
                score=item.score / max_fused,
                dense_score=item.dense_score,
                lexical_score=item.lexical_score,
                explanation=item.explanation,
            )
            for item in fused[:limit]
        ]

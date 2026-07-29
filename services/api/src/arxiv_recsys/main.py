from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from arxiv_recsys import __version__
from arxiv_recsys.config import get_settings
from arxiv_recsys.models import HealthResponse, IndexManifest, Paper, SearchResponse
from arxiv_recsys.normalization import parse_arxiv_identifier
from arxiv_recsys.repository import FixturePaperRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.paper_repository = FixturePaperRepository.from_package_data()
    yield


app = FastAPI(
    title="Aster API",
    summary="Citation-aware scholarly metadata and retrieval contracts.",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["accept", "content-type", "x-request-id"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    response: Response = await call_next(request)
    response.headers["x-request-id"] = request_id
    response.headers["x-content-type-options"] = "nosniff"
    return response


@app.get("/healthz", response_model=HealthResponse, tags=["operations"])
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="arxiv-recsys-api",
        version=__version__,
        timestamp=datetime.now(tz=UTC),
    )


@app.get("/v1/manifest", response_model=IndexManifest, tags=["retrieval"])
async def manifest(request: Request) -> IndexManifest:
    return request.app.state.paper_repository.manifest()


@app.get("/v1/papers/{arxiv_id:path}", response_model=Paper, tags=["papers"])
async def paper_detail(arxiv_id: str, request: Request) -> Paper:
    try:
        identifier = parse_arxiv_identifier(arxiv_id)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_arxiv_id", "arxiv_id": arxiv_id},
        ) from error
    paper = request.app.state.paper_repository.get(identifier.canonical_id)
    if paper is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "paper_not_found", "arxiv_id": arxiv_id},
        )
    return paper


@app.get("/v1/search", response_model=SearchResponse, tags=["retrieval"])
async def search(
    request: Request,
    query: Annotated[str, Query(min_length=2, max_length=300)],
    category: Annotated[str | None, Query(min_length=2, max_length=40)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> SearchResponse:
    return request.app.state.paper_repository.search(
        query=query,
        category=category,
        limit=limit,
    )

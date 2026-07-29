from fastapi.testclient import TestClient

from arxiv_recsys.main import app


def test_health_contract_and_request_id() -> None:
    with TestClient(app) as client:
        response = client.get("/healthz", headers={"x-request-id": "test-trace"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "test-trace"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.json()["status"] == "ok"


def test_search_returns_versioned_explainable_results() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/v1/search",
            params={
                "query": "language models for scientific discovery",
                "category": "cs.LG",
                "limit": 3,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ranking_version"] == "hybrid-rrf-v1"
    assert payload["index_manifest"] == "fixture-2026-07-28"
    assert payload["source_mode"] == "fixture"
    assert len(payload["results"]) <= 3
    assert payload["results"][0]["rank"] == 1
    assert "explanation" in payload["results"][0]["evidence"]


def test_search_rejects_unsafe_unbounded_inputs() -> None:
    with TestClient(app) as client:
        short_query = client.get("/v1/search", params={"query": "x"})
        excessive_limit = client.get(
            "/v1/search",
            params={"query": "scientific discovery", "limit": 101},
        )

    assert short_query.status_code == 422
    assert excessive_limit.status_code == 422


def test_paper_detail_and_not_found_contract() -> None:
    with TestClient(app) as client:
        found = client.get("/v1/papers/2402.19427")
        missing = client.get("/v1/papers/9999.99999")

    assert found.status_code == 200
    assert found.json()["title"].startswith("The AI Scientist")
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "paper_not_found"


def test_manifest_labels_fixture_data_truthfully() -> None:
    with TestClient(app) as client:
        response = client.get("/v1/manifest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_mode"] == "fixture"
    assert payload["paper_count"] == 4
    assert "not a production corpus" in payload["notes"]

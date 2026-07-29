from fastapi.testclient import TestClient

from arxiv_recsys.main import app, settings


def test_health_contract_and_request_id() -> None:
    with TestClient(app) as client:
        response = client.get("/healthz", headers={"x-request-id": "test-trace"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "test-trace"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["server-timing"].startswith("app;dur=")
    assert response.json()["status"] == "ok"


def test_readiness_checks_repository() -> None:
    with TestClient(app) as client:
        response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_operations_endpoint_is_hidden_without_a_token() -> None:
    with TestClient(app) as client:
        response = client.get("/internal/operations")
        schema = client.get("/openapi.json").json()

    assert response.status_code == 404
    assert "/internal/operations" not in schema["paths"]


def test_operations_endpoint_requires_and_accepts_bearer_token(monkeypatch) -> None:
    monkeypatch.setattr(settings, "operations_token", "test-operations-secret")
    with TestClient(app) as client:
        unauthorized = client.get(
            "/internal/operations",
            headers={"authorization": "Bearer incorrect"},
        )
        authorized = client.get(
            "/internal/operations",
            headers={"authorization": "Bearer test-operations-secret"},
        )

    assert unauthorized.status_code == 401
    assert unauthorized.headers["www-authenticate"] == "Bearer"
    assert authorized.status_code == 200
    assert authorized.json()["request_count"] >= 1


def test_readiness_reports_repository_failure() -> None:
    class UnavailableRepository:
        def manifest(self):
            raise RuntimeError("unavailable")

    with TestClient(app) as client:
        client.app.state.paper_repository = UnavailableRepository()
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "repository_unavailable"


def test_unhandled_errors_are_sanitized_and_counted() -> None:
    class FailingRepository:
        def search(self, **kwargs):
            raise RuntimeError("database password must never be returned")

    with TestClient(app, raise_server_exceptions=False) as client:
        client.app.state.paper_repository = FailingRepository()
        response = client.get("/v1/search", params={"query": "science"})
        snapshot = client.app.state.request_metrics.snapshot()

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "internal_server_error"
    assert "password" not in response.text
    assert snapshot.error_count == 1


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

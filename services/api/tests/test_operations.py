import json
import logging

from arxiv_recsys.operations import (
    RequestMetrics,
    add_security_headers,
    log_request,
    log_unhandled_error,
)


def test_metrics_track_status_latency_errors_and_in_flight_requests() -> None:
    metrics = RequestMetrics()
    assert metrics.snapshot().mean_duration_ms == 0

    metrics.begin()
    assert metrics.snapshot().in_flight == 1
    metrics.finish(status_code=200, duration_ms=10.0)
    metrics.begin()
    metrics.finish(status_code=503, duration_ms=20.0)

    snapshot = metrics.snapshot()
    assert snapshot.request_count == 2
    assert snapshot.error_count == 1
    assert snapshot.in_flight == 0
    assert snapshot.mean_duration_ms == 15.0
    assert snapshot.status_counts == {"200": 1, "503": 1}


def test_security_headers_are_complete() -> None:
    headers: dict[str, str] = {}
    add_security_headers(headers)

    assert headers == {
        "cache-control": "no-store",
        "content-security-policy": (
            "default-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        ),
        "permissions-policy": "camera=(), geolocation=(), microphone=()",
        "referrer-policy": "no-referrer",
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
    }


def test_request_log_is_structured_json(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="aster.requests"):
        log_request(
            request_id="request-123",
            method="GET",
            path="/v1/search",
            status_code=200,
            duration_ms=12.3456,
        )

    payload = json.loads(caplog.messages[-1])
    assert payload == {
        "duration_ms": 12.346,
        "event": "http_request",
        "method": "GET",
        "path": "/v1/search",
        "request_id": "request-123",
        "status_code": 200,
    }


def test_unhandled_error_log_is_structured_and_preserves_trace(caplog) -> None:
    with caplog.at_level(logging.ERROR, logger="aster.requests"):
        try:
            raise RuntimeError("private detail")
        except RuntimeError:
            log_unhandled_error(
                request_id="request-456",
                method="GET",
                path="/v1/search",
            )

    payload = json.loads(caplog.messages[-1])
    assert payload == {
        "event": "unhandled_request_error",
        "method": "GET",
        "path": "/v1/search",
        "request_id": "request-456",
    }

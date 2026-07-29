import json
import logging
from collections import Counter
from dataclasses import dataclass, field
from threading import Lock

from arxiv_recsys.models import OperationsSnapshot

logger = logging.getLogger("aster.requests")


@dataclass
class RequestMetrics:
    """Process-local service metrics.

    Production collectors should scrape each replica and aggregate externally.
    The lock keeps updates safe when synchronous test and worker threads share a
    process.
    """

    request_count: int = 0
    error_count: int = 0
    in_flight: int = 0
    total_duration_ms: float = 0.0
    status_counts: Counter[int] = field(default_factory=Counter)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def begin(self) -> None:
        with self._lock:
            self.in_flight += 1

    def finish(self, *, status_code: int, duration_ms: float) -> None:
        with self._lock:
            self.in_flight -= 1
            self.request_count += 1
            self.error_count += int(status_code >= 500)
            self.total_duration_ms += duration_ms
            self.status_counts[status_code] += 1

    def snapshot(self) -> OperationsSnapshot:
        with self._lock:
            mean_duration = (
                self.total_duration_ms / self.request_count
                if self.request_count
                else 0.0
            )
            return OperationsSnapshot(
                request_count=self.request_count,
                error_count=self.error_count,
                in_flight=self.in_flight,
                mean_duration_ms=round(mean_duration, 3),
                status_counts={
                    str(status): count
                    for status, count in sorted(self.status_counts.items())
                },
            )


def log_request(
    *,
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
) -> None:
    logger.info(
        json.dumps(
            {
                "duration_ms": round(duration_ms, 3),
                "event": "http_request",
                "method": method,
                "path": path,
                "request_id": request_id,
                "status_code": status_code,
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )


def log_unhandled_error(*, request_id: str, method: str, path: str) -> None:
    logger.exception(
        json.dumps(
            {
                "event": "unhandled_request_error",
                "method": method,
                "path": path,
                "request_id": request_id,
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )


def add_security_headers(headers: dict[str, str]) -> None:
    headers["cache-control"] = "no-store"
    headers["content-security-policy"] = (
        "default-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    )
    headers["permissions-policy"] = "camera=(), geolocation=(), microphone=()"
    headers["referrer-policy"] = "no-referrer"
    headers["x-content-type-options"] = "nosniff"
    headers["x-frame-options"] = "DENY"

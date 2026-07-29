from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass
from time import perf_counter

import httpx

from arxiv_recsys.load_testing import percentile


@dataclass(frozen=True)
class LoadReport:
    base_url: str
    concurrency: int
    request_count: int
    success_count: int
    error_count: int
    requests_per_second: float
    p50_ms: float
    p95_ms: float
    p99_ms: float


async def run_load(
    *,
    base_url: str,
    request_count: int,
    concurrency: int,
    timeout_seconds: float,
) -> LoadReport:
    if request_count <= 0 or concurrency <= 0:
        raise ValueError("Request count and concurrency must be positive")
    semaphore = asyncio.Semaphore(concurrency)
    durations: list[float] = []
    success_count = 0

    async with httpx.AsyncClient(base_url=base_url, timeout=timeout_seconds) as client:
        async def execute(index: int) -> bool:
            async with semaphore:
                started = perf_counter()
                try:
                    response = await client.get(
                        "/v1/search",
                        params={
                            "query": "scientific language models",
                            "limit": 10,
                        },
                        headers={"x-request-id": f"load-{index}"},
                    )
                    return response.status_code == 200
                except httpx.HTTPError:
                    return False
                finally:
                    durations.append((perf_counter() - started) * 1000)

        started = perf_counter()
        outcomes = await asyncio.gather(
            *(execute(index) for index in range(request_count)),
            return_exceptions=True,
        )
        wall_seconds = perf_counter() - started

    success_count = sum(outcome is True for outcome in outcomes)
    error_count = request_count - success_count
    return LoadReport(
        base_url=base_url,
        concurrency=concurrency,
        request_count=request_count,
        success_count=success_count,
        error_count=error_count,
        requests_per_second=round(request_count / wall_seconds, 2),
        p50_ms=round(percentile(durations, 50), 3),
        p95_ms=round(percentile(durations, 95), 3),
        p99_ms=round(percentile(durations, 99), 3),
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load-test a running Aster API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=1_000)
    parser.add_argument("--concurrency", type=int, default=25)
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    parser.add_argument("--max-error-rate", type=float, default=0.001)
    parser.add_argument("--max-p99-ms", type=float, default=80.0)
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    report = asyncio.run(
        run_load(
            base_url=arguments.base_url,
            request_count=arguments.requests,
            concurrency=arguments.concurrency,
            timeout_seconds=arguments.timeout_seconds,
        )
    )
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    error_rate = report.error_count / report.request_count
    if error_rate > arguments.max_error_rate or report.p99_ms > arguments.max_p99_ms:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

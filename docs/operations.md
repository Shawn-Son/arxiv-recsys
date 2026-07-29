# Operations runbook

## Service probes

- `GET /healthz` is a liveness probe and does not call dependencies.
- `GET /readyz` verifies that the configured paper repository can expose its
  manifest. Remove a replica from service when this returns `503`.
- Every response includes `x-request-id` and `server-timing`. Forward a caller's
  `x-request-id` when present so a report can be correlated across services.

The process emits one JSON request log per response. Do not log query text,
authorization headers, saved papers, or reader identifiers.

## Internal metrics

Set `ASTER_OPERATIONS_TOKEN` to expose `GET /internal/operations`; the route is
excluded from OpenAPI and otherwise returns `404`. Keep it on a private network,
send `Authorization: Bearer <token>`, and rotate the token through the platform
secret manager. The process-local counters must be aggregated across replicas.

## Load test

Start the API, then run:

```bash
uv run python benchmarks/run_load.py \
  --base-url http://127.0.0.1:8000 \
  --requests 1000 \
  --concurrency 25 \
  --max-error-rate 0.001 \
  --max-p99-ms 80
```

Record the image digest, index manifest, instance type, replica count, commit,
request profile, and raw JSON output. The default latency target is a release
gate, not a claim about an environment that has not been measured.

## Incident sequence

1. Identify the affected commit, model version, and index manifest.
2. Compare error rate and latency by status and replica.
3. Remove unready replicas; do not rebuild an index inside the serving process.
4. Roll back the application or blue/green index pointer independently.
5. Preserve sanitized logs and benchmark output, then document the correction.

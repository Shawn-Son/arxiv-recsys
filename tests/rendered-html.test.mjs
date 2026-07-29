import assert from "node:assert/strict";
import test from "node:test";

const workerUrl = new URL("../dist/server/index.js", import.meta.url);

async function loadWorker() {
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker;
}

const environment = {
  ASSETS: {
    fetch: async () => new Response("Not found", { status: 404 }),
  },
};

const context = {
  waitUntil() {},
  passThroughOnException() {},
};

test("server-renders the research discovery product", async () => {
  const worker = await loadWorker();
  const response = await worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    environment,
    context,
  );

  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(
    html,
    /<title>Aster — Research discovery, made deliberate<\/title>/i,
  );
  assert.match(html, /Find the work that/);
  assert.match(html, /language models for scientific discovery/);
  assert.match(html, /The AI Scientist/);
  assert.match(html, /Evidence before popularity/);
  assert.match(html, /The ranking contract/);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape/i);
});

test("exposes a no-cache health contract", async () => {
  const worker = await loadWorker();
  const response = await worker.fetch(
    new Request("http://localhost/api/health"),
    environment,
    context,
  );

  assert.equal(response.status, 200);
  assert.equal(response.headers.get("cache-control"), "no-store");
  assert.deepEqual(await response.json(), {
    service: "arxiv-recsys-web",
    status: "ok",
    version: "0.1.0",
  });
});

test("serves the versioned preview search contract", async () => {
  const worker = await loadWorker();
  const response = await worker.fetch(
    new Request(
      "http://localhost/api/v1/search?query=scientific%20discovery&category=cs.LG&limit=3",
      { headers: { accept: "application/json" } },
    ),
    environment,
    context,
  );

  assert.equal(response.status, 200);
  assert.equal(response.headers.get("x-aster-source"), "preview-index");
  const payload = await response.json();
  assert.equal(payload.query, "scientific discovery");
  assert.equal(payload.ranking_version, "web-contract-adapter-v1");
  assert.equal(payload.index_manifest, "fixture-2026-07-28");
  assert.ok(payload.results.length > 0);
  assert.ok(payload.results.length <= 3);
  assert.equal(payload.results[0].rank, 1);
  assert.match(payload.results[0].paper.source_url, /^https:\/\/arxiv\.org\/abs\//);
});

test("rejects invalid preview search queries", async () => {
  const worker = await loadWorker();
  const response = await worker.fetch(
    new Request("http://localhost/api/v1/search?query=x"),
    environment,
    context,
  );

  assert.equal(response.status, 422);
  assert.equal((await response.json()).error.code, "invalid_query");
});

test("publishes the production canonical URL in the sitemap", async () => {
  const worker = await loadWorker();
  const response = await worker.fetch(
    new Request("http://localhost/sitemap.xml"),
    environment,
    context,
  );

  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /xml/i);
  assert.match(
    await response.text(),
    /https:\/\/aster-research\.shawn22587\.chatgpt\.site/,
  );
});

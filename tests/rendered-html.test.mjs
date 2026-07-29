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

import { papers } from "../../../data/papers";

export const dynamic = "force-dynamic";

type BackendPaper = {
  arxiv_id: string;
  version: number;
  title: string;
  abstract: string;
  authors: { name: string; orcid?: string | null }[];
  categories: string[];
  primary_category: string;
  published_at: string;
  updated_at: string;
  citation_count: number;
  source_url: string;
};

function tokenize(value: string) {
  return value
    .toLowerCase()
    .split(/\W+/)
    .filter((token) => token.length > 2);
}

function localSearch(query: string, category: string | null, limit: number) {
  const queryTokens = new Set(tokenize(query));
  const ranked = papers
    .filter((paper) => !category || paper.categories.includes(category))
    .map((paper) => {
      const titleTokens = new Set(tokenize(paper.title));
      const abstractTokens = new Set(tokenize(paper.abstract));
      const titleMatches = [...queryTokens].filter((token) => titleTokens.has(token)).length;
      const abstractMatches = [...queryTokens].filter((token) =>
        abstractTokens.has(token),
      ).length;
      const lexical = Math.min(
        1,
        (titleMatches * 1.5 + abstractMatches) / Math.max(1, queryTokens.size),
      );
      const semantic = Math.min(1, 0.35 + lexical * 0.65);
      return {
        paper,
        lexical,
        semantic,
        score: semantic * 0.7 + lexical * 0.3,
        explanation: `${titleMatches + abstractMatches} query concepts matched in the preview index.`,
      };
    })
    .sort((left, right) => right.score - left.score || left.paper.id.localeCompare(right.paper.id))
    .slice(0, limit);

  return {
    query,
    total: ranked.length,
    limit,
    ranking_version: "web-contract-adapter-v1",
    index_manifest: "fixture-2026-07-28",
    source_mode: "fixture",
    took_ms: 0,
    results: ranked.map((item, index) => ({
      rank: index + 1,
      score: item.score,
      evidence: {
        semantic: item.semantic,
        lexical: item.lexical,
        citation: 0,
        explanation: item.explanation,
      },
      paper: {
        arxiv_id: item.paper.id,
        version: 1,
        title: item.paper.title,
        abstract: item.paper.abstract,
        authors: item.paper.authors.map((name) => ({ name })),
        categories: item.paper.categories,
        primary_category: item.paper.categories[0],
        published_at: `${item.paper.published}T00:00:00Z`,
        updated_at: `${item.paper.updated}T00:00:00Z`,
        citation_count: item.paper.citations,
        source_url:
          item.paper.sourceUrl ?? `https://arxiv.org/abs/${item.paper.id}`,
      } satisfies BackendPaper,
    })),
  };
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const query = url.searchParams.get("query")?.trim() ?? "";
  const category = url.searchParams.get("category")?.trim() || null;
  const requestedLimit = Number(url.searchParams.get("limit") ?? 20);
  const limit = Number.isInteger(requestedLimit)
    ? Math.min(100, Math.max(1, requestedLimit))
    : 20;

  if (query.length < 2 || query.length > 300) {
    return Response.json(
      {
        error: {
          code: "invalid_query",
          message: "Query length must be between 2 and 300 characters.",
        },
      },
      { status: 422 },
    );
  }

  const apiBaseUrl = process.env.ASTER_API_BASE_URL?.replace(/\/$/, "");
  if (apiBaseUrl) {
    const upstream = new URL(`${apiBaseUrl}/v1/search`);
    upstream.searchParams.set("query", query);
    upstream.searchParams.set("limit", String(limit));
    if (category) {
      upstream.searchParams.set("category", category);
    }
    const response = await fetch(upstream, {
      headers: { accept: "application/json" },
      signal: AbortSignal.timeout(8_000),
    });
    if (!response.ok) {
      return Response.json(
        {
          error: {
            code: "search_upstream_error",
            message: "The retrieval service could not complete this search.",
          },
        },
        { status: 502 },
      );
    }
    return new Response(response.body, {
      headers: {
        "cache-control": "public, max-age=30, stale-while-revalidate=300",
        "content-type": "application/json",
        "x-aster-source": "retrieval-api",
      },
    });
  }

  return Response.json(localSearch(query, category, limit), {
    headers: {
      "cache-control": "public, max-age=30, stale-while-revalidate=300",
      "x-aster-source": "preview-index",
    },
  });
}

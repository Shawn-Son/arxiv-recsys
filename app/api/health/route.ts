export const dynamic = "force-dynamic";

export async function GET() {
  return Response.json(
    {
      service: "arxiv-recsys-web",
      status: "ok",
      version: "0.1.0",
    },
    {
      headers: {
        "cache-control": "no-store",
      },
    },
  );
}

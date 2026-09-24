import { createFileRoute } from "@tanstack/react-router";

// Same-origin gateway to the FastAPI backend: every /api/* request is
// forwarded to API_INTERNAL_URL (default http://127.0.0.1:8000) with its
// method, headers, body and cookies, and the response is streamed back. The
// browser therefore talks to one origin in development and in production, so
// the session cookie stays first-party and no CORS setup is needed. Set
// VITE_API_URL instead to call a separately hosted API directly.

const HOP_BY_HOP = [
  "connection",
  "keep-alive",
  "transfer-encoding",
  "upgrade",
  "host",
  "content-length",
];

// Vercel sets VERCEL=1; there is no API on localhost in a Vercel function.
const deployed = Boolean(process.env["VERCEL"]);

async function forward({ request }: { request: Request }): Promise<Response> {
  const configured = process.env["API_INTERNAL_URL"];
  if (!configured && deployed) {
    // On a deployment there is no API on localhost: say what is missing instead of timing out.
    return Response.json(
      {
        detail:
          "The StandardOS API is not configured for this deployment. Deploy the API (deploy/vercel-api, see docs/DEPLOYMENT.md) and set API_INTERNAL_URL to its URL.",
      },
      { status: 503 },
    );
  }
  const target = (configured ?? "http://127.0.0.1:8000").replace(/\/$/, "");
  const url = new URL(request.url);
  const headers = new Headers(request.headers);
  for (const name of HOP_BY_HOP) headers.delete(name);
  headers.set("x-forwarded-host", url.host);
  headers.set("x-forwarded-proto", url.protocol.replace(":", ""));
  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  try {
    const upstream = await fetch(`${target}${url.pathname}${url.search}`, {
      method: request.method,
      headers,
      body: hasBody ? await request.arrayBuffer() : null,
      redirect: "manual",
    });
    const responseHeaders = new Headers(upstream.headers);
    for (const name of HOP_BY_HOP) responseHeaders.delete(name);
    responseHeaders.delete("content-encoding");
    return new Response(upstream.body, { status: upstream.status, headers: responseHeaders });
  } catch {
    return Response.json(
      {
        detail: deployed
          ? `The StandardOS API at ${target} is unreachable. Check the backend deployment and API_INTERNAL_URL.`
          : "The StandardOS API is unreachable. Start it with `bun run api:dev`.",
      },
      { status: 502 },
    );
  }
}

export const Route = createFileRoute("/api/$")({
  server: {
    handlers: {
      GET: forward,
      POST: forward,
      PUT: forward,
      PATCH: forward,
      DELETE: forward,
    },
  },
});

// HTTP client for the StandardOS FastAPI backend (backend/).
//
// In the browser, requests go to `${VITE_API_URL}/api/...`; when VITE_API_URL
// is unset they are same-origin (`/api/...`) and the gateway route
// src/routes/api/$.ts forwards them to FastAPI. During
// server-side rendering there is no origin, so an absolute base is required:
// API_INTERNAL_URL, else VITE_API_URL, else http://127.0.0.1:8000.

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function baseUrl(): string {
  const configured =
    (import.meta.env["VITE_API_URL"] as string | undefined)?.replace(/\/$/, "") ?? "";
  if (typeof window !== "undefined") return configured;
  const internal = typeof process !== "undefined" ? process.env["API_INTERNAL_URL"] : undefined;
  return (internal ?? configured) || "http://127.0.0.1:8000";
}

type Query = Record<string, string | number | boolean | string[] | null | undefined>;

function withQuery(path: string, query?: Query): string {
  if (!query) return path;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) value.forEach((v) => params.append(key, v));
    else params.append(key, String(value));
  }
  const qs = params.toString();
  return qs ? `${path}?${qs}` : path;
}

async function request<T>(
  method: string,
  path: string,
  options: { query?: Query | undefined; json?: unknown; form?: FormData | undefined } = {},
): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  let body: BodyInit | null = null;
  if (options.form) body = options.form;
  else if (options.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.json);
  }
  let response: Response;
  try {
    response = await fetch(`${baseUrl()}${withQuery(path, options.query)}`, {
      method,
      headers,
      body,
      credentials: "include",
    });
  } catch {
    throw new ApiError("The StandardOS service is unreachable. Check that the API is running.", 0);
  }
  const text = await response.text();
  const payload: unknown = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail =
      payload && typeof payload === "object" && "detail" in payload
        ? (payload as { detail: unknown }).detail
        : null;
    throw new ApiError(
      typeof detail === "string" ? detail : `Request failed (${response.status}).`,
      response.status,
    );
  }
  return payload as T;
}

export const api = {
  get: <T>(path: string, query?: Query) => request<T>("GET", path, { query }),
  post: <T>(path: string, json?: unknown) => request<T>("POST", path, { json }),
  patch: <T>(path: string, json?: unknown) => request<T>("PATCH", path, { json }),
  upload: <T>(path: string, form: FormData) => request<T>("POST", path, { form }),
};

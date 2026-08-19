/**
 * Thin fetch wrapper for calling the backend REST API.
 *
 * All backend communication must go through this client — the frontend
 * never talks to the database directly (see CLAUDE.md architecture rules).
 * Works from both server code (route handlers, server components — pass an
 * `Authorization` header via `init`) and client code (relies on
 * NEXT_PUBLIC_API_URL being inlined into the browser bundle).
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  /** The backend's `detail` field, when it's a plain string (e.g. auth
   * errors). Validation errors (422) carry a structured `detail` array
   * instead, which is intentionally not surfaced here — callers fall back
   * to a generic message for those. */
  detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => undefined);
    const rawDetail =
      body && typeof body === "object" && "detail" in body
        ? (body as { detail: unknown }).detail
        : undefined;
    const detail = typeof rawDetail === "string" ? rawDetail : undefined;

    throw new ApiError(
      response.status,
      detail ?? `Request to ${path} failed with status ${response.status}`,
      detail,
    );
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string, init?: RequestInit) => request<T>(path, { method: "GET", ...init }),
  post: <T>(path: string, body?: unknown, init?: RequestInit) =>
    request<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
      ...init,
    }),
};

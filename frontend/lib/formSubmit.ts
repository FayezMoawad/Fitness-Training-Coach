/**
 * Shared client-side helper for submitting a form to one of our own
 * `/api/*` proxy routes — never the backend directly, since the session
 * token lives in an httpOnly cookie only route handlers can read (see
 * docs/ERROR_CONVENTIONS.md).
 *
 * Normalizes the try/catch + response.ok + detail-parsing boilerplate that
 * every form was repeating: a network failure, a validation error, and a
 * 500 all resolve to the same shape, so callers only ever have to check
 * one thing.
 */

// `ok` is a literal-typed discriminant (rather than, say, an optional
// `error` field) so TypeScript can actually narrow `result.data` vs
// `result.error` after an `if (!result.ok)` check.
type SubmitResult<T> = { ok: true; data: T } | { ok: false; error: string };

const GENERIC_ERROR = "Something went wrong. Please try again.";

export async function submitJson<T>(url: string, body: unknown): Promise<SubmitResult<T>> {
  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    return { ok: false, error: GENERIC_ERROR };
  }

  const payload: unknown = await response.json().catch(() => undefined);

  if (!response.ok) {
    const detail =
      payload && typeof payload === "object" && "detail" in payload
        ? (payload as { detail: unknown }).detail
        : undefined;
    return { ok: false, error: typeof detail === "string" ? detail : GENERIC_ERROR };
  }

  return { ok: true, data: payload as T };
}

/**
 * Server-only helpers for reading the current session. The JWT itself lives
 * only in an httpOnly cookie, set by the `/api/auth/*` route handlers — it's
 * never exposed to client-side JS. Only usable from Server Components,
 * Server Functions, and Route Handlers (anywhere `next/headers` works).
 */

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { apiClient, ApiError } from "@/lib/apiClient";
import { SESSION_COOKIE_NAME } from "@/lib/constants";
import type { User } from "@/types/user";

export async function getSessionToken(): Promise<string | null> {
  const cookieStore = await cookies();
  return cookieStore.get(SESSION_COOKIE_NAME)?.value ?? null;
}

/** Resolves the current user by asking the backend to validate the token —
 * never trusts the cookie's contents directly. Returns `null` for "not
 * logged in" *or* "session invalid/expired"; only unexpected backend
 * failures propagate. */
export async function getCurrentUser(): Promise<User | null> {
  const token = await getSessionToken();
  if (!token) {
    return null;
  }

  try {
    return await apiClient.get<User>("/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null;
    }
    throw error;
  }
}

/** For protected Server Component pages that also need to make further
 * authenticated backend calls (e.g. GET /workouts) — returns both the user
 * and the raw token, redirecting to /login if there's no valid session.
 * `proxy.ts` already blocks unauthenticated requests to /coach/* and
 * /client/*, but this is the real (non-UX-only) check. */
export async function requireUser(): Promise<{ user: User; token: string }> {
  const token = await getSessionToken();
  if (!token) {
    redirect("/login");
  }

  try {
    const user = await apiClient.get<User>("/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    });
    return { user, token };
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      redirect("/login");
    }
    throw error;
  }
}

/**
 * Server-only helpers for reading the current session. The JWT itself lives
 * only in an httpOnly cookie, set by the `/api/auth/*` route handlers — it's
 * never exposed to client-side JS. Only usable from Server Components,
 * Server Functions, and Route Handlers (anywhere `next/headers` works).
 */

import { cookies } from "next/headers";

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

/**
 * Shared constants with no server/client-only dependencies, so they're safe
 * to import from anywhere — including `proxy.ts`, which runs in a separate
 * bundle from route handlers/server components and can't pull in
 * `next/headers`.
 */

export const SESSION_COOKIE_NAME = "ftc_session";

/** Options for the httpOnly session cookie. `maxAge` is just the cookie's
 * outer lifetime in the browser — the JWT inside still expires on its own
 * schedule (`JWT_EXPIRE_MINUTES`, backend-enforced), so an expired-but-still
 * -present cookie simply fails validation in `getCurrentUser`. */
export function sessionCookieOptions() {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
  };
}

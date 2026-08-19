/**
 * Redirects unauthenticated visitors away from protected routes.
 *
 * This is a UX convenience only — it just checks that the session cookie is
 * present, not that it's valid or which role it belongs to. The backend
 * (Steps 3–6) is the actual source of truth for authorization; nothing here
 * should ever be trusted as a security boundary.
 *
 * Named `proxy.ts`, not `middleware.ts` — Next.js 16 renamed the
 * convention (middleware.ts is deprecated).
 */

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { SESSION_COOKIE_NAME } from "@/lib/constants";

const PROTECTED_PREFIXES = ["/coach", "/client"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtected = PROTECTED_PREFIXES.some((prefix) => pathname.startsWith(prefix));
  if (!isProtected) {
    return NextResponse.next();
  }

  const hasSession = request.cookies.has(SESSION_COOKIE_NAME);
  if (!hasSession) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/coach/:path*", "/client/:path*"],
};

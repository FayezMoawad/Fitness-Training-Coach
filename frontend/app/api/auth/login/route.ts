/**
 * Proxies login to the backend and, on success, stores the JWT in an
 * httpOnly cookie — the browser never sees the token itself, only this
 * route's JSON response (the user, no token).
 */

import { NextResponse } from "next/server";

import { apiClient, ApiError } from "@/lib/apiClient";
import { SESSION_COOKIE_NAME, sessionCookieOptions } from "@/lib/constants";
import type { User } from "@/types/user";

export async function POST(request: Request) {
  const body = await request.json();

  try {
    const { access_token } = await apiClient.post<{ access_token: string }>(
      "/auth/login",
      body,
    );
    const user = await apiClient.get<User>("/auth/me", {
      headers: { Authorization: `Bearer ${access_token}` },
    });

    const response = NextResponse.json({ user });
    response.cookies.set(SESSION_COOKIE_NAME, access_token, sessionCookieOptions());
    return response;
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const detail = error instanceof ApiError ? error.detail : undefined;
    return NextResponse.json({ detail: detail ?? "Incorrect email or password" }, { status });
  }
}

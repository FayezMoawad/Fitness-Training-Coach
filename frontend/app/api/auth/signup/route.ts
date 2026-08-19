/**
 * Proxies signup to the backend, then immediately logs the new user in
 * (backend signup doesn't return a token) so the httpOnly session cookie is
 * set in the same request — no separate login step needed.
 */

import { NextResponse } from "next/server";

import { apiClient, ApiError } from "@/lib/apiClient";
import { SESSION_COOKIE_NAME, sessionCookieOptions } from "@/lib/constants";
import type { User } from "@/types/user";

export async function POST(request: Request) {
  const body = await request.json();

  try {
    const user = await apiClient.post<User>("/auth/signup", body);
    const { access_token } = await apiClient.post<{ access_token: string }>("/auth/login", {
      email: body.email,
      password: body.password,
    });

    const response = NextResponse.json({ user }, { status: 201 });
    response.cookies.set(SESSION_COOKIE_NAME, access_token, sessionCookieOptions());
    return response;
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const detail = error instanceof ApiError ? error.detail : undefined;
    return NextResponse.json({ detail: detail ?? "Signup failed" }, { status });
  }
}

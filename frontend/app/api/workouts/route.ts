/**
 * Proxies workout creation to the backend, attaching the session token as
 * the Authorization header — client components can't do this themselves
 * since the token lives in an httpOnly cookie they can't read.
 */

import { NextResponse } from "next/server";

import { apiClient, ApiError } from "@/lib/apiClient";
import { getSessionToken } from "@/lib/session";

export async function POST(request: Request) {
  const token = await getSessionToken();
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const body = await request.json();

  try {
    const workout = await apiClient.post("/workouts", body, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return NextResponse.json(workout, { status: 201 });
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const detail = error instanceof ApiError ? error.detail : undefined;
    return NextResponse.json({ detail: detail ?? "Could not create workout." }, { status });
  }
}

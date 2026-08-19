/** Proxies workout-result logging to the backend, same reasoning as
 * app/api/workouts/route.ts (Step 8): client components can't attach the
 * session token themselves since it lives in an httpOnly cookie. */

import { NextResponse } from "next/server";

import { apiClient, ApiError } from "@/lib/apiClient";
import { getSessionToken } from "@/lib/session";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ assignmentId: string }> },
) {
  const token = await getSessionToken();
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const { assignmentId } = await params;
  const body = await request.json();

  try {
    const log = await apiClient.post(`/assignments/${assignmentId}/logs`, body, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return NextResponse.json(log, { status: 201 });
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const detail = error instanceof ApiError ? error.detail : undefined;
    return NextResponse.json({ detail: detail ?? "Could not log workout result." }, { status });
  }
}

/** Proxies workout-assignment to the backend, same reasoning as
 * app/api/workouts/route.ts. */

import { NextResponse } from "next/server";

import { apiClient, ApiError } from "@/lib/apiClient";
import { getSessionToken } from "@/lib/session";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ workoutId: string }> },
) {
  const token = await getSessionToken();
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const { workoutId } = await params;
  const body = await request.json();

  try {
    const assignment = await apiClient.post(`/workouts/${workoutId}/assign`, body, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return NextResponse.json(assignment, { status: 201 });
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    const detail = error instanceof ApiError ? error.detail : undefined;
    return NextResponse.json({ detail: detail ?? "Could not assign workout." }, { status });
  }
}

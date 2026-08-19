/**
 * Lets client components (via `useAuth`) find out who's logged in, without
 * ever handing the JWT itself to the browser. Always 200s — `user` is
 * `null` for "not logged in" so the hook doesn't need to special-case
 * status codes.
 */

import { NextResponse } from "next/server";

import { getCurrentUser } from "@/lib/session";

export async function GET() {
  const user = await getCurrentUser();
  return NextResponse.json({ user });
}

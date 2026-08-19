import Link from "next/link";
import { redirect } from "next/navigation";

import { getCurrentUser } from "@/lib/session";

/** Placeholder — workout assignment tools land in Step 8. The redirects
 * here are UX only, same caveat as `proxy.ts`: the backend is what actually
 * enforces role/ownership once this page starts fetching real data. */
export default async function CoachDashboardPage() {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login");
  }
  if (user.role !== "coach") {
    redirect("/client/dashboard");
  }

  return (
    <div className="mx-auto w-full max-w-5xl px-6 py-16">
      <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
        Welcome, {user.full_name}
      </h1>
      <p className="mt-2 text-zinc-600 dark:text-zinc-400">
        Create and assign workouts to your clients.
      </p>
      <Link
        href="/coach/workouts"
        className="mt-6 inline-block rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
      >
        Go to workouts
      </Link>
    </div>
  );
}

import Link from "next/link";
import { redirect } from "next/navigation";

import { getCurrentUser } from "@/lib/session";

/** The redirects here are UX only; the backend enforces role/ownership. */
export default async function ClientDashboardPage() {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login");
  }
  if (user.role !== "client") {
    redirect("/coach/dashboard");
  }

  return (
    <div className="mx-auto w-full max-w-5xl px-6 py-16">
      <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
        Welcome, {user.full_name}
      </h1>
      <p className="mt-2 text-zinc-600 dark:text-zinc-400">
        View your assigned workouts and log your results.
      </p>
      <Link
        href="/client/workouts"
        className="mt-6 inline-block rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
      >
        Go to your workouts
      </Link>
      <p className="mt-6 text-sm text-zinc-600 dark:text-zinc-400">
        Your client ID is{" "}
        <span className="rounded-md bg-zinc-100 px-1.5 py-0.5 font-mono font-medium text-zinc-900 dark:bg-zinc-900 dark:text-zinc-50">
          {user.id}
        </span>{" "}
        — share it with your coach so they can assign you a workout.
      </p>
    </div>
  );
}

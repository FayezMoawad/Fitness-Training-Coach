import { redirect } from "next/navigation";

import { getCurrentUser } from "@/lib/session";

/** Placeholder — assigned-workout and logging UI land in Steps 9–10. The
 * redirects here are UX only; the backend enforces role/ownership. */
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
        Your assigned workouts are coming in the next step.
      </p>
    </div>
  );
}

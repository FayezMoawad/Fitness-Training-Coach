import Link from "next/link";
import { redirect } from "next/navigation";

import { apiClient, ApiError } from "@/lib/apiClient";
import { requireUser } from "@/lib/session";
import type { ClientProgressResponse } from "@/types/workout";

const statusLabel: Record<"assigned" | "completed", string> = {
  assigned: "Assigned",
  completed: "Completed",
};

export default async function ClientProgressPage({
  params,
}: {
  params: Promise<{ clientId: string }>;
}) {
  const { user, token } = await requireUser();
  if (user.role !== "coach") {
    redirect("/client/dashboard");
  }

  const { clientId } = await params;
  const authHeader = { headers: { Authorization: `Bearer ${token}` } };

  // A 404 here means "no assignment relationship with this client" -- same
  // response whether the id doesn't exist or just isn't this coach's
  // client (backend's don't-leak-which-ids-exist convention, Step 6).
  // Rendered as an empty state, not a crash, per this step's test table.
  let progress: ClientProgressResponse | null = null;
  try {
    progress = await apiClient.get<ClientProgressResponse>(
      `/clients/${clientId}/progress`,
      authHeader,
    );
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 404) {
      throw error;
    }
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-16">
      <Link
        href="/coach/workouts"
        className="text-sm text-zinc-600 underline dark:text-zinc-400"
      >
        &larr; Back to workouts
      </Link>

      <h1 className="mt-4 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
        Client #{clientId} progress
      </h1>

      {!progress || progress.assignments.length === 0 ? (
        <p className="mt-8 text-sm text-zinc-600 dark:text-zinc-400">No logged workouts yet.</p>
      ) : (
        <ul className="mt-8 flex flex-col gap-6">
          {progress.assignments.map((assignment) => (
            <li
              key={assignment.assignment_id}
              className="rounded-xl border border-zinc-200 p-6 dark:border-zinc-800"
            >
              <div className="flex items-center justify-between">
                <p className="font-medium text-zinc-900 dark:text-zinc-50">
                  {assignment.workout_name}
                </p>
                <span className="rounded-full border border-zinc-300 px-2.5 py-1 text-xs font-medium text-zinc-700 dark:border-zinc-700 dark:text-zinc-300">
                  {statusLabel[assignment.status]}
                </span>
              </div>
              <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-500">
                Assigned {new Date(assignment.assigned_at).toLocaleDateString()}
              </p>

              {assignment.logs.length === 0 ? (
                <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-400">
                  No logged workouts yet.
                </p>
              ) : (
                <div className="mt-3 flex flex-col gap-3">
                  {assignment.logs.map((log) => (
                    <div
                      key={log.id}
                      className="rounded-lg bg-zinc-50 p-4 text-sm dark:bg-zinc-900"
                    >
                      <p className="text-xs text-zinc-500 dark:text-zinc-500">
                        Logged {new Date(log.logged_at).toLocaleString()}
                      </p>
                      <ul className="mt-1 flex flex-col gap-1">
                        {log.exercises.map((exercise, index) => (
                          <li key={index} className="text-zinc-700 dark:text-zinc-300">
                            {exercise.name}: {exercise.sets} × {exercise.reps} @ {exercise.weight}
                          </li>
                        ))}
                      </ul>
                      {log.notes && (
                        <p className="mt-2 text-zinc-600 dark:text-zinc-400">{log.notes}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

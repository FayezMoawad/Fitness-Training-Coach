import { redirect } from "next/navigation";

import { LogResultForm } from "@/components/LogResultForm";
import { apiClient } from "@/lib/apiClient";
import { requireUser } from "@/lib/session";
import type { Assignment, WorkoutLog } from "@/types/workout";

const statusLabel: Record<Assignment["status"], string> = {
  assigned: "Assigned",
  completed: "Completed",
};

export default async function ClientWorkoutsPage() {
  const { user, token } = await requireUser();
  if (user.role !== "client") {
    redirect("/coach/dashboard");
  }

  const authHeader = { headers: { Authorization: `Bearer ${token}` } };
  // Scoped to this client server-side (Step 4/6's GET /assignments already
  // filters by the caller's role) -- nothing further to filter here.
  const assignments = await apiClient.get<Assignment[]>("/assignments", authHeader);

  const completedAssignments = assignments.filter((a) => a.status === "completed");
  const logEntries = await Promise.all(
    completedAssignments.map((a) =>
      apiClient.get<WorkoutLog[]>(`/assignments/${a.id}/logs`, authHeader),
    ),
  );
  const logsByAssignment = new Map(completedAssignments.map((a, i) => [a.id, logEntries[i]]));

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-16">
      <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">Your workouts</h1>
      <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
        Log your results once you&apos;ve completed an assigned workout.
      </p>

      {assignments.length === 0 ? (
        <p className="mt-8 text-sm text-zinc-600 dark:text-zinc-400">
          Nothing assigned to you yet.
        </p>
      ) : (
        <ul className="mt-8 flex flex-col gap-6">
          {assignments.map((assignment) => (
            <li
              key={assignment.id}
              className="rounded-xl border border-zinc-200 p-6 dark:border-zinc-800"
            >
              <div className="flex items-center justify-between">
                <p className="font-medium text-zinc-900 dark:text-zinc-50">
                  Workout #{assignment.workout_id}
                </p>
                <span className="rounded-full border border-zinc-300 px-2.5 py-1 text-xs font-medium text-zinc-700 dark:border-zinc-700 dark:text-zinc-300">
                  {statusLabel[assignment.status]}
                </span>
              </div>

              {assignment.status === "completed" ? (
                <div className="mt-4 flex flex-col gap-3">
                  {(logsByAssignment.get(assignment.id) ?? []).map((log) => (
                    <div
                      key={log.id}
                      className="rounded-lg bg-zinc-50 p-4 text-sm dark:bg-zinc-900"
                    >
                      <ul className="flex flex-col gap-1">
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
              ) : (
                <div className="mt-4">
                  <LogResultForm assignmentId={assignment.id} />
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

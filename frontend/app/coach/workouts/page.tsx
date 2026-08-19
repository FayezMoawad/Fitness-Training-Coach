import Link from "next/link";
import { redirect } from "next/navigation";

import { AssignWorkoutForm } from "@/components/AssignWorkoutForm";
import { WorkoutForm } from "@/components/WorkoutForm";
import { apiClient } from "@/lib/apiClient";
import { requireUser } from "@/lib/session";
import type { Assignment, Workout } from "@/types/workout";

const statusLabel: Record<Assignment["status"], string> = {
  assigned: "Assigned",
  completed: "Completed",
};

export default async function CoachWorkoutsPage() {
  const { user, token } = await requireUser();
  if (user.role !== "coach") {
    redirect("/client/dashboard");
  }

  const authHeader = { headers: { Authorization: `Bearer ${token}` } };
  const [workouts, assignments] = await Promise.all([
    apiClient.get<Workout[]>("/workouts", authHeader),
    apiClient.get<Assignment[]>("/assignments", authHeader),
  ]);

  const knownClientIds = [...new Set(assignments.map((assignment) => assignment.client_id))];

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-16">
      <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">Workouts</h1>
      <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
        Create a workout, then assign it to a client.
      </p>

      <section className="mt-8 rounded-xl border border-zinc-200 p-6 dark:border-zinc-800">
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">New workout</h2>
        <div className="mt-4">
          <WorkoutForm />
        </div>
      </section>

      <section className="mt-8 rounded-xl border border-zinc-200 p-6 dark:border-zinc-800">
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">Assign a workout</h2>
        <div className="mt-4">
          <AssignWorkoutForm workouts={workouts} knownClientIds={knownClientIds} />
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">Your workouts</h2>
        {workouts.length === 0 ? (
          <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
            You haven&apos;t created any workouts yet.
          </p>
        ) : (
          <ul className="mt-4 flex flex-col gap-3">
            {workouts.map((workout) => (
              <li
                key={workout.id}
                className="rounded-lg border border-zinc-200 p-4 dark:border-zinc-800"
              >
                <p className="font-medium text-zinc-900 dark:text-zinc-50">{workout.name}</p>
                {workout.description && (
                  <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
                    {workout.description}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="mt-8">
        <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">Assignments</h2>
        {assignments.length === 0 ? (
          <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
            No workouts assigned yet.
          </p>
        ) : (
          <ul className="mt-4 flex flex-col gap-3">
            {assignments.map((assignment) => {
              const workout = workouts.find((w) => w.id === assignment.workout_id);
              return (
                <li
                  key={assignment.id}
                  className="flex items-center justify-between rounded-lg border border-zinc-200 p-4 dark:border-zinc-800"
                >
                  <div>
                    <p className="font-medium text-zinc-900 dark:text-zinc-50">
                      {workout?.name ?? `Workout #${assignment.workout_id}`}
                    </p>
                    <Link
                      href={`/coach/clients/${assignment.client_id}/progress`}
                      className="mt-1 block text-sm text-zinc-600 underline dark:text-zinc-400"
                    >
                      Client #{assignment.client_id} — view progress
                    </Link>
                  </div>
                  <span className="rounded-full border border-zinc-300 px-2.5 py-1 text-xs font-medium text-zinc-700 dark:border-zinc-700 dark:text-zinc-300">
                    {statusLabel[assignment.status]}
                  </span>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}

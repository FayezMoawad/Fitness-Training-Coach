"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";

import type { Workout } from "@/types/workout";

const inputClass =
  "mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-50";

interface AssignWorkoutFormProps {
  workouts: Workout[];
  /** Client ids this coach has assigned something to before, for a
   * quick-pick shortcut. There's no roster/client-list endpoint (out of
   * MVP scope, per docs/PLAN.md) — a client shares their id (shown on
   * their own dashboard) with their coach the first time. */
  knownClientIds: number[];
}

export function AssignWorkoutForm({ workouts, knownClientIds }: AssignWorkoutFormProps) {
  const router = useRouter();
  const [workoutId, setWorkoutId] = useState(String(workouts[0]?.id ?? ""));
  const [clientId, setClientId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const parsedClientId = Number(clientId);
    if (!workoutId) {
      setError("Create a workout first.");
      return;
    }
    if (!clientId || !Number.isInteger(parsedClientId) || parsedClientId <= 0) {
      setError("Enter a valid client ID.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(`/api/workouts/${workoutId}/assign`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ client_id: parsedClientId }),
      });
      const data: { detail?: string } = await response.json();

      if (!response.ok) {
        setError(data.detail ?? "Could not assign workout.");
        return;
      }

      setClientId("");
      router.refresh();
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (workouts.length === 0) {
    return (
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Create a workout above before assigning one.
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
        Workout
        <select
          value={workoutId}
          onChange={(event) => setWorkoutId(event.target.value)}
          className={inputClass}
        >
          {workouts.map((workout) => (
            <option key={workout.id} value={workout.id}>
              {workout.name}
            </option>
          ))}
        </select>
      </label>

      <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
        Client ID
        <input
          type="number"
          min={1}
          required
          value={clientId}
          onChange={(event) => setClientId(event.target.value)}
          placeholder="Ask your client for their ID"
          className={inputClass}
        />
      </label>

      {knownClientIds.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400">
          Previously assigned:
          {knownClientIds.map((id) => (
            <button
              key={id}
              type="button"
              onClick={() => setClientId(String(id))}
              className="rounded-full border border-zinc-300 px-2 py-0.5 transition hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-900"
            >
              #{id}
            </button>
          ))}
        </div>
      )}

      {error && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        className="self-start rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:opacity-60 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
      >
        {isSubmitting ? "Assigning..." : "Assign workout"}
      </button>
    </form>
  );
}

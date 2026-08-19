"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";

import { FormError } from "@/components/FormError";
import { submitJson } from "@/lib/formSubmit";
import type { WorkoutLog } from "@/types/workout";

interface ExerciseRow {
  name: string;
  sets: string;
  reps: string;
  weight: string;
}

const emptyRow: ExerciseRow = { name: "", sets: "", reps: "", weight: "" };

const inputClass =
  "mt-1 block w-full rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-50";

/** Per-assignment log form, one row per exercise. Mirrors the backend's
 * constraints (ExerciseResult, app/schemas/log.py): non-empty name,
 * positive sets/reps, non-negative weight, at least one exercise. */
export function LogResultForm({ assignmentId }: { assignmentId: number }) {
  const router = useRouter();
  const [exercises, setExercises] = useState<ExerciseRow[]>([{ ...emptyRow }]);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function updateExercise(index: number, field: keyof ExerciseRow, value: string) {
    setExercises((prev) =>
      prev.map((row, i) => (i === index ? { ...row, [field]: value } : row)),
    );
  }

  function addExercise() {
    setExercises((prev) => [...prev, { ...emptyRow }]);
  }

  function removeExercise(index: number) {
    setExercises((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const parsedExercises = [];
    for (const row of exercises) {
      const name = row.name.trim();
      const sets = Number(row.sets);
      const reps = Number(row.reps);
      const weight = Number(row.weight);

      if (!name) {
        setError("Each exercise needs a name.");
        return;
      }
      if (!Number.isInteger(sets) || sets <= 0) {
        setError("Sets must be a positive whole number.");
        return;
      }
      if (!Number.isInteger(reps) || reps <= 0) {
        setError("Reps must be a positive whole number.");
        return;
      }
      if (!Number.isFinite(weight) || weight < 0) {
        setError("Weight must be zero or greater.");
        return;
      }
      parsedExercises.push({ name, sets, reps, weight });
    }

    setIsSubmitting(true);
    const result = await submitJson<WorkoutLog>(`/api/assignments/${assignmentId}/logs`, {
      exercises: parsedExercises,
      notes: notes.trim() || null,
    });
    setIsSubmitting(false);

    if (!result.ok) {
      setError(result.error);
      return;
    }

    router.refresh();
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="flex flex-col gap-3">
        {exercises.map((row, index) => (
          <div key={index} className="flex flex-wrap items-end gap-2">
            <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Exercise
              <input
                value={row.name}
                onChange={(event) => updateExercise(index, "name", event.target.value)}
                className={`${inputClass} w-40`}
                required
              />
            </label>
            <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Sets
              <input
                type="number"
                min={1}
                value={row.sets}
                onChange={(event) => updateExercise(index, "sets", event.target.value)}
                className={`${inputClass} w-16`}
                required
              />
            </label>
            <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Reps
              <input
                type="number"
                min={1}
                value={row.reps}
                onChange={(event) => updateExercise(index, "reps", event.target.value)}
                className={`${inputClass} w-16`}
                required
              />
            </label>
            <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Weight
              <input
                type="number"
                min={0}
                step="0.5"
                value={row.weight}
                onChange={(event) => updateExercise(index, "weight", event.target.value)}
                className={`${inputClass} w-20`}
                required
              />
            </label>
            <button
              type="button"
              onClick={() => removeExercise(index)}
              disabled={exercises.length === 1}
              className="rounded-md border border-zinc-300 px-2 py-1.5 text-sm text-zinc-600 transition hover:bg-zinc-100 disabled:opacity-40 dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-900"
            >
              Remove
            </button>
          </div>
        ))}
      </div>

      <button
        type="button"
        onClick={addExercise}
        className="self-start text-sm font-medium text-zinc-700 underline dark:text-zinc-300"
      >
        + Add exercise
      </button>

      <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
        Notes (optional)
        <textarea
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          rows={2}
          className={inputClass}
        />
      </label>

      <FormError message={error} />

      <button
        type="submit"
        disabled={isSubmitting}
        className="self-start rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:opacity-60 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
      >
        {isSubmitting ? "Logging..." : "Log result"}
      </button>
    </form>
  );
}

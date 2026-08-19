"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";

import { FormError } from "@/components/FormError";
import { submitJson } from "@/lib/formSubmit";
import type { Workout } from "@/types/workout";

const inputClass =
  "mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-50";

/** Name/description only — the `Workout` model (Step 1) has no
 * exercise-level fields; those live on `WorkoutLog`, filled in by the
 * client when logging results (Step 5/9). */
export function WorkoutForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const trimmedName = name.trim();
    if (!trimmedName) {
      setError("Name is required.");
      return;
    }

    setIsSubmitting(true);
    const result = await submitJson<Workout>("/api/workouts", {
      name: trimmedName,
      description: description.trim() || null,
    });
    setIsSubmitting(false);

    if (!result.ok) {
      setError(result.error);
      return;
    }

    setName("");
    setDescription("");
    router.refresh();
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
        Name
        <input
          type="text"
          required
          value={name}
          onChange={(event) => setName(event.target.value)}
          className={inputClass}
        />
      </label>

      <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
        Description (optional)
        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          rows={3}
          className={inputClass}
        />
      </label>

      <FormError message={error} />

      <button
        type="submit"
        disabled={isSubmitting}
        className="self-start rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:opacity-60 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
      >
        {isSubmitting ? "Creating..." : "Create workout"}
      </button>
    </form>
  );
}

"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";

import { FormError } from "@/components/FormError";
import { submitJson } from "@/lib/formSubmit";
import type { User } from "@/types/user";

const inputClass =
  "mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-50";

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const result = await submitJson<{ user: User }>("/api/auth/login", { email, password });
    setIsSubmitting(false);

    if (!result.ok) {
      setError(result.error);
      return;
    }

    router.push(`/${result.data.user.role}/dashboard`);
    router.refresh();
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
        Email
        <input
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className={inputClass}
        />
      </label>

      <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
        Password
        <input
          type="password"
          required
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className={inputClass}
        />
      </label>

      <FormError message={error} />

      <button
        type="submit"
        disabled={isSubmitting}
        className="mt-2 rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:opacity-60 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
      >
        {isSubmitting ? "Logging in..." : "Log in"}
      </button>
    </form>
  );
}

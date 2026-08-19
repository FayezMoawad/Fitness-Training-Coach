"use client";

import Link from "next/link";

import { useAuth } from "@/lib/useAuth";

const linkClass =
  "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50";

export function NavBar() {
  const { user, isLoading, logout } = useAuth();

  return (
    <header className="border-b border-zinc-200 dark:border-zinc-800">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <Link href="/" className="font-semibold text-zinc-900 dark:text-zinc-50">
          Fitness Training Coach
        </Link>

        <nav className="flex items-center gap-4 text-sm">
          {isLoading ? null : user ? (
            <>
              <Link href={`/${user.role}/dashboard`} className={linkClass}>
                Dashboard
              </Link>
              <span className="text-zinc-500 dark:text-zinc-400">{user.full_name}</span>
              <button
                type="button"
                onClick={() => logout()}
                className="rounded-md border border-zinc-300 px-3 py-1.5 text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className={linkClass}>
                Log in
              </Link>
              <Link
                href="/signup"
                className="rounded-md bg-zinc-900 px-3 py-1.5 text-white transition hover:bg-zinc-700 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
              >
                Sign up
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

import Link from "next/link";

import { SignupForm } from "@/components/SignupForm";

export default function SignupPage() {
  return (
    <div className="flex flex-1 items-center justify-center bg-zinc-50 px-6 py-16 dark:bg-black">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">Sign up</h1>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
          Create an account to get started.
        </p>

        <div className="mt-8">
          <SignupForm />
        </div>

        <p className="mt-6 text-sm text-zinc-600 dark:text-zinc-400">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-zinc-900 underline dark:text-zinc-50">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}

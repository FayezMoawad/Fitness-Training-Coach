"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import type { User } from "@/types/user";

interface UseAuthResult {
  user: User | null;
  isLoading: boolean;
  logout: () => Promise<void>;
}

/** Client-side session state, backed by GET /api/auth/session (never reads
 * the httpOnly cookie directly — it can't). Used by client components like
 * `NavBar` that need to react to who's logged in. */
export function useAuth(): UseAuthResult {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    fetch("/api/auth/session")
      .then((response) => response.json())
      .then((data: { user: User | null }) => {
        if (!cancelled) {
          setUser(data.user);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const logout = useCallback(async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    setUser(null);
    router.push("/login");
    router.refresh();
  }, [router]);

  return { user, isLoading, logout };
}

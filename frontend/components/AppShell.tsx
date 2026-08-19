import type { ReactNode } from "react";

import { NavBar } from "@/components/NavBar";

/** Base layout every page renders inside: nav bar + content area. Role-aware
 * nav lives in `NavBar` (a client component, via `useAuth`); this shell
 * itself stays a Server Component since it has no interactivity of its own. */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-full flex-1 flex-col">
      <NavBar />
      <div className="flex flex-1 flex-col">{children}</div>
    </div>
  );
}

const steps = [
  {
    label: "Assign",
    title: "Coach assigns a workout",
    description: "Build a workout and send it to a client in a few clicks.",
  },
  {
    label: "Complete",
    title: "Client completes it",
    description: "The client sees exactly what's assigned and works through it.",
  },
  {
    label: "Log",
    title: "Client logs results",
    description: "Sets, reps, and weight get recorded against the assignment.",
  },
  {
    label: "Review",
    title: "Coach reviews progress",
    description: "See what was completed and how it's trending over time.",
  },
];

export default function Home() {
  return (
    <div className="flex flex-1 items-center justify-center bg-zinc-50 px-6 py-20 dark:bg-black">
      <main className="w-full max-w-3xl">
        <div className="flex flex-col items-center text-center">
          <span className="rounded-full border border-emerald-600/20 bg-emerald-50 px-3 py-1 text-xs font-medium tracking-wide text-emerald-700 uppercase dark:border-emerald-400/20 dark:bg-emerald-400/10 dark:text-emerald-400">
            In development
          </span>

          <h1 className="mt-6 text-4xl font-semibold tracking-tight text-zinc-900 sm:text-5xl dark:text-zinc-50">
            Fitness Training Coach
          </h1>

          <p className="mt-4 max-w-xl text-lg leading-relaxed text-zinc-600 dark:text-zinc-400">
            A simple, focused workflow for coaches and clients: assign a
            workout, complete it, log the results, and review progress.
          </p>
        </div>

        <ol className="mt-16 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {steps.map((step, index) => (
            <li
              key={step.label}
              className="flex gap-4 rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950"
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-900 text-sm font-medium text-white dark:bg-zinc-50 dark:text-zinc-900">
                {index + 1}
              </span>
              <div>
                <p className="text-xs font-medium tracking-wide text-emerald-600 uppercase dark:text-emerald-400">
                  {step.label}
                </p>
                <h2 className="mt-1 font-medium text-zinc-900 dark:text-zinc-50">
                  {step.title}
                </h2>
                <p className="mt-1 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
                  {step.description}
                </p>
              </div>
            </li>
          ))}
        </ol>
      </main>
    </div>
  );
}

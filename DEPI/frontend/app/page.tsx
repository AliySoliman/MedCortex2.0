export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col justify-center px-6 py-14 sm:px-10">
      <section className="rounded-3xl border border-border/70 bg-surface p-8 shadow-[0_16px_40px_rgba(76,57,142,0.12)] sm:p-12">
        <span className="inline-flex items-center rounded-full bg-primary-soft px-4 py-1 text-sm font-semibold text-primary-strong">
          Care Dashboard
        </span>
        <h1 className="mt-5 max-w-2xl text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
          Calm, modern interface for healthcare teams.
        </h1>
        <p className="mt-5 max-w-2xl text-base text-muted sm:text-lg">
          Tailwind CSS is configured and ready. This global theme uses soft
          purple tones, high readability, and clean spacing suitable for
          medical workflows.
        </p>
        <div className="mt-9 flex flex-wrap gap-3">
          <button className="rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-white transition hover:bg-primary-strong">
            Start Building
          </button>
          <button className="rounded-xl border border-border bg-surface-soft px-5 py-2.5 text-sm font-medium text-foreground transition hover:bg-primary-soft">
            View Components
          </button>
        </div>
      </section>
    </main>
  );
}

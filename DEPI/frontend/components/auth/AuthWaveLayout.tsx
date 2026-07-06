type AuthWaveLayoutProps = {
  children: React.ReactNode;
  rightTitle: string;
  rightDescription: string;
  badge?: string;
};

function CloudRow({
  position,
  circles,
  className = "",
}: {
  position: "top" | "bottom";
  circles: string[];
  className?: string;
}) {
  const base =
    position === "top"
      ? "absolute left-[36%] right-[-6%] top-0 h-[170px] items-start"
      : "absolute bottom-0 left-[18%] right-[-2%] h-[170px] items-end";

  const translate = position === "top" ? "-translate-y-1/2" : "translate-y-1/2";

  return (
    <div className={`pointer-events-none hidden lg:flex ${base} ${className}`} aria-hidden="true">
      {circles.map((size, index) => (
        <span
          key={`${position}-${index}`}
          className={`block shrink-0 rounded-full bg-white ${size} ${translate} ${index > 0 ? "-ml-8" : ""}`}
        />
      ))}
    </div>
  );
}

export default function AuthWaveLayout({
  children,
  rightTitle,
  rightDescription,
  badge = "MedCortex",
}: AuthWaveLayoutProps) {
  return (
    <main className="min-h-screen bg-[#f3efff] px-4 py-5 sm:px-6 lg:px-8 lg:py-6">
      <div className="mx-auto flex min-h-[calc(100vh-2rem)] max-w-[1320px] items-stretch">
        <section className="relative grid w-full overflow-hidden rounded-[2rem] bg-white shadow-[0_30px_80px_rgba(162,133,255,0.18)] lg:min-h-[760px] lg:grid-cols-[1.02fr_0.98fr]">
          <div
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_12%_20%,rgba(214,201,255,0.65),transparent_28%),radial-gradient(circle_at_30%_56%,rgba(211,203,255,0.5),transparent_30%),linear-gradient(180deg,#ffffff_0%,#fffefe_100%)]"
            aria-hidden="true"
          />

          <div
            className="pointer-events-none absolute right-0 top-0 h-[240px] w-full bg-[linear-gradient(130deg,#d3c3ff_0%,#b999ff_38%,#9b74f3_72%,#8a63e8_100%)] lg:w-[63%]"
            style={{
              clipPath:
                "polygon(28% 0%,100% 0%,100% 100%,86% 100%,76% 88%,61% 94%,45% 78%,20% 72%,9% 48%,0% 14%)",
            }}
            aria-hidden="true"
          />

          <div
            className="pointer-events-none absolute bottom-0 right-0 h-[230px] w-full bg-[linear-gradient(130deg,#cdbaff_0%,#ad8cff_42%,#9469ef_76%,#8258e1_100%)] lg:w-[78%]"
            style={{
              clipPath:
                "polygon(27% 100%,100% 100%,100% 0%,93% 8%,84% 10%,76% 28%,60% 22%,48% 40%,36% 44%,26% 66%,9% 72%,0% 92%)",
            }}
            aria-hidden="true"
          />

          <CloudRow
            position="top"
            circles={["h-36 w-36", "h-44 w-44", "h-32 w-32", "h-28 w-28", "h-24 w-24"]}
          />
          <CloudRow
            position="bottom"
            circles={["h-24 w-24", "h-32 w-32", "h-28 w-28", "h-36 w-36", "h-24 w-24", "h-20 w-20"]}
          />

          <div className="relative z-10 flex flex-col justify-between px-6 py-8 sm:px-10 sm:py-10 lg:px-16 lg:py-14">
            <div className="inline-flex w-fit items-center rounded-full border border-[#ece7fb] bg-white/85 px-4 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-[#9475ef] shadow-[0_10px_30px_rgba(185,153,255,0.12)] backdrop-blur">
              {badge}
            </div>
            <div className="flex-1 py-8 lg:py-10">{children}</div>
          </div>

          <aside className="relative z-10 flex items-center px-6 pb-10 pt-2 sm:px-10 lg:px-14 lg:pb-0 lg:pt-0">
            <div className="mx-auto max-w-[430px] text-center">
              <h2 className="text-4xl font-bold tracking-[-0.04em] text-[#111111] sm:text-5xl">
                {rightTitle}
              </h2>
              <p className="mt-6 text-lg leading-10 text-[#4c445a] sm:text-[1.75rem] sm:leading-[1.85] lg:text-[1.15rem] lg:leading-10">
                {rightDescription}
              </p>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}

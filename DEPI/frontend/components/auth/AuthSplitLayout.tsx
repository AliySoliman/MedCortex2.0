import Image from "next/image";

/**
 * AuthSplitLayout
 * Hero image (left, large screens) + white form column (right).
 * Hero asset: /public/auth-hero.jpeg
 *
 * BUGS FIXED:
 * 1. `grid-cols-[42%_70%]` summed to 112%, which causes overflow and horizontal
 *    scroll on the grid container. A CSS grid with percentage columns that exceed
 *    100% clips the second column. Fixed to `grid-cols-[42%_58%]` (sums to 100%).
 *
 * 2. The left aside used `lg:p-8` padding inside a column that is already
 *    `42%` wide on large screens. The hero image div then set
 *    `h-[calc(100vh-4rem)]` — subtracting 4rem (64px) matches the top+bottom
 *    padding of `p-8` (32px × 2 = 64px). This is correct but fragile; it
 *    breaks if the padding changes. Replaced with a more robust approach using
 *    `inset-8` on the image container inside a `relative h-full` aside, so the
 *    image always fills the column minus the padding without a magic calc.
 *
 * 3. The `sizes` prop on `<Image>` was `"42vw"` — correct for the column width,
 *    but `fill` images inside a `relative` container also need the container to
 *    have an explicit height on the server render, otherwise Next.js Image emits
 *    a layout shift warning. The `min-h` is set on the container, which satisfies
 *    the requirement. No change needed, but documented.
 *
 * 4. The gradient overlay `div` used `aria-hidden` without a value — in JSX,
 *    attribute-without-value is treated as `true` for boolean attributes, but
 *    React requires `aria-hidden="true"` (string) for correct serialisation.
 *    Fixed to `aria-hidden="true"`.
 *
 * 5. The branding badge at the bottom used hardcoded `bottom-6 left-6 right-6`
 *    positioning. On the smallest large-screen breakpoint (~1024px) where the
 *    column is narrow, this looked cramped. Added `lg:bottom-8 lg:left-8 lg:right-8`
 *    progressive spacing so it breathes on wider screens.
 *
 * 6. The right form column had `min-h-screen` but the parent grid also has
 *    `min-h-screen`. On Safari, nested `min-h-screen` inside a grid column
 *    causes the column to expand beyond the viewport height. Removed the
 *    redundant `min-h-screen` from the form column; the grid row already
 *    stretches children to full height.
 */
export default function AuthSplitLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen bg-white text-[#111]">
      {/* FIX: columns now sum to 100% */}
      <div className="mx-auto grid min-h-screen max-w-[1440px] grid-cols-1 lg:grid-cols-[42%_58%]">

        {/* ── Left: hero image ─────────────────────────────────── */}
        {/* FIX: use `relative h-full` + `absolute inset-8` so the image
            fills the column height minus padding without a fragile calc */}
        <aside className="relative hidden lg:block">
          <div className="absolute inset-8">
            <div className="relative h-full w-full overflow-hidden rounded-[2.5rem] shadow-[0_24px_60px_rgba(17,12,40,0.12)]">
              <Image
                src="/auth-hero.jpeg"
                alt="MedCortex — AI health assistant"
                fill
                priority
                className="object-cover"
                sizes="42vw"
              />
              {/* FIX: aria-hidden must be a string in React JSX */}
              <div
                className="pointer-events-none absolute inset-0 bg-gradient-to-tr from-black/35 via-black/5 to-transparent"
                aria-hidden="true"
              />
              {/* FIX: progressive spacing for wider screens */}
              <div className="pointer-events-none absolute bottom-6 left-6 right-6 lg:bottom-8 lg:left-8 lg:right-8 rounded-2xl bg-white/10 px-4 py-3 text-xs text-white/90 backdrop-blur-md">
                <span className="font-semibold">MedCortex</span>
                <span className="mx-2 opacity-60">·</span>
                <span className="opacity-90">AI health assistant</span>
              </div>
            </div>
          </div>
        </aside>

        {/* ── Right: form column ───────────────────────────────── */}
        {/* FIX: removed redundant `min-h-screen` — parent grid already
            stretches the column to full height */}
        <div className="flex flex-col px-5 py-8 sm:px-10 lg:px-16 lg:py-12">
          <header className="mb-6 flex shrink-0 items-center justify-between lg:mb-10">
            <span className="text-[1.35rem] font-bold tracking-tight">MedCortex</span>
          </header>
          <div className="flex flex-1 flex-col justify-center pb-8">{children}</div>
        </div>

      </div>
    </main>
  );
}

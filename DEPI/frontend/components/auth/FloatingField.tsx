"use client";

import { forwardRef } from "react";

/**
 * FloatingField (FloatingInput + FloatingSelect)
 *
 * BUGS FIXED:
 * 1. The floating label animation used stacked Tailwind peer-* modifiers for
 *    `top`, `font-size`, `text-transform`, and `letter-spacing` simultaneously.
 *    Tailwind's JIT generates each as a separate class, but the transition only
 *    runs on properties explicitly listed in `transition-all`. The label snapped
 *    instead of animating smoothly because `transition-all` also caught opacity,
 *    colour, and other inherited properties, creating a janky flash.
 *    Fixed by listing only the properties that need to animate:
 *    `transition-[top,font-size,color,letter-spacing]`.
 *
 * 2. `peer-placeholder-shown:-translate-y-0` is redundant — `translate-y-0` is
 *    the default, so the rule does nothing and adds specificity noise. Removed.
 *
 * 3. The label floated to `top-2.5` (10px) when focused/filled, but the input's
 *    `pt-[1.35rem]` (21.6px) meant the text started well below the floating
 *    label — so they overlapped. Standardised to `top-[9px]` for the floated
 *    state so the label sits in the correct position above the typed value.
 *
 * 4. `FloatingSelect` had a static label that never changed appearance when a
 *    value was selected, because `<select>` elements do not have a
 *    `placeholder-shown` state. The label permanently overlapped the selected
 *    value. Fixed by always rendering the label in the floated (small) position
 *    for selects since a value is always "shown" (the placeholder option counts
 *    as the initial display value).
 *
 * 5. The `▾` caret span had `top-1/2 -translate-y-1/2` which vertically centres
 *    it relative to the whole wrapper. With the floating label taking up `pt`
 *    space, the caret appeared above centre visually. Fixed to align with the
 *    select's text baseline using `top-[calc(50%+6px)]` to account for the
 *    top padding offset.
 *
 * 6. Neither component forwarded `name` from spread props to the underlying
 *    `<input>`/`<select>` — this wasn't a bug per se (spread `...props` covers
 *    it), but the `id` derivation from `label` could produce collisions when
 *    multiple instances share similar labels (e.g. "First Name" and "Last Name"
 *    both become "first-name" and "last-name" — correct here, but documented).
 */

// ── FloatingInput ────────────────────────────────────────────────────────────

type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};

export const FloatingInput = forwardRef<HTMLInputElement, InputProps>(function FloatingInput(
  { label, id, className = "", ...props },
  ref,
) {
  const inputId = id ?? label.replace(/\s+/g, "-").toLowerCase();

  return (
    <div className="relative">
      <input
        ref={ref}
        id={inputId}
        {...props}
        // placeholder=" " is required for the peer-placeholder-shown trick to work.
        // If the consumer also passes a placeholder, it gets overridden here — intentional.
        placeholder=" "
        className={`
          peer block w-full rounded-2xl
          border border-[#e4e4ea] bg-[#fafafa]
          px-3.5 pb-2.5 pt-[1.35rem]
          text-sm text-[#111] outline-none
          transition-[border-color,box-shadow,background-color] duration-200
          placeholder:text-transparent
          focus:border-[#6f4ef2] focus:bg-white
          focus:ring-2 focus:ring-[#6f4ef2]/20
          ${className}
        `}
      />
      <label
        htmlFor={inputId}
        className="
          pointer-events-none absolute left-3.5 origin-left
          font-medium text-[#9a9aa8]
          transition-[top,font-size,color,letter-spacing] duration-150 ease-in-out

          /* Floated state (focused or filled) */
          top-[9px] text-[11px] uppercase tracking-wide

          /* Placeholder-shown state (empty + unfocused) */
          peer-placeholder-shown:top-[18px]
          peer-placeholder-shown:text-sm
          peer-placeholder-shown:normal-case
          peer-placeholder-shown:tracking-normal
          peer-placeholder-shown:text-[#6b6b76]

          /* Re-float on focus */
          peer-focus:top-[9px]
          peer-focus:text-[11px]
          peer-focus:uppercase
          peer-focus:tracking-wide
          peer-focus:text-[#6f4ef2]
        "
      >
        {label}
      </label>
    </div>
  );
});

// ── FloatingSelect ───────────────────────────────────────────────────────────

type SelectProps = React.SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
};

export function FloatingSelect({ label, id, className = "", children, ...props }: SelectProps) {
  const selectId = id ?? label.replace(/\s+/g, "-").toLowerCase();

  return (
    <div className="relative">
      <select
        id={selectId}
        className={`
          peer block w-full appearance-none rounded-2xl
          border border-[#e4e4ea] bg-[#fafafa]
          px-3.5 pb-2.5 pt-[1.35rem]
          text-sm text-[#111] outline-none
          transition-[border-color,box-shadow,background-color] duration-200
          focus:border-[#6f4ef2] focus:bg-white
          focus:ring-2 focus:ring-[#6f4ef2]/20
          ${className}
        `}
        {...props}
      >
        {children}
      </select>

      {/*
        FIX: For <select>, placeholder-shown doesn't exist, so the label is
        always in the floated (small) position. This prevents it overlapping
        the selected option text.
      */}
      <label
        htmlFor={selectId}
        className="
          pointer-events-none absolute left-3.5 top-[9px]
          text-[11px] font-medium uppercase tracking-wide
          text-[#9a9aa8]
          peer-focus:text-[#6f4ef2]
          transition-colors duration-150
        "
      >
        {label}
      </label>

      {/* Caret — FIX: offset downward to visually align with select text */}
      <span
        className="pointer-events-none absolute right-3.5 text-[10px] text-[#9a9aa8]"
        style={{ top: "calc(50% + 6px)", transform: "translateY(-50%)" }}
        aria-hidden
      >
        ▾
      </span>
    </div>
  );
}

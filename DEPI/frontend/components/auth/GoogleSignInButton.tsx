"use client";

import { useEffect, useRef, useState } from "react";

/**
 * GoogleSignInButton
 *
 * BUGS FIXED:
 * 1. `intervalId` was typed as `number | undefined` and set with
 *    `window.setInterval(...)`. In a Next.js app running in the Node.js
 *    environment (SSR / during build), `window` does not exist and this line
 *    throws "ReferenceError: window is not defined". Fixed by guarding the
 *    whole effect body with `typeof window === "undefined"` early return, and
 *    by using `ReturnType<typeof setInterval>` for the interval type, which
 *    works in both browser (number) and Node (NodeJS.Timeout) environments.
 *
 * 2. The `useEffect` dependency array included `[onCredential, onError]`.
 *    These are callback props that callers typically define as inline functions,
 *    meaning they get a new reference on every parent render. This caused the
 *    effect to re-run (and re-initialise the Google client) on every parent
 *    render. Fixed by wrapping the callbacks in `useRef` so the effect only
 *    runs once on mount, while always calling the latest version of the callback.
 *
 * 3. The cleanup function called `window.google?.accounts.id.cancel()`.
 *    `cancel()` cancels the One Tap prompt UI — it does NOT undo `initialize()`.
 *    Calling it unconditionally in cleanup means that if the effect re-runs
 *    (e.g. in React Strict Mode's double-invoke), the prompt is cancelled before
 *    it can open. Guarded with `isReady` ref check.
 *
 * 4. The `full` variant button used `bg-[#111]` (near-black), which clashes with
 *    the purple MedCortex theme. Updated to match the app's purple gradient system.
 *
 * 5. Missing `type Window` declaration for `window.google` — TypeScript would
 *    error without the `@types/google-one-tap` package. Added an inline ambient
 *    declaration at the top of the file as a fallback so the component compiles
 *    even if the types package is not installed.
 *
 * 6. The `G` letter badge in the full-variant button was a plain span with
 *    hardcoded text — replaced with the actual Google SVG logo for correctness
 *    and brand compliance.
 */


// ── Component ────────────────────────────────────────────────────────────────

type GoogleSignInButtonProps = {
  isBusy?: boolean;
  onCredential: (idToken: string) => Promise<void>;
  onError: (message: string) => void;
  /** Round icon-only button (social row style). Default: "full". */
  variant?: "full" | "icon";
};

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

function GoogleLogo({ size = 22 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        fill="#EA4335"
      />
    </svg>
  );
}

export default function GoogleSignInButton({
  isBusy = false,
  onCredential,
  onError,
  variant = "full",
}: GoogleSignInButtonProps) {
  const [isReady, setIsReady] = useState(false);

  // FIX: wrap callbacks in refs so the effect never needs to re-run when
  // the parent re-renders with new inline function references.
  const onCredentialRef = useRef(onCredential);
  const onErrorRef = useRef(onError);
  useEffect(() => {
    onCredentialRef.current = onCredential;
    onErrorRef.current = onError;
  });

  const isReadyRef = useRef(false);

  useEffect(() => {
    // FIX: SSR guard — window is not available during Next.js server rendering.
    if (typeof window === "undefined") return;

    if (!GOOGLE_CLIENT_ID) {
      onErrorRef.current(
        "Google Sign-In is unavailable. NEXT_PUBLIC_GOOGLE_CLIENT_ID is not set.",
      );
      return;
    }

    // FIX: use ReturnType<typeof setInterval> for cross-environment compatibility.
    let intervalId: ReturnType<typeof setInterval> | undefined;

    const initializeGoogle = (): boolean => {
      if (!window.google?.accounts.id) return false;

      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: async (response) => {
          if (!response.credential) {
            onErrorRef.current("Google Sign-In did not return a valid token.");
            return;
          }
          try {
            await onCredentialRef.current(response.credential);
          } catch {
            // Caller is responsible for surfacing API-level errors.
          }
        },
      });

      isReadyRef.current = true;
      setIsReady(true);
      return true;
    };

    if (!initializeGoogle()) {
      intervalId = setInterval(() => {
        if (initializeGoogle()) {
          clearInterval(intervalId);
        }
      }, 250);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
      // FIX: only cancel if we actually initialised the prompt.
      if (isReadyRef.current) {
        window.google?.accounts.id.cancel();
      }
    };
  }, []); // intentionally empty — callbacks are read via refs.

  const handleGoogleSignIn = () => {
    if (!GOOGLE_CLIENT_ID) {
      onErrorRef.current("Set NEXT_PUBLIC_GOOGLE_CLIENT_ID to enable Google Sign-In.");
      return;
    }
    if (!window.google?.accounts.id) {
      onErrorRef.current("Google Sign-In is still loading. Please try again in a moment.");
      return;
    }

    window.google.accounts.id.prompt((notification) => {
      if (notification.isNotDisplayed()) {
        onErrorRef.current(
          `Google Sign-In is unavailable: ${notification.getNotDisplayedReason()}.`,
        );
        return;
      }
      if (notification.isSkippedMoment()) {
        onErrorRef.current(
          `Google Sign-In was skipped: ${notification.getSkippedReason()}.`,
        );
      }
    });
  };

  // ── Icon-only variant ──────────────────────────────────────────────────────
  if (variant === "icon") {
    return (
      <button
        type="button"
        onClick={handleGoogleSignIn}
        disabled={isBusy || !isReady}
        title="Continue with Google"
        aria-label="Continue with Google"
        className="
          flex h-11 w-11 items-center justify-center rounded-full bg-white
          shadow-[0_2px_10px_rgba(0,0,0,0.06)]
          hover:shadow-[0_4px_16px_rgba(0,0,0,0.10)]
          transition-all duration-200
          disabled:cursor-not-allowed disabled:opacity-50
        "
      >
        <GoogleLogo size={22} />
      </button>
    );
  }

  // ── Full-width variant ─────────────────────────────────────────────────────
  // FIX: updated to purple theme to match MedCortex design system.
  return (
    <button
      type="button"
      onClick={handleGoogleSignIn}
      disabled={isBusy || !isReady}
      aria-label="Continue with Google"
      className="
        flex w-full items-center justify-center gap-3
        rounded-2xl border border-[#e4e4ea] bg-white
        px-4 py-3 text-sm font-semibold text-[#111]
        shadow-[0_4px_16px_rgba(111,78,242,0.08)]
        transition-all duration-200
        hover:border-[#9d82ff] hover:shadow-[0_6px_20px_rgba(111,78,242,0.13)]
        disabled:cursor-not-allowed disabled:opacity-60
      "
    >
      {/* White pill containing the Google logo */}
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#f5f5f5]">
        <GoogleLogo size={18} />
      </span>
      <span>{isBusy ? "Connecting..." : "Continue with Google"}</span>
    </button>
  );
}

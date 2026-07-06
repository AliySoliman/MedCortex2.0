"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import axios from "axios";
import { Eye, EyeOff, LockKeyhole, Mail } from "lucide-react";

import { persistSession } from "@/lib/session";
import { login } from "@/services/auth";
import type { User } from "@/types/user";

type PillInputProps = {
  icon: React.ReactNode;
  type: string;
  value: string;
  placeholder: string;
  autoComplete?: string;
  onChange: (value: string) => void;
  required?: boolean;
  onTrailingIconClick?: () => void;
  trailingIcon?: React.ReactNode;
};

function PillInput({
  icon,
  type,
  value,
  placeholder,
  autoComplete,
  onChange,
  required,
  onTrailingIconClick,
  trailingIcon,
}: PillInputProps) {
  return (
    <div className="flex items-center rounded-full bg-white pl-3 pr-5 shadow-[0_18px_50px_rgba(192,177,255,0.35)] ring-1 ring-[#efebfb]">
      <span className="mr-4 flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[linear-gradient(180deg,#d2c1ff_0%,#b897ff_45%,#976cf0_100%)] text-white shadow-[0_10px_24px_rgba(176,145,255,0.38)]">
        {icon}
      </span>

      <input
        type={type}
        value={value}
        autoComplete={autoComplete}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        required={required}
        className="h-16 w-full bg-transparent text-base text-[#5d5a72] outline-none placeholder:text-[#9b97b3]"
      />

      {trailingIcon && (
        <button
          type="button"
          onClick={onTrailingIconClick}
          className="ml-4 flex h-10 w-10 items-center justify-center rounded-full text-[#936aef] transition hover:bg-[#f6f0ff]"
          aria-label="Toggle password visibility"
        >
          {trailingIcon}
        </button>
      )}
    </div>
  );
}

export default function LoginForm() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(false);

  const completeAuthentication = useCallback(
    (token: string, user: User) => {
      persistSession(token, user);
      router.push("/chat");
    },
    [router]
  );

  const handleSubmit = async (
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    setError(null);
    setIsLoading(true);

    try {
      const response = await login({
        email,
        password,
      });

      completeAuthentication(
        response.access_token,
        response.user
      );
    } catch (err: unknown) {
      let message =
        "Login failed. Please check your credentials.";

      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;

        if (typeof detail === "string") {
          message = detail;
        } else if (Array.isArray(detail)) {
          message = detail
            .map((item: any) => {
              if (typeof item === "string") return item;
              if (item?.msg) return item.msg;
              if (item?.message) return item.message;
              return JSON.stringify(item);
            })
            .join("\n");
        } else if (
          detail &&
          typeof detail === "object"
        ) {
          message =
            detail.message ??
            detail.error ??
            JSON.stringify(detail);
        } else if (err.message) {
          message = err.message;
        }
      } else if (err instanceof Error) {
        message = err.message;
      }

      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-[560px] flex-col items-center text-center">
      <h1 className="text-5xl font-bold tracking-[-0.045em] text-[#111111] sm:text-6xl">
        Hello!
      </h1>

      <p className="mt-2 text-xl text-[#3d3949]">
        Sign in to your account
      </p>

      <form
        className="mt-12 w-full space-y-6 text-left"
        onSubmit={handleSubmit}
      >
        <PillInput
          icon={<Mail size={22} strokeWidth={2.2} />}
          type="email"
          value={email}
          placeholder="E-mail"
          autoComplete="email"
          onChange={setEmail}
          required
        />

        <PillInput
          icon={<LockKeyhole size={22} strokeWidth={2.2} />}
          type={showPassword ? "text" : "password"}
          value={password}
          placeholder="Password"
          autoComplete="current-password"
          onChange={setPassword}
          required
          onTrailingIconClick={() =>
            setShowPassword((current) => !current)
          }
          trailingIcon={
            showPassword ? (
              <EyeOff size={22} strokeWidth={1.9} />
            ) : (
              <Eye size={22} strokeWidth={1.9} />
            )
          }
        />

        <div className="flex flex-col gap-3 px-3 text-[0.95rem] text-[#8a83a7] sm:flex-row sm:items-center sm:justify-between">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              defaultChecked
              className="h-5 w-5 rounded border-[#d2c5fa] text-[#9f7bf5] accent-[#9f7bf5]"
            />
            <span>Remember me</span>
          </label>

          <Link
            href="#"
            onClick={(e) => e.preventDefault()}
            className="font-medium text-[#8a83a7] transition hover:text-[#8e6bf2]"
          >
            Forgot password?
          </Link>
        </div>

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 whitespace-pre-line">
            {error}
          </div>
        )}

        <div className="flex justify-center pt-2">
          <button
            type="submit"
            disabled={isLoading}
            className="min-w-[280px] rounded-full bg-[linear-gradient(90deg,#b089ff_0%,#9a73f3_52%,#875fe6_100%)] px-10 py-4 text-xl font-semibold tracking-wide text-white shadow-[0_18px_40px_rgba(161,127,248,0.4)] transition hover:scale-[1.01] hover:shadow-[0_22px_46px_rgba(161,127,248,0.46)] disabled:cursor-not-allowed disabled:opacity-65"
          >
            {isLoading ? "Signing In..." : "SIGN IN"}
          </button>
        </div>
      </form>

      <p className="mt-12 text-lg text-[#8a83a7]">
        Don&apos;t have an account?{" "}
        <Link
          href="/signup"
          className="font-semibold text-[#936aef] transition hover:text-[#7d55e0]"
        >
          Create
        </Link>
      </p>
    </div>
  );
}
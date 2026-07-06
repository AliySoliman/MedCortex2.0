"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import axios from "axios";
import {
  Activity,
  Eye,
  EyeOff,
  HeartPulse,
  LockKeyhole,
  Mail,
  ShieldAlert,
  UserRound,
  VenusAndMars,
} from "lucide-react";

import { persistSession } from "@/lib/session";
import { signup } from "@/services/auth";
import type { User } from "@/types/user";

type PillInputProps = {
  icon: React.ReactNode;
  type?: string;
  value: string;
  placeholder: string;
  autoComplete?: string;
  onChange: (value: string) => void;
  required?: boolean;
  min?: number;
  onTrailingIconClick?: () => void;
  trailingIcon?: React.ReactNode;
};

function PillInput({
  icon,
  type = "text",
  value,
  placeholder,
  autoComplete,
  onChange,
  required,
  min,
  onTrailingIconClick,
  trailingIcon,
}: PillInputProps) {
  return (
    <div className="flex items-center rounded-full bg-white pl-3 pr-5 shadow-[0_16px_42px_rgba(194,179,255,0.32)] ring-1 ring-[#efeafb]">
      <span className="mr-4 flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[linear-gradient(180deg,#d5c8ff_0%,#bc9cff_48%,#986cf1_100%)] text-white shadow-[0_10px_24px_rgba(176,145,255,0.35)]">
        {icon}
      </span>
      <input
        type={type}
        value={value}
        autoComplete={autoComplete}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        required={required}
        min={min}
        className="h-14 w-full bg-transparent text-[0.95rem] text-[#5d5a72] outline-none placeholder:text-[#9b97b3]"
      />
      {trailingIcon ? (
        <button
          type="button"
          onClick={onTrailingIconClick}
          className="ml-4 flex h-10 w-10 items-center justify-center rounded-full text-[#936aef] transition hover:bg-[#f6f0ff]"
          aria-label="Toggle password visibility"
        >
          {trailingIcon}
        </button>
      ) : null}
    </div>
  );
}

type PillSelectProps = {
  icon: React.ReactNode;
  value: string;
  onChange: (value: string) => void;
  children: React.ReactNode;
};

function PillSelect({ icon, value, onChange, children }: PillSelectProps) {
  return (
    <div className="flex items-center rounded-full bg-white pl-3 pr-5 shadow-[0_16px_42px_rgba(194,179,255,0.32)] ring-1 ring-[#efeafb]">
      <span className="mr-4 flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[linear-gradient(180deg,#d5c8ff_0%,#bc9cff_48%,#986cf1_100%)] text-white shadow-[0_10px_24px_rgba(176,145,255,0.35)]">
        {icon}
      </span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-14 w-full appearance-none bg-transparent text-[0.95rem] text-[#5d5a72] outline-none"
      >
        {children}
      </select>
    </div>
  );
}

export default function SignupForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("");
  const [activityLevel, setActivityLevel] = useState("");
  const [allergies, setAllergies] = useState("");
  const [conditions, setConditions] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const completeAuthentication = useCallback(
    (token: string, user: User) => {
      persistSession(token, user);
      router.push("/chat");
    },
    [router],
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const response = await signup({
        name,
        email,
        password,
        age: age ? Number(age) : undefined,
        gender: gender || undefined,
        activity_level:
          activityLevel === "low" || activityLevel === "medium" || activityLevel === "high"
            ? activityLevel
            : undefined,
        allergies: allergies || undefined,
        conditions: conditions || undefined,
      });
      completeAuthentication(response.access_token, response.user);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data;

        let message = "Signup failed. Please review your details.";

        if (typeof data?.detail === "string") {
          message = data.detail;
        } else if (Array.isArray(data?.detail)) {
          message = data.detail[0]?.msg || message;
        }

        setError(message);
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-[640px] flex-col items-center text-center">
      <h1 className="text-4xl font-bold tracking-[-0.045em] text-[#111111] sm:text-5xl">
        Hello!
      </h1>
      <p className="mt-2 text-lg text-[#3d3949]">Create your MedCortex account</p>

      <form className="mt-10 w-full space-y-4 text-left" onSubmit={handleSubmit}>
        <PillInput
          icon={<UserRound size={20} strokeWidth={2.1} />}
          value={name}
          placeholder="Full name"
          autoComplete="name"
          onChange={setName}
          required
        />

        <div className="grid gap-4 sm:grid-cols-2">
          <PillInput
            icon={<Mail size={20} strokeWidth={2.1} />}
            type="email"
            value={email}
            placeholder="E-mail"
            autoComplete="email"
            onChange={setEmail}
            required
          />
          <PillInput
            icon={<LockKeyhole size={20} strokeWidth={2.1} />}
            type={showPassword ? "text" : "password"}
            value={password}
            placeholder="Password"
            autoComplete="new-password"
            onChange={setPassword}
            onTrailingIconClick={() => setShowPassword((current) => !current)}
            trailingIcon={
              showPassword ? <EyeOff size={20} strokeWidth={1.9} /> : <Eye size={20} strokeWidth={1.9} />
            }
            required
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <PillInput
            icon={<HeartPulse size={20} strokeWidth={2.1} />}
            type="number"
            value={age}
            placeholder="Age"
            onChange={setAge}
            min={0}
          />
          <PillSelect
            icon={<VenusAndMars size={20} strokeWidth={2.1} />}
            value={gender}
            onChange={setGender}
          >
            <option value="">Gender</option>
            <option value="female">Female</option>
            <option value="male">Male</option>
          </PillSelect>
        </div>

        <PillSelect
          icon={<Activity size={20} strokeWidth={2.1} />}
          value={activityLevel}
          onChange={setActivityLevel}
        >
          <option value="">Activity level</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </PillSelect>

        <div className="grid gap-4 sm:grid-cols-2">
          <PillInput
            icon={<ShieldAlert size={20} strokeWidth={2.1} />}
            value={allergies}
            placeholder="Allergies"
            onChange={setAllergies}
          />
          <PillInput
            icon={<HeartPulse size={20} strokeWidth={2.1} />}
            value={conditions}
            placeholder="Conditions"
            onChange={setConditions}
          />
        </div>

        {error ? (
          <p className="rounded-[1.25rem] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        <div className="flex justify-center pt-2">
          <button
            type="submit"
            disabled={isLoading}
            className="min-w-[280px] rounded-full bg-[linear-gradient(90deg,#b089ff_0%,#9a73f3_52%,#875fe6_100%)] px-10 py-4 text-lg font-semibold tracking-wide text-white shadow-[0_18px_40px_rgba(161,127,248,0.4)] transition hover:scale-[1.01] hover:shadow-[0_22px_46px_rgba(161,127,248,0.46)] disabled:cursor-not-allowed disabled:opacity-65"
          >
            {isLoading ? "Creating Account..." : "CREATE ACCOUNT"}
          </button>
        </div>
      </form>

      <p className="mt-10 text-base text-[#8a83a7]">
        Already have an account?{" "}
        <Link className="font-semibold text-[#936aef] transition hover:text-[#7d55e0]" href="/login">
          Sign in
        </Link>
      </p>
    </div>
  );
}

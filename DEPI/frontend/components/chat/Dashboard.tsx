"use client";

import { useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  Calendar,
  Heart,
  MessageSquare,
  Stethoscope,
  TrendingUp,
  Utensils,
  Zap,
} from "lucide-react";
import type { ChatThread } from "@/services/chat";
import type { User } from "@/types/user";

// ─────────────────────────────────────────────────────────────────────────────

interface DashboardProps {
  user: User | null;
  threads: ChatThread[];
}

// ─────────────────────────────────────────────────────────────────────────────
// Analytics helpers
// ─────────────────────────────────────────────────────────────────────────────

function frequencyMap(items: string[]): Record<string, number> {
  const map: Record<string, number> = {};
  items.forEach((item) => {
    const key = item.trim();
    if (key) map[key] = (map[key] ?? 0) + 1;
  });
  return map;
}

function unique(items: string[]): string[] {
  return [...new Set(items.filter(Boolean))];
}

function topEntries(
  freq: Record<string, number>,
  n: number,
): [string, number][] {
  return Object.entries(freq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, n);
}

function useAnalytics(threads: ChatThread[], referenceTime: number) {
  return useMemo(() => {
    const DAY_MS = 86_400_000;
    const WINDOW = 30;

    const allSymptoms: string[] = [];
    const allConditions: string[] = [];
    const allFoods: string[] = [];
    const allFoodsAvoid: string[] = [];
    const allExercises: string[] = [];
    const allRest: string[] = [];
    const activityByDay = new Array<number>(WINDOW).fill(0);

    for (const thread of threads) {
      for (const msg of thread.messages) {
        const ts = new Date(msg.timestamp).getTime();
        const daysAgo = Math.floor((referenceTime - ts) / DAY_MS);

        if (msg.role === "user") {
          if (daysAgo >= 0 && daysAgo < WINDOW) {
            activityByDay[WINDOW - 1 - daysAgo]++;
          }
        }

        if (msg.role === "assistant" && msg.data) {
          allSymptoms.push(...msg.data.symptoms);
          allConditions.push(...msg.data.suspected_conditions);
          allFoods.push(...msg.data.recommendations.foods_to_eat);
          allFoodsAvoid.push(...msg.data.recommendations.foods_to_avoid);
          allExercises.push(...msg.data.recommendations.exercises_recommended);
          if (msg.data.recommendations.rest_recommendation) {
            allRest.push(msg.data.recommendations.rest_recommendation);
          }
        }
      }
    }

    const symptomFreq = frequencyMap(allSymptoms);
    const conditionFreq = frequencyMap(allConditions);
    const foodFreq = frequencyMap(allFoods);
    const exerciseFreq = frequencyMap(allExercises);

    const topSymptoms = topEntries(symptomFreq, 10);
    const topConditions = topEntries(conditionFreq, 20);
    const topFoods = topEntries(foodFreq, 6).map(([f]) => f);
    const topExercises = topEntries(exerciseFreq, 5).map(([e]) => e);

    const totalSessions = threads.filter((t) => t.messages.length > 0).length;
    const uniqueSymptoms = Object.keys(symptomFreq).length;
    const uniqueConditions = Object.keys(conditionFreq).length;
    const daysActive = activityByDay.filter((d) => d > 0).length;

    const recentThreads = [...threads]
      .filter((t) => t.messages.length > 0)
      .sort((a, b) => b.updatedAt - a.updatedAt)
      .slice(0, 5)
      .map((t) => {
        const topCond =
          t.messages
            .filter((m) => m.role === "assistant" && m.data)
            .flatMap((m) => m.data!.suspected_conditions)
            .at(0) ?? null;
        return { ...t, topCond };
      });

    const latestRest = allRest.at(-1) ?? null;

    return {
      topSymptoms,
      topConditions,
      activityByDay,
      totalSessions,
      uniqueSymptoms,
      uniqueConditions,
      daysActive,
      topFoods,
      topExercises,
      latestRest,
      recentThreads,
    };
  }, [referenceTime, threads]);
}

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: number | string;
  color: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-[#ebebef] bg-white p-4 shadow-sm">
      <div
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${color}`}
      >
        <Icon className="h-5 w-5" strokeWidth={2} />
      </div>
      <div>
        <p className="text-2xl font-bold text-[#111]">{value}</p>
        <p className="text-xs text-[#8f8f95]">{label}</p>
      </div>
    </div>
  );
}

// ── Horizontal bar chart (pure SVG) ──────────────────────────────────────────
function SymptomBarChart({ data }: { data: [string, number][] }) {
  if (data.length === 0) {
    return (
      <EmptyState icon={Activity} text="No symptoms recorded yet. Start a chat to see your data." />
    );
  }

  const max = data[0]![1];
  const BAR_H = 24;
  const GAP = 10;
  const LABEL_W = 160;
  const BAR_AREA = 200;
  const TOTAL_W = LABEL_W + BAR_AREA + 40;
  const height = data.length * (BAR_H + GAP) - GAP + 4;

  return (
    <svg
      viewBox={`0 0 ${TOTAL_W} ${height}`}
      className="w-full overflow-visible"
      aria-label="Symptom frequency chart"
    >
      <defs>
        <linearGradient id="barGrad" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%" stopColor="#ae84ff" />
          <stop offset="100%" stopColor="#6f4ef2" />
        </linearGradient>
      </defs>
      {data.map(([symptom, count], i) => {
        const y = i * (BAR_H + GAP);
        const barW = Math.max(8, (count / max) * BAR_AREA);
        return (
          <g key={symptom}>
            <text
              x={LABEL_W - 8}
              y={y + BAR_H / 2 + 5}
              textAnchor="end"
              fontSize={12}
              fill="#3a3a42"
              className="font-sans"
            >
              {symptom.length > 22 ? symptom.slice(0, 21) + "…" : symptom}
            </text>
            <rect
              x={LABEL_W}
              y={y}
              width={barW}
              height={BAR_H}
              rx={6}
              fill="url(#barGrad)"
              opacity={0.85 - i * 0.06}
            />
            <text
              x={LABEL_W + barW + 6}
              y={y + BAR_H / 2 + 5}
              fontSize={11}
              fill="#8f8f95"
            >
              {count}×
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ── Activity sparkline ────────────────────────────────────────────────────────
function ActivitySparkline({
  data,
  referenceTime,
}: {
  data: number[];
  referenceTime: number;
}) {
  const max = Math.max(...data, 1);
  const W = 560;
  const H = 72;
  const PAD = 8;

  const pts = data.map((v, i) => {
    const x = PAD + (i / (data.length - 1)) * (W - PAD * 2);
    const y = H - PAD - ((v / max) * (H - PAD * 2 - 4));
    return [x, y] as [number, number];
  });

  const lineD = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p[0]},${p[1]}`).join(" ");
  const areaD =
    lineD +
    ` L${pts[pts.length - 1]![0]},${H - PAD} L${pts[0]![0]},${H - PAD} Z`;

  // Week labels (every 7 days)
  const weekLabels = [0, 7, 14, 21, 27].map((i) => {
    const d = new Date(referenceTime - (29 - i) * 86_400_000);
    return {
      x: PAD + (i / 29) * (W - PAD * 2),
      label: d.toLocaleDateString("en", { month: "short", day: "numeric" }),
    };
  });

  const hasData = data.some((d) => d > 0);

  return (
    <div>
      {!hasData ? (
        <EmptyState icon={TrendingUp} text="No activity in the last 30 days." />
      ) : (
        <svg
          viewBox={`0 0 ${W} ${H + 20}`}
          className="w-full"
          aria-label="Daily activity over the last 30 days"
        >
          <defs>
            <linearGradient id="areaGrad" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#ae84ff" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#ae84ff" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          {/* Grid lines */}
          {[0, 0.5, 1].map((frac) => (
            <line
              key={frac}
              x1={PAD}
              x2={W - PAD}
              y1={H - PAD - frac * (H - PAD * 2 - 4)}
              y2={H - PAD - frac * (H - PAD * 2 - 4)}
              stroke="#ebebef"
              strokeWidth={1}
            />
          ))}
          {/* Area fill */}
          <path d={areaD} fill="url(#areaGrad)" />
          {/* Line */}
          <path
            d={lineD}
            fill="none"
            stroke="#6f4ef2"
            strokeWidth={2.5}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Dots on non-zero days */}
          {pts.map((p, i) =>
            data[i]! > 0 ? (
              <circle
                key={i}
                cx={p[0]}
                cy={p[1]}
                r={3.5}
                fill="white"
                stroke="#6f4ef2"
                strokeWidth={2}
              />
            ) : null,
          )}
          {/* Week labels */}
          {weekLabels.map((wl) => (
            <text
              key={wl.label}
              x={wl.x}
              y={H + 18}
              textAnchor="middle"
              fontSize={10}
              fill="#a0a0aa"
            >
              {wl.label}
            </text>
          ))}
        </svg>
      )}
    </div>
  );
}

// ── Condition tag cloud ───────────────────────────────────────────────────────
function ConditionCloud({ data }: { data: [string, number][] }) {
  if (data.length === 0) {
    return (
      <EmptyState icon={Stethoscope} text="No conditions detected yet." />
    );
  }
  const max = data[0]![1];
  return (
    <div className="flex flex-wrap gap-2">
      {data.map(([cond, count]) => {
        const weight = count / max;
        const size = 11 + Math.round(weight * 10);
        const opacity = 0.55 + weight * 0.45;
        return (
          <span
            key={cond}
            style={{ fontSize: size, opacity }}
            className="rounded-full border border-[#d9c5ff] bg-[#f4eeff] px-3 py-1 font-medium text-[#5d42d4]"
          >
            {cond}
            {count > 1 && (
              <span className="ml-1 text-[10px] text-[#ae84ff]">×{count}</span>
            )}
          </span>
        );
      })}
    </div>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────
function EmptyState({
  icon: Icon,
  text,
}: {
  icon: React.ElementType;
  text: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-8 text-center">
      <Icon className="h-8 w-8 text-[#d9c5ff]" strokeWidth={1.5} />
      <p className="max-w-xs text-sm text-[#8f8f95]">{text}</p>
    </div>
  );
}

// ── Activity level pill ───────────────────────────────────────────────────────
const activityColor: Record<string, string> = {
  low: "bg-amber-100 text-amber-700 border-amber-200",
  medium: "bg-sky-100 text-sky-700 border-sky-200",
  high: "bg-emerald-100 text-emerald-700 border-emerald-200",
};

function Pill({ label, subtle }: { label: string; subtle?: boolean }) {
  return (
    <span
      className={`rounded-full border px-3 py-1 text-sm font-medium ${
        subtle
          ? "border-[#e4d9ff] bg-[#f4eeff] text-[#5d42d4]"
          : "border-[#ebebef] bg-[#fafafa] text-[#3a3a42]"
      }`}
    >
      {label}
    </span>
  );
}

type TimelineEntry = {
  id: string;
  title: string;
  updatedAt: number;
  symptoms: string[];
  conditions: string[];
  recommendationHighlights: string[];
  newSymptoms: string[];
  newConditions: string[];
  newRecommendations: string[];
  summary: string;
};

function buildTimelineEntries(threads: ChatThread[]): TimelineEntry[] {
  const sorted = [...threads]
    .filter((thread) => thread.messages.length > 0)
    .sort((a, b) => a.updatedAt - b.updatedAt);

  const entries: TimelineEntry[] = [];
  let previousSymptoms = new Set<string>();
  let previousConditions = new Set<string>();
  let previousRecommendations = new Set<string>();

  for (const thread of sorted) {
    const assistantResponses = thread.messages.filter(
      (message) => message.role === "assistant" && message.data,
    );
    const latest = assistantResponses.at(-1)?.data;
    if (!latest) continue;

    const symptoms = unique(latest.symptoms);
    const conditions = unique(latest.suspected_conditions);
    const recommendationHighlights = unique([
      ...latest.recommendations.foods_to_eat,
      ...latest.recommendations.exercises_recommended,
      latest.recommendations.rest_recommendation,
    ]);

    const symptomSet = new Set(symptoms);
    const conditionSet = new Set(conditions);
    const recommendationSet = new Set(recommendationHighlights);

    entries.push({
      id: thread.id,
      title: thread.title,
      updatedAt: thread.updatedAt,
      symptoms,
      conditions,
      recommendationHighlights,
      newSymptoms: symptoms.filter((item) => !previousSymptoms.has(item)),
      newConditions: conditions.filter((item) => !previousConditions.has(item)),
      newRecommendations: recommendationHighlights.filter(
        (item) => !previousRecommendations.has(item),
      ),
      summary: latest.answer,
    });

    previousSymptoms = symptomSet;
    previousConditions = conditionSet;
    previousRecommendations = recommendationSet;
  }

  return entries.reverse();
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Dashboard
// ─────────────────────────────────────────────────────────────────────────────

export default function Dashboard({ user, threads }: DashboardProps) {
  const [referenceTime] = useState(() => Date.now());
  const analytics = useAnalytics(threads, referenceTime);
  const timelineEntries = useMemo(() => buildTimelineEntries(threads), [threads]);

  const avatarLetter = (
    user?.name?.trim()?.[0] ??
    user?.email?.[0] ??
    "?"
  ).toUpperCase();

  const allergiesList = user?.allergies
    ?.split(",")
    .map((s) => s.trim())
    .filter(Boolean) ?? [];

  const conditionsList = user?.conditions
    ?.split(",")
    .map((s) => s.trim())
    .filter(Boolean) ?? [];

  return (
    <div className="h-full overflow-y-auto bg-gradient-to-b from-[#fdfcff] to-[#f6f5fa] pb-10">
      {/* ── Hero / Header ─────────────────────────────────────────────────── */}
      <div className="relative overflow-hidden border-b border-[#ececf1] bg-white px-6 py-10 md:px-10">
        <div
          aria-hidden
          className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full opacity-20 blur-3xl"
          style={{
            background: "radial-gradient(circle, #8a57ff 0%, #6f4ef2 60%, transparent 100%)",
          }}
        />
        <div className="relative flex flex-col gap-6 sm:flex-row sm:items-center sm:gap-8">
          {/* Modern Avatar */}
          <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#ae84ff] to-[#6f4ef2] text-3xl font-bold text-white shadow-[0_10px_30px_rgba(111,78,242,0.25)] border border-[#c5a6ff]/20">
            {avatarLetter}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight text-[#16151a]">
                {user?.name?.trim() || "Your"} — Health Dashboard
              </h1>
              <span className="rounded-full border border-[#e4d9ff] bg-[#f4eeff] px-3 py-1 text-xs font-semibold text-[#6f4ef2] shadow-sm">
                ✦ MedCortex
              </span>
            </div>
            <p className="mt-1 text-sm text-[#8c8c9a] font-medium">{user?.email}</p>
            <div className="mt-4 flex flex-wrap gap-2.5">
              {user?.age && (
                <span className="rounded-full border border-[#ececf2] bg-[#fafafa] px-3.5 py-1 text-xs font-medium text-[#4e4d58] shadow-sm">
                  Age {user.age}
                </span>
              )}
              {user?.gender && (
                <span className="rounded-full border border-[#ececf2] bg-[#fafafa] px-3.5 py-1 text-xs font-medium capitalize text-[#4e4d58] shadow-sm">
                  {user.gender}
                </span>
              )}
              {user?.activity_level && (
                <span
                  className={`rounded-full border px-3.5 py-1 text-xs font-semibold capitalize shadow-sm ${
                    activityColor[user.activity_level] ??
                    "border-[#ececf2] bg-[#fafafa] text-[#4e4d58]"
                  }`}
                >
                  {user.activity_level} activity
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="px-6 py-8 md:px-10 space-y-8">
        {/* ── Stats Strip ─────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <StatCard
            icon={MessageSquare}
            label="Chat Sessions"
            value={analytics.totalSessions}
            color="bg-[#f4eeff] text-[#6f4ef2] border border-[#e4d9ff]"
          />
          <StatCard
            icon={Activity}
            label="Unique Symptoms"
            value={analytics.uniqueSymptoms}
            color="bg-rose-50 text-rose-500 border border-rose-100"
          />
          <StatCard
            icon={Stethoscope}
            label="Conditions Flagged"
            value={analytics.uniqueConditions}
            color="bg-sky-50 text-sky-500 border border-sky-100"
          />
          <StatCard
            icon={Calendar}
            label="Days Active"
            value={analytics.daysActive}
            color="bg-emerald-50 text-emerald-500 border border-emerald-100"
          />
        </div>

        {/* ── Health Profile ──────────────────────────────────────────────── */}
        {(allergiesList.length > 0 || conditionsList.length > 0) && (
          <div className="rounded-3xl border border-[#ececf2] bg-white p-6 shadow-[0_4px_20px_rgba(0,0,0,0.02)] transition hover:shadow-[0_6px_24px_rgba(0,0,0,0.03)]">
            <h2 className="mb-5 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#6f4ef2]">
              <AlertCircle className="h-4 w-4" strokeWidth={2.5} />
              Health Profile
            </h2>
            <div className="grid gap-6 sm:grid-cols-2">
              {allergiesList.length > 0 && (
                <div className="rounded-2xl bg-[#faf9fe] p-4 border border-[#f0ebff]">
                  <p className="mb-2.5 text-xs font-bold uppercase tracking-wider text-[#8f8f95]">
                    Allergies
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {allergiesList.map((a) => (
                      <Pill key={a} label={a} subtle />
                    ))}
                  </div>
                </div>
              )}
              {conditionsList.length > 0 && (
                <div className="rounded-2xl bg-[#fafafa] p-4 border border-[#ebebef]">
                  <p className="mb-2.5 text-xs font-bold uppercase tracking-wider text-[#8f8f95]">
                    Known Conditions
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {conditionsList.map((c) => (
                      <Pill key={c} label={c} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Clinical Metrics ────────────────────────────────────────────── */}
        <div className="grid gap-6 md:grid-cols-5">
          {/* Top Reported Symptoms */}
          <div className="md:col-span-3 rounded-3xl border border-[#ececf2] bg-white p-6 shadow-[0_4px_20px_rgba(0,0,0,0.02)] transition hover:shadow-[0_6px_24px_rgba(0,0,0,0.03)]">
            <h2 className="mb-6 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#6f4ef2]">
              <Activity className="h-4 w-4" strokeWidth={2.5} />
              Top Reported Symptoms
            </h2>
            <SymptomBarChart data={analytics.topSymptoms} />
          </div>

          {/* Suspected Conditions */}
          <div className="md:col-span-2 rounded-3xl border border-[#ececf2] bg-white p-6 shadow-[0_4px_20px_rgba(0,0,0,0.02)] transition hover:shadow-[0_6px_24px_rgba(0,0,0,0.03)]">
            <h2 className="mb-5 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#6f4ef2]">
              <Stethoscope className="h-4 w-4" strokeWidth={2.5} />
              Suspected Conditions
            </h2>
            <ConditionCloud data={analytics.topConditions} />
          </div>
        </div>

        {/* ── Activity Sparkline ──────────────────────────────────────────── */}
        <div className="rounded-3xl border border-[#ececf2] bg-white p-6 shadow-[0_4px_20px_rgba(0,0,0,0.02)] transition hover:shadow-[0_6px_24px_rgba(0,0,0,0.03)]">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#6f4ef2]">
              <TrendingUp className="h-4 w-4" strokeWidth={2.5} />
              Activity — Last 30 Days
            </h2>
            <span className="text-xs font-medium text-[#8f8f95]">messages sent per day</span>
          </div>
          <ActivitySparkline data={analytics.activityByDay} referenceTime={referenceTime} />
        </div>

        {/* ── Patient Timeline ────────────────────────────────────────────── */}
        <div className="rounded-3xl border border-[#ececf2] bg-white p-6 shadow-[0_4px_20px_rgba(0,0,0,0.02)] transition hover:shadow-[0_6px_24px_rgba(0,0,0,0.03)]">
          <div className="mb-6">
            <h2 className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#6f4ef2]">
              <Calendar className="h-4 w-4" strokeWidth={2.5} />
              Patient Timeline
            </h2>
            <p className="mt-1 text-sm font-medium text-[#8f8f95]">
              Progression timeline tracking changes in symptoms, flagged conditions, and care recommendations.
            </p>
          </div>

          {timelineEntries.length === 0 ? (
            <EmptyState
              icon={Calendar}
              text="No clinical timeline yet. Start a few conversations and your progression will appear here."
            />
          ) : (
            <div className="space-y-6">
              {timelineEntries.slice(0, 6).map((entry, index) => (
                <div key={entry.id} className="flex gap-5">
                  {/* Timeline track node */}
                  <div className="flex w-6 flex-col items-center">
                    <span className="mt-1.5 h-3.5 w-3.5 rounded-full bg-[#ae84ff] border-2 border-white ring-2 ring-[#e9e2fb]" />
                    {index < timelineEntries.slice(0, 6).length - 1 ? (
                      <span className="mt-2.5 h-full w-px bg-gradient-to-b from-[#e9e2fb] to-transparent" />
                    ) : null}
                  </div>
                  {/* Timeline Entry Card - clinical summary removed for clean visual flow */}
                  <div className="min-w-0 flex-1 rounded-2xl border border-[#f0ebfa] bg-[#faf9fe]/30 p-5 transition hover:bg-[#faf9fe]/60">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0">
                        <p className="text-base font-bold text-[#1a1a24]">{entry.title}</p>
                        <p className="text-xs font-semibold text-[#8f8f95] mt-0.5">
                          {new Date(entry.updatedAt).toLocaleDateString("en", {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {entry.newSymptoms.length > 0 ? (
                          <span className="rounded-full border border-rose-200 bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-700 shadow-sm">
                            {entry.newSymptoms.length} new symptom{entry.newSymptoms.length !== 1 && "s"}
                          </span>
                        ) : null}
                        {entry.newConditions.length > 0 ? (
                          <span className="rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700 shadow-sm">
                            {entry.newConditions.length} new condition flag
                          </span>
                        ) : null}
                        {entry.newRecommendations.length > 0 ? (
                          <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 shadow-sm">
                            care plan updated
                          </span>
                        ) : null}
                      </div>
                    </div>

                    <div className="mt-5 grid gap-4 sm:grid-cols-3 border-t border-[#f0ebfa] pt-4">
                      <div>
                        <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-[#9c90b8]">
                          Symptoms
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {entry.symptoms.slice(0, 4).map((item) => (
                            <Pill key={item} label={item} />
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-[#9c90b8]">
                          Conditions
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {entry.conditions.slice(0, 4).map((item) => (
                            <Pill key={item} label={item} subtle />
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-[#9c90b8]">
                          Recommendation Highlights
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {entry.newRecommendations.slice(0, 3).map((item) => (
                            <span
                              key={item}
                              className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700"
                            >
                              {item}
                            </span>
                          ))}
                          {entry.newRecommendations.length === 0 ? (
                            <span className="text-xs font-medium text-[#b3abc7]">No major change noted.</span>
                          ) : null}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── Wellness Aggregation ────────────────────────────────────────── */}
        <div className="rounded-3xl border border-[#ececf2] bg-white p-6 shadow-[0_4px_20px_rgba(0,0,0,0.02)] transition hover:shadow-[0_6px_24px_rgba(0,0,0,0.03)]">
          <h2 className="mb-6 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#6f4ef2]">
            <Heart className="h-4 w-4" strokeWidth={2.5} />
            Wellness Recommendations (aggregated)
          </h2>
          <div className="grid gap-5 md:grid-cols-3">
            {/* Foods */}
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-5 transition hover:shadow-sm">
              <p className="mb-3.5 flex items-center gap-1.5 text-xs font-bold uppercase tracking-widest text-emerald-700">
                <Utensils className="h-4 w-4" strokeWidth={2} />
                Recommended Foods
              </p>
              {analytics.topFoods.length > 0 ? (
                <ul className="space-y-2">
                  {analytics.topFoods.map((f) => (
                    <li
                      key={f}
                      className="flex items-start gap-2 text-sm font-medium text-emerald-800"
                    >
                      <span className="mt-1 text-xs opacity-60">•</span>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-emerald-600 opacity-70">
                  No data yet — start chatting!
                </p>
              )}
            </div>

            {/* Exercise */}
            <div className="rounded-2xl border border-violet-200 bg-violet-50/50 p-5 transition hover:shadow-sm">
              <p className="mb-3.5 flex items-center gap-1.5 text-xs font-bold uppercase tracking-widest text-violet-700">
                <Zap className="h-4 w-4" strokeWidth={2} />
                Recommended Exercises
              </p>
              {analytics.topExercises.length > 0 ? (
                <ul className="space-y-2">
                  {analytics.topExercises.map((e) => (
                    <li
                      key={e}
                      className="flex items-start gap-2 text-sm font-medium text-violet-800"
                    >
                      <span className="mt-1 text-xs opacity-60">•</span>
                      <span>{e}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-violet-600 opacity-70">
                  No exercise recommendations yet.
                </p>
              )}
            </div>

            {/* Rest */}
            <div className="rounded-2xl border border-sky-200 bg-sky-50/50 p-5 transition hover:shadow-sm">
              <p className="mb-3.5 flex items-center gap-1.5 text-xs font-bold uppercase tracking-widest text-sky-700">
                <Activity className="h-4 w-4" strokeWidth={2} />
                Rest Recommendation
              </p>
              {analytics.latestRest ? (
                <p className="text-sm font-medium leading-relaxed text-sky-800">
                  {analytics.latestRest}
                </p>
              ) : (
                <p className="text-xs text-sky-600 opacity-70">
                  No rest recommendations yet.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* ── Recent Sessions ─────────────────────────────────────────────── */}
        <div className="rounded-3xl border border-[#ececf2] bg-white p-6 shadow-[0_4px_20px_rgba(0,0,0,0.02)] transition hover:shadow-[0_6px_24px_rgba(0,0,0,0.03)]">
          <h2 className="mb-5 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#6f4ef2]">
            <MessageSquare className="h-4 w-4" strokeWidth={2.5} />
            Recent Chat Sessions
          </h2>
          {analytics.recentThreads.length === 0 ? (
            <EmptyState
              icon={MessageSquare}
              text="No sessions yet. Start a conversation to track your health journey."
            />
          ) : (
            <div className="divide-y divide-[#ececf2]">
              {analytics.recentThreads.map((t) => {
                const date = new Date(t.updatedAt).toLocaleDateString("en", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                });
                return (
                  <div
                    key={t.id}
                    className="flex items-center justify-between gap-4 py-4 first:pt-0 last:pb-0"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold text-[#1a1a24]">
                        {t.title}
                      </p>
                      {t.topCond && (
                        <p className="mt-1 truncate text-xs font-medium text-[#8f8f95]">
                          {t.topCond}
                        </p>
                      )}
                    </div>
                    <div className="shrink-0 text-right">
                      <span className="text-xs font-semibold text-[#a8a8b0]">{date}</span>
                      <p className="text-[11px] font-semibold text-[#ae84ff] mt-0.5">
                        {t.messages.length} msg{t.messages.length !== 1 && "s"}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* ── Disclaimer ──────────────────────────────────────────────────── */}
        <p className="pb-4 text-center text-[11px] font-medium text-[#b4b4bc]">
          MedCortex Dashboard — for informational purposes only. Not a substitute for professional medical advice.
        </p>
      </div>
    </div>
  );
}

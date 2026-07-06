"use client";

import type { DoctorReferral } from "@/lib/extractDoctorReferral";
import type { Doctor } from "@/hooks/useDoctorRecommendations";

interface DoctorRecommendationCardProps {
  referral: DoctorReferral;
  doctors: Doctor[];
  loading: boolean;
  error: string | null;
}

const urgencyTone: Record<DoctorReferral["urgency"], string> = {
  routine: "bg-[#f3f4f6] text-[#4b5563]",
  soon: "bg-[#fef3c7] text-[#b45309]",
  urgent: "bg-[#fee2e2] text-[#ef4444]",
};

export default function DoctorRecommendationCard({
  referral,
  doctors,
  loading,
  error,
}: DoctorRecommendationCardProps) {
  if (loading) {
    return (
      <div className="rounded-2xl border border-[#e4e4ea] bg-white p-4 shadow-sm animate-pulse">
        <div className="h-4 w-40 rounded bg-[#ececf2]" />
        <div className="mt-3 h-3 w-56 rounded bg-[#ececf2]" />
      </div>
    );
  }

  if (error && doctors.length === 0) {
    return <p className="text-sm text-[#8f8f95]">{error}</p>;
  }

  if (doctors.length === 0) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-[#e4e4ea] bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-[#111]">
            Recommended: {referral.specialist}
          </p>
          {doctors[0]?.source === "places" ? (
            <p className="mt-1 text-xs text-[#8f8f95]">via Google Maps</p>
          ) : (
            <p className="mt-1 text-xs text-[#8f8f95]">
              Primary results shown first. Google Maps matches are included when available.
            </p>
          )}
        </div>
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-medium capitalize ${urgencyTone[referral.urgency]}`}
        >
          {referral.urgency}
        </span>
      </div>

      <div className="mt-4 space-y-3">
        {doctors.slice(0, 5).map((doctor, index) => (
          <div
            key={`${doctor.name}-${doctor.address}-${index}`}
            className="rounded-xl border border-[#ebebef] bg-[#fafafa] p-3"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-semibold text-[#111]">{doctor.name}</p>
                <p className="mt-1 text-xs text-[#6b6b76]">{doctor.address}</p>
                {doctor.rating !== null ? (
                  <p className="mt-1 text-xs text-[#6b6b76]">
                    ⭐ {doctor.rating.toFixed(1)} ({doctor.reviewCount})
                  </p>
                ) : null}
                {doctor.phone ? (
                  <p className="mt-1 text-xs text-[#6b6b76]">{doctor.phone}</p>
                ) : null}
              </div>
              <div className="text-right">
                <span className="rounded-full bg-[#f4eeff] px-2 py-1 text-[11px] font-medium text-[#6f4ef2]">
                  {doctor.source === "places" ? "Google Maps" : "Primary API"}
                </span>
                {doctor.mapsUrl ? (
                  <a
                    href={doctor.mapsUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-2 block text-xs font-medium text-[#6f4ef2] hover:underline"
                  >
                    View on Maps
                  </a>
                ) : null}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

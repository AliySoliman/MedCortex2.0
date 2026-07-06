"use client";

import type { ReactNode } from "react";
import { useState, useEffect, useCallback } from "react";
import { useDoctorRecommendations, type Doctor as RecommendedDoctor } from "@/hooks/useDoctorRecommendations";
import { useEgyptianDoctors } from "@/hooks/useEgyptianDoctors";
import { useEgyptianHospitals } from "@/hooks/useEgyptianHospitals";
import { useDrugs } from "@/hooks/useDrugs";
import { useNutrition } from "@/hooks/useNutrition";
import { useRehab } from "@/hooks/useRehab";
import { extractDoctorReferral, type DoctorReferral } from "@/lib/extractDoctorReferral";
import type { ChatResponse, Doctor as ApiDoctor, Source } from "@/services/chat";

type EgyptianDoctor = {
  name: string;
  specialty: string;
  address: string;
  latitude: number;
  longitude: number;
  phone: string;
  reviews: number;
  rating: number;
  url: string;
  distance: number | null;
  similarity: number;
  location_match: boolean;
  source: string;
};

interface ResponseCardProps {
  data: ChatResponse;
  referral?: DoctorReferral | null;
  coordinates?: { lat: number; lng: number } | null;
  userQuery?: string;
}

type Tab = "diagnosis" | "lifestyle" | "doctors" | "hospitals" | "drugs" | "nutrition" | "rehab";
type DoctorTab = "foreign" | "egyptian";

type DisplayDoctor = {
  name: string;
  specialty: string;
  address: string;
  phone: string | null;
  mapsUrl: string | null;
  rating: number | null;
  reviewCount: number;
  badgeLabel: string;
  badgeTone: string;
  sourceText: string;
  reference: string | null;
};

const EGYPT_LOCATION_REGEX =
  /\b(egypt|cairo|giza|alexandria|alexandrie|dakahlia|mansoura|tanta|zagazig|aswan|luxor|sohag|minya|assiut|faiyum|fayoum|ismailia|port said|suez|beni suef|qena|damietta|monufia|menoufia|beheira|kafr el-sheikh|kafr el sheikh|gharbia|sharqia)\b/i;

function buildMapsUrl(name: string, address: string) {
  const query = [name, address].filter(Boolean).join(", ");
  return query
    ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`
    : null;
}

function isEgyptDoctor(address: string, sourceText: string) {
  return /egypt/i.test(sourceText) || EGYPT_LOCATION_REGEX.test(address);
}

function mapApiDoctorToDisplay(doctor: ApiDoctor): DisplayDoctor {
  const egyptDoctor = isEgyptDoctor(doctor.address, doctor.source);

  return {
    name: doctor.name,
    specialty: doctor.specialty,
    address: doctor.address,
    phone: doctor.phone || null,
    mapsUrl: buildMapsUrl(doctor.name, doctor.address),
    rating: null,
    reviewCount: 0,
    badgeLabel: egyptDoctor ? "Egypt doctor/clinic" : "Foreign doctor",
    badgeTone: egyptDoctor
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : "border-sky-200 bg-sky-50 text-sky-700",
    sourceText: doctor.source,
    reference: doctor.npi ? `Ref: ${doctor.npi.slice(-6)}` : null,
  };
}

function mapRecommendedDoctorToDisplay(doctor: RecommendedDoctor): DisplayDoctor {
  const egyptDoctor = doctor.source === "places" || isEgyptDoctor(doctor.address, doctor.sourceLabel);

  return {
    name: doctor.name,
    specialty: doctor.specialty || "Doctor",
    address: doctor.address,
    phone: doctor.phone || null,
    mapsUrl: doctor.mapsUrl ?? buildMapsUrl(doctor.name, doctor.address),
    rating: doctor.rating,
    reviewCount: doctor.reviewCount,
    badgeLabel: egyptDoctor ? "Egypt doctor/clinic" : "Foreign doctor",
    badgeTone: egyptDoctor
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : "border-sky-200 bg-sky-50 text-sky-700",
    sourceText: doctor.source === "places" ? "Google Maps nearby search" : doctor.sourceLabel,
    reference: null,
  };
}

export default function ResponseCard({ data, referral = null, coordinates = null, userQuery = "" }: ResponseCardProps) {
  const determineInitialTab = (): Tab => {
    if (!userQuery) return "diagnosis";
    
    const query = userQuery.toLowerCase();
    
    // Rehab keywords
    if (/\b(rehab|rehabilitation|exercise|physical therapy|physio|stretch|workout|training)\b/i.test(query) || 
        /(تأهيل|تمارين|علاج طبيعي|ممارسة|رياضة)/.test(query)) {
      return "rehab";
    }
    
    // Nutrition keywords
    if (/\b(nutrition|diet|food|eat|meal|calories|fat|protein|carb|nutritionist)\b/i.test(query) || 
        /(تغذية|أكل|دايت|رجيم|وجبة|طعام|وجبات)/.test(query)) {
      return "nutrition";
    }
    
    // Drug keywords
    if (/\b(drug|medication|medicine|pill|tablet|capsule|side effect|dose|dosage|pharmacy|pharmacist)\b/i.test(query) || 
        /(دواء|أدوية|علاج|جرعة|صيدلية|حبوب|أقراص)/.test(query)) {
      return "drugs";
    }
    
    // Doctor keywords
    if (/\b(doctor|clinic|physician|specialist|hospital|pediatrician|cardiologist|dermatologist|dentist)\b/i.test(query) || 
        /(طبيب|دكتور|عيادة|مستشفى|أخصائي)/.test(query)) {
      return "doctors";
    }
    
    return "diagnosis";
  };

  const [activeTab, setActiveTab] = useState<Tab>(determineInitialTab);
  const [activeDoctorTab, setActiveDoctorTab] = useState<DoctorTab>("foreign");
  const { cleanText: displayAnswer } = extractDoctorReferral(data.answer);
  const doctorState = useDoctorRecommendations({
    referral,
    coordinates,
    primaryDoctors: data.doctors,
  });

  // ── Egyptian Doctors ──────────────────────────────────────────────────────
  const {
    doctors: egyptianDoctors,
    loading: egyptianLoading,
    error: egyptianError,
    searchEgyptianDoctors,
  } = useEgyptianDoctors();

  // ── Egyptian Hospitals ─────────────────────────────────────────────────────
  const {
    hospitals: egyptianHospitals,
    loading: hospitalsLoading,
    error: hospitalsError,
    searchEgyptianHospitals,
  } = useEgyptianHospitals();

  // ── Drugs / Nutrition / Rehab ─────────────────────────────────────────────
  const { answer: drugsAnswer, loading: drugsLoading, error: drugsError, getDrugInfo } = useDrugs(data.drugs_answer);
  const { answer: nutritionAnswer, loading: nutritionLoading, error: nutritionError, getNutritionInfo } = useNutrition(data.nutrition_answer);
  const { answer: rehabAnswer, loading: rehabLoading, error: rehabError, getRehabInfo } = useRehab(data.rehab_answer);

  const doctorsForDisplay: DisplayDoctor[] = referral
    ? doctorState.doctors.map(mapRecommendedDoctorToDisplay)
    : data.doctors.map(mapApiDoctorToDisplay);

  // Build a shared context string from the diagnosis for the AI branches
  const diagnosisContext = [
    data.answer,
    data.suspected_conditions.length > 0 ? `Conditions: ${data.suspected_conditions.join(", ")}` : "",
    data.symptoms.length > 0 ? `Symptoms: ${data.symptoms.join(", ")}` : "",
  ].filter(Boolean).join("\n");

  // ── Trigger branch fetches on tab activation ──────────────────────────────
  useEffect(() => {
    if (activeTab === "doctors" && activeDoctorTab === "egyptian") {
      const specialty = referral?.specialist || data.suspected_conditions[0] || "general";
      searchEgyptianDoctors(specialty, undefined, undefined, coordinates);
    }
  }, [activeTab, activeDoctorTab, referral, data.suspected_conditions, searchEgyptianDoctors, coordinates]);

  useEffect(() => {
    if (activeTab === "hospitals") {
      searchEgyptianHospitals(undefined, coordinates);
    }
  }, [activeTab, coordinates, searchEgyptianHospitals]);

  useEffect(() => {
    if (activeTab === "drugs" && !drugsAnswer && !drugsLoading) {
      const query = `Drug information for: ${data.suspected_conditions.join(", ") || "general health"}`;
      getDrugInfo(query, diagnosisContext);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === "nutrition" && !nutritionAnswer && !nutritionLoading) {
      const query = `Nutrition plan for: ${data.suspected_conditions.join(", ") || "general health"}`;
      getNutritionInfo(query, diagnosisContext);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === "rehab" && !rehabAnswer && !rehabLoading) {
      const query = `Rehabilitation exercises for: ${data.suspected_conditions.join(", ") || "general health"}`;
      getRehabInfo(query, diagnosisContext);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  // Stable tab switch helpers that also trigger fetch for first visit
  const switchToDrugs = useCallback(() => {
    setActiveTab("drugs");
    if (!drugsAnswer && !drugsLoading) {
      const query = `Drug information for: ${data.suspected_conditions.join(", ") || "general health"}`;
      getDrugInfo(query, diagnosisContext);
    }
  }, [drugsAnswer, drugsLoading, getDrugInfo, diagnosisContext, data.suspected_conditions]);

  const switchToNutrition = useCallback(() => {
    setActiveTab("nutrition");
    if (!nutritionAnswer && !nutritionLoading) {
      const query = `Nutrition plan for: ${data.suspected_conditions.join(", ") || "general health"}`;
      getNutritionInfo(query, diagnosisContext);
    }
  }, [nutritionAnswer, nutritionLoading, getNutritionInfo, diagnosisContext, data.suspected_conditions]);

  const switchToRehab = useCallback(() => {
    setActiveTab("rehab");
    if (!rehabAnswer && !rehabLoading) {
      const query = `Rehabilitation exercises for: ${data.suspected_conditions.join(", ") || "general health"}`;
      getRehabInfo(query, diagnosisContext);
    }
  }, [rehabAnswer, rehabLoading, getRehabInfo, diagnosisContext, data.suspected_conditions]);

  const egyptianDoctorsForDisplay: DisplayDoctor[] = egyptianDoctors.map((doc) => ({
    name: doc.name,
    specialty: doc.specialty,
    address: doc.address,
    phone: doc.phone || null,
    mapsUrl: doc.url || null,
    rating: doc.rating,
    reviewCount: doc.reviews,
    badgeLabel: "Egypt doctor/clinic",
    badgeTone: "border-emerald-200 bg-emerald-50 text-emerald-700",
    sourceText: "Egyptian database",
    reference: null,
  }));

  const tabs: { key: Tab; label: string; emoji: string }[] = [
    { key: "diagnosis", label: "Diagnosis", emoji: "🩺" },
    { key: "lifestyle", label: "Lifestyle", emoji: "🥗" },
    { key: "doctors", label: "Doctors", emoji: "👨‍⚕️" },
    { key: "hospitals", label: "Hospitals", emoji: "🏥" },
    { key: "drugs", label: "Drugs", emoji: "💊" },
    { key: "nutrition", label: "Nutrition", emoji: "🥗" },
    { key: "rehab", label: "Rehab", emoji: "🏃" },
  ];

  return (
    <div className="w-full overflow-hidden rounded-2xl border border-[#ebebef] bg-white shadow-sm">
      <div className="flex border-b border-[#ebebef] bg-[#fafafa]">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 py-3 text-sm font-semibold transition ${
              activeTab === tab.key
                ? "border-b-2 border-[#6f4ef2] bg-white text-[#6f4ef2]"
                : "text-[#6b6b76] hover:text-[#111]"
            }`}
          >
            {tab.emoji} {tab.label}
          </button>
        ))}
      </div>

      <div className="p-5">
        {activeTab === "diagnosis" && (
          <div className="space-y-4">
            {displayAnswer && (
              <div>
                <p className="mb-2 text-xs font-bold uppercase tracking-widest text-[#7b7b88]">
                  Clinical response
                </p>
                <ClinicalAnswer text={displayAnswer} />
              </div>
            )}

            {data.suspected_conditions.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-bold uppercase tracking-widest text-[#6f4ef2]">
                  Suspected conditions
                </p>
                <div className="flex flex-wrap gap-2">
                  {data.suspected_conditions.map((c, i) => (
                    <span
                      key={i}
                      className="rounded-full border border-[#e4d9ff] bg-[#f4eeff] px-3 py-1 text-sm font-medium text-[#5d42d4]"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {data.symptoms.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-bold uppercase tracking-widest text-[#7b7b88]">
                  Detected symptoms
                </p>
                <div className="flex flex-wrap gap-2">
                  {data.symptoms.map((s, i) => (
                    <span
                      key={i}
                      className="rounded-full border border-[#ebebef] bg-[#fafafa] px-3 py-1 text-sm text-[#3a3a42]"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <p className="border-t border-[#ebebef] pt-3 text-xs text-[#8f8f95]">
              For educational purposes only. Not a substitute for professional medical advice.
            </p>
          </div>
        )}

        {activeTab === "lifestyle" && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <RecommendationSection title="Foods to Eat" emoji="✅" tone="green" items={data.recommendations.foods_to_eat} />
            <RecommendationSection title="Foods to Avoid" emoji="❌" tone="rose" items={data.recommendations.foods_to_avoid} />
            <RecommendationSection title="Drinks to Have" emoji="💧" tone="sky" items={data.recommendations.drinks_to_have} />
            <RecommendationSection title="Drinks to Avoid" emoji="🚫" tone="amber" items={data.recommendations.drinks_to_avoid} />
            <RecommendationSection title="Exercise — Do" emoji="🏃" tone="violet" items={data.recommendations.exercises_recommended} />
            <RecommendationSection title="Exercise — Avoid" emoji="🛑" tone="rose" items={data.recommendations.exercises_to_avoid} />
            {data.recommendations.rest_recommendation && (
              <div className="rounded-xl border border-[#ebebef] bg-[#fafafa] p-4 md:col-span-2">
                <p className="mb-1 text-xs font-bold uppercase tracking-widest text-[#6f4ef2]">
                  Rest recommendation
                </p>
                <p className="text-sm text-[#1a1a1a]">{data.recommendations.rest_recommendation}</p>
              </div>
            )}
          </div>
        )}

        {activeTab === "doctors" && (
          <div className="space-y-3">
            <div className="flex border-b border-[#ebebef] mb-3">
              <button
                type="button"
                onClick={() => setActiveDoctorTab("foreign")}
                className={`flex-1 py-2 text-sm font-semibold transition ${
                  activeDoctorTab === "foreign"
                    ? "border-b-2 border-[#6f4ef2] text-[#6f4ef2]"
                    : "text-[#6b6b76] hover:text-[#111]"
                }`}
              >
                🌍 Foreign Doctors
              </button>
              <button
                type="button"
                onClick={() => setActiveDoctorTab("egyptian")}
                className={`flex-1 py-2 text-sm font-semibold transition ${
                  activeDoctorTab === "egyptian"
                    ? "border-b-2 border-[#6f4ef2] text-[#6f4ef2]"
                    : "text-[#6b6b76] hover:text-[#111]"
                }`}
              >
                🇪🇬 Egyptian Doctors
              </button>
            </div>
            
            {activeDoctorTab === "foreign" && (
              <div className="space-y-3">
                {referral && doctorState.loading ? (
                  <div className="space-y-3">
                    <div className="animate-pulse rounded-xl border border-[#ebebef] bg-[#fafafa] p-4">
                      <div className="h-4 w-40 rounded bg-[#ececf2]" />
                      <div className="mt-3 h-3 w-64 rounded bg-[#ececf2]" />
                    </div>
                  </div>
                ) : doctorsForDisplay.filter(doc => !doc.badgeLabel.includes("Egypt")).length === 0 ? (
                  <p className="py-6 text-center text-sm text-[#8f8f95]">
                    {referral && doctorState.error
                      ? doctorState.error
                      : "No foreign doctor results available for the detected conditions."}
                  </p>
                ) : (
                  <>
                    {referral && coordinates && (
                      <p className="text-xs text-[#8f8f95]">
                        Nearby Google Maps results are shown first using your current location, with additional registry matches listed after them when available.
                      </p>
                    )}
                    {doctorsForDisplay.filter(doc => !doc.badgeLabel.includes("Egypt")).map((doc, i) => <DoctorCard key={i} doctor={doc} />)}
                  </>
                )}
              </div>
            )}
            
            {activeDoctorTab === "egyptian" && (
              <div className="space-y-3">
                <p className="text-xs text-[#8f8f95]">
                  Egyptian doctors are searched based on your location and medical specialty using our local database.
                </p>
                {egyptianLoading ? (
                  <div className="space-y-3">
                    <div className="animate-pulse rounded-xl border border-[#ebebef] bg-[#fafafa] p-4">
                      <div className="h-4 w-40 rounded bg-[#ececf2]" />
                      <div className="mt-3 h-3 w-64 rounded bg-[#ececf2]" />
                    </div>
                  </div>
                ) : egyptianError ? (
                  <p className="py-6 text-center text-sm text-red-600">
                    {egyptianError}
                  </p>
                ) : egyptianDoctorsForDisplay.length === 0 ? (
                  <p className="py-6 text-center text-sm text-[#8f8f95]">
                    No Egyptian doctor results available. Try the foreign doctors tab or provide more specific location information.
                  </p>
                ) : (
                  egyptianDoctorsForDisplay.map((doc, i) => <DoctorCard key={i} doctor={doc} />)
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === "hospitals" && (
          <div className="space-y-3">
            <p className="text-xs text-[#8f8f95]">
              Egyptian hospitals are searched based on your location using our local database.
            </p>
            {hospitalsLoading ? (
              <div className="space-y-3">
                <div className="animate-pulse rounded-xl border border-[#ebebef] bg-[#fafafa] p-4">
                  <div className="h-4 w-40 rounded bg-[#ececf2]" />
                  <div className="mt-3 h-3 w-64 rounded bg-[#ececf2]" />
                </div>
              </div>
            ) : hospitalsError ? (
              <p className="py-6 text-center text-sm text-red-600">
                {hospitalsError}
              </p>
            ) : egyptianHospitals.length === 0 ? (
              <p className="py-6 text-center text-sm text-[#8f8f95]">
                No Egyptian hospital results available. Try providing more specific location information.
              </p>
            ) : (
              <div className="space-y-3">
                {egyptianHospitals.slice(0, 10).map((hospital, i) => (
                  <div
                    key={`${hospital.name}-${hospital.address}-${i}`}
                    className="rounded-xl border border-[#ebebef] bg-[#fafafa] p-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold text-[#111]">{hospital.name}</p>
                        <p className="mt-1 text-xs text-[#6b6b76]">{hospital.address}</p>
                        <p className="mt-1 text-xs text-[#6b6b76]">
                          <span className="font-medium">Governorate:</span> {hospital.governorate}
                        </p>
                        {hospital.distance !== null ? (
                          <p className="mt-1 text-xs text-[#6b6b76]">
                            📍 {hospital.distance.toFixed(2)} km away
                          </p>
                        ) : null}
                      </div>
                      <div className="text-right">
                        <span className="rounded-full bg-[#f4eeff] px-2 py-1 text-[11px] font-medium text-[#6f4ef2]">
                          Egyptian Hospital
                        </span>
                        {hospital.latitude && hospital.longitude ? (
                          <a
                            href={`https://www.google.com/maps/search/?api=1&query=${hospital.latitude},${hospital.longitude}`}
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
            )}
          </div>
        )}

        {activeTab === "drugs" && (
          <div className="space-y-3">
            <p className="text-sm text-[#6b6b76]">
              💊 Drug information based on your diagnosis and detected conditions.
            </p>
            <div className="rounded-xl border border-[#ebebef] bg-[#fafafa] p-4">
              <p className="text-xs text-[#8f8f95] mb-2">
                <strong>Relevant conditions:</strong> {data.suspected_conditions.join(", ") || "General health"}
              </p>
              {drugsLoading ? (
                <div className="space-y-2 animate-pulse mt-3">
                  <div className="h-3 w-full rounded bg-[#ececf2]" />
                  <div className="h-3 w-5/6 rounded bg-[#ececf2]" />
                  <div className="h-3 w-4/6 rounded bg-[#ececf2]" />
                  <div className="h-3 w-full rounded bg-[#ececf2]" />
                  <div className="h-3 w-3/4 rounded bg-[#ececf2]" />
                </div>
              ) : drugsError ? (
                <p className="mt-3 text-sm text-red-600">{drugsError}</p>
              ) : drugsAnswer ? (
                <div className="mt-3">
                  <ClinicalAnswer text={drugsAnswer} />
                </div>
              ) : null}
            </div>
          </div>
        )}

        {activeTab === "nutrition" && (
          <div className="space-y-3">
            <p className="text-sm text-[#6b6b76]">
              🥗 Personalized nutrition plan based on your diagnosis.
            </p>
            <div className="rounded-xl border border-[#ebebef] bg-[#fafafa] p-4">
              <p className="text-xs text-[#8f8f95] mb-2">
                <strong>Relevant conditions:</strong> {data.suspected_conditions.join(", ") || "General health"}
              </p>
              {nutritionLoading ? (
                <div className="space-y-2 animate-pulse mt-3">
                  <div className="h-3 w-full rounded bg-[#ececf2]" />
                  <div className="h-3 w-5/6 rounded bg-[#ececf2]" />
                  <div className="h-3 w-4/6 rounded bg-[#ececf2]" />
                  <div className="h-3 w-full rounded bg-[#ececf2]" />
                  <div className="h-3 w-3/4 rounded bg-[#ececf2]" />
                </div>
              ) : nutritionError ? (
                <p className="mt-3 text-sm text-red-600">{nutritionError}</p>
              ) : nutritionAnswer ? (
                <div className="mt-3">
                  <ClinicalAnswer text={nutritionAnswer} />
                </div>
              ) : null}
            </div>
          </div>
        )}

        {activeTab === "rehab" && (
          <div className="space-y-3">
            <p className="text-sm text-[#6b6b76]">
              🏃 Rehabilitation exercises and recovery plan based on your condition.
            </p>
            <div className="rounded-xl border border-[#ebebef] bg-[#fafafa] p-4">
              <p className="text-xs text-[#8f8f95] mb-2">
                <strong>Relevant conditions:</strong> {data.suspected_conditions.join(", ") || "General health"}
              </p>
              {rehabLoading ? (
                <div className="space-y-2 animate-pulse mt-3">
                  <div className="h-3 w-full rounded bg-[#ececf2]" />
                  <div className="h-3 w-5/6 rounded bg-[#ececf2]" />
                  <div className="h-3 w-4/6 rounded bg-[#ececf2]" />
                  <div className="h-3 w-full rounded bg-[#ececf2]" />
                  <div className="h-3 w-3/4 rounded bg-[#ececf2]" />
                </div>
              ) : rehabError ? (
                <p className="mt-3 text-sm text-red-600">{rehabError}</p>
              ) : rehabAnswer ? (
                <div className="mt-3">
                  <ClinicalAnswer text={rehabAnswer} />
                </div>
              ) : null}
            </div>
          </div>
        )}
      </div>
      
      {/* How else can I help section */}
      <div className="border-t border-[#ebebef] bg-[#fafafa] p-4">
        <p className="text-sm font-semibold text-[#111] mb-3">How else can I help you?</p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={switchToDrugs}
            className="rounded-full border border-[#e4d9ff] bg-[#f4eeff] px-3 py-1.5 text-sm font-medium text-[#5d42d4] hover:bg-[#e4d9ff] transition"
          >
            💊 Drug Information
          </button>
          <button
            type="button"
            onClick={switchToNutrition}
            className="rounded-full border border-[#d1fae5] bg-[#ecfdf5] px-3 py-1.5 text-sm font-medium text-[#059669] hover:bg-[#d1fae5] transition"
          >
            🥗 Nutrition Plan
          </button>
          <button
            type="button"
            onClick={switchToRehab}
            className="rounded-full border border-[#ede9fe] bg-[#f5f3ff] px-3 py-1.5 text-sm font-medium text-[#7c3aed] hover:bg-[#ede9fe] transition"
          >
            🏃 Rehab Exercises
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("doctors")}
            className="rounded-full border border-[#dbeafe] bg-[#eff6ff] px-3 py-1.5 text-sm font-medium text-[#2563eb] hover:bg-[#dbeafe] transition"
          >
            👨‍⚕️ Find Doctors
          </button>
        </div>
      </div>
    </div>
  );
}

function ClinicalAnswer({ text }: { text: string }) {
  const blocks = text
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean)
    .filter((block) => !block.includes("[DOCTOR_REFERRAL]"));

  return (
    <div className="space-y-4 text-sm leading-relaxed text-[#1a1a1a]">
      {blocks.map((block, blockIndex) => {
        if (/^-{3,}$/.test(block)) {
          return <hr key={blockIndex} className="border-[#ebebef]" />;
        }

        const lines = block.split("\n").map((line) => line.trim()).filter(Boolean);
        const table = parseMarkdownTable(lines);
        if (table) {
          return <MarkdownTable key={blockIndex} table={table} />;
        }

        const bulletLines = lines.filter((line) => /^[-*]\s+/.test(line));
        const headingLine = lines[0] ?? "";
        const markdownHeading = headingLine.match(/^(#{1,3})\s+(.+)$/);
        const headingLike =
          lines.length === 1 &&
          /^(?:[A-Z][A-Z\s&/:-]{4,}|[^.?!:]{2,60}:)$/.test(headingLine);

        if (bulletLines.length > 0 && bulletLines.length === lines.length) {
          return (
            <ul key={blockIndex} className="space-y-2">
              {bulletLines.map((line, lineIndex) => (
                <li key={lineIndex} className="flex gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#6f4ef2]" />
                  <span>{renderInlineMarkdown(line.replace(/^[-*]\s+/, ""))}</span>
                </li>
              ))}
            </ul>
          );
        }

        if (markdownHeading) {
          const level = markdownHeading[1].length;
          const headingText = markdownHeading[2];
          const headingClass =
            level === 1
              ? "text-[22px] font-semibold tracking-tight text-[#111]"
              : level === 2
                ? "text-[15px] font-semibold tracking-tight text-[#111]"
                : "text-xs font-bold uppercase tracking-widest text-[#7b7b88]";
          return (
            <div key={blockIndex} className="space-y-2">
              <p className={headingClass}>{renderInlineMarkdown(headingText)}</p>
              {lines.slice(1).map((line, lineIndex) => (
                <p key={lineIndex}>{renderInlineMarkdown(line)}</p>
              ))}
            </div>
          );
        }

        if (headingLike && lines[0]) {
          return (
            <p key={blockIndex} className="text-xs font-bold uppercase tracking-widest text-[#7b7b88]">
              {renderInlineMarkdown(lines[0])}
            </p>
          );
        }

        return (
          <div key={blockIndex} className="space-y-2">
            {lines.map((line, lineIndex) => (
              <p key={lineIndex}>{renderInlineMarkdown(line)}</p>
            ))}
          </div>
        );
      })}
    </div>
  );
}

function renderInlineMarkdown(text: string) {
  const nodes: ReactNode[] = [];
  const boldPattern = /\*\*(.+?)\*\*/g;
  let cursor = 0;
  let match: RegExpExecArray | null;

  while ((match = boldPattern.exec(text)) !== null) {
    const [fullMatch, boldText] = match;
    if (match.index > cursor) {
      nodes.push(text.slice(cursor, match.index));
    }
    nodes.push(<strong key={`${match.index}-${fullMatch}`}>{boldText}</strong>);
    cursor = match.index + fullMatch.length;
  }

  if (cursor < text.length) {
    nodes.push(text.slice(cursor));
  }

  return nodes.length > 0 ? nodes : text;
}

type MarkdownTableData = {
  headers: string[];
  rows: string[][];
};

function parseMarkdownTable(lines: string[]): MarkdownTableData | null {
  if (lines.length < 2) return null;
  if (!lines.every((line) => line.startsWith("|") && line.endsWith("|"))) return null;

  const normalized = lines.map((line) =>
    line
      .slice(1, -1)
      .split("|")
      .map((cell) => cell.trim())
  );

  if (normalized.length < 2) return null;
  const [headers, separator, ...rows] = normalized;
  if (!separator.every((cell) => /^:?-{3,}:?$/.test(cell))) return null;
  if (!headers.length || !rows.length) return null;

  return { headers, rows };
}

function MarkdownTable({ table }: { table: MarkdownTableData }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-[#ebebef] bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse text-sm">
          <thead className="bg-[#fafafa]">
            <tr>
              {table.headers.map((header, i) => (
                <th
                  key={i}
                  className="border-b border-[#ebebef] px-4 py-3 text-left text-xs font-bold uppercase tracking-widest text-[#7b7b88]"
                >
                  {renderInlineMarkdown(header)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row, rowIndex) => (
              <tr key={rowIndex} className="odd:bg-white even:bg-[#fcfcfd]">
                {table.headers.map((_, colIndex) => (
                  <td key={colIndex} className="border-b border-[#f1f1f4] px-4 py-3 align-top text-[#1a1a1a]">
                    {renderInlineMarkdown(row[colIndex] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

type Tone = "green" | "rose" | "sky" | "amber" | "violet";

const toneClass: Record<Tone, string> = {
  green:  "border-emerald-200 bg-emerald-50 text-emerald-900",
  rose:   "border-rose-200 bg-rose-50 text-rose-900",
  sky:    "border-sky-200 bg-sky-50 text-sky-900",
  amber:  "border-amber-200 bg-amber-50 text-amber-900",
  violet: "border-violet-200 bg-violet-50 text-violet-900",
};

function RecommendationSection({
  title,
  emoji,
  tone,
  items,
}: {
  title: string;
  emoji: string;
  tone: Tone;
  items: string[];
}) {
  if (!items?.length) return null;
  return (
    <div className={`rounded-xl border p-4 ${toneClass[tone]}`}>
      <p className="mb-2 text-xs font-bold uppercase tracking-widest opacity-80">
        {emoji} {title}
      </p>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm">
            <span className="mt-1 text-xs opacity-60">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function DoctorCard({ doctor }: { doctor: DisplayDoctor }) {
  return (
    <div className="rounded-xl border border-[#ebebef] bg-[#fafafa] p-4 transition hover:border-[#d9c5ff]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-[#111]">{doctor.name}</p>
          <p className="text-sm text-[#6f4ef2]">{doctor.specialty}</p>
          <p className="mt-1 text-xs text-[#6b6b76]">{doctor.address}</p>
          {doctor.phone ? <p className="text-xs text-[#6b6b76]">{doctor.phone}</p> : null}
          {doctor.rating !== null ? (
            <p className="mt-1 text-xs text-[#6b6b76]">
              ⭐ {doctor.rating.toFixed(1)} ({doctor.reviewCount})
            </p>
          ) : null}
          {doctor.mapsUrl ? (
            <a
              href={doctor.mapsUrl}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-block text-xs font-medium text-[#6f4ef2] hover:underline"
            >
              View on Maps
            </a>
          ) : null}
        </div>
        <div className="shrink-0 text-right">
          <span className={`rounded-full border px-2 py-1 text-xs font-medium ${doctor.badgeTone}`}>
            {doctor.badgeLabel}
          </span>
          <p className="mt-1 text-xs text-[#8f8f95]">{doctor.sourceText}</p>
          {doctor.reference ? (
            <p className="mt-1 text-[11px] text-[#b09adf]">{doctor.reference}</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function SourceBadge({ source }: { source: Source }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-[#ebebef] bg-[#fafafa] p-3">
      <span className="text-lg">📘</span>
      <div>
        <p className="text-sm font-medium text-[#111]">{source.book}</p>
        {source.section && <p className="text-xs text-[#6b6b76]">{source.section}</p>}
      </div>
    </div>
  );
}

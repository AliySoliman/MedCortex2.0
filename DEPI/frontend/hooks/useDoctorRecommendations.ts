"use client";

import { useEffect, useState } from "react";

import type { Doctor as PrimaryDoctor } from "@/services/chat";
import type { DoctorReferral } from "@/lib/extractDoctorReferral";

export type Doctor = {
  name: string;
  address: string;
  rating: number | null;
  reviewCount: number;
  phone: string | null;
  mapsUrl: string | null;
  source: "primary" | "places";
  sourceLabel: string;
  specialty?: string;
  isOpen?: boolean | null;
};

type Coordinates = {
  lat: number;
  lng: number;
};

type UseDoctorRecommendationsOptions = {
  referral: DoctorReferral | null;
  coordinates: Coordinates | null;
  primaryDoctors?: PrimaryDoctor[];
};

type PlacesResponse = {
  doctors?: Array<{
    name: string;
    address: string;
    rating: number | null;
    reviewCount: number;
    phone: string | null;
    mapsUrl: string | null;
    source: "google_places";
    isOpen?: boolean | null;
  }>;
};

function mapPrimaryDoctors(doctors: PrimaryDoctor[] = []): Doctor[] {
  return doctors.map((doctor) => ({
    name: doctor.name,
    address: doctor.address || "Address not available",
    rating: null,
    reviewCount: 0,
    phone: doctor.phone || null,
    mapsUrl: null,
    source: "primary",
    sourceLabel: doctor.source || "Primary recommendation API",
    specialty: doctor.specialty,
    isOpen: null,
  }));
}

function dedupeDoctors(doctors: Doctor[]): Doctor[] {
  const seen = new Set<string>();
  return doctors.filter((doctor) => {
    const key = `${doctor.name.toLowerCase()}|${doctor.address.toLowerCase()}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

export function resolveDoctorRecommendationState(primary: Doctor[], places: Doctor[]) {
  if (primary.length > 0 || places.length > 0) {
    const ordered = places.length > 0 ? [...places, ...primary] : [...primary, ...places];
    return {
      doctors: dedupeDoctors(ordered).slice(0, 10),
      source: (places.length > 0 ? "places" : "primary") as "primary" | "places",
      error: null,
    };
  }

  return {
    doctors: [] as Doctor[],
    source: null,
    error: "No doctors found nearby. Try searching manually.",
  };
}

export function useDoctorRecommendations({
  referral,
  coordinates,
  primaryDoctors = [],
}: UseDoctorRecommendationsOptions) {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [source, setSource] = useState<"primary" | "places" | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!referral) {
      return;
    }

    let cancelled = false;

    const loadDoctors = async () => {
      setLoading(true);
      setDoctors([]);
      setSource(null);
      setError(null);

      const primaryPromise = Promise.resolve(mapPrimaryDoctors(primaryDoctors));
      const placesPromise = coordinates
        ? fetch("/api/doctors/places", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              specialist: referral.specialist,
              lat: coordinates.lat,
              lng: coordinates.lng,
              reason: referral.reason,
            }),
          })
            .then(async (response) => {
              const payload = (await response.json()) as PlacesResponse & { error?: string };
              if (!response.ok) {
                throw new Error(payload.error || "Places search failed");
              }
              return (payload.doctors ?? []).map((doctor) => ({
                ...doctor,
                source: "places" as const,
                sourceLabel: "Google Maps",
                specialty: referral.specialist,
              }));
            })
        : Promise.resolve([] as Doctor[]);

      const [primaryResult, placesResult] = await Promise.allSettled([primaryPromise, placesPromise]);

      if (cancelled) {
        return;
      }

      const primary = primaryResult.status === "fulfilled" ? primaryResult.value : [];
      const places = placesResult.status === "fulfilled" ? placesResult.value : [];
      const resolved = resolveDoctorRecommendationState(primary, places);
      setDoctors(resolved.doctors);
      setSource(resolved.source);
      setError(resolved.error);

      setLoading(false);
    };

    void loadDoctors();

    return () => {
      cancelled = true;
    };
  }, [coordinates, primaryDoctors, referral]);

  if (!referral) {
    return { doctors: [], source: null, loading: false, error: null };
  }

  return { doctors, source, loading, error };
}

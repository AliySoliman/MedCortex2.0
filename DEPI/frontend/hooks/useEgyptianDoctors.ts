// frontend/hooks/useEgyptianDoctors.ts
// ─────────────────────────────────────────────────────────────────────────────
// Hook for Egyptian doctors search
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useCallback } from "react";

interface EgyptianDoctor {
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
}

interface EgyptianDoctorsResponse {
  doctors: EgyptianDoctor[];
  count: number;
  source: string;
}

interface EgyptianDoctorsState {
  doctors: EgyptianDoctor[];
  loading: boolean;
  error: string | null;
}

export function useEgyptianDoctors() {
  const [state, setState] = useState<EgyptianDoctorsState>({
    doctors: [],
    loading: false,
    error: null,
  });

  const searchEgyptianDoctors = useCallback(async (
    query: string,
    location?: string,
    specialty?: string
  ) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const response = await fetch("/api/egyptian-doctors", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          location,
          specialty,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: EgyptianDoctorsResponse = await response.json();
      setState({
        doctors: data.doctors,
        loading: false,
        error: null,
      });
    } catch (error) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : "Failed to search Egyptian doctors",
      }));
    }
  }, []);

  return {
    ...state,
    searchEgyptianDoctors,
  };
}

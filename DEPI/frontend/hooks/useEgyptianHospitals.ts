// frontend/hooks/useEgyptianHospitals.ts
// ─────────────────────────────────────────────────────────────────────────────
// Hook for Egyptian hospitals search
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useCallback } from "react";

interface EgyptianHospital {
  name: string;
  governorate: string;
  address: string;
  latitude: number;
  longitude: number;
  distance: number | null;
  source: string;
}

interface EgyptianHospitalsResponse {
  hospitals: EgyptianHospital[];
  count: number;
  source: string;
}

interface EgyptianHospitalsState {
  hospitals: EgyptianHospital[];
  loading: boolean;
  error: string | null;
}

export function useEgyptianHospitals() {
  const [state, setState] = useState<EgyptianHospitalsState>({
    hospitals: [],
    loading: false,
    error: null,
  });

  const searchEgyptianHospitals = useCallback(async (
    query?: string,
    userCoordinates?: { lat: number; lng: number },
    governorate?: string
  ) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const response = await fetch("/api/egyptian-hospitals", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          userCoordinates,
          governorate,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: EgyptianHospitalsResponse = await response.json();
      setState({
        hospitals: data.hospitals,
        loading: false,
        error: null,
      });
    } catch (error) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : "Failed to search Egyptian hospitals",
      }));
    }
  }, []);

  return {
    ...state,
    searchEgyptianHospitals,
  };
}

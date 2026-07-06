// frontend/hooks/useNutrition.ts
// ─────────────────────────────────────────────────────────────────────────────
// Hook for nutrition plan information
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useCallback } from "react";

interface NutritionResponse {
  answer: string;
  language: string;
  source: string;
}

interface NutritionState {
  answer: string | null;
  loading: boolean;
  error: string | null;
}

export function useNutrition(initialAnswer: string | null = null) {
  const [state, setState] = useState<NutritionState>({
    answer: initialAnswer,
    loading: false,
    error: null,
  });

  const getNutritionInfo = useCallback(async (query: string, context: string, language: string = "en") => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const response = await fetch("/api/nutrition", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          context,
          language,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: NutritionResponse = await response.json();
      setState({
        answer: data.answer,
        loading: false,
        error: null,
      });
    } catch (error) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : "Failed to get nutrition information",
      }));
    }
  }, []);

  return {
    ...state,
    getNutritionInfo,
  };
}

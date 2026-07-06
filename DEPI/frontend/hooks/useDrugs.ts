// frontend/hooks/useDrugs.ts
// ─────────────────────────────────────────────────────────────────────────────
// Hook for drug information
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useCallback } from "react";

interface DrugsResponse {
  answer: string;
  language: string;
  source: string;
}

interface DrugsState {
  answer: string | null;
  loading: boolean;
  error: string | null;
}

export function useDrugs(initialAnswer: string | null = null) {
  const [state, setState] = useState<DrugsState>({
    answer: initialAnswer,
    loading: false,
    error: null,
  });

  const getDrugInfo = useCallback(async (query: string, context: string, language: string = "en") => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const response = await fetch("/api/drugs", {
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

      const data: DrugsResponse = await response.json();
      setState({
        answer: data.answer,
        loading: false,
        error: null,
      });
    } catch (error) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : "Failed to get drug information",
      }));
    }
  }, []);

  return {
    ...state,
    getDrugInfo,
  };
}

// frontend/hooks/useRehab.ts
// ─────────────────────────────────────────────────────────────────────────────
// Hook for rehabilitation exercise information
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useCallback } from "react";

interface RehabResponse {
  answer: string;
  language: string;
  source: string;
}

interface RehabState {
  answer: string | null;
  loading: boolean;
  error: string | null;
}

export function useRehab(initialAnswer: string | null = null) {
  const [state, setState] = useState<RehabState>({
    answer: initialAnswer,
    loading: false,
    error: null,
  });

  const getRehabInfo = useCallback(async (query: string, context: string, language: string = "en") => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const response = await fetch("/api/rehab", {
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

      const data: RehabResponse = await response.json();
      setState({
        answer: data.answer,
        loading: false,
        error: null,
      });
    } catch (error) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : "Failed to get rehabilitation information",
      }));
    }
  }, []);

  return {
    ...state,
    getRehabInfo,
  };
}

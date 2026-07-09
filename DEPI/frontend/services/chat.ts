// frontend/services/chat.ts
// ─────────────────────────────────────────────────────────────────────────────
// MedCortex Chat Service
// Handles all API calls to the FastAPI /chat endpoint
// ─────────────────────────────────────────────────────────────────────────────

import api, { API_BASE_URL } from "./api";
import type { DoctorReferral } from "@/lib/extractDoctorReferral";

// ─────────────────────────────────────────────────────────────────────────────
// TYPES — mirror the FastAPI ChatResponse schema exactly
// ─────────────────────────────────────────────────────────────────────────────
export interface Source {
  book: string;
  section: string;
}

export interface LifestyleRecommendations {
  foods_to_eat:           string[];
  foods_to_avoid:         string[];
  drinks_to_have:         string[];
  drinks_to_avoid:        string[];
  exercises_recommended:  string[];
  exercises_to_avoid:     string[];
  rest_recommendation:    string;
}

export interface Doctor {
  name:      string;
  specialty: string;
  address:   string;
  phone:     string;
  npi:       string;
  source:    string;
}

export interface ChatResponse {
  answer:               string;
  suspected_conditions: string[];
  symptoms:             string[];
  sources:              Source[];
  recommendations:      LifestyleRecommendations;
  doctors:              Doctor[];
  conversation_id?:     number | null;
  drugs_answer?:        string | null;
  nutrition_answer?:    string | null;
  rehab_answer?:        string | null;
}

export interface ChatMessage {
  id:        string;
  role:      "user" | "assistant";
  content:   string;
  data?:     ChatResponse;   // only on assistant messages
  doctorReferral?: DoctorReferral | null;
  timestamp: Date;
}

export interface ChatThread {
  id:        string;
  title:     string;
  messages:  ChatMessage[];
  updatedAt: number;
  pinned?:   boolean;
}

// ─────────────────────────────────────────────────────────────────────────────
// API CALLS
// ─────────────────────────────────────────────────────────────────────────────
export async function sendMessage(message: string, unified_context?: any): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>("/chat", { message, unified_context });
  return response.data;
}

export async function uploadFile(file: File, uploadType: string = "document"): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("upload_type", uploadType);

  // Vision pipeline can take up to 90 s (AI_MAX_TIMEOUT_VISION on the backend).
  // The global Axios timeout of 30 s is too short — override it for this call only
  // so the global timeout for chat and other fast endpoints is unaffected.
  const response = await api.post("/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    timeout: 120_000, // 2 minutes — comfortably above the 90 s backend ceiling
  });

  return response.data;
}

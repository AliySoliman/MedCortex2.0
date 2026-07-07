// frontend/services/chat.ts
// ─────────────────────────────────────────────────────────────────────────────
// MedCortex Chat Service
// Handles all API calls to the FastAPI /chat endpoint
// ─────────────────────────────────────────────────────────────────────────────

import axios from "axios";
import type { DoctorReferral } from "@/lib/extractDoctorReferral";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  const token = localStorage.getItem("token");

  const response = await axios.post<ChatResponse>(
    `${API_BASE}/chat`,
    { message, unified_context },
    {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    }
  );

  return response.data;
}

export async function uploadFile(file: File, uploadType: string = "document"): Promise<any> {
  const token = localStorage.getItem("token");
  const formData = new FormData();
  formData.append("file", file);
  formData.append("upload_type", uploadType);

  const response = await axios.post(
    `${API_BASE}/upload`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    }
  );

  return response.data;
}

// frontend/app/api/rehab/route.ts
// ─────────────────────────────────────────────────────────────────────────────
// API route for rehabilitation exercise information
// ─────────────────────────────────────────────────────────────────────────────

import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query, context, language } = body;

    const response = await fetch(
      `${API_BASE_URL}/rehab`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          context: context || "",
          language: language || "en",
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Rehab API error:", error);
    return NextResponse.json(
      { error: "Failed to get rehabilitation information" },
      { status: 500 }
    );
  }
}

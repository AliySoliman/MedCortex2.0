// frontend/app/api/nutrition/route.ts
// ─────────────────────────────────────────────────────────────────────────────
// API route for nutrition plan information
// ─────────────────────────────────────────────────────────────────────────────

import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query, context, language } = body;

    const response = await fetch(
      `${API_BASE_URL}/nutrition`,
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
    console.error("Nutrition API error:", error);
    return NextResponse.json(
      { error: "Failed to get nutrition information" },
      { status: 500 }
    );
  }
}

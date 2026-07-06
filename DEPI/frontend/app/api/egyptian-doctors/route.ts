// frontend/app/api/egyptian-doctors/route.ts
// ─────────────────────────────────────────────────────────────────────────────
// API route for Egyptian doctors search
// ─────────────────────────────────────────────────────────────────────────────

import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query, location, specialty } = body;

    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/egyptian-doctors`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          location,
          specialty,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Egyptian doctors API error:", error);
    return NextResponse.json(
      { error: "Failed to search Egyptian doctors" },
      { status: 500 }
    );
  }
}

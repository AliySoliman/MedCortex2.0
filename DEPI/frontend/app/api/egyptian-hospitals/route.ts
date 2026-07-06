// frontend/app/api/egyptian-hospitals/route.ts
// ─────────────────────────────────────────────────────────────────────────────
// API route for Egyptian hospitals search
// ─────────────────────────────────────────────────────────────────────────────

import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query, userCoordinates, governorate } = body;

    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/egyptian-hospitals`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          userCoordinates,
          governorate,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Egyptian hospitals API error:", error);
    return NextResponse.json(
      { error: "Failed to search Egyptian hospitals" },
      { status: 500 }
    );
  }
}

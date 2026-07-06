import { NextResponse } from "next/server";

export async function POST(request: Request) {
  try {
    const apiKey = process.env.GROQ_API_KEY;
    if (!apiKey) {
      return NextResponse.json(
        { error: "Transcription is not configured (missing GROQ_API_KEY)." },
        { status: 503 }
      );
    }

    const incomingFormData = await request.formData();
    const file = incomingFormData.get("file");

    if (!(file instanceof Blob)) {
      return NextResponse.json(
        { error: "Missing audio file." },
        { status: 400 }
      );
    }

    const mimeType = file.type || "audio/webm";
    const extension = mimeType.includes("ogg") ? "ogg" : "webm";

    const formData = new FormData();
    formData.append("file", file, `recording.${extension}`);
    formData.append("model", "whisper-large-v3-turbo");
    formData.append("response_format", "json");
    formData.append("language", "en");

    const response = await fetch("https://api.groq.com/openai/v1/audio/transcriptions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
      body: formData,
    });

    if (!response.ok) {
      // Surface the upstream error so the UI/log shows the real cause
      // (e.g. 429 quota, 401 bad key) instead of a generic 500.
      const errorText = await response.text().catch(() => "");
      return NextResponse.json(
        { error: `Groq transcription failed (${response.status}). ${errorText}`.trim() },
        { status: response.status }
      );
    }

    const data = (await response.json()) as { text?: string };
    return NextResponse.json({ text: data.text ?? "" });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Transcription failed.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

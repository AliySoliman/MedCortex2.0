import type { ChatResponse, ChatThread } from "@/services/chat";

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function unique(items: string[]): string[] {
  return [...new Set(items.filter(Boolean))];
}

function getAssistantResponses(thread: ChatThread): ChatResponse[] {
  return thread.messages
    .filter((message) => message.role === "assistant" && message.data)
    .map((message) => message.data as ChatResponse);
}

function buildSummary(thread: ChatThread) {
  const responses = getAssistantResponses(thread);
  const latest = responses.at(-1);

  return {
    latest,
    symptoms: unique(responses.flatMap((response) => response.symptoms)),
    conditions: unique(responses.flatMap((response) => response.suspected_conditions)),
    foodsToEat: unique(
      responses.flatMap((response) => response.recommendations.foods_to_eat),
    ),
    foodsToAvoid: unique(
      responses.flatMap((response) => response.recommendations.foods_to_avoid),
    ),
    exercises: unique(
      responses.flatMap((response) => response.recommendations.exercises_recommended),
    ),
    doctors: unique(
      responses.flatMap((response) =>
        response.doctors.map((doctor) => `${doctor.name} — ${doctor.specialty}`),
      ),
    ),
  };
}

function downloadTextFile(filename: string, content: string): void {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function slugify(title: string): string {
  return title.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "chat";
}

export function exportVisitNotes(thread: ChatThread): void {
  const summary = buildSummary(thread);
  const patientMessages = thread.messages
    .filter((message) => message.role === "user")
    .map((message) => `- ${message.content}`);

  const content = [
    `MedCortex Visit Notes`,
    `Conversation: ${thread.title}`,
    `Updated: ${new Date(thread.updatedAt).toLocaleString()}`,
    "",
    "Patient concerns",
    patientMessages.length > 0 ? patientMessages.join("\n") : "- No patient notes recorded.",
    "",
    "Symptoms mentioned",
    summary.symptoms.length > 0 ? summary.symptoms.map((item) => `- ${item}`).join("\n") : "- None",
    "",
    "Flagged conditions",
    summary.conditions.length > 0
      ? summary.conditions.map((item) => `- ${item}`).join("\n")
      : "- None",
    "",
    "Recommended foods",
    summary.foodsToEat.length > 0
      ? summary.foodsToEat.map((item) => `- ${item}`).join("\n")
      : "- None",
    "",
    "Foods to avoid",
    summary.foodsToAvoid.length > 0
      ? summary.foodsToAvoid.map((item) => `- ${item}`).join("\n")
      : "- None",
    "",
    "Recommended exercise",
    summary.exercises.length > 0
      ? summary.exercises.map((item) => `- ${item}`).join("\n")
      : "- None",
    "",
    "Rest recommendation",
    summary.latest?.recommendations.rest_recommendation || "None",
    "",
    "Suggested doctors or clinics",
    summary.doctors.length > 0 ? summary.doctors.map((item) => `- ${item}`).join("\n") : "- None",
    "",
    "Clinical response",
    summary.latest?.answer || "No AI response available.",
  ].join("\n");

  downloadTextFile(`${slugify(thread.title)}-visit-notes.txt`, content);
}

export function exportThreadSummaryAsPdf(thread: ChatThread): void {
  const summary = buildSummary(thread);
  const windowRef = window.open("", "_blank", "noopener,noreferrer");
  if (!windowRef) {
    exportVisitNotes(thread);
    return;
  }

  const renderList = (items: string[]) =>
    items.length > 0
      ? `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
      : "<p>None recorded.</p>";

  const html = `
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>${escapeHtml(thread.title)} - MedCortex Summary</title>
        <style>
          body { font-family: Arial, sans-serif; color: #18181b; margin: 40px; line-height: 1.55; }
          h1, h2 { margin-bottom: 8px; }
          h1 { font-size: 28px; }
          h2 { font-size: 16px; color: #6f4ef2; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 28px; }
          .meta { color: #71717a; margin-bottom: 24px; }
          .card { border: 1px solid #e9e4f7; border-radius: 18px; padding: 18px; margin-top: 12px; }
          ul { margin: 8px 0 0 18px; padding: 0; }
          p { margin: 8px 0; }
        </style>
      </head>
      <body>
        <h1>${escapeHtml(thread.title)}</h1>
        <p class="meta">Exported ${escapeHtml(new Date(thread.updatedAt).toLocaleString())}</p>
        <div class="card">
          <h2>Symptoms</h2>
          ${renderList(summary.symptoms)}
          <h2>Flagged Conditions</h2>
          ${renderList(summary.conditions)}
          <h2>Foods To Eat</h2>
          ${renderList(summary.foodsToEat)}
          <h2>Foods To Avoid</h2>
          ${renderList(summary.foodsToAvoid)}
          <h2>Recommended Exercise</h2>
          ${renderList(summary.exercises)}
          <h2>Suggested Doctors or Clinics</h2>
          ${renderList(summary.doctors)}
          <h2>Clinical Summary</h2>
          <p>${escapeHtml(summary.latest?.answer || "No AI response available.")}</p>
        </div>
      </body>
    </html>
  `;

  windowRef.document.open();
  windowRef.document.write(html);
  windowRef.document.close();
  windowRef.focus();
  windowRef.print();
}

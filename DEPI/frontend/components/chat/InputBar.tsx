"use client";

import { useEffect, useRef, useState, KeyboardEvent } from "react";

import VoiceButton from "@/components/chat/VoiceButton";
import FileUpload from "@/components/chat/FileUpload";

interface Props {
  onSend: (message: string, context?: any) => void;
  disabled: boolean;
}

function getDocumentLabel(context: any) {
  const classification = context?.classification || context?.document_type || context?.modality;
  if (typeof classification === "string" && classification.trim()) {
    return classification;
  }
  return "Medical document";
}

function getDocumentTitle(context: any) {
  const filename = context?.filename;
  const title = context?.document_information?.title;
  if (typeof title === "string" && title.trim()) return title;
  if (typeof filename === "string" && filename.trim()) return filename;
  return "Uploaded document";
}

function buildDocumentSummary(context: any) {
  const findingCount = Array.isArray(context?.clinical_findings) ? context.clinical_findings.length : 0;
  const medCount = Array.isArray(context?.medications) ? context.medications.length : 0;
  const labCount = Array.isArray(context?.lab_values) ? context.lab_values.length : 0;
  const warningCount = Array.isArray(context?.warnings) ? context.warnings.length : 0;

  const parts: string[] = [];
  if (findingCount > 0) parts.push(`${findingCount} finding${findingCount === 1 ? "" : "s"}`);
  if (medCount > 0) parts.push(`${medCount} medication${medCount === 1 ? "" : "s"}`);
  if (labCount > 0) parts.push(`${labCount} lab value${labCount === 1 ? "" : "s"}`);
  if (warningCount > 0) parts.push(`${warningCount} warning${warningCount === 1 ? "" : "s"}`);

  if (parts.length === 0) {
    return "Ready for follow-up questions.";
  }

  return `Detected ${parts.join(" • ")}.`;
}

function buildSuggestedPrompts(context: any) {
  const classification = String(context?.classification || context?.document_type || "").toLowerCase();
  const prompts: string[] = [
    "Summarize this document for me.",
    "What should I pay attention to?",
  ];

  if (classification.includes("prescription")) {
    prompts.unshift("What medications and doses are listed?");
    prompts.push("Are there any safety warnings or interactions?");
  } else if (classification.includes("lab")) {
    prompts.unshift("Which lab results are abnormal?");
    prompts.push("Explain these results in simple terms.");
  } else {
    prompts.unshift("Tell me the key findings from this document.");
  }

  return prompts.slice(0, 4);
}

export default function InputBar({ onSend, disabled }: Props) {
  const [text, setText] = useState("");
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [uploadedContext, setUploadedContext] = useState<any>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 140)}px`;
    }
  }, [text]);

  const handleSend = () => {
    if ((!text.trim() && !uploadedContext) || disabled) return;
    const fallbackPrompt = "Summarize this uploaded medical document and highlight anything important.";
    onSend(text.trim() || fallbackPrompt, uploadedContext);
    setText("");
    setVoiceError(null);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleTranscript = (transcript: string) => {
    setText((prev) => (prev ? `${prev} ${transcript}` : transcript));
    setVoiceError(null);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 140)}px`;
    }
  };

  const handleUploadSuccess = (context: any) => {
    setUploadedContext(context);
    setVoiceError(null);
    textareaRef.current?.focus();
  };

  const suggestedPrompts = uploadedContext ? buildSuggestedPrompts(uploadedContext) : [];

  return (
    <div className="mx-auto w-full max-w-3xl space-y-2">
      {uploadedContext && (
        <div className="rounded-2xl border border-[#e8e1fb] bg-gradient-to-br from-[#faf7ff] via-white to-[#f6f1ff] px-4 py-3 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-[#7b7b88]">
                Document ready
              </p>
              <p className="mt-1 truncate text-sm font-semibold text-[#111]">
                {getDocumentTitle(uploadedContext)}
              </p>
              <p className="mt-1 text-sm text-[#5f5f69]">
                {getDocumentLabel(uploadedContext)} · {buildDocumentSummary(uploadedContext)}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setUploadedContext(null)}
              className="rounded-full px-2 py-1 text-[#7b7b88] transition hover:bg-white hover:text-[#111]"
              aria-label="Clear uploaded document"
            >
              ✕
            </button>
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            {suggestedPrompts.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => {
                  setText(prompt);
                  textareaRef.current?.focus();
                }}
                className="rounded-full border border-[#e4d9ff] bg-white px-3 py-1.5 text-xs font-medium text-[#5d42d4] transition hover:border-[#cdb8ff] hover:bg-[#f8f4ff]"
              >
                {prompt}
              </button>
            ))}
          </div>

          <p className="mt-2 text-xs text-[#8f8f95]">
            Ask a follow-up while this document stays attached, or clear it to start a new topic.
          </p>
        </div>
      )}
      <div
        className="flex items-end gap-2 rounded-2xl border border-[#e4e4ea] bg-[#fafafa] px-4 py-3 shadow-sm transition
                   focus-within:border-[#c5a6ff] focus-within:ring-2 focus-within:ring-[#c5a6ff]/25"
      >
        <FileUpload onUploadSuccess={handleUploadSuccess} disabled={disabled} />
        
        <VoiceButton
          onTranscript={handleTranscript}
          onError={(message) => setVoiceError(message)}
          disabled={disabled}
        />

        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          disabled={disabled}
          placeholder={uploadedContext ? "Ask about this document…" : "Ask me anything…"}
          rows={1}
          className="max-h-36 min-h-[44px] flex-1 resize-none bg-transparent text-sm leading-relaxed text-[#111] outline-none placeholder:text-[#a8a8b0] disabled:opacity-50"
        />

        <button
          type="button"
          onClick={handleSend}
          disabled={((!text.trim() && !uploadedContext) || disabled)}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#6f4ef2] text-base font-bold text-white shadow-md transition hover:bg-[#5d42d4] disabled:cursor-not-allowed disabled:opacity-35"
          aria-label="Send message"
        >
          ↑
        </button>
      </div>

      {voiceError && <p className="mt-1 px-1 text-xs text-red-500">{voiceError}</p>}

      <p className="text-center text-xs text-[#8f8f95]">
        MedCortex is for educational purposes only — not a substitute for professional medical advice.
      </p>
    </div>
  );
}

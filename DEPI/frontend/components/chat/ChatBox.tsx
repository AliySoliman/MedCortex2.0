"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Download, FileText } from "lucide-react";
import MessageBubble from "./MessageBubble";
import InputBar from "./InputBar";
import ResponseCard from "./ResponseCard";
import { sendMessage, type ChatMessage } from "@/services/chat";
import { useUserLocation } from "@/hooks/useUserLocation";
import { extractDoctorReferral } from "@/lib/extractDoctorReferral";

interface ChatBoxProps {
  threadId: string;
  threadTitle: string;
  messages: ChatMessage[];
  firstName: string;
  onCommitMessages: (threadId: string, messages: ChatMessage[]) => void;
  onFirstUserMessageTitle: (threadId: string, title: string) => void;
  onExportPdf: () => void;
  onExportVisitNotes: () => void;
}

export default function ChatBox({
  threadId,
  threadTitle,
  messages,
  firstName,
  onCommitMessages,
  onFirstUserMessageTitle,
  onExportPdf,
  onExportVisitNotes,
}: ChatBoxProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const { coordinates } = useUserLocation();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, threadId]);

  const handleSend = useCallback(
    async (text: string, context?: any) => {
      if ((!text.trim() && !context) || isLoading) return;
      setError(null);

      const wasEmpty = messages.length === 0;
      if (wasEmpty) {
        onFirstUserMessageTitle(threadId, text.trim() || "Document Upload");
      }

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text.trim() || "Analyzed medical document.",
        timestamp: new Date(),
      };
      const withUser = [...messages, userMsg];
      onCommitMessages(threadId, withUser);
      setIsLoading(true);

      try {
        const response = await sendMessage(text.trim() || "Analyzed medical document.", context);
        const { referral, cleanText } = extractDoctorReferral(response.answer);
        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: cleanText,
          data: {
            ...response,
            answer: cleanText,
          },
          doctorReferral: referral,
          timestamp: new Date(),
        };
        onCommitMessages(threadId, [...withUser, assistantMsg]);
      } catch (err: unknown) {
        const data = (err as { response?: { data?: any } })?.response?.data;
        let message = "Something went wrong. Please try again.";
        
        if (data) {
          if (typeof data.detail === "string") {
            message = data.detail;
          } else if (Array.isArray(data.detail)) {
            message = data.detail.map((d: any) => `${d.loc?.join(".") || "error"}: ${d.msg || "invalid value"}`).join(", ");
          } else if (data.detail && typeof data.detail === "object") {
            message = JSON.stringify(data.detail);
          } else if (data.error) {
            message = data.error;
          }
        }
        setError(message);
      } finally {
        setIsLoading(false);
      }
    },
    [
      isLoading,
      messages,
      onCommitMessages,
      onFirstUserMessageTitle,
      threadId,
    ],
  );

  const empty = messages.length === 0;

  return (
    <div className="flex h-full min-h-0 flex-col bg-white">
      <header className="flex shrink-0 items-center justify-between gap-3 border-b border-[#ebebef] px-5 py-3.5">
        <div className="flex min-w-0 items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#f4eeff] text-sm text-[#6f4ef2]">
            ✦
          </div>
          <div className="min-w-0">
            <span className="block truncate text-lg font-medium tracking-tight text-[#111]">
              {messages.length > 0 ? threadTitle : "MedCortex"}
            </span>
            {messages.length > 0 ? (
              <span className="text-xs text-[#8f8f95]">Conversation exports ready</span>
            ) : null}
          </div>
        </div>
        {messages.length > 0 ? (
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onExportVisitNotes}
              className="inline-flex items-center gap-2 rounded-xl border border-[#e8e1fb] bg-[#faf7ff] px-3 py-2 text-xs font-medium text-[#6f4ef2] transition hover:bg-[#f4eeff]"
            >
              <FileText className="h-4 w-4" strokeWidth={2} />
              Visit Notes
            </button>
            <button
              type="button"
              onClick={onExportPdf}
              className="inline-flex items-center gap-2 rounded-xl border border-[#ebebef] bg-white px-3 py-2 text-xs font-medium text-[#3a3a42] transition hover:border-[#d8cdf6] hover:text-[#6f4ef2]"
            >
              <Download className="h-4 w-4" strokeWidth={2} />
              Export PDF
            </button>
          </div>
        ) : null}
      </header>

      <div className="relative min-h-0 flex-1 overflow-y-auto">
        {empty ? (
          <div className="flex min-h-[calc(100%-1rem)] flex-col items-center justify-center px-6 pb-32 pt-10">
            <div
              className="mb-8 h-28 w-28 rounded-full bg-[radial-gradient(circle_at_35%_30%,#faf5ff_0%,#e9dfff_28%,#d9c5ff_52%,#c5a6ff_72%,rgba(197,166,255,0.15)_100%)] shadow-[0_20px_60px_rgba(111,78,242,0.22)]"
              aria-hidden
            />
            <p className="text-center text-lg font-medium text-[#6f4ef2]">
              Hello, {firstName}
            </p>
            <h1 className="mt-1 text-center text-3xl font-semibold tracking-tight text-[#111] sm:text-4xl">
              How are you feeling today?
            </h1>
            <p className="mt-4 max-w-md text-center text-sm text-[#6b6b76]">
              Describe your symptoms or health questions below. Your conversations are saved in
              History so you can pick them up anytime.
            </p>
          </div>
        ) : (
          <div className="space-y-5 px-4 py-6 md:px-8">
            {messages.map((msg, index) => {
              const prevMsg = index > 0 ? messages[index - 1] : null;
              const userQuery = prevMsg?.role === "user" ? prevMsg.content : undefined;
              return (
                <AssistantMessageGroup
                  key={msg.id}
                  message={msg}
                  coordinates={coordinates}
                  userQuery={userQuery}
                />
              );
            })}

            {isLoading && (
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#f4eeff] text-sm text-[#6f4ef2]">
                  ✦
                </div>
                <div className="flex items-center gap-1.5 rounded-2xl border border-[#ebebef] bg-[#fafafa] px-4 py-3">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-[#ae84ff] [animation-delay:0ms]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-[#ae84ff] [animation-delay:150ms]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-[#ae84ff] [animation-delay:300ms]" />
                  <span className="ml-2 text-xs text-[#8f8f95]">Analysing…</span>
                </div>
              </div>
            )}

            {error && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="shrink-0 border-t border-[#ebebef] bg-white px-4 pb-4 pt-3 md:px-8">
        <InputBar onSend={handleSend} disabled={isLoading} />
      </div>
    </div>
  );
}

function AssistantMessageGroup({
  message,
  coordinates,
  userQuery,
}: {
  message: ChatMessage;
  coordinates: { lat: number; lng: number } | null;
  userQuery?: string;
}) {
  if (message.role !== "assistant") {
    return <MessageBubble message={message} />;
  }

  if (message.data) {
    return (
      <div className="md:ml-11">
        <ResponseCard
          data={message.data}
          referral={message.doctorReferral ?? null}
          coordinates={coordinates}
          userQuery={userQuery}
        />
      </div>
    );
  }

  return (
    <MessageBubble message={message} />
  );
}

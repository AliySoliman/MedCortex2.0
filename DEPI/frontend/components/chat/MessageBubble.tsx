"use client";

import type { ChatMessage } from "@/services/chat";

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex items-end gap-2.5 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#f4eeff] text-sm text-[#6f4ef2] shadow-sm">
          ✦
        </div>
      )}

      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-line ${
          isUser
            ? "rounded-br-sm bg-[#0d0d0d] text-white"
            : "rounded-bl-sm border border-[#ebebef] bg-white text-[#1a1a1a] shadow-sm"
        }`}
      >
        <FormattedText text={message.content} variant={isUser ? "user" : "assistant"} />

        <p
          className={`mt-1.5 text-xs opacity-50 ${isUser ? "text-right text-white" : "text-[#6b6b76]"}`}
        >
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </p>
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#eaeaf0] text-sm">
          👤
        </div>
      )}
    </div>
  );
}

function FormattedText({
  text,
  variant,
}: {
  text: any;
  variant: "user" | "assistant";
}) {
  const safeText = typeof text === "string" ? text : (text ? JSON.stringify(text) : "");
  const parts = safeText.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return (
            <strong
              key={i}
              className={
                variant === "user" ? "font-semibold text-white" : "font-semibold text-[#111]"
              }
            >
              {part.slice(2, -2)}
            </strong>
          );
        }
        if (part.startsWith("*") && part.endsWith("*")) {
          return (
            <em
              key={i}
              className={variant === "user" ? "italic text-white/90" : "italic text-[#5c5c66]"}
            >
              {part.slice(1, -1)}
            </em>
          );
        }
        return (
          <span key={i} className={variant === "user" ? "text-white" : "text-[#1a1a1a]"}>
            {part}
          </span>
        );
      })}
    </>
  );
}

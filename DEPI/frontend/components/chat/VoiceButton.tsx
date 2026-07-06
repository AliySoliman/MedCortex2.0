"use client";

import { useSpeechToText } from "@/hooks/useSpeechToText";

interface VoiceButtonProps {
  onTranscript: (text: string) => void;
  onError: (message: string) => void;
  disabled?: boolean;
}

function MicrophoneIcon({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={className}
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z M19 10v2a7 7 0 0 1-14 0v-2 M12 19v3 M8 22h8" />
    </svg>
  );
}

function StopIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true">
      <rect x="4" y="4" width="16" height="16" rx="2" fill="white" />
    </svg>
  );
}

export default function VoiceButton({
  onTranscript,
  onError,
  disabled = false,
}: VoiceButtonProps) {
  const { status, startRecording, stopRecording } = useSpeechToText({
    onTranscript,
    onError,
  });

  const isDisabled = disabled || status === "processing";
  const handleClick = () => {
    if (status === "recording") {
      stopRecording();
      return;
    }

    void startRecording();
  };

  let title = "Start recording";
  let className =
    "relative flex items-center justify-center w-10 h-10 rounded-full transition-all duration-200 outline-none focus:ring-2 focus:ring-[#6f4ef2]/50 text-[#6f4ef2]";
  let content = <MicrophoneIcon className="h-5 w-5" />;

  if (status === "requesting") {
    title = "Requesting microphone access...";
    className += " opacity-50 cursor-not-allowed";
  } else if (status === "recording") {
    title = "Stop recording";
    className += " bg-[#ef4444] text-white animate-pulse";
    content = <StopIcon />;
  } else if (status === "processing") {
    title = "Transcribing...";
    className += " cursor-not-allowed text-[#6f4ef2]/70";
    content = (
      <span
        className="h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent"
        aria-hidden="true"
      />
    );
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isDisabled}
      title={title}
      aria-label={title}
      className={className}
    >
      {content}
    </button>
  );
}

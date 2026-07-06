"use client";

import { useRef, useState } from "react";

type SpeechToTextStatus = "idle" | "requesting" | "recording" | "processing";

interface UseSpeechToTextOptions {
  onTranscript: (text: string) => void;
  onError: (message: string) => void;
}

export function useSpeechToText({
  onTranscript,
  onError,
}: UseSpeechToTextOptions) {
  const [status, setStatus] = useState<SpeechToTextStatus>("idle");
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<BlobPart[]>([]);
  const mimeTypeRef = useRef("audio/webm");

  const transcribe = async (audioBlob: Blob, mimeType: string) => {
    try {
      const extension = mimeType.includes("ogg") ? "ogg" : "webm";
      const file = new File([audioBlob], `recording.${extension}`, { type: mimeType });
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/transcribe", {
        method: "POST",
        body: formData,
      });

      const data = (await response.json()) as { text?: string; error?: string };

      if (!response.ok || !data.text) {
        throw new Error(data.error || "Transcription failed");
      }

      onTranscript(data.text);
      setStatus("idle");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to transcribe your recording.";
      onError(message);
      setStatus("idle");
    }
  };

  const startRecording = async () => {
    if (typeof window === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      onError("Your browser does not support audio recording.");
      return;
    }

    try {
      setStatus("requesting");

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const preferredMimeType = MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : MediaRecorder.isTypeSupported("audio/ogg")
          ? "audio/ogg"
          : "";

      const recorder = preferredMimeType
        ? new MediaRecorder(stream, { mimeType: preferredMimeType })
        : new MediaRecorder(stream);

      mimeTypeRef.current = recorder.mimeType || preferredMimeType || "audio/webm";
      audioChunks.current = [];
      mediaRecorder.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(audioChunks.current, {
          type: mimeTypeRef.current || recorder.mimeType || "audio/webm",
        });

        audioChunks.current = [];
        mediaRecorder.current = null;
        stream.getTracks().forEach((track) => track.stop());
        setStatus("processing");
        void transcribe(blob, mimeTypeRef.current || recorder.mimeType || "audio/webm");
      };

      recorder.start();
      setStatus("recording");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to access your microphone.";
      onError(message);
      setStatus("idle");
    }
  };

  const stopRecording = () => {
    if (status === "recording" && mediaRecorder.current) {
      mediaRecorder.current.stop();
    }
  };

  return { status, startRecording, stopRecording };
}

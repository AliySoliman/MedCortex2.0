// frontend/components/chat/FileUpload.tsx
"use client";

import { useRef, useState } from "react";
import { uploadFile } from "@/services/chat";

interface Props {
  onUploadSuccess: (context: any) => void;
  disabled?: boolean;
}

export default function FileUpload({ onUploadSuccess, disabled }: Props) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setIsUploading(true);
      setError(null);
      const data = await uploadFile(file);
      if (data.status === "success" && data.unified_context) {
        onUploadSuccess(data.unified_context);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to upload and process document");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <div className="relative flex items-center">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        disabled={disabled || isUploading}
        accept="image/*,application/pdf"
      />
      <button
        type="button"
        onClick={() => fileInputRef.current?.click()}
        disabled={disabled || isUploading}
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition ${
          isUploading ? "animate-pulse bg-[#e0d6ff] text-[#6f4ef2]" : "bg-transparent text-[#6f4ef2] hover:bg-[#f4efff]"
        } disabled:cursor-not-allowed disabled:opacity-50`}
        aria-label="Upload document or image"
        title="Upload Medical Document"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
          className="h-5 w-5"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
      </button>
      {error && (
        <div className="absolute bottom-12 left-0 w-48 rounded bg-red-100 p-2 text-xs text-red-600 shadow">
          {error}
        </div>
      )}
    </div>
  );
}

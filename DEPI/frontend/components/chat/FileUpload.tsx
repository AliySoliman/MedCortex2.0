// frontend/components/chat/FileUpload.tsx
"use client";

import { useRef, useState, useEffect } from "react";
import { uploadFile } from "@/services/chat";

interface Props {
  onUploadSuccess: (context: any) => void;
  disabled?: boolean;
}

export default function FileUpload({ onUploadSuccess, disabled }: Props) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [currentUploadType, setCurrentUploadType] = useState<string>("document");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setIsUploading(true);
      setError(null);
      const data = await uploadFile(file, currentUploadType);
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

  const handleOptionClick = (type: string) => {
    setCurrentUploadType(type);
    setIsOpen(false);
    fileInputRef.current?.click();
  };

  return (
    <div className="relative flex items-center" ref={dropdownRef}>
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
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || isUploading}
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition ${
          isUploading ? "animate-pulse bg-[#e0d6ff] text-[#6f4ef2]" : "bg-transparent text-[#6f4ef2] hover:bg-[#f4efff]"
        } disabled:cursor-not-allowed disabled:opacity-50`}
        aria-label="Upload document or image"
        title="Upload File"
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

      {isOpen && (
        <div className="absolute bottom-12 left-0 z-50 w-48 rounded-xl border border-[#e8e1fb] bg-white p-1 shadow-lg">
          <button
            onClick={() => handleOptionClick("document")}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm font-medium text-[#111] hover:bg-[#f4efff] hover:text-[#6f4ef2]"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            Lab Report / Rx
          </button>
          <button
            onClick={() => handleOptionClick("medical_image")}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm font-medium text-[#111] hover:bg-[#f4efff] hover:text-[#6f4ef2]"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Medical Image
          </button>
        </div>
      )}

      {error && (
        <div className="absolute bottom-12 left-0 z-50 w-48 rounded bg-red-100 p-2 text-xs text-red-600 shadow">
          {error}
        </div>
      )}
    </div>
  );
}

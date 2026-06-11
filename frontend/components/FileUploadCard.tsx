"use client"

import { useState, useRef } from "react"

interface Props {
  title: string
  accept: string
  description: string
  onUpload: (file: File) => Promise<void>
}

export default function FileUploadCard({
  title,
  accept,
  description,
  onUpload,
}: Props) {
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [fileName, setFileName] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    setFileName(file.name)
    setUploading(true)
    try {
      await onUpload(file)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div
      className={`rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
        dragOver
          ? "border-blue-400 bg-blue-50"
          : "border-zinc-200 bg-white hover:border-zinc-300"
      }`}
      onDragOver={(e) => {
        e.preventDefault()
        setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragOver(false)
        const file = e.dataTransfer.files[0]
        if (file) handleFile(file)
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) handleFile(file)
        }}
      />

      <div className="mb-3 text-3xl text-zinc-300">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="mx-auto h-10 w-10"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
      </div>

      <h3 className="mb-1 text-lg font-semibold text-zinc-800">{title}</h3>
      <p className="mb-4 text-sm text-zinc-500">{description}</p>

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={uploading}
        className="rounded-lg bg-zinc-900 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:opacity-50"
      >
        {uploading ? "Uploading..." : "Choose File"}
      </button>

      {fileName && (
        <p className="mt-3 text-sm text-zinc-600">
          Selected: <span className="font-medium">{fileName}</span>
        </p>
      )}
    </div>
  )
}

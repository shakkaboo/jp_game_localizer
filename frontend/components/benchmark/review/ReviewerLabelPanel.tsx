"use client"

import { useState } from "react"

interface Props {
  reviewerLabel: string
  onLabelChange: (label: string) => void
}

function normalizeLabel(label: string): string {
  return label.trim().replace(/\s+/g, " ")
}

const STORAGE_KEY = "benchmark_reviewer_label"

export default function ReviewerLabelPanel({ reviewerLabel, onLabelChange }: Props) {
  const [localValue, setLocalValue] = useState(reviewerLabel)

  const handleBlur = () => {
    const normalized = normalizeLabel(localValue)
    setLocalValue(normalized)
    onLabelChange(normalized)
    localStorage.setItem(STORAGE_KEY, normalized)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleBlur()
    }
  }

  if (!reviewerLabel) {
    return (
      <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-6">
        <h2 className="mb-2 text-base font-semibold text-amber-800">
          Enter Your Reviewer Label
        </h2>
        <p className="mb-4 text-sm text-amber-700">
          Provide a label to identify your reviews. This is persisted locally.
        </p>
        <input
          type="text"
          value={localValue}
          onChange={(e) => setLocalValue(e.target.value)}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          placeholder="e.g. reviewer-1"
          className="w-full max-w-xs rounded-lg border border-amber-300 bg-white px-4 py-2 text-sm text-zinc-800 placeholder-zinc-400"
        />
      </div>
    )
  }

  return (
    <div className="mb-6 flex items-center gap-3 rounded-xl border border-zinc-200 bg-white px-5 py-3">
      <span className="text-sm text-zinc-500">Reviewer:</span>
      <input
        type="text"
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        className="flex-1 rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-800"
      />
      <span className="text-xs text-zinc-400">saved locally</span>
    </div>
  )
}

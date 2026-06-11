"use client"

import type { ChunkItem } from "@/types"
import StatusBadge from "./StatusBadge"

interface Props {
  chunk: ChunkItem
  onTranslate: (id: number) => void
  onReview: (id: number) => void
  translating: boolean
}

export default function ProgressCard({
  chunk,
  onTranslate,
  onReview,
  translating,
}: Props) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-zinc-200 bg-white p-5">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-3">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-zinc-100 text-xs font-bold text-zinc-500">
            {chunk.chunk_number}
          </span>
          <h3 className="truncate text-base font-semibold text-zinc-800">
            {chunk.chunk_title}
          </h3>
          <StatusBadge status={chunk.status} />
        </div>
        {chunk.scene_hint && (
          <p className="mt-1 ml-10 text-sm text-zinc-500">
            Scene: {chunk.scene_hint}
            {chunk.lines_count != null && ` · ${chunk.lines_count} lines`}
          </p>
        )}
      </div>

      <div className="ml-4 flex shrink-0 gap-2">
        <button
          type="button"
          onClick={() => onTranslate(chunk.id)}
          disabled={translating}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:opacity-50"
        >
          {translating ? "Translating..." : "Translate"}
        </button>
        <button
          type="button"
          onClick={() => onReview(chunk.id)}
          className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
        >
          Review
        </button>
      </div>
    </div>
  )
}
